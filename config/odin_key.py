import os
import cryptography
print(cryptography.__version__)

from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())