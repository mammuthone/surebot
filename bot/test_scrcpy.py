import sys
import subprocess  # Aggiunto l'import mancante
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer

# Importa il modulo AndroidManager
from android_manager import AndroidManager

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configura la finestra
        self.setWindowTitle("Test scrcpy")
        self.setGeometry(100, 100, 800, 600)
        
        # Crea il widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Crea i controlli
        self.status_label = QLabel("Status: Non connesso")
        connect_button = QPushButton("Connetti dispositivo")
        connect_button.clicked.connect(self.connect_device)
        
        disconnect_button = QPushButton("Disconnetti")
        disconnect_button.clicked.connect(self.disconnect_device)
        
        screenshot_button = QPushButton("Screenshot")
        screenshot_button.clicked.connect(self.take_screenshot)
        
        # Crea l'etichetta informativa
        self.info_label = QLabel("Il dispositivo Android verrà visualizzato in una finestra separata")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: white; background-color: #333; padding: 10px;")
        
        # Crea il frame per il display
        self.display_frame = QFrame()
        self.display_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.display_frame.setMinimumHeight(400)
        self.display_frame.setStyleSheet("background-color: #222;")
        
        # Aggiungi i widget al layout
        layout.addWidget(self.status_label)
        layout.addWidget(connect_button)
        layout.addWidget(disconnect_button)
        layout.addWidget(screenshot_button)
        layout.addWidget(self.info_label)
        layout.addWidget(self.display_frame)
        
        # Inizializza AndroidManager
        self.android_mgr = AndroidManager(message_callback=self.log_message)
        
        # Verifica installazione
        if not self.android_mgr.check_adb_installed():
            self.log_message("ATTENZIONE: ADB non installato!")
        
        if not self.android_mgr.check_scrcpy_installed():
            self.log_message("ATTENZIONE: scrcpy non installato!")
    
    def log_message(self, message):
        """Mostra un messaggio di log"""
        print(f"[LOG] {message}")
        self.status_label.setText(f"Status: {message}")
    
    def connect_device(self):
        """Connette un dispositivo Android"""
        devices = self.android_mgr.get_connected_devices()
        if not devices:
            self.log_message("Nessun dispositivo trovato")
            return
            
        self.log_message(f"Trovato dispositivo: {devices[0]}")
        
        # Avvia scrcpy in modalità finestra separata
        success = self.start_scrcpy_standalone()
        
        if success:
            self.log_message("Dispositivo connesso in finestra separata")
        else:
            self.log_message("Errore nella connessione")
    
    def start_scrcpy_standalone(self):
        """Avvia scrcpy in una finestra separata senza --window-parent-id"""
        try:
            devices = self.android_mgr.get_connected_devices()
            if not devices:
                self.log_message("Nessun dispositivo Android connesso")
                return False
                
            # Usa un comando scrcpy di base senza l'opzione problematica
            cmd = [
                "scrcpy",
                "--window-title", "FinderBet Android View",
                "--stay-awake",
                "--video-bit-rate", "8M",
                "--max-fps", "30"
            ]
            
            # Avvia il processo
            self.android_mgr.process = subprocess.Popen(cmd)
            self.android_mgr.connected = True
            
            self.log_message("Dispositivo Android visualizzato in finestra separata")
            return True
        except Exception as e:
            self.log_message(f"Errore: {str(e)}")
            return False
    
    def disconnect_device(self):
        """Disconnette il dispositivo"""
        if self.android_mgr.stop_scrcpy():
            self.log_message("Dispositivo disconnesso")
    
    def take_screenshot(self):
        """Cattura uno screenshot"""
        if self.android_mgr.screenshot("test_screenshot.png"):
            self.log_message("Screenshot salvato come test_screenshot.png")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()