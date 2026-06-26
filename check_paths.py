import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"BASE_DIR: {BASE_DIR}")
print(f"Contents: {os.listdir(BASE_DIR)}")

data_dir = os.path.join(BASE_DIR, 'state-electric-data')
if os.path.exists(data_dir):
    print(f"state-electric-data contents: {os.listdir(data_dir)}")
else:
    print("state-electric-data/ NOT FOUND in app directory")

# Show .gitignore to see if we're ignoring it
git_file = os.path.join(BASE_DIR, '.gitignore')
if os.path.exists(git_file):
    with open(git_file) as f:
        content = f.read()
        if 'state-electric-data' in content:
            print("WARNING: state-electric-data is in .gitignore!")
