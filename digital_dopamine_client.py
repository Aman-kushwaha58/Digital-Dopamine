import time
import requests
import psutil
import threading
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
# This MUST be your live Render URL
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
            if "vlc" in process_name.lower(): return "VLC Player"
            if "chrome" in process_name.lower(): return "Chrome"
            if "msedge" in process_name.lower(): return "Edge"
            if "code" in process_name.lower(): return "VS Code"
            
            return process_name
        except:
            return "Desktop"

    def app_monitor_loop(self):
        while True:
            curr = self.get_active_app_raw()
            with self.lock:
                if curr != self.last_detected_app:
                    if self.last_detected_app != "":
                        self.app_switches += 1
                    self.last_detected_app = curr
                self.current_app = curr
            time.sleep(0.5)

    def on_press(self, key):
        with self.lock:
            self.keystroke_count += 1

    def calculate_report_data(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            kpm = int((self.keystroke_count / elapsed) * 60) if elapsed > 0 else 0
            
            data = {
                "app": self.current_app,
                "typing_speed": kpm,
                "switches": self.app_switches,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            
            self.keystroke_count = 0
            self.start_time = time.time()
            self.app_switches = 0
            return data

    def test_connection(self):
        print(f"📡 Testing connection to {SERVER_URL}...")
        try:
            # Test simple GET to stats to verify server is up
            response = requests.get(f"{SERVER_URL}/api/stats/", timeout=10)
            if response.status_code == 200:
                print("✅ Connection Successful! Server is responsive.")
                return True
            else:
                print(f"❌ Server returned status {response.status_code}. Please check your Render logs.")
                return False
        except Exception as e:
            print(f"❌ Connection Failed: {e}")
            print("💡 Tip: Make sure the SERVER_URL is correct and your Render app is active.")
            return False

    def run(self):
        print("==========================================")
        print("🧠 Digital Dopamine Desktop Client")
        print("==========================================")
        
        if not self.test_connection():
            print("⚠️ Proceeding anyway, but data may not be saved.")

        # Start background threads
        threading.Thread(target=self.app_monitor_loop, daemon=True).start()
        
        try:
            listener = keyboard.Listener(on_press=lambda k: self.on_press(k))
            listener.daemon = True
            listener.start()
            print("⌨️  Keyboard monitoring: ACTIVE")
        except:
            print("⚠️  Keyboard monitoring: FAILED")
        
        print(f"🚀 Tracking started. Reporting every 7s to Cloud.")
        
        while True:
            try:
                data = self.calculate_report_data()
                response = requests.post(f"{SERVER_URL}/api/report/", json=data, timeout=10)
                
                if response.status_code == 200:
                    print(f"[{data['timestamp']}] ✅ Sent: {data['app']} | {data['typing_speed']} KPM")
                else:
                    print(f"[{data['timestamp']}] ❌ Sync Error ({response.status_code})")
                    
            except Exception as e:
                print(f"🌐 Cloud Connection Error: {e}")
            
            time.sleep(7)

if __name__ == "__main__":
    client = ActivityClient()
    client.run()
