import os

import requests

SERVER_URL = os.getenv('SERVER_URL') or "http://localhost:8000"
USER = os.getenv('USERNAME') or "admin"
PASSWORD = os.getenv('PASSWORD') or "reset123"

session = requests.Session()
session.auth = (USER, PASSWORD)
resp = session.get(f"{SERVER_URL}/users/")
resp.raise_for_status()

return resp.json()
