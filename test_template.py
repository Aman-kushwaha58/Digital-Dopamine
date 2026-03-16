# test_template.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_dopamine_project.settings')
django.setup()

from django.template.loader import get_template

try:
    template = get_template('tracker/dashboard.html')
    print("✅ SUCCESS: Template found!")
    print(f"Template path: {template.origin}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    
# Check file existence
import os
template_path = os.path.join('tracker', 'templates', 'tracker', 'dashboard.html')
print(f"File exists: {os.path.exists(template_path)}")
print(f"Full path: {os.path.abspath(template_path)}")