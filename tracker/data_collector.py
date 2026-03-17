# tracker/data_collector.py
import time
import threading
import psutil
from datetime import datetime
try:
    from pynput import keyboard, mouse
except:
    keyboard = None
    mouse = None

from django.utils import timezone
from .models import UserActivity

try:
    import win32gui
    import win32process
except ImportError:
    win32gui = None
    win32process = None

class DataCollector:
    def __init__(self):
        self.current_app = ""
        self.typing_speed = 0
        self.keystroke_count = 0
        self.start_time = time.time()
        self.app_switches = 0
        self.previous_app = ""
        self.is_collecting = False
        self.scroll_count = 0
        self.night_usage_time = 0
        self.consecutive_focus = 0
        self.last_app = ""
        
        self.APP_CATEGORIES = {
            "code": "productive",
            "visual studio": "productive",
            "vscode": "productive",
            "pycharm": "productive",
            "notepad": "productive",
            "word": "productive",
            "excel": "productive",
            "powerpoint": "productive",
            "youtube": "dopamine",
            "instagram": "dopamine",
            "whatsapp": "dopamine",
            "reddit": "dopamine",
            "facebook": "dopamine",
            "tiktok": "dopamine",
            "twitter": "dopamine",
            "netflix": "dopamine",
            "browser": "neutral",
            "explorer": "neutral",
            "terminal": "neutral"
        }
        
    def get_active_app(self):
        """Get currently active application (Windows)"""
        import os
        if os.name != 'nt':
            return "" # Return empty on non-Windows (Server)
            
        try:
            if not win32gui or not win32process:
                return "Unknown (Install pywin32)"
            
            def get_window_title(hwnd):
                return win32gui.GetWindowText(hwnd)
            
            def get_process_name(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    return process.name()
                except:
                    return "Unknown"
            
            # Get foreground window
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd: return "Desktop/Background"
            
            window_title = get_window_title(hwnd)
            process_name = get_process_name(hwnd)
            
            # Return meaningful app name
            if window_title or process_name:
                # Extract app name from window title or process
                title_lower = window_title.lower() if window_title else ""
                proc_lower = process_name.lower() if process_name else ""
                
                if "youtube" in title_lower:
                    return "YouTube"
                elif "instagram" in title_lower:
                    return "Instagram"
                elif "whatsapp" in title_lower:
                    return "WhatsApp Web"
                elif "reddit" in title_lower:
                    return "Reddit"
                elif "facebook" in title_lower:
                    return "Facebook"
                elif "chrome" in proc_lower or "msedge" in proc_lower:
                    return "Browser"
                elif "notepad" in proc_lower:
                    return "Notepad"
                elif "code" in proc_lower or "pycharm" in proc_lower:
                    return "Code Editor"
                elif "explorer" in proc_lower:
                    return "File Explorer"
                elif "cmd" in proc_lower or "powershell" in proc_lower:
                    return "Terminal"
                elif "word" in proc_lower:
                    return "Microsoft Word"
                elif "excel" in proc_lower:
                    return "Microsoft Excel"
                elif "powerpoint" in proc_lower:
                    return "Microsoft PowerPoint"
                else:
                    return process_name.replace('.exe', '').title()
            else:
                return "Desktop/Background"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def on_press(self, key):
        """Count keystrokes for typing speed calculation"""
        self.keystroke_count += 1

    def on_scroll(self, x, y, dx, dy):
        """Count mouse scrolls"""
        self.scroll_count += 1
    
    def get_category(self, app_name):
        for key, category in self.APP_CATEGORIES.items():
            if key in app_name.lower():
                return category
        return "neutral"
    
    def calculate_typing_speed(self):
        """Calculate typing speed in keys per minute"""
        current_time = time.time()
        time_elapsed = current_time - self.start_time
        if time_elapsed > 0:
            speed = (self.keystroke_count / time_elapsed) * 60
            self.keystroke_count = 0
            self.start_time = current_time
            return int(speed)
        return 0
    
    def detect_user_status(self, typing_speed, app_switches, scroll_count, is_night):
        """Simple rule-based status detection"""
        social_media = ["YouTube", "Instagram", "WhatsApp Web", "Reddit", "Facebook"]
        if is_night and self.current_app in social_media and typing_speed == 0:
            return "High Dopamine Risk"
        elif self.current_app in social_media and typing_speed == 0 and scroll_count > 10:
            return "Doomscrolling"
        elif app_switches > 5:
            return "Distracted"
        elif typing_speed < 10 and self.current_app not in ["Unknown", "Desktop", "Desktop/Background", "Browser", "File Explorer", "Terminal", ""]:
            return "Doomscrolling"
        elif typing_speed > 30 and app_switches <= 2:
            return "Focused"
        else:
            return "Neutral"
    
    def calculate_dopamine_score(self, typing_speed, app_switches, category):
        """Calculate simple dopamine score (0-100)"""
        base_score = min(typing_speed * 0.5 + app_switches * 10, 100)
        if category == "dopamine":
            base_score += 20
        elif category == "productive":
            base_score = max(base_score - 10, 0)
        return int(min(max(base_score, 0), 100))
    
    def collect_data(self):
        """Main data collection loop"""

        self.is_collecting = True
        
        # Start keyboard listener with robust error handling
        if keyboard:
            try:
                def on_press_wrapper(key):
                    try:
                        self.on_press(key)
                    except:
                        pass # Ignore listener internal errors
                
                keyboard_listener = keyboard.Listener(on_press=on_press_wrapper)
                keyboard_listener.daemon = True
                keyboard_listener.start()
            except Exception as e:
                print(f"Keyboard listener failed (Python 3.13 compatibility issue): {e}")

        # Start mouse listener with robust error handling
        if mouse:
            try:
                def on_scroll_wrapper(x, y, dx, dy):
                    try:
                        self.on_scroll(x, y, dx, dy)
                    except:
                        pass
                
                mouse_listener = mouse.Listener(on_scroll=on_scroll_wrapper)
                mouse_listener.daemon = True
                mouse_listener.start()
            except Exception as e:
                print(f"Mouse listener failed: {e}")
        
        while self.is_collecting:
            # Check if it's night time
            now = timezone.now()
            hour = now.hour
            is_night = hour >= 23 or hour <= 2
            
            # Update current app
            new_app = self.get_active_app()
            
            # Check for app switch
            if new_app != self.previous_app and self.previous_app != "":
                self.app_switches += 1
            
            self.current_app = new_app
            self.previous_app = new_app
            
            # Accumulate night usage time
            if is_night:
                self.night_usage_time += 5
            
            # Calculate metrics
            typing_speed = self.calculate_typing_speed()
            category = self.get_category(self.current_app)
            dopamine_score = self.calculate_dopamine_score(typing_speed, self.app_switches, category)
            status = self.detect_user_status(typing_speed, self.app_switches, self.scroll_count, is_night)
            
            # Check for deep focus session
            if self.current_app == self.last_app and typing_speed > 30 and self.app_switches < 2:
                self.consecutive_focus += 1
                if self.consecutive_focus >= 180:  # 15 minutes
                    status = "Deep Focus Session"
            else:
                self.consecutive_focus = 0
            
            self.last_app = self.current_app
            
            # Check for dopamine spike
            if self.app_switches > 5 and typing_speed < 5:
                status = "DOPAMINE SPIKE DETECTED"
            
            # Save to database (Only on Windows - preventing server-side dummy entries)
            import os
            if os.name == 'nt' and self.current_app:
                activity = UserActivity(
                    active_app=self.current_app,
                    typing_speed=typing_speed,
                    app_switch_count=self.app_switches,
                    dopamine_score=dopamine_score,
                    status=status
                )
                activity.save()
            
            # Reset counters for next period
            self.app_switches = 0
            self.scroll_count = 0
            
            # Wait 5 seconds before next collection
            time.sleep(5)
    
    def start_collection(self):
        """Start data collection in background thread"""
        thread = threading.Thread(target=self.collect_data)
        thread.daemon = True
        thread.start()
        print("Data collection started...")
    
    def stop_collection(self):
        """Stop data collection"""
        self.is_collecting = False
        print("Data collection stopped.")