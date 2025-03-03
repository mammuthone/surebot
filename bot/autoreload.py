import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = script_path
        self.process = None

    def restart_app(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
        
        self.process = subprocess.Popen([sys.executable, self.script_path])

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"File modificato: {event.src_path}")
            self.restart_app()

def start_reload_watcher(script_path):
    event_handler = ReloadHandler(script_path)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    
    try:
        event_handler.restart_app()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    start_reload_watcher('finderbet_gui.py')