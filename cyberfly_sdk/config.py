import json

DEFAULT_PATH = '/cyberfly_config.json'


def load_config(path=DEFAULT_PATH):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def save_config(cfg, path=DEFAULT_PATH):
    with open(path, 'w') as f:
        json.dump(cfg, f)
    return True
