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
        self.last_detected_app = ""
        self.app_switches = 0
        self.current_app = "Desktop"
        self.lock = threading.Lock()
        
    def get_active_app_raw(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd: return "Desktop"
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().replace('.exe', '').title()
            window_title = win32gui.GetWindowText(hwnd).lower()
            
            # Smart detection
            if "youtube" in window_title: return "YouTube"
            if "instagram" in window_title: return "Instagram"
            if "whatsapp" in window_title: return "WhatsApp"
            if "netflix" in window_title: return "Netflix"
            if "vlc" in process_name.lower(): return "VLC Media Player"
            if "chrome" in process_name.lower(): return "Google Chrome"
            if "msedge" in process_name.lower(): return "Microsoft Edge"
            if "firefox" in process_name.lower(): return "Firefox"
            if "code" in process_name.lower(): return "VS Code"
            if "discord" in process_name.lower(): return "Discord"
            if "spotify" in process_name.lower(): return "Spotify"
            
            return process_name
        except:
            return "Desktop"

    def app_monitor_loop(self):
        """High-frequency thread to catch every single app switch"""
        while True:
            curr = self.get_active_app_raw()
            with self.lock:
                if curr != self.last_detected_app:
                    if self.last_detected_app != "":
                        self.app_switches += 1
                    self.last_detected_app = curr
                self.current_app = curr
            time.sleep(0.5) # Check twice a second

    def on_press(self, key):
        with self.lock:
            self.keystroke_count += 1

    def calculate_report_data(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            kpm = int((self.keystroke_count / elapsed) * 60) if elapsed > 0 else 0
            
            # Extract data for report
            data = {
                "app": self.current_app,
                "typing_speed": kpm,
                "switches": self.app_switches,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            
            # Reset interval counters
            self.keystroke_count = 0
            self.start_time = time.time()
            self.app_switches = 0
            
            return data

    def run(self):
        print(f"==========================================")
        print(f"🚀 Digital Dopamine Live Tracker")
        print(f"📡 Status: Sending to {SERVER_URL}")
        print(f"==========================================")
        
        # Start high-frequency app monitor thread
        monitor_thread = threading.Thread(target=self.app_monitor_loop, daemon=True)
        monitor_thread.start()
        
        # Start keyboard listener
        try:
            def on_press_wrapper(key):
                try: self.on_press(key)
                except: pass
            
            listener = keyboard.Listener(on_press=on_press_wrapper)
            listener.daemon = True
            listener.start()
            print("⌨️  Keyboard tracking: ACTIVE")
        except Exception as e:
            print(f"⚠️  Keyboard tracking: FAILED (Using app tracking only)")
        
        while True:
            try:
                data = self.calculate_report_data()
                
                # Basic terminal feedback
                print(f"[{data['timestamp']}] Active: {data['app']} | Speed: {data['typing_speed']} KPM | Switches: {data['switches']}")
                
                response = requests.post(f"{SERVER_URL}/api/report/", json=data, timeout=5)
                if response.status_code != 200:
                    print(f"❌ Server Error: {response.status_code}")
                
            except Exception as e:
                print(f"🌐 Connection Error: {e}")
            
            time.sleep(7)

if __name__ == "__main__":
    client = ActivityClient()
    client.run()
