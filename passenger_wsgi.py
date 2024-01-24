# passenger_wsgi.py
import sys, os

# Adjust the Python version in the next line as necessary
INTERP = os.path.expanduser("~/chefgpt.adamyuras.com/venv/bin/python3")

# INTERP is present twice so that the new Python interpreter
# knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

from app import app as application
