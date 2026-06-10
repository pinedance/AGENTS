from pathlib import Path
import os
import shutil
import urllib.request
import zipfile
from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).parent.resolve()

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

def download_repo_zip(repo_id: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    # Use github default zip url
    url = f"https://api.github.com/repos/{repo_id}/zipball"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SkillManagerAgent"}
    )
    with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
        out_file.write(response.read())

def sync(config_path: Path, root_path: Path):
    config = load_config(config_path)
    repos_dir = root_path / ".skills-repos"
    library_dir = root_path / "skills-library"
    mine_dir = root_path / "skills-mine"
    skills_dir = root_path / "skills"
    
    repos_dir.mkdir(parents=True, exist_ok=True)
    library_dir.mkdir(parents=True, exist_ok=True)
    mine_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    active_zips = set()
    active_libs = set()
    
    # 1. Sync library (Downloads & Extractions)
    for repo in config.get("library", []):
        repo_id = repo["repoId"]
        zip_path = repos_dir / f"{repo_id}.zip"
        active_zips.add(zip_path.resolve())
        
        # Download zip if missing
        if not zip_path.exists():
            download_repo_zip(repo_id, zip_path)
            
        # Extract files based on configured skills
        for skill_item in repo.get("skills", []):
            skill_path = skill_item["path"]  # e.g., 'skills/brainstorming/SKILL.md'
            skill_parent_dir_rel = Path(skill_path).parent # 'skills/brainstorming'
            
            # Destination path inside skills-library
            dest_skill_dir = library_dir / repo_id / skill_parent_dir_rel
            active_libs.add(dest_skill_dir.resolve())
            
            # Extract if not exists
            if not dest_skill_dir.exists():
                dest_skill_dir.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    # Find matching file in zip (GitHub zipballs prefix folders with hashes)
                    members = zf.namelist()
                    # We look for the folder structure ending in the skill_parent_dir_rel
                    prefix = ""
                    for m in members:
                        if m.endswith(str(skill_parent_dir_rel) + "/SKILL.md"):
                            prefix = m[:-len(str(skill_parent_dir_rel) + "/SKILL.md")]
                            break
                    
                    if not prefix:
                        # Fallback for SKILL.md directly at root
                        for m in members:
                            if m.endswith("SKILL.md") and "/" not in m[m.find("SKILL.md")-5:m.find("SKILL.md")]:
                                prefix = m[:-len("SKILL.md")]
                                break
                    
                    # Extract files belonging to this skill directory
                    target_zip_dir_prefix = prefix + str(skill_parent_dir_rel) + "/"
                    for m in members:
                        if m.startswith(target_zip_dir_prefix):
                            relative_member = m[len(prefix):]
                            dest_file = library_dir / repo_id / relative_member
                            if m.endswith('/'):
                                dest_file.mkdir(parents=True, exist_ok=True)
                            else:
                                dest_file.parent.mkdir(parents=True, exist_ok=True)
                                with zf.open(m) as source_f, open(dest_file, "wb") as target_f:
                                    shutil.copyfileobj(source_f, target_f)

    # 2. Prune obsolete zips
    for root, dirs, files in os.walk(repos_dir):
        for f in files:
            p = Path(root) / f
            if p.suffix == ".zip" and p.resolve() not in active_zips:
                p.unlink()
                # remove empty parents
                try:
                    p.parent.rmdir()
                except OSError:
                    pass

    # 3. Prune obsolete library folders
    # Clean folders in library_dir that are not in active_libs
    for root, dirs, files in os.walk(library_dir, topdown=False):
        for d in dirs:
            p = Path(root) / d
            # Check if this directory contains SKILL.md (is a skill root)
            if (p / "SKILL.md").exists():
                if p.resolve() not in active_libs:
                    shutil.rmtree(p)

    # Clean empty directories in library_dir
    for root, dirs, files in os.walk(library_dir, topdown=False):
        for d in dirs:
            p = Path(root) / d
            try:
                p.rmdir()
            except OSError:
                pass

    # 4. Sync workspace & mine links (symlinks inside skills/)
    target_links = {} # target_name -> source_absolute_path
    
    # External workspace skills
    for repo in config.get("workspace", []):
        repo_id = repo["repoId"]
        for skill_item in repo.get("skills", []):
            source = skill_item["source"] # 'obra/superpowers/skills/brainstorming'
            target = skill_item["target"] # 'sp-brainstorming'
            target_links[target] = (library_dir / source).resolve()
            
    # Local mine skills
    for mine_item in config.get("mine", []):
        source = mine_item["source"] # 'superpowers/writing-plan'
        target = mine_item["target"] # 'my-writing-plan'
        target_links[target] = (mine_dir / source).resolve()
        
    # Rebuild symlinks in skills/
    # Delete stale links/files in skills/
    for item in os.listdir(skills_dir):
        item_path = skills_dir / item
        if item not in target_links:
            if item_path.is_symlink() or item_path.is_file():
                item_path.unlink()
            else:
                shutil.rmtree(item_path)
        else:
            # If it exists but points to wrong destination, remove it
            if item_path.is_symlink():
                real_link = os.readlink(item_path)
                if Path(real_link).resolve() != target_links[item]:
                    item_path.unlink()
            else:
                shutil.rmtree(item_path)
                
    # Create missing symlinks
    for target, source_abs in target_links.items():
        link_path = skills_dir / target
        if not link_path.exists() and not link_path.is_symlink():
            os.symlink(source_abs, link_path)

