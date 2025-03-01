import json
import socket

def process_bookmaker(item):
    """
    Elabora un singolo elemento di bookmaker e stampa le informazioni rilevanti.
    """
    bookmakers = json.loads(item)  # Decodifica la stringa JSON nell'elemento "items"
    for bookmaker in bookmakers:
        print(f"Bookmaker: {bookmaker['bname']}")
        print(f"Evento: {bookmaker['evento']}")
        print(f"Valore: {bookmaker['value']}")
        print(f"Descrizione: {bookmaker['desc']}")
        print(f"URL Desktop: {bookmaker['url_desktop']}")
        print(f"URL Mobile: {bookmaker['url_mobile']}")
        print(f"Media: {bookmaker['avg']}")
        print(f"Flag: {bookmaker['flag']}")
        print("-" * 40)

def mine_data(file_path):
    """
    Apre il file JSON, carica i dati e li processa.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)  # Carica il contenuto del file JSON in un oggetto Python
    
    filtered_items = [
        item for item in betting_items
        if len(item["bookmakers"]) < 3 and item["sport"].lower() in ["calcio", "calcio"]
    ]
    
    return filtered_items[0]
    
    for event in data:
            
        # Processa la lista degli items
        process_bookmaker(event['items'])

if __name__ == "__main__":
    file_path = 'decoded_items.json'  # Percorso del file JSON
    primo_evento=mine_data(file_path)
    
    try:
        server_address = ("127.0.0.1", 9999)  # IP e porta del server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(server_address)
        message = primo_evento
        # Converti il JSON in stringa e invialo
        json_message = json.dumps(message)
        client_socket.sendall(json_message.encode("utf-8"))# Chiama la funzione per avviare l'elaborazione
    except Exception as e:
        print(e)
