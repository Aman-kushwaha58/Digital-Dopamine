# test_collector.py
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_dopamine_project.settings')
django.setup()

from tracker.data_collector import DataCollector

def test_real_detection():
    print("🧪 Testing Real App Detection...")
    
    collector = DataCollector()
    
    # Test app detection without starting collection
    print("🔍 Testing app detection (switch between different apps)...")
    for i in range(10):
        app_name = collector.get_active_app()
        print(f"Detected app: {app_name}")
        time.sleep(2)
    
    print("✅ Real app detection test completed!")

if __name__ == "__main__":
    test_real_detection()