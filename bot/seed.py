import socket
import json

HOST = "127.0.0.1"
PORT = 9999

def send_data_to_server(data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, PORT))
            client.sendall(json.dumps(data).encode())
            response = client.recv(4096).decode()
            print(f"Risposta dal server: {response}")
    except Exception as e:
        print(f"Errore durante l'invio dei dati: {str(e)}")

# Carica il file JSON
def main():
    try:
        with open("decoded_items.json", "r", encoding="utf-8") as file:
            decoded_items = json.load(file)
            
            for item in decoded_items:
                send_data_to_server(item)
    except FileNotFoundError:
        print("Errore: Il file decoded_items.json non è stato trovato.")
    except json.JSONDecodeError:
        print("Errore: Formato JSON non valido.")

if __name__ == "__main__":
    main()