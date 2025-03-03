import socket
import subprocess
import threading
import time

HOST = "127.0.0.1"
PORT = 9999

def start_subprocess():
    """Esegue un subprocess ogni 60 secondi"""
    while True:
        print("🔄 Avvio subprocess...")
        subprocess.Popen(["python3", "./bot/finderbet_v4.py"])  # Avvia uno script esterno
        time.sleep(600)  # Aspetta 600 secondi prima di rieseguire il subprocess

def evaluate_data(data):
    if data["action"] == "DECODED_ITEMS":
        return True

def handle_client(client_socket):
    """Gestisce la comunicazione con un client"""
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            print(f"📩 Ricevuto dal client: {data}")
            evaluate_data(data)
            response = f"Echo: {data}"
            client_socket.send(response.encode())
        except ConnectionResetError:
            break
    print("❌ Connessione chiusa.")
    client_socket.close()

def start_server():
    """Avvia il socket server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"🚀 Server in ascolto su {HOST}:{PORT}...")

    while True:
        client_socket, addr = server.accept()
        print(f"✅ Connessione accettata da {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

# Avvia il subprocess in un thread separato
subprocess_thread = threading.Thread(target=start_subprocess, daemon=True)
subprocess_thread.start()

# Avvia il server
start_server()
