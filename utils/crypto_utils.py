import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env"))

def odin_encrypt(plain_text):
    """Encrypt a value with the configured ODIN key."""
    if plain_text is None: 
        return None
    try:
        key = os.environ.get("ODIN_KEY")
        if not key:
            raise ValueError("ODIN_KEY not found in environment variables")
        cipher_suite = Fernet(key.encode())
        encrypted_text = cipher_suite.encrypt(str(plain_text).encode())
        return encrypted_text.decode()
    except Exception as e:
        return f"ENCRYPTION_ERROR: {str(e)}"

def odin_decrypt(encrypted_text):
    """Decrypt a value with the configured ODIN key."""
    if encrypted_text is None: 
        return None
    try:
        key = os.environ.get("ODIN_KEY")
        if not key:
            raise ValueError("ODIN_KEY not found in environment variables")
        cipher_suite = Fernet(key.encode())
        decrypted_text = cipher_suite.decrypt(encrypted_text.encode())
        return decrypted_text.decode()
    except Exception as e:
        return f"DECRYPTION_ERROR: {str(e)}"
