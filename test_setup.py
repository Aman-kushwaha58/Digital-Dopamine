# test_setup.py
try:
    import Django
    import psutil
    import pynput
    print("✅ Core dependencies installed successfully!")
    print(f"✅ Django version: {Django.__version__}")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")