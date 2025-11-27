# auth.py

VALID_USERNAME = "admin"
VALID_PASSWORD = "flowmetriq"

def check_credentials(username, password):
    return username == VALID_USERNAME and password == VALID_PASSWORD
