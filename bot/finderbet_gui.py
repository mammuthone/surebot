import socket
import subprocess
import threading
import time
import os
import sys
import json
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
                            QTabWidget, QSplitter, QGridLayout, QStatusBar, QMessageBox, QFrame,
                            QComboBox, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QColor, QFont
from android_manager import AndroidManager


# Configurazione server
HOST = "127.0.0.1"
PORT = 9999

def parse_float(value):
    """
    Converte in modo sicuro un valore a float
    
    Args:
    value: Valore da convertire
    
    Returns:
    float: Valore convertito o 0 se non convertibile
    """
    try:
        # Rimuovi eventuali spazi, virgole, sostituisci virgola con punto
        if isinstance(value, str):
            value = value.replace(',', '.').strip()
        
        # Converti a float
        return float(value)
    except (ValueError, TypeError):
        print(f"Impossibile convertire {value} a float")
        return 0.0

class SocketWorker(QObject):
    """Classe per gestire le comunicazioni socket in un thread separato"""
    message_received = pyqtSignal(str)
    client_connected = pyqtSignal(str)
    client_disconnected = pyqtSignal(str)
    server_started = pyqtSignal()
    server_error = pyqtSignal(str)
    decoded_data = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.server = None
        self.clients = []
        self.running = False
        self.received_data = []

    def start_server(self):
        """Avvia il socket server"""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((HOST, PORT))
            self.server.listen(5)
            self.running = True
            self.server_started.emit()
            
            while self.running:
                try:
                    self.server.settimeout(1)  # Timeout di 1 secondo per permettere stop gradevole
                    client_socket, addr = self.server.accept()
                    self.clients.append(client_socket)
                    self.client_connected.emit(f"{addr[0]}:{addr[1]}")
                    
                    # Avvia un thread per gestire questo client
                    client_thread = threading.Thread(target=self.handle_client, 
                                                    args=(client_socket, addr))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # Ignora errori durante lo shutdown
                        self.server_error.emit(str(e))
                        
        except Exception as e:
            self.server_error.emit(str(e))
            
    def handle_client(self, client_socket, addr):
        """Gestisce la comunicazione con un client"""
        addr_str = f"{addr[0]}:{addr[1]}"
        
        while self.running:
            try:
                data = client_socket.recv(4096).decode()
                if not data:
                    break
                print(data)
                self.message_received.emit(f"Da {addr_str}: {data}")
                
                # Prova a interpretare i dati come JSON
                try:
                    json_data = json.loads(data)
                    if "action" in json_data and (json_data["action"] == "DECODED_ITEMS" or json_data["action"] == "NEW_BET"):
                        if "data" in json_data:
                            self.decoded_data.emit(json_data["data"])
                            response = json.dumps({"status": "success", "message": "Dati ricevuti"})
                        else:
                            response = json.dumps({"status": "error", "message": "Nessun dato trovato"})
                    else:
                        self.decoded_data.emit(json_data)
                        response = json.dumps({"status": "success", "message": "Comando ricevuto"})
                except json.JSONDecodeError:
                    response = json.dumps({"status": "error", "message": "Formato JSON non valido"})
                
                # Invia la risposta
                print('invio al server')
                client_socket.send(response.encode())
                
            except ConnectionResetError:
                break
            except Exception as e:
                self.message_received.emit(f"Errore con {addr_str}: {str(e)}")
                break
                
        # Clean up
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()
        self.client_disconnected.emit(addr_str)
    
    def stop_server(self):
        """Ferma il server socket"""
        self.running = False
        
        # Chiude tutte le connessioni client
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients = []
        
        # Chiude il server
        if self.server:
            try:
                self.server.close()
            except:
                pass
            self.server = None

class SubprocessManager:
    """Gestisce l'avvio e l'arresto del subprocess finderbet"""
    def __init__(self, interval=600):
        self.interval = interval  # Intervallo in secondi
        self.process = None
        self.running = False
        self.thread = None
    
    def start(self):
        """Avvia il thread che eseguirà il subprocess periodicamente"""
        if self.thread and self.thread.is_alive():
            return False  # Già in esecuzione
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def _run_loop(self):
        """Loop che esegue il subprocess"""
        while self.running:
            self._start_process()
            # Aspetta per l'intervallo specificato o fino a quando running diventa False
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _start_process(self):
        """Avvia un singolo processo"""
        if self.process and self.process.poll() is None:
            # Termina il processo precedente se ancora in esecuzione
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        
        try:
            self.process = subprocess.Popen(["python3", "finderbet_v4.py"])
            return True
        except Exception as e:
            print(f"Errore nell'avvio del subprocess: {e}")
            return False
    
    def stop(self):
        """Ferma il thread e il subprocess"""
        self.running = False
        
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        
        self.process = None
        # Il thread si fermerà da solo quando running è False

