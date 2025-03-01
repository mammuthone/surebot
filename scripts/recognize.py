import pytesseract
from PIL import Image

def riconosci_testo(percorso_immagine):
    # Apri l'immagine
    img = Image.open(percorso_immagine)
    
    # Estrai il testo
    testo = pytesseract.image_to_string(img, lang="ita")
    
    return testo

if __name__ == "__main__":
    testo = sys.argv[1]
    testo_estratto = riconosci_testo(testo)
    print("Testo riconosciuto:")
    print(testo_estratto)