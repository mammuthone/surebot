import asyncio
from playwright.async_api import async_playwright
import json
import os
import base64
from datetime import datetime

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
        self.browser = await playwright.chromium.launch(headless=False)  # headless=True per esecuzione senza UI
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        )
        
        # Crea una nuova pagina
        self.page = await self.context.new_page()
        
        # Imposta event listener per intercettare richieste e risposte
        self.page.on("request", self.handle_request)
        self.page.on("response", self.handle_response)
        
        print("Browser inizializzato con successo")
    
    async def handle_request(self, request):
        """Gestisce e intercetta le richieste di rete"""
        # Filtra solo le richieste che corrispondono al pattern specificato
        if self.api_pattern in request.url and request.resource_type in ["xhr", "fetch"]:
            try:
                # Cattura i dettagli della richiesta
                request_data = {
                    "request_id": request.url,  # Usa l'URL come ID per collegare richiesta e risposta
                    "url": request.url,
                    "method": request.method,
                    "headers": request.headers,
                    "resource_type": request.resource_type,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Prova a catturare il body della richiesta se disponibile
                if request.post_data:
                    try:
                        # Prova a parsare come JSON
                        request_data["body"] = json.loads(request.post_data)
                    except:
                        # Altrimenti salva come testo
                        request_data["body"] = request.post_data
                
                self.captured_requests.append(request_data)
                print(f"Intercettata richiesta {request.method} {request.url}")
            except Exception as e:
                print(f"Errore nell'analisi della richiesta: {e}")
    
    async def handle_response(self, response):
        """Gestisce e intercetta le risposte di rete"""
        # Ottieni la richiesta associata a questa risposta
        request = response.request
        
        # Filtra solo le risposte a richieste che corrispondono al pattern specificato
        if self.api_pattern in request.url and request.resource_type in ["xhr", "fetch"]:
            try:
                # Cerca la richiesta corrispondente nei dati catturati usando l'URL come identificatore
                matching_requests = [r for r in self.captured_requests if r["url"] == request.url and "response" not in r]
                
                if matching_requests:
                    # Trova la richiesta più recente che corrisponde a questo URL
                    request_entry = matching_requests[-1]
                    
                    # Ottieni il body della risposta
                    try:
                        # Tenta di ottenere il body come JSON
                        response_body = await response.json()
                    except:
                        try:
                            # Se non è JSON, prova a ottenere come testo
                            response_body = await response.text()
                        except:
                            response_body = "Impossibile estrarre il body della risposta"
                    
                    # Aggiungi le informazioni della risposta all'entrata della richiesta
                    request_entry["response"] = {
                        "status": response.status,
                        "status_text": response.status_text,
                        "headers": response.headers,
                        "body": response_body
                    }
                    
                    print(f"Intercettata risposta per {request.method} {request.url}: {response.status}")
                    
                    # Se la risposta contiene la proprietà "items" in base64, decodificala
                    if isinstance(response_body, dict) and "items" in response_body:
                        try:
                            # Decodifica il contenuto base64
                            decoded_data = self.decode_base64_items(response_body["items"])
                            # Salva i dati decodificati in un file JSON separato
                            self.save_decoded_items(decoded_data)
                        except Exception as e:
                            print(f"Errore nella decodifica base64: {e}")
            except Exception as e:
                print(f"Errore nell'analisi della risposta: {e}")
    
    def decode_base64_items(self, base64_data):
        """Decodifica i dati base64 della proprietà items"""
        try:
            # Decodifica da base64 a bytes
            decoded_bytes = base64.b64decode(base64_data)
            # Converti i bytes in stringa
            decoded_str = decoded_bytes.decode('utf-8')
            # Parse della stringa JSON in oggetto Python
            decoded_json = json.loads(decoded_str)
            return decoded_json
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
            # Naviga alla pagina di login
            print(f"Navigazione verso {self.url}")
            await self.page.goto(self.url)
            
            # Attendi che la pagina sia completamente caricata
            await self.page.wait_for_load_state("networkidle")
            
            # Login usando i selettori corretti
            await self.page.get_by_role("textbox", name="Nome utente o email").fill(self.username)
            await self.page.get_by_role("textbox", name="Password").fill(self.password)
            await self.page.get_by_role("button", name="Login").click()
            
            # Attendi che il login sia completato
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
    
    async def analyze_page(self, wait_time=7):
        """Analizza la pagina e attende le richieste XHR"""
        try:
            print(f"Analisi della pagina in corso... (attesa: {wait_time} secondi)")
            
            # Attendi il tempo specificato per catturare le richieste XHR/fetch
            await asyncio.sleep(wait_time)
            
            # Puoi anche interagire con elementi nella pagina per attivare richieste specifiche
            # Esempio: await self.page.click('#some-button-that-triggers-xhr')
            
            print(f"Analisi completata. Richieste XHR/fetch catturate: {len(self.captured_requests)}")
            return True
        except Exception as e:
            print(f"Errore durante l'analisi della pagina: {e}")
            return False
    
    def save_captured_requests(self, filename="captured_requests.json"):
        """Salva le richieste catturate in un file JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.captured_requests, f, indent=2, ensure_ascii=False)
            print(f"Richieste salvate nel file: {filename}")
            return filename
        except Exception as e:
            print(f"Errore durante il salvataggio delle richieste: {e}")
            return None
    
    def get_items_from_responses(self):
        """Estrae e decodifica gli items dalle risposte"""
        for entry in self.captured_requests:
            if "response" in entry and isinstance(entry["response"]["body"], dict) and "items" in entry["response"]["body"]:
                print(f"Trovata risposta con campo 'items' in: {entry['url']}")
                try:
                    decoded_data = self.decode_base64_items(entry["response"]["body"]["items"])
                    if decoded_data:
                        self.save_decoded_items(decoded_data)
                        return decoded_data
                except Exception as e:
                    print(f"Errore nell'estrazione degli items: {e}")
        print("Nessuna risposta con campo 'items' trovata")
        return None
    
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
    api_pattern = "getItems"  # Pattern per filtrare le richieste
    
    # Inizializza e esegui il bot
    bot = PlaywrightBot(login_url, username, password, target_page_url, api_pattern)
    
    try:
        # Inizializza il browser
        await bot.initialize()
        
        # Effettua il login
        login_success = await bot.login()
        if not login_success:
            print("Impossibile continuare a causa del fallimento del login")
            await bot.close()
            return
        
        # Naviga alla pagina target
        navigation_success = await bot.navigate_to_target_page()
        if not navigation_success:
            print("Impossibile continuare a causa del fallimento della navigazione")
            await bot.close()
            return
        
        # Analizza la pagina e intercetta le richieste XHR
        await bot.analyze_page(wait_time=15)
        
        # Estrai e decodifica gli items dalle risposte
        items_data = bot.get_items_from_responses()
        
        if items_data:
            print("Dati 'items' estratti e decodificati con successo!")
        else:
            print("Non è stato possibile estrarre i dati 'items'")
        
        # Salva comunque tutte le richieste catturate
        saved_file = bot.save_captured_requests()
        if saved_file:
            print(f"Processo completato con successo. Tutte le richieste salvate in {saved_file}")
    
    finally:
        # Assicurati di chiudere il browser alla fine
        await bot.close()

if __name__ == "__main__":
    # Esegui il bot
    asyncio.run(main())