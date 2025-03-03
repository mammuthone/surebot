import subprocess
import platform
import threading
import time
import os

class AndroidManager:
    """
    Classe che gestisce la connessione a dispositivi Android tramite ADB e la visualizzazione
    tramite scrcpy. Progettata per essere facilmente importata in qualsiasi applicazione PyQt.
    """
    def __init__(self, message_callback=None):
        """
        Inizializza l'AndroidManager
        
        Args:
            message_callback: funzione callback per i messaggi di log (opzionale)
        """
        self.process = None
        self.connected = False
        self.message_callback = message_callback
    
    def log_message(self, message):
        """Invia un messaggio al callback se disponibile"""
        if self.message_callback:
            self.message_callback(message)
        else:
            print(message)
    
    def check_adb_installed(self):
        """Verifica se ADB è installato"""
        try:
            result = subprocess.run(["adb", "version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def check_scrcpy_installed(self):
        """Verifica se scrcpy è installato"""
        try:
            result = subprocess.run(["scrcpy", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_connected_devices(self):
        """Ottiene la lista dei dispositivi Android connessi"""
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            devices_output = result.stdout.strip().split('\n')[1:]
            devices = []
            
            for line in devices_output:
                if line.strip() and not line.endswith('offline'):
                    parts = line.strip().split('\t')
                    if len(parts) == 2 and parts[1] == 'device':
                        devices.append(parts[0])
            
            return devices
        except:
            return []
    
    def start_scrcpy(self, frame_widget, no_control=False, bit_rate="8M", max_fps=30, 
                     stay_awake=True, crop=None, fullscreen=False):
        """
        Avvia scrcpy per visualizzare il display del dispositivo Android
        
        Args:
            frame_widget: widget PyQt dove visualizzare il dispositivo
            no_control: se True, disabilita il controllo del dispositivo
            bit_rate: bitrate per la qualità video (es: "8M")
            max_fps: massimo frame rate
            stay_awake: se True, impedisce al dispositivo di andare in standby
            crop: ritaglio dello schermo (es: "1224:1440:0:0")
            fullscreen: se True, avvia in modalità fullscreen
        
        Returns:
            bool: True se avviato con successo, False altrimenti
        """
        if self.process and self.process.poll() is None:
            # Termina il processo precedente se ancora in esecuzione
            self.stop_scrcpy()
        
        try:
            # Verifica se ci sono dispositivi connessi
            devices = self.get_connected_devices()
            if not devices:
                self.log_message("Nessun dispositivo Android connesso")
                return False
            
            # Prepara le dimensioni per scrcpy
            width = frame_widget.width()
            height = frame_widget.height()
            
            # Imposta il comando scrcpy
            cmd = [
                "scrcpy",
                "--window-title", "Android Display",
                "--render-driver", "software",  # Più compatibile con l'embedding
                "--window-x", "0",
                "--window-y", "0",
                "--window-width", str(width),
                "--window-height", str(height),
                "--video-bit-rate", bit_rate,
                "--max-fps", str(max_fps)
            ]
            
            # Opzioni aggiuntive
            if stay_awake:
                cmd.append("--stay-awake")
            
            if no_control:
                cmd.append("--no-control")
            
            if crop:
                cmd.extend(["--crop", crop])
            
            if fullscreen:
                cmd.append("--fullscreen")
            
            # Aggiungi il parametro di display embedded in base al sistema operativo
            if platform.system() == "Windows":
                # Su Windows, usa --window-parent-id con il valore intero
                cmd.extend(["--window-parent-id", str(int(frame_widget.winId()))])
            else:
                # Su Linux/Mac usa direttamente il valore winId
                cmd.extend(["--window-parent-id", str(frame_widget.winId())])
            
            # Avvia scrcpy
            self.process = subprocess.Popen(cmd)
            self.connected = True
            
            self.log_message(f"Dispositivo Android connesso: {devices[0]}")
            return True
            
        except Exception as e:
            self.log_message(f"Errore nell'avvio di scrcpy: {str(e)}")
            return False
    
    def screenshot(self, output_path="screenshot.png"):
        """
        Cattura uno screenshot del dispositivo Android
        
        Args:
            output_path: percorso dove salvare lo screenshot
        
        Returns:
            bool: True se lo screenshot è stato salvato, False altrimenti
        """
        try:
            # Verifica se ci sono dispositivi connessi
            devices = self.get_connected_devices()
            if not devices:
                self.log_message("Nessun dispositivo Android connesso")
                return False
                
            # Usa adb per catturare lo screenshot
            subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screenshot.png"])
            subprocess.run(["adb", "pull", "/sdcard/screenshot.png", output_path])
            subprocess.run(["adb", "shell", "rm", "/sdcard/screenshot.png"])
            
            self.log_message(f"Screenshot salvato in: {output_path}")
            return os.path.exists(output_path)
            
        except Exception as e:
            self.log_message(f"Errore nella cattura dello screenshot: {str(e)}")
            return False
    
    def stop_scrcpy(self):
        """Ferma scrcpy"""
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
            self.connected = False
            
            self.log_message("Dispositivo Android disconnesso")
            return True
        
        return False
    
    def is_connected(self):
        """Verifica se un dispositivo è connesso e visualizzato"""
        return self.connected and self.process and self.process.poll() is None

    def execute_command(self, command):
        """
        Esegue un comando ADB sul dispositivo connesso
        
        Args:
            command: comando da eseguire (senza "adb shell")
        
        Returns:
            str: output del comando
        """
        try:
            devices = self.get_connected_devices()
            if not devices:
                self.log_message("Nessun dispositivo Android connesso")
                return None
                
            result = subprocess.run(["adb", "shell", command], 
                                    capture_output=True, text=True)
            return result.stdout.strip()
            
        except Exception as e:
            self.log_message(f"Errore nell'esecuzione del comando: {str(e)}")
            return None