import subprocess
import time
import cv2
import numpy as np

SCREENSHOT_PATH = "/sdcard/screen.png"
LOCAL_SCREENSHOT_PATH = "screen.png"



def take_screenshot():
    """Cattura uno screenshot con ADB e lo salva in locale."""
    print("Catturando screenshot...")
    exec_adb_command(f"adb shell screencap -p {SCREENSHOT_PATH}")
    exec_adb_command(f"adb pull {SCREENSHOT_PATH} {LOCAL_SCREENSHOT_PATH}")
    print("Screenshot salvato.")


def find_button(threshold=0.95):
    """Trova un elemento nell'immagine usando il template matching e visualizza il risultato."""
    screenshot = cv2.imread(LOCAL_SCREENSHOT_PATH, cv2.IMREAD_GRAYSCALE)

    # screenshot = cv2.imread("screen.png")

    # Definisci le coordinate della regione di interesse (ROI)
    x, y, w, h = 885, 120, 135, 35  # (x, y, width, height)

    # Ritaglia la porzione dallo screenshot
    cropped_image = screenshot[y:y+h, x:x+w]

    # Salva o visualizza l'immagine ritagliata
    cv2.imwrite("cropped.png", cropped_image)
    cv2.imshow("Cropped", cropped_image)
    template = cv2.imread("cropped.png", cv2.IMREAD_GRAYSCALE)
    print(f"Screenshot size: {screenshot.shape}")  # (altezza, larghezza)
    print(f"Template size: {template.shape}")
    cv2.waitKey(0)
    cv2.destroyAllWindows()



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

def launch_sisal_app():
    try:
        # Lancia l'app Sisal tramite ADB monkey
        exec_adb_command("adb shell monkey -p it.betway 1")

        print("App Betway avviata con successo")
        
        # Attendi il caricamento dell'app
        time.sleep(6)

        take_screenshot()

        return True
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'avvio dell'app Sisal: {e}")
        print(f"Output di errore: {e.stderr}")
        return False

if __name__ == "__main__":
    # launch_sisal_app()
    take_screenshot()

    position = find_button()
    if position:
        x, y = position
        tap_on_button(x + 10, y + 10)  # Centr