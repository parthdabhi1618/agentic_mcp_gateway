# backend/vault.py
import os
import json
from cryptography.fernet import Fernet

VAULT_FILE = "vault.enc"
_KEY_FILE  = ".vault_key"

def _get_fernet() -> Fernet:
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(_KEY_FILE, "wb") as f:
            f.write(key)
    return Fernet(key)

def save_key(tool: str, api_key: str):
    fernet = _get_fernet()
    data = load_all_keys()
    data[tool] = api_key
    encrypted = fernet.encrypt(json.dumps(data).encode())
    with open(VAULT_FILE, "wb") as f:
        f.write(encrypted)

def load_all_keys() -> dict:
    if not os.path.exists(VAULT_FILE):
        return {}
    fernet = _get_fernet()
    with open(VAULT_FILE, "rb") as f:
        decrypted = fernet.decrypt(f.read())
    return json.loads(decrypted.decode())

def get_key(tool: str) -> str | None:
    return load_all_keys().get(tool)

def inject_env_from_vault():
    """Call at startup to inject vault keys into os.environ."""
    keys = load_all_keys()
    env_map = {
        "github": "GITHUB_TOKEN", "slack": "SLACK_TOKEN",
        "jira": "JIRA_TOKEN",     "sheets": "GOOGLE_SHEETS_CREDS_JSON",
        "linear": "LINEAR_API_KEY", "notion": "NOTION_TOKEN",
        "discord": "DISCORD_TOKEN",
    }
    for tool, key in keys.items():
        env_var = env_map.get(tool)
        if env_var:
            os.environ[env_var] = key
