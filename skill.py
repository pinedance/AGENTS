from pathlib import Path
from ruamel.yaml import YAML

def get_yaml_parser():
    yaml = YAML()
    yaml.preserve_quotes = True
    return yaml

def load_config(path: Path) -> dict:
    yaml = get_yaml_parser()
    if not path.exists():
        return {"library": [], "workspace": [], "mine": []}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    if not data:
        return {"library": [], "workspace": [], "mine": []}
    return data

def save_config(config: dict, path: Path):
    yaml = get_yaml_parser()
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
