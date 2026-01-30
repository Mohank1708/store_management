# WSGI configuration for PythonAnywhere
import sys
import os

# Add the project directory to the path
project_home = '/home/YOUR_USERNAME/store_management'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the working directory
os.chdir(project_home)

# Import the Flask app
from app import app as application

# Initialize database on first run
from database import init_db
init_db()
