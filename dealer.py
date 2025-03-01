import json
import subprocess
import os

# Percorso del file JSON
JSON_FILE_PATH = "decoded_items.json"

def load_items():
    """Legge e importa i dati dal file JSON."""
    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        print("Dati importati con successo.")
        return data
    except Exception as e:
        print(f"Errore nel caricamento del file JSON: {e}")
        return None


def estrai_bookmakers(filtered_items):
    bookmakers_unici = ['Sisal','Snai','888', 'Bet365', 'Marathonbet', 'Planetwin365', '1xbet', 'Efbet', 'Betfair', 'Pokerstars', 'Unibet', 'Vincitubet', 'Goldbet', 'Betpassion', 'Bwin', 'Betpoint', 'Originalbet']

    # Iteriamo su ogni item nella lista filtrata
    try:
        for bookmaker in bookmakers_unici:
            file_name = f"bookmakers/{bookmaker.lower()}.py"
            print(bookmaker)
            # Crea il file
            with open(file_name, 'w') as f:
                f.write(f"# Questo file è stato creato per il bookmaker: {bookmaker}\n")
                f.write(f"# Puoi aggiungere il codice specifico per il bookmaker {bookmaker} qui.\n")
                f.write(f"\n")
                f.write(f"import os\n")
                f.write(f"print(f'Il nome del file in esecuzione è: {{os.path.basename(__file__)}}')\n")
            print(f"File creato: {file_name}")
    except KeyError:
            print(f"Errore: la chiave 'items' non esiste in item: {item}")
    except json.JSONDecodeError:
            print(f"Errore nel parsing JSON per item: {item}")

    return bookmakers_unici
# Esegui il caricamento e stampa i dati per verifica
if __name__ == "__main__":
    items = load_items()
    for item in items:
        try:
            item["items"] = json.loads(item["items"])  # Effettua il parsing della stringa JSON
        except json.JSONDecodeError:
            print(f"Errore nel parsing JSON per item: {item}")
    filtered_items = [item for item in items if len(item.get("bookmakers", [])) < 3]
    # print(filtered_items[0])
    book1 = filtered_items[0]["bookmakers"][0].get('bname')
    book2 = filtered_items[0]["bookmakers"][1].get('bname')
    # Rimuovi o modifica a seconda di cosa vuoi fare
    unici=estrai_bookmakers(filtered_items)
    # print(unici)
    # print(book1)
    # print(book2)
    subprocess.run(["python", f"bookmakers/{book1.lower()}.py"])
    subprocess.run(["python", f"bookmakers/{book2.lower()}.py"])
