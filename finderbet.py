import asyncio
from playwright.async_api import async_playwright
import json
import os
from datetime import datetime

class PlaywrightBot:
    def __init__(self, url, username, password, target_page_url):
        self.url = url
        self.username = username
        self.password = password
        self.target_page_url = target_page_url
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
        
        # Abilita il tracciamento delle richieste di rete
        await self.context.route("**/*", self.route_handler)
        
        # Crea una nuova pagina
        self.page = await self.context.new_page()
        print("Browser inizializzato con successo")
    
    async def route_handler(self, route, request):
        """Gestisce e intercetta le richieste di rete"""
        # Continua con la richiesta originale
        await route.continue_()
        
        # Filtra solo le richieste XHR/fetch
        if request.resource_type in ["xhr", "fetch"]:
            try:
                # Cattura i dettagli della richiesta
                request_data = {
                    "url": request.url,
                    "method": request.method,
                    "headers": request.headers,
                    "resource_type": request.resource_type,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Prova a catturare il body della richiesta se disponibile
                if hasattr(request, "post_data") and request.post_data:
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
    
    async def login(self):
        """Visita la pagina di login ed effettua l'autenticazione"""
        try:
            # Naviga alla pagina di login
            print(f"Navigazione verso {self.url}")
            await self.page.goto(self.url)
            
            # await self.page.pause()
            # Attendi che la pagina sia completamente caricata
            await self.page.wait_for_load_state("networkidle")
            
            # Qui devi adattare i selettori in base alla struttura della pagina di login
            # Esempio generico:
            await self.page.get_by_role("textbox", name="Nome utente o email").fill(self.username)
            await self.page.get_by_role("textbox", name="Password").fill(self.password)
            await self.page.get_by_role("button", name="Login").click()
            
            # Attendi che il login sia completato
            # Potresti dover modificare questo in base al comportamento del sito
            await self.page.wait_for_load_state("networkidle")
            return True
            # Verifica se il login è riuscito (adatta in base al tuo caso)
            # Esempio: controlla se esiste un elemento che appare solo dopo il login
            # if await self.page.is_visible('.user-profile') or await self.page.is_visible('.dashboard'):
            #     print("Login effettuato con successo")
            #     return True
            # else:
            #     print("Login fallito")
            #     return False
                
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
    
    async def analyze_page(self, wait_time=10):
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
    
    async def close(self):
        """Chiude il browser e le risorse"""
        if self.browser:
            await self.browser.close()
            print("Browser chiuso")

    async def handle_response(self, response):
        """Gestisce e intercetta le risposte di rete"""
        # Ottieni la richiesta associata a questa risposta
        request = response.request
        
        # Filtra solo le risposte a richieste XHR/fetch
        if request.resource_type in ["xhr", "fetch"]:
            try:
                # Crea un ID per collegare questa risposta alla richiesta corrispondente
                request_id = request.url + "_" + datetime.now().isoformat()
                
                # Cerca la richiesta corrispondente nei dati catturati
                # Nota: potrebbe non essere esatta a causa dell'ID basato sul timestamp
                matching_requests = [r for r in self.captured_data if r["url"] == request.url and r.get("response") is None]
                
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
            except Exception as e:
                print(f"Errore nell'analisi della risposta: {e}")

    def find_response_by_url_pattern(self, url_pattern):
        """Trova una risposta specifica in base a un pattern di URL"""
        matching_entries = [entry for entry in self.captured_requests 
            if url_pattern in entry["url"]]
        
        print(matching_entries)

        
        if matching_entries:
            print(f"Trovate {len(matching_entries)} risposte per il pattern '{url_pattern}'")
            return matching_entries
        else:
            print(f"Nessuna risposta trovata per il pattern '{url_pattern}'")
            return []
    
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
    api_pattern = "bet/v1/getItems"
    
    # Inizializza e esegui il bot
    bot = PlaywrightBot(login_url, username, password, target_page_url)
    
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
        
        # Salva le richieste catturate
        # saved_file = bot.save_captured_requests()
        # if saved_file:
        #     print(f"Processo completato con successo. Risultati salvati in {saved_file}")
    
        target_responses = bot.find_response_by_url_pattern(api_pattern)

        if target_responses:
            for i, entry in enumerate(target_responses):
                print(f"\nRisposta {i+1}:")
                print(f"URL: {entry['url']}")
                print(f"Metodo: {entry['method']}")
                print(f"Stato: {entry['response']['status']}")
                print("Corpo della risposta:")
                print(json.dumps(entry['response']['body'], indent=2))
        
        # Salva comunque tutti i dati catturati
        saved_file = bot.save_captured_requests()
        if saved_file:
            print(f"Processo completato con successo. Tutti i dati salvati in {saved_file}")
    
    finally:
        # Assicurati di chiudere il browser alla fine
        await bot.close()

if __name__ == "__main__":
    # Esegui il bot
    asyncio.run(main())