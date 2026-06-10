import sys
from pathlib import Path
from ruamel.yaml import YAML

def get_yaml_parser():
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True
    return yaml

def load_config(path: Path) -> dict:
    yaml = get_yaml_parser()
    if not path.exists():
        return {"library": [], "workspace": [], "mine": []}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f)

def save_config(config: dict, path: Path):
    yaml = get_yaml_parser()
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
