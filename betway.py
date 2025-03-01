import subprocess
import time
import cv2
import numpy as np

SCREENSHOT_PATH = "/sdcard/screen.png"
LOCAL_SCREENSHOT_PATH = "screen.png"
ACCEDI_BUTTON_TEMPLATE_PATH = "./images_library/betway/patterns/bottone_accedi.png"
RICERCA_BUTTON_TEMPLATE_PATH = "./images_library/betway/patterns/bottone_ricerca_homepage.png"

def take_screenshot():
    """Cattura uno screenshot con ADB e lo salva in locale."""
    print("Catturando screenshot...")
    exec_adb_command(f"adb shell screencap -p {SCREENSHOT_PATH}")
    exec_adb_command(f"adb pull {SCREENSHOT_PATH} {LOCAL_SCREENSHOT_PATH}")
    print("Screenshot salvato.")


def find_button(template_path, threshold=0.95):
    """Trova un elemento nell'immagine usando il template matching e visualizza il risultato."""
    screenshot = cv2.imread(LOCAL_SCREENSHOT_PATH, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    print(f"Screenshot size: {screenshot.shape}")  # (altezza, larghezza)
    print(f"Template size: {template.shape}")

    if screenshot is None or template is None:
        print("Errore nel caricamento delle immagini.")
        return None

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"Confidenza max trovata: {max_val}")

    if max_val >= threshold:
        print(f"Elemento trovato con confidenza {max_val}")

        # Disegna un rettangolo sul risultato per debug
        h, w = template.shape
        screenshot_color = cv2.imread(LOCAL_SCREENSHOT_PATH)  # A colori per la visualizzazione
        cv2.rectangle(screenshot_color, max_loc, (max_loc[0] + w, max_loc[1] + h), (0, 255, 0), 2)
        cv2.imwrite("debug_match.png", screenshot_color)  # Salva l'immagine con il match

        return max_loc  # Coordinate (x, y) del punto in alto a sinistra
    else:
        print("Elemento non trovato.")
        return None

def tap_on_button(x, y):
    """Esegue un TAP sulla posizione trovata."""
    exec_adb_command(f"adb shell input tap {x} {y}")
    print(f"TAP eseguito su ({x}, {y})")


def exec_adb_command(command):
    """Esegue un comando ADB e restituisce l'output."""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione di '{command}': {e}")
        print(f"Output di errore: {e.stderr}")

def launch_application():
    try:
        exec_adb_command("adb shell monkey -p it.betway 1")
        print("App Betway avviata con successo")
        time.sleep(7)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'avvio dell'app Sisal: {e}")
        print(f"Output di errore: {e.stderr}")
        return False
    
def trova_e_tappa(path):
    position = find_button(path)
    if position:
        x, y = position
        tap_on_button(x + 10, y + 10)

def login():
    print("Eseguo TAP sul campo username...")
    exec_adb_command("adb shell input tap 300 500")
    print("Inserimento username...")
    for letter in "mammuthone":
        exec_adb_command(f"adb shell input text {letter}")
    # TAP sul campo password
    print("Eseguo TAP sul campo password...")
    exec_adb_command("adb shell input tap 230 650")
    time.sleep(1)
    # Inserimento della password "89sumellU!!"
    print("Inserimento password...")
    for char in "89sumellU!!":
        exec_adb_command(f"adb shell input text {char}")
    # Invio (ENTER)
    exec_adb_command("adb shell input keyevent 66")
    time.sleep(5)
    exec_adb_command("adb shell input tap 770 1370")
    time.sleep(1)

def input_partita(match):
    for letter in match:
        if letter == " ":
            exec_adb_command("adb shell input keyevent 62")  # Keyevent per lo spazio
        else:
            exec_adb_command(f"adb shell input text {letter}")
    # exec_adb_command(f"adb shell input text {match}")
    time.sleep(1)
    exec_adb_command("adb shell input keyevent 66")
    time.sleep(1)

def esegui_login():
    trova_e_tappa(ACCEDI_BUTTON_TEMPLATE_PATH)
    login()

def cerca_partita(match):
    trova_e_tappa(RICERCA_BUTTON_TEMPLATE_PATH)
    input_partita(match)

def apri_menu():
    exec_adb_command("adb shell input tap 50 150")
    exec_adb_command("adb shell input tap 270 387")

def apri_partita():
    exec_adb_command("adb shell input tap 290 520")
    

if __name__ == "__main__":
    launch_application()
    take_screenshot()
    # esegui_login()
    apri_menu()
    input_partita("bologna fc - milan")
    apri_partita()
    # cerca_partita("bologna milan")
    