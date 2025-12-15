# tracker/data_collector.py
from .models import UserActivity
import psutil
import time
import threading
from datetime import datetime
from pynput import keyboard

class DataCollector:
    def __init__(self):
        self.current_app = ""
        self.typing_speed = 0
        self.keystroke_count = 0
        self.start_time = time.time()
        self.app_switches = 0
        self.previous_app = ""
        self.is_collecting = False
        
    def get_active_app(self):
        """Get currently active application (Windows)"""
        try:
            import win32gui
            import win32process
            import psutil
            
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
            window_title = get_window_title(hwnd)
            process_name = get_process_name(hwnd)
            
            # Return meaningful app name
            if window_title:
                # Extract app name from window title or process
                if "chrome" in process_name.lower() or "msedge" in process_name.lower():
                    return "Browser"
                elif "notepad" in process_name.lower():
                    return "Notepad"
                elif "code" in process_name.lower() or "pycharm" in process_name.lower():
                    return "Code Editor"
                elif "explorer" in process_name.lower():
                    return "File Explorer"
                elif "cmd" in process_name.lower() or "powershell" in process_name.lower():
                    return "Terminal"
                elif "word" in process_name.lower():
                    return "Microsoft Word"
                elif "excel" in process_name.lower():
                    return "Microsoft Excel"
                elif "powerpoint" in process_name.lower():
                    return "Microsoft PowerPoint"
                else:
                    # Return process name without .exe
                    return process_name.replace('.exe', '').title()
            else:
                return "Desktop/Background"
                
        except ImportError:
            # Fallback if win32gui not available
            return "Unknown (Install pywin32)"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def on_press(self, key):
        """Count keystrokes for typing speed calculation"""
        self.keystroke_count += 1
    
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
    
    def detect_user_status(self, typing_speed, app_switches):
        """Simple rule-based status detection"""
        if app_switches > 5:
            return "Distracted"
        elif typing_speed < 10 and self.current_app != "Unknown":
            return "Doomscrolling"
        elif typing_speed > 30 and app_switches <= 2:
            return "Focused"
        else:
            return "Neutral"
    
    def calculate_dopamine_score(self, typing_speed, app_switches):
        """Calculate simple dopamine score (0-100)"""
        base_score = min(typing_speed * 0.5 + app_switches * 10, 100)
        return int(min(max(base_score, 0), 100))
    
    def collect_data(self):
        """Main data collection loop"""
        keyboard_listener = keyboard.Listener(on_press=self.on_press)
        keyboard_listener.start()
        
        self.is_collecting = True
        
        while self.is_collecting:
            # Update current app
            new_app = self.get_active_app()
            
            # Check for app switch
            if new_app != self.previous_app and self.previous_app != "":
                self.app_switches += 1
            
            self.current_app = new_app
            self.previous_app = new_app
            
            # Calculate metrics
            typing_speed = self.calculate_typing_speed()
            dopamine_score = self.calculate_dopamine_score(typing_speed, self.app_switches)
            status = self.detect_user_status(typing_speed, self.app_switches)
            
            # Save to database
            activity = UserActivity(
                active_app=self.current_app,
                typing_speed=typing_speed,
                app_switch_count=self.app_switches,
                dopamine_score=dopamine_score,
                status=status
            )
            activity.save()
            
            # Reset app switches for next period
            self.app_switches = 0
            
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