class FinderbetGUI(QMainWindow):
    """Finestra principale dell'applicazione FinderBet"""
    def __init__(self):
        super().__init__()
        
        # Inizializza i manager
        self.socket_worker = SocketWorker()
        self.subprocess_mgr = SubprocessManager(interval=600)
        
        # Configura i segnali
        self.setup_signals()
        
        self.android_mgr = AndroidManager(message_callback=self.display_message)

        # Imposta l'interfaccia grafica
        self.init_ui()
        
        # Stato iniziale
        self.server_running = False
        self.subprocess_running = False
        self.bet_data = []
        
        # Timer per aggiornare l'orario
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Aggiorna ogni secondo
        
    def setup_signals(self):
        """Configura i segnali tra i thread e l'interfaccia"""
        # Segnali del socket worker
        self.socket_worker.message_received.connect(self.display_message)
        self.socket_worker.client_connected.connect(self.client_connected)
        self.socket_worker.client_disconnected.connect(self.client_disconnected)
        self.socket_worker.server_started.connect(self.server_started)
        self.socket_worker.server_error.connect(self.server_error)
        self.socket_worker.decoded_data.connect(self.process_decoded_data)
        
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Configurazione finestra principale
        self.setWindowTitle("FinderBet - Analizzatore di Scommesse")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header con informazioni e controlli
        header_layout = QHBoxLayout()
        
        # Informazioni server
        server_info = QWidget()
        server_layout = QVBoxLayout(server_info)
        self.server_status = QLabel("Server: SPENTO")
        self.server_status.setStyleSheet("color: red; font-weight: bold;")
        
        self.time_label = QLabel(f"Ora: {datetime.now().strftime('%H:%M:%S')}")
        
        server_controls = QHBoxLayout()
        self.server_btn = QPushButton("Avvia Server")
        self.server_btn.clicked.connect(self.toggle_server)
        
        server_controls.addWidget(self.server_btn)
        server_layout.addWidget(self.server_status)
        server_layout.addWidget(self.time_label)
        server_layout.addLayout(server_controls)
        
        # Informazioni subprocess
        subprocess_info = QWidget()
        subprocess_layout = QVBoxLayout(subprocess_info)
        self.subprocess_status = QLabel("Bot: SPENTO")
        self.subprocess_status.setStyleSheet("color: red; font-weight: bold;")
        
        self.last_run = QLabel("Ultimo avvio: -")
        
        subprocess_controls = QVBoxLayout()
        self.subprocess_btn = QPushButton("Avvia Bot")
        self.subprocess_btn_import = QPushButton("Importa dati")
        self.subprocess_btn.clicked.connect(self.toggle_subprocess)
        self.subprocess_btn_import.clicked.connect(self.start_import_data)
        
        subprocess_controls.addWidget(self.subprocess_btn)
        subprocess_controls.addWidget(self.subprocess_btn_import)
        subprocess_layout.addWidget(self.subprocess_status)
        subprocess_layout.addWidget(self.last_run)
        subprocess_layout.addLayout(subprocess_controls)
        
        # Aggiungi widget al layout dell'header
        header_layout.addWidget(server_info)
        header_layout.addWidget(subprocess_info)
        
        # Tab per le varie visualizzazioni
        self.tabs = QTabWidget()

        
        # Tab scommesse
        self.bets_tab = QWidget()
        bets_layout = QHBoxLayout(self.bets_tab)
        left_widget = QFrame()
        left_layout = QVBoxLayout(left_widget)
        # Controlli di filtro
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtra per:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tutte le scommesse", "Solo calcio", "Solo tennis", "Solo basket"])
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_combo)
        left_layout.addLayout(filter_layout)

        # Aggiungi altri controlli di filtro se necessario
        
        bets_layout.addLayout(filter_layout)
        
        # Tabella scommesse
        self.bets_table = QTableWidget()
        self.bets_table.setColumnCount(5)
        self.bets_table.setHorizontalHeaderLabels(["Bet_id", "Sport","ROI", "Bookmaker1", "Bookmaker2"])
        self.bets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.bets_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # self.bets_table.itemSelectionChanged.connect(self.show_bet_details)
        self.bets_table.cellClicked.connect(self.show_bet_details)

        left_layout.addWidget(self.bets_table) 

        play_btn = QPushButton("Gioca Ora!")        
        play_btn.setObjectName("play_button")


        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)

        self.bet_details_widget = QTextEdit()
        self.bet_details_widget.setReadOnly(True)
        self.bet_details_widget.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 10px;
            }
        """)

        details_layout.addWidget(self.bet_details_widget)
        details_layout.addWidget(play_btn)

        # Aggiungi un titolo per i dettagli
        details_title = QLabel("Dettagli Scommessa")
        details_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        right_widget = QFrame()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(details_title)
        right_layout.addWidget(self.details_widget)
        
        # Aggiungi i widget al layout principale
        bets_layout.addWidget(left_widget, 2)  # Larghezza 2 parti
        bets_layout.addWidget(right_widget, 1)  # Larghezza 1 parte        
        # Tab log
        self.log_tab = QWidget()
        log_layout = QVBoxLayout(self.log_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        

        self.android_tab = QWidget()
        android_layout = QVBoxLayout(self.android_tab)
        # Aggiungi i tab
        self.tabs.addTab(self.bets_tab, "Scommesse")
        self.tabs.addTab(self.log_tab, "Log")
        self.tabs.addTab(self.android_tab, "Android device")
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Pronto")
        
        # Aggiungi i layout principali
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.tabs)
        
    def check_bookmaker_file(self, bookmaker_name):
        """Verifica l'esistenza del file del bookmaker"""
        bookmakers_dir = '../bookmakers/'
        file_path = os.path.join(bookmakers_dir, f'''{bookmaker_name.lower()}.py''')
        print(file_path)
        print(bookmaker_name.lower())
        return os.path.exists(file_path)

    def show_bet_details(self, row, column):
        """Mostra i dettagli della riga selezionata"""
        # Ottieni le righe selezionate
        selected_rows = self.bets_table.selectedIndexes()

        if not selected_rows:
            self.bet_details_widget.clear()
            return
    
        button = self.details_widget.findChild(QPushButton, "play_button")
        button.disconnect()
        button.clicked.connect(lambda: self.play_now(row, column))

        # Prendi la prima riga selezionata
        row = selected_rows[0].row()
        print(self.bets_table.item(row,0).text())
        try:
            # Leggi l'intero file JSON
            with open('decoded_items.json', 'r') as file:
                all_items = json.load(file)
        
            # Recupera l'elemento specifico
            # Questo è un esempio, dovrai adattarlo al formato esatto del tuo JSON
            selected_item = None
            for item in all_items:
                # Criteri di ricerca - adatta secondo il tuo formato
                # Esempio: se hai un campo 'id' o un identificatore univoco
                if item.get('bet_id') == self.bets_table.item(row, 0).text():
                    selected_item = item
                    break
            
            if selected_item:
                # Formatta i dettagli in HTML
                details_html = "<h2>Dettagli Completi Scommessa</h2><hr>"
                
                # Aggiungi tutti i campi disponibili
                for key, value in selected_item.items():
                    # Gestisci casi speciali come liste o dizionari nidificati
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value, indent=2)
                    
                    details_html += f"<b>{key}:</b> {value}<br>"
                
                # Gestisci array specifici in modo più dettagliato
                if 'bookmakers' in selected_item:
                    details_html += "<h3>Bookmakers:</h3>"
                    for bm in selected_item['bookmakers']:
                        details_html += f"<b>{bm.get('bname', 'N/A')}:</b> {bm.get('value', 'N/A')}<br>"
                
                if 'items' in selected_item:
                    details_html += "<h3>Items:</h3>"
                    for item in selected_item['items']:
                        details_html += f"<b>{item.get('bname', 'N/A')}:</b> {item.get('value', 'N/A')}<br>"
                
                # Imposta il testo HTML
                self.bet_details_widget.setHtml(details_html)
            else:
                self.bet_details_widget.setHtml("<h2>Dettagli non trovati</h2>")
        
        except FileNotFoundError:
            self.bet_details_widget.setHtml("<h2>File decoded_items.json non trovato</h2>")
        except json.JSONDecodeError:
            self.bet_details_widget.setHtml("<h2>Errore nel parsing del file JSON</h2>")
        except Exception as e:
            self.bet_details_widget.setHtml(f"<h2>Errore: {str(e)}</h2>")

         
        details = f"""
            <h2>Dettagli Scommessa</h2>
            <hr>
            <b>BetID:</b> {self.bets_table.item(row, 0).text() if self.bets_table.item(row, 0) else 'N/A'}
            <br>
            <b>Sport:</b> {self.bets_table.item(row, 1).text() if self.bets_table.item(row, 1) else 'N/A'}
            <br>
            <b>ROI:</b> {self.bets_table.item(row, 2).text() if self.bets_table.item(row, 2) else 'N/A'}
            <br>
            <b>Bookmaker 1:</b> {self.bets_table.item(row, 3).text() if self.bets_table.item(row, 3) else 'N/A'}
            <br>
            <b>Bookmaker 2:</b> {self.bets_table.item(row, 4).text() if self.bets_table.item(row, 4) else 'N/A'}
            <br>
            """
        
        if(column == 3 or column == 4):
            importo1, importo2, roi =  self.calcola_arbitraggio(self.bet_data[row]["b1_data"]["value"], self.bet_data[row]["b2_data"]["value"])
            importotondo1, importotondo2, roitondo =  self.calcola_arbitraggio_tondi(self.bet_data[row]["b1_data"]["value"], self.bet_data[row]["b2_data"]["value"])
            details = f"""
                <h2>{self.bets_table.item(row, column).text()}</h2>
                <hr>
            <br>

                <b>BetID:</b> {self.bets_table.item(row, 0).text() if self.bets_table.item(row, 0) else 'N/A'}
            <br>


                <ul>
                    <li><b>Evento</b>: {
                        self.bet_data[row]["b1_data"]["evento"] if column % 2 == 1 
                        else self.bet_data[row]["b2_data"]["evento"]
                    }</li>
                    <li><b>Quota</b>: {
                        self.bet_data[row]["b1_data"]["value"] if column % 2 == 1
                        else self.bet_data[row]["b2_data"]["value"]
                    }</li>
                    <li><b>Gruppo</b>: {
                        self.bet_data[row]["b1_data"]["gruppo"] if column % 2 == 1 
                        else self.bet_data[row]["b2_data"]["gruppo"]
                    }</li>
                    <li><b>Descrizione</b>: {
                        self.bet_data[row]["b1_data"]["desc"] if column % 2 == 1
                        else self.bet_data[row]["b2_data"]["desc"]
                    }</li>
                    <li>
                        <b>Arbitraggio</b>: {
                            self.calcola_arbitraggio(self.bet_data[row]["b1_data"]["value"], self.bet_data[row]["b2_data"]["value"])
                        }
                    </li>
                    <li>
                        <b>Quota suggerita</b>: {
                            importo1 if column % 2 == 0
                            else importo2
                        }
                    </li>
                    <li>
                        <b>Quota tonda suggerita</b>: {
                            importotondo1 if column % 2 == 0
                            else importotondo2
                        }
                    </li>
                <ul>
                <br>
                <br>
                <p>
                    <b>Totale giocato: {parse_float(importotondo1 if column % 2 == 0
                            else importotondo2) * parse_float(self.bet_data[row]["b1_data"]["value"] if column % 2 == 1
                        else self.bet_data[row]["b2_data"]["value"])}</b>
                </p>
                <br>
                <br>
                <br>
                """
            
        # Sostituisci il contenuto del widget dei dettagli
        # self.bet_details_widget.clear()
        self.bet_details_widget.setHtml(details)

        # Imposta il testo nei dettagli


    def play_now(self, row, column):
        print(row, column)
        print(self.bet_data)
        if column == 3:
            bookmaker_name = self.bet_data[row]['b1_data']['bname'].lower()
        elif column == 4:
            bookmaker_name = self.bet_data[row]['b2_data']['bname'].lower()
        else:
            print("Colonna non valida")
            return
        
        print(f"Bookmaker selezionato: {bookmaker_name}")
        print(row, column)
        # Costruisci il percorso del file
        bookmaker_main = os.path.join('../bookmakers', f'{bookmaker_name}.py')
    
        try:
            # Esegui il file Python
            result = subprocess.Popen(['python3', bookmaker_main])
        
            # Se vuoi attendere che il processo termini
            # result.wait()
        
            print(f"Avviato script per {bookmaker_name}")
    
        except FileNotFoundError:
            print(f"File non trovato per il bookmaker {bookmaker_name}")
        except Exception as e:
            print(f"Errore nell'avvio dello script: {e}")

    def toggle_server(self):
        """Avvia o ferma il server socket"""
        if not self.server_running:
            # Avvia il server
            self.server_btn.setEnabled(False)  # Disabilita temporaneamente
            self.statusBar.showMessage("Avvio del server in corso...")
            
            # Avvia il server in un thread separato
            server_thread = threading.Thread(target=self.socket_worker.start_server)
            server_thread.daemon = True
            server_thread.start()
        else:
            # Ferma il server
            self.socket_worker.stop_server()
            self.server_running = False
            self.server_status.setText("Server: SPENTO")
            self.server_status.setStyleSheet("color: red; font-weight: bold;")
            self.server_btn.setText("Avvia Server")
            self.statusBar.showMessage("Server arrestato")
            
    def toggle_subprocess(self):
        """Avvia o ferma il subprocess manager"""
        if not self.subprocess_running:
            # Avvia il subprocess manager
            if self.subprocess_mgr.start():
                self.subprocess_running = True
                self.subprocess_status.setText("Bot: IN ESECUZIONE")
                self.subprocess_status.setStyleSheet("color: green; font-weight: bold;")
                self.subprocess_btn.setText("Ferma Bot")
                self.last_run.setText(f"Ultimo avvio: {datetime.now().strftime('%H:%M:%S')}")
                self.statusBar.showMessage("Bot avviato")
                self.display_message("Bot avviato, esecuzione ogni 600 secondi")
        else:
            # Ferma il subprocess manager
            self.subprocess_mgr.stop()
            self.subprocess_running = False
            self.subprocess_status.setText("Bot: SPENTO")
            self.subprocess_status.setStyleSheet("color: red; font-weight: bold;")
            self.subprocess_btn.setText("Avvia Bot")
            self.statusBar.showMessage("Bot arrestato")
            self.display_message("Bot arrestato")
            
    def start_import_data(self):
        """Importa dati da decoded_items.json e li invia al socket server tramite netcat"""
        file_path = 'decoded_items.json'
        
        # Verifica l'esistenza del file
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Errore", f"Il file {file_path} non esiste.")
            return
        
        try:
            # Leggi il file JSON
            with open(file_path, 'r') as file:
                data = json.load(file)
            
            # Verifica che il file contenga un array di oggetti
            if not isinstance(data, list):
                QMessageBox.warning(self, "Errore", "Il file deve contenere un array di oggetti.")
                return
            
            # Contatori per tracciare l'invio
            total_items = len(data)
            sent_items = 0
            errors = 0
            
            # Invia ogni elemento al socket server
            for item in data:
                try:

                    bookmakers = item['bookmakers']
                    # Prepara il payload JSON per ogni elemento
                    payload = {
                        "action": "NEW_BET",
                        "data": {
                            "bet_id": item["bet_id"],
                            "sport": item["sport"],
                            "ROI": item["valore_surebet"],
                            "bookmaker1" : bookmakers[0]["bname"],
                            "bookmaker2" : bookmakers[1]["bname"],
                            "b1_data": bookmakers[0],
                            "b2_data": bookmakers[1],
                        }
                        # "data": bookmakers  # Invia un singolo elemento per volta
                    }
                    
                    # Converte il payload in JSON
                    payload_json = json.dumps(payload["data"])
                    
                    # Usa subprocess per eseguire netcat
                    result = subprocess.run(
                        ['nc', '127.0.0.1', '9999'], 
                        input=payload_json, 
                        capture_output=True, 
                        text=True
                    )
                    
                    # Verifica l'esito dell'invio
                    if result.returncode == 0:
                        sent_items += 1
                    else:
                        errors += 1
                        self.display_message(f"Errore durante l'invio: {result.stderr}")
                    
                except Exception as e:
                    errors += 1
                    self.display_message(f"Eccezione durante l'invio: {str(e)}")
            
            # Messaggio di riepilogo
            # summary_msg = f"Importazione completata:\nTotale elementi: {total_items}\nInviati: {sent_items}\nErrori: {errors}"
            # QMessageBox.information(self, "Importazione completata", summary_msg)
            # self.display_message(summary_msg)
            
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Errore", "Il file non è un JSON valido.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante l'importazione: {str(e)}")

    def update_time(self):
        """Aggiorna l'orario visualizzato"""
        self.time_label.setText(f"Ora: {datetime.now().strftime('%H:%M:%S')}")
        
    def display_message(self, message):
        """Aggiunge un messaggio al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def client_connected(self, client_addr):
        """Gestisce un nuovo client connesso"""
        self.display_message(f"Nuovo client connesso: {client_addr}")
        self.statusBar.showMessage(f"Client connesso: {client_addr}")
        
    def client_disconnected(self, client_addr):
        """Gestisce un client disconnesso"""
        self.display_message(f"Client disconnesso: {client_addr}")
        
    def server_started(self):
        """Gestisce l'evento di server avviato"""
        self.server_running = True
        self.server_status.setText("Server: IN ASCOLTO")
        self.server_status.setStyleSheet("color: green; font-weight: bold;")
        self.server_btn.setText("Ferma Server")
        self.server_btn.setEnabled(True)
        self.statusBar.showMessage(f"Server in ascolto su {HOST}:{PORT}")
        self.display_message(f"Server avviato su {HOST}:{PORT}")
        
    def server_error(self, error_message):
        """Gestisce un errore del server"""
        self.display_message(f"Errore del server: {error_message}")
        self.server_running = False
        self.server_status.setText("Server: ERRORE")
        self.server_status.setStyleSheet("color: red; font-weight: bold;")
        self.server_btn.setText("Avvia Server")
        self.server_btn.setEnabled(True)
        
        # Mostra una finestra di dialogo con l'errore
        QMessageBox.critical(self, "Errore del server", 
                             f"Si è verificato un errore con il server:\n{error_message}")
        
    def process_decoded_data(self, data):
        """Elabora i dati decodificati ricevuti"""
        self.display_message(f"Ricevuti nuovi dati ({len(data)} elementi)")
        self.statusBar.showMessage(f"Nuovi dati ricevuti: {len(data)} elementi")
        
        # Aggiorna i dati
        self.bet_data.append(data)
        
        # Aggiorna la visualizzazione
        self.update_bets_table()

    def calcola_arbitraggio(self, quota1, quota2):
        """
        Calcola l'importo da scommettere per garantire un guadagno
        
        Args:
        quota1 (float): Prima quota
        quota2 (float): Seconda quota
        
        Returns:
        tuple: (importo1, importo2, percentuale_profitto)
        """
        quota1 = parse_float(quota1)
        quota2 = parse_float(quota2)
        
        # Calcola la probabilità implicita
        prob1 = 1 / quota1
        prob2 = 1 / quota2
        
        # Somma delle probabilità
        somma_probabilita = prob1 + prob2
        
        # Calcola la percentuale di arbitraggio
        perc_arbitraggio = (1 - somma_probabilita) * 100
        
        # Se non c'è opportunità di arbitraggio, restituisci None
        if perc_arbitraggio <= 0:
            return None
        
        # Calcola gli importi
        importo_totale = 100  # Importo base
        
        importo1 = importo_totale * (prob2 / somma_probabilita)
        importo2 = importo_totale * (prob1 / somma_probabilita)
        
        # Calcola i ritorni
        ritorno1 = importo1 * quota1
        ritorno2 = importo2 * quota2
        
        return (
            round(importo1, 2),  # Importo da scommettere sulla prima quota
            round(importo2, 2),  # Importo da scommettere sulla seconda quota
            round(perc_arbitraggio, 2)  # Percentuale di profitto
        )    
        

    def calcola_arbitraggio_tondi(self, quota1, quota2):
        """
        Calcola l'arbitraggio con importi tondi
        preservando la percentuale di profitto
        """
        # Converti quote a float
        quota1 = parse_float(quota1)
        quota2 = parse_float(quota2)
        
        # Calcola le probabilità implicite
        prob1 = 1 / quota1
        prob2 = 1 / quota2
        somma_probabilita = prob1 + prob2
        
        # Calcolo base
        importo_base = 100
        
        # Trova il primo multiplo che mantiene la percentuale di profitto
        moltiplicatore = 1
        while True:
            importo_totale = importo_base * moltiplicatore
            
            importo1 = round(importo_totale * (prob2 / somma_probabilita))
            importo2 = round(importo_totale * (prob1 / somma_probabilita))
            
            # Ricalcola le probabilità con gli importi arrotondati
            ritorno1 = importo1 * quota1
            ritorno2 = importo2 * quota2
            
            # Calcola la percentuale di profitto
            perc_profitto = ((ritorno1 + ritorno2 - importo_totale) / importo_totale) * 100
            
            # Cerca di mantenere un profitto simile
            if perc_profitto > 0.4:
                return (
                    importo1,  # Importo da scommettere sulla prima quota
                    importo2,  # Importo da scommettere sulla seconda quota
                    round(perc_profitto, 2)  # Percentuale di profitto
                )
            
            moltiplicatore += 1

    def update_bets_table(self):
        """Aggiorna la tabella delle scommesse"""
        self.bets_table.setRowCount(0)  # Cancella la tabella
        
        # Filtra i dati in base alla selezione
        filtered_data = self.apply_filter()
        
        # Popola la tabella
        for row, bet in enumerate(filtered_data):
            item1 = QTableWidgetItem(str(bet.get("bookmaker1", "")))
            # Colora lo sfondo dell'item
            if self.check_bookmaker_file(bet.get("bookmaker1", "")):
                item1.setBackground(QColor(200, 255, 200))  # Verde chiaro se il file esiste
            else:
                item1.setBackground(QColor(255, 200, 200)) 
            
            item2 = QTableWidgetItem(str(bet.get("bookmaker2", "")))
            # Colora lo sfondo dell'item
            if self.check_bookmaker_file(bet.get("bookmaker2", "")):
                item2.setBackground(QColor(200, 255, 200))  # Verde chiaro se il file esiste
            else:
                item2.setBackground(QColor(255, 200, 200)) 
            self.bets_table.insertRow(row)
            # Qui devi adattare i campi in base alla struttura effettiva dei dati
            # Questo è solo un esempio:
            self.bets_table.setItem(row, 0, QTableWidgetItem(str(bet.get("bet_id", ""))))
            self.bets_table.setItem(row, 1, QTableWidgetItem(str(bet.get("sport", ""))))
            self.bets_table.setItem(row, 2, QTableWidgetItem(str(bet.get("ROI", ""))))
            self.bets_table.setItem(row, 3, item1)
            self.bets_table.setItem(row, 4, item2)
            self.bets_table.setItem(row, 5, QTableWidgetItem(json.dumps(bet.get("b1_data", {}), indent=2)))
            self.bets_table.setItem(row, 6, QTableWidgetItem(json.dumps(bet.get("b2_data", {}), indent=2)))
            
            

            # Quote - potrebbero essere in un formato più complesso
            odds = bet.get("odds", "")
            if isinstance(odds, dict):
                odds_str = ", ".join([f"{k}: {v}" for k, v in odds.items()])
            else:
                odds_str = str(odds)
            self.bets_table.setItem(row, 7, QTableWidgetItem(odds_str))
            
            # Timestamp
            timestamp = bet.get("timestamp", "")
            self.bets_table.setItem(row, 8, QTableWidgetItem(str(timestamp)))
        for row in range(self.bets_table.rowCount()):
            color = QColor(220, 220, 220) if (row // 1) % 2 == 0 else QColor(255, 255, 255)

        for col in range(self.bets_table.columnCount()):
            # Escludi le colonne 3 e 4 (indici 2 e 3)
            if col not in [2, 3]:
                item = self.bets_table.item(row, col)
                if item:
                    item.setBackground(color)
            
    def apply_filter(self):
        """Applica un filtro ai dati e restituisce i dati filtrati"""
        filter_option = self.filter_combo.currentText()
        
        # Filtra i dati
        if filter_option == "Tutte le scommesse":
            filtered_data = self.bet_data
        elif filter_option == "Solo calcio":
            filtered_data = [bet for bet in self.bet_data if bet.get("sport", "").lower() == "calcio"]
        elif filter_option == "Solo tennis":
            filtered_data = [bet for bet in self.bet_data if bet.get("sport", "").lower() == "tennis"]
        elif filter_option == "Solo basket":
            filtered_data = [bet for bet in self.bet_data if bet.get("sport", "").lower() == "basket"]
        else:
            filtered_data = self.bet_data
            
        # Aggiorna la tabella solo se chiamato direttamente
        if self.sender() == self.filter_combo:
            self.update_bets_table()
            
        return filtered_data
        
    def closeEvent(self, event):
        """Gestisce la chiusura dell'applicazione"""
        # Chiedi conferma prima di chiudere
        reply = QMessageBox.question(self, 'Conferma Uscita',
            "Sei sicuro di voler uscire? Tutti i processi verranno terminati.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Ferma il subprocess manager
            if self.subprocess_running:
                self.subprocess_mgr.stop()
                
            # Ferma il server socket
            if self.server_running:
                self.socket_worker.stop_server()
                
            event.accept()
        else:
            event.ignore()

# Crea un nuovo tab Android nell'interfaccia
def init_android_tab(self):
    """Inizializza il tab per la visualizzazione del dispositivo Android"""
    self.android_tab = QWidget()
    android_layout = QVBoxLayout(self.android_tab)
    
    # Controlli per la connessione
    controls_layout = QHBoxLayout()
    
    # Status e info
    info_layout = QVBoxLayout()
    self.android_status = QLabel("Android: Non connesso")
    self.android_status.setStyleSheet("color: red; font-weight: bold;")
    
    # Verifica la presenza degli strumenti necessari
    adb_installed = self.android_mgr.check_adb_installed()
    scrcpy_installed = self.android_mgr.check_scrcpy_installed()
    
    adb_status_txt = "ADB: Installato ✓" if adb_installed else "ADB: Non installato ✗"
    scrcpy_status_txt = "scrcpy: Installato ✓" if scrcpy_installed else "scrcpy: Non installato ✗"
    
    self.adb_status = QLabel(adb_status_txt)
    self.adb_status.setStyleSheet("color: green;" if adb_installed else "color: red;")
    
    self.scrcpy_status = QLabel(scrcpy_status_txt)
    self.scrcpy_status.setStyleSheet("color: green;" if scrcpy_installed else "color: red;")
    
    info_layout.addWidget(self.android_status)
    info_layout.addWidget(self.adb_status)
    info_layout.addWidget(self.scrcpy_status)
    
    # Pulsanti
    buttons_layout = QVBoxLayout()
    self.connect_btn = QPushButton("Connetti dispositivo")
    self.connect_btn.clicked.connect(self.connect_android_device)
    self.connect_btn.setEnabled(adb_installed and scrcpy_installed)
    
    self.disconnect_btn = QPushButton("Disconnetti")
    self.disconnect_btn.clicked.connect(self.disconnect_android_device)
    self.disconnect_btn.setEnabled(False)
    
    # Pulsante per screenshot
    self.screenshot_btn = QPushButton("Screenshot")
    self.screenshot_btn.clicked.connect(self.take_android_screenshot)
    self.screenshot_btn.setEnabled(False)
    
    buttons_layout.addWidget(self.connect_btn)
    buttons_layout.addWidget(self.disconnect_btn)
    buttons_layout.addWidget(self.screenshot_btn)
    
    # Aggiungi a controls_layout
    controls_layout.addLayout(info_layout)
    controls_layout.addStretch()
    controls_layout.addLayout(buttons_layout)
    
    android_layout.addLayout(controls_layout)
    
    # Frame per il display Android
    self.android_frame = QFrame()
    self.android_frame.setFrameShape(QFrame.Shape.StyledPanel)
    self.android_frame.setMinimumHeight(600)
    self.android_frame.setStyleSheet("background-color: #222;")
    
    # Messaggio di aiuto quando non c'è nessun dispositivo connesso
    self.android_help_label = QLabel("Collega un dispositivo Android tramite USB e abilita il Debug USB nelle impostazioni sviluppatore.")
    self.android_help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.android_help_label.setStyleSheet("color: white; background-color: transparent;")
    
    # Aggiungi la label al frame
    frame_layout = QVBoxLayout(self.android_frame)
    frame_layout.addWidget(self.android_help_label)
    
    android_layout.addWidget(self.android_frame)
    
    # Aggiungi il tab
    self.tabs.addTab(self.android_tab, "Android")

# Metodi per gestire le funzionalità Android
def connect_android_device(self):
    """Connette un dispositivo Android tramite scrcpy"""
    # Disabilita il pulsante durante il tentativo di connessione
    self.connect_btn.setEnabled(False)
    self.statusBar.showMessage("Connessione al dispositivo Android in corso...")
    
    # Verifica se ci sono dispositivi connessi
    devices = self.android_mgr.get_connected_devices()
    if not devices:
        self.display_message("Nessun dispositivo Android trovato. Verifica la connessione USB e il Debug USB.")
        self.statusBar.showMessage("Nessun dispositivo Android trovato")
        self.connect_btn.setEnabled(True)
        return
    
    # Nascondi la label di aiuto
    self.android_help_label.setVisible(False)
    
    # Avvia scrcpy
    if self.android_mgr.start_scrcpy(self.android_frame):
        # Aggiorna lo stato
        self.android_status.setText("Android: Connesso")
        self.android_status.setStyleSheet("color: green; font-weight: bold;")
        self.disconnect_btn.setEnabled(True)
        self.screenshot_btn.setEnabled(True)
        self.statusBar.showMessage(f"Dispositivo Android connesso: {devices[0]}")
    else:
        # Ripristina l'interfaccia in caso di errore
        self.android_help_label.setVisible(True)
        self.connect_btn.setEnabled(True)
        self.statusBar.showMessage("Errore nella connessione al dispositivo Android")

def disconnect_android_device(self):
    """Disconnette il dispositivo Android"""
    if self.android_mgr.stop_scrcpy():
        # Aggiorna lo stato
        self.android_status.setText("Android: Non connesso")
        self.android_status.setStyleSheet("color: red; font-weight: bold;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.screenshot_btn.setEnabled(False)
        self.android_help_label.setVisible(True)
        self.statusBar.showMessage("Dispositivo Android disconnesso")

def take_android_screenshot(self):
    """Cattura uno screenshot del dispositivo Android"""
    if self.android_mgr.is_connected():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"android_screenshot_{timestamp}.png"
        
        if self.android_mgr.screenshot(output_path=filename):
            self.statusBar.showMessage(f"Screenshot salvato come {filename}")
            self.display_message(f"Screenshot del dispositivo Android salvato: {filename}")
        else:
            self.statusBar.showMessage("Errore durante la cattura dello screenshot")

def main():
    app = QApplication(sys.argv)
    window = FinderbetGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()