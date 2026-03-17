import time
import requests
import psutil
import threading
from datetime import datetime

# CONFIGURATION
# Set this to your Render URL (e.g., 'https://digital-dopamine.onrender.com')
SERVER_URL = "https://digital-dopamine-2.onrender.com" 

try:
    import win32gui
    import win32process
    from pynput import keyboard
except ImportError:
    print("Dependencies missing! Run: pip install pywin32 pynput requests psutil")
    exit()

class ActivityClient:
    def __init__(self):
        self.keystroke_count = 0
        self.start_time = time.time()
        self.last_app = ""
        self.app_switches = 0
        
    def get_active_app(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().replace('.exe', '').title()
            window_title = win32gui.GetWindowText(hwnd).lower()
            
            # Smart detection
            if "youtube" in window_title: return "YouTube"
            if "instagram" in window_title: return "Instagram"
            if "whatsapp" in window_title: return "WhatsApp"
            if "code" in process_name.lower(): return "VS Code"
            
            return process_name
        except:
            return "Desktop"

    def on_press(self, key):
        self.keystroke_count += 1

    def calculate_stats(self):
        curr_app = self.get_active_app()
        if curr_app != self.last_app and self.last_app != "":
            self.app_switches += 1
        
        elapsed = time.time() - self.start_time
        kpm = int((self.keystroke_count / elapsed) * 60) if elapsed > 0 else 0
        
        # Reset counters
        self.keystroke_count = 0
        self.start_time = time.time()
        switches = self.app_switches
        self.app_switches = 0
        self.last_app = curr_app
        
        return {
            "app": curr_app,
            "typing_speed": kpm,
            "switches": switches,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

    def run(self):
        print(f"Digital Dopamine Client starting... Sending to {SERVER_URL}")
        
        # Start keyboard listener with robust error handling for Python 3.13 compatibility
        try:
            def on_press_wrapper(key):
                try:
                    self.on_press(key)
                except:
                    pass
            
            listener = keyboard.Listener(on_press=on_press_wrapper)
            listener.daemon = True
            listener.start()
        except Exception as e:
            print(f"Keyboard tracking failed (Python 3.13 issue): {e}. Continuing with app tracking only.")
        
        while True:
            try:
                data = self.calculate_stats()
                # Basic status rules
                speed = int(data.get('typing_speed', 0))
                switches = int(data.get('switches', 0))
                
                if speed > 30: data['status'] = "Focused"
                elif switches > 3: data['status'] = "Distracted"
                else: data['status'] = "Neutral"
                
                # Simple dopamine score logic
                raw_score = float(speed * 0.5 + switches * 15)
                data['dopamine_score'] = int(min(100.0, raw_score))
                
                response = requests.post(f"{SERVER_URL}/api/report/", json=data, timeout=5)
                if response.status_code == 200:
                    print(f"[{data['timestamp']}] Report successful: {data['app']} ({data['typing_speed']} KPM)")
                else:
                    print(f"Error: Server returned {response.status_code}")
            except Exception as e:
                print(f"Connection failed: {e}")
            
            time.sleep(7)

if __name__ == "__main__":
    client = ActivityClient()
    client.run()
