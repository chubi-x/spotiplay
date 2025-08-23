"""
WSGI entry point for the Spotiplay application.
This file is used by production WSGI servers like Gunicorn to serve the app.
"""

from app import app

if __name__ == "__main__":
    app.run()

