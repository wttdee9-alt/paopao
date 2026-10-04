from cryptography.fernet import Fernet
SERVICE="MetaBuyerIntelligence"

def _kr():
    import keyring
    return keyring
def set_secret(name,value): _kr().set_password(SERVICE,name,value)
def get_secret(name):
    try: return _kr().get_password(SERVICE,name)
    except Exception: return None
def _fernet():
    k=get_secret("pii_fernet_key")
    if not k:
        k=Fernet.generate_key().decode(); set_secret("pii_fernet_key",k)
    return Fernet(k.encode())
def encrypt_text(v): return _fernet().encrypt(v.encode()) if v else None
def decrypt_text(v):
    if not v:return ""
    try:return _fernet().decrypt(v).decode()
    except Exception:return ""
