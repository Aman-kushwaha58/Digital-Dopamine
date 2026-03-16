# test_template_find.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_dopamine_project.settings')
django.setup()

from django.template.loader import get_template
from django.conf import settings

print("=== Testing Template Discovery ===")

# Check if file exists
template_path = os.path.join('tracker', 'templates', 'tracker', 'dashboard.html')
print(f"File exists: {os.path.exists(template_path)}")
print(f"Full path: {os.path.abspath(template_path)}")

# Try to load template
try:
    template = get_template('tracker/dashboard.html')
    print("✅ SUCCESS: Template loaded!")
    print(f"Template origin: {template.origin}")
except Exception as e:
    print(f"❌ ERROR loading template: {e}")

# Check template loaders
print("\n=== Template Loaders ===")
for loader in settings.TEMPLATES[0]['OPTIONS']['loaders']:
    print(f"Loader: {loader}")