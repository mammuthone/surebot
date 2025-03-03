import subprocess
import asyncio
from playwright.async_api import async_playwright
import json
import base64
from datetime import datetime
import socket

class PlaywrightBot:
    def __init__(self, url, username, password, target_page_url, api_pattern):
        self.url = url
        self.username = username
        self.password = password
        self.target_page_url = target_page_url
        self.api_pattern = api_pattern
        self.captured_requests = []
        self.browser = None
        self.context = None
        self.page = None
    
    async def initialize(self):
        """Inizializza il browser Playwright"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        )
        
        # Crea una nuova pagina e configura gli event listener
        self.page = await self.context.new_page()
        self.page.on("response", self.handle_response)
        print("Browser inizializzato con successo")
    
    async def handle_response(self, response):
        """Gestisce e intercetta le risposte di rete"""
        # Filtra solo le risposte di tipo XHR/fetch che contengono il pattern specificato
        request = response.request
        if self.api_pattern in request.url and request.resource_type in ["xhr", "fetch"]:
            try:
                # Ottieni il body della risposta
                try:
                    response_body = await response.json()
                except:
                    try:
                        response_body = await response.text()
                    except:
                        print(f"Impossibile estrarre il body della risposta per: {request.url}")
                        return
                
                # Salva i dettagli della richiesta/risposta
                request_data = {
                    "url": request.url,
                    "method": request.method,
                    "resource_type": request.resource_type,
                    "timestamp": datetime.now().isoformat(),
                    "response": {
                        "status": response.status,
                        "body": response_body
                    }
                }
                
                self.captured_requests.append(request_data)
                print(f"Intercettata risposta per {request.method} {request.url}: {response.status}")
                
                # Se la risposta contiene la proprietà "items" in base64, decodificala immediatamente
                if isinstance(response_body, dict) and "items" in response_body:
                    try:
                        decoded_data = self.decode_base64_items(response_body["items"])
                        if decoded_data:
                            filtered_data = [ x for x in decoded_data if x["sport"] == "Calcio" ]
                        if filtered_data:
                            self.save_decoded_items(filtered_data)
                            print(f"Dati 'items' estratti e decodificati con successo!")
                    except Exception as e:
                        print(f"Errore nella decodifica base64: {e}")
            except Exception as e:
                print(f"Errore nell'analisi della risposta: {e}")
    
    def decode_base64_items(self, base64_data):
        """Decodifica i dati base64 della proprietà items"""
        try:
            decoded_bytes = base64.b64decode(base64_data)
            decoded_str = decoded_bytes.decode('utf-8')
            return json.loads(decoded_str)
        except Exception as e:
            print(f"Errore nella decodifica base64: {e}")
            return None
    
    def save_decoded_items(self, decoded_data, filename="decoded_items.json"):
        """Salva i dati decodificati in un file JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(decoded_data, f, indent=2, ensure_ascii=False)
            print(f"Dati decodificati salvati nel file: {filename}")
            return filename
        except Exception as e:
            print(f"Errore durante il salvataggio dei dati decodificati: {e}")
            return None
    
    async def login(self):
        """Visita la pagina di login ed effettua l'autenticazione"""
        try:
            print(f"Navigazione verso {self.url}")
            await self.page.goto(self.url)
            await self.page.wait_for_load_state("networkidle")
            
            # Login usando i selettori
            await self.page.get_by_role("textbox", name="Nome utente o email").fill(self.username)
            await self.page.get_by_role("textbox", name="Password").fill(self.password)
            await self.page.get_by_role("button", name="Login").click()
            
            await self.page.wait_for_load_state("networkidle")
            print("Login effettuato con successo")
            return True
        except Exception as e:
            print(f"Errore durante il login: {e}")
            return False
    
    async def navigate_to_target_page(self):
        """Naviga alla pagina target dopo il login"""
        try:
            print(f"Navigazione verso la pagina target: {self.target_page_url}")
            await self.page.goto(self.target_page_url)
            await self.page.wait_for_load_state("networkidle")
            print("Navigazione completata")
            return True
        except Exception as e:
            print(f"Errore durante la navigazione alla pagina target: {e}")
            return False
    
    async def wait_for_api_calls(self, wait_time=7):
        """Attende che avvengano le chiamate API"""
        print(f"Attesa di {wait_time} secondi per le chiamate API...")
        await asyncio.sleep(wait_time)
        print(f"Attesa completata. Richieste catturate: {len(self.captured_requests)}")
        return True
    
    async def close(self):
        """Chiude il browser e le risorse"""
        if self.browser:
            await self.browser.close()
            print("Browser chiuso")

async def main():
    # Configura i parametri per il bot
    login_url = "https://www.finderbet.com/login/"
    username = "perconte@hotmail.it"
    password = "80sumellU!"
    target_page_url = "https://www.finderbet.com/surebet/"
    api_pattern = "getItems"
    
    # Inizializza e esegui il bot
    bot = PlaywrightBot(login_url, username, password, target_page_url, api_pattern)
    
    try:
        # Inizializza il browser
        await bot.initialize()
        
        # Esegui la sequenza: login -> navigazione -> attesa
        if await bot.login() and await bot.navigate_to_target_page():
            await bot.wait_for_api_calls()
            
            # Verifica se abbiamo catturato la risposta che cerchiamo
            items_found = any(
                isinstance(req.get("response", {}).get("body"), dict) and 
                "items" in req.get("response", {}).get("body", {})
                for req in bot.captured_requests
            )
            
            if items_found:
                print("Operazione completata con successo!")
            else:
                print("Nessuna risposta con campo 'items' trovata!")
        
    finally:
        # Chiudi il browser alla fine
        await bot.close()
        try:
            server_address = ("127.0.0.1", 9999)  # IP e porta del server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(server_address)
            message = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "captured_requests": len(bot.captured_requests),
                "action": "DATA_DECODED"
            }
            # Converti il JSON in stringa e invialo
            json_message = json.dumps(message)
            client_socket.sendall(json_message.encode("utf-8"))
        except Exception as e:
            print(f"Errore nell'invio del messaggio al server: {e}")
        # subprocess.run(["python", "dealer.py"])

if __name__ == "__main__":
    # Esegui il bot
    asyncio.run(main())