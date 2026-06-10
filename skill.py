from pathlib import Path
import os
import shutil
import sys
import urllib.error
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
    # Avoid api.github.com due to strict rate limits.
    # Try downloading from main branch first, then fallback to master branch.
    urls = [
        f"https://github.com/{repo_id}/archive/refs/heads/main.zip",
        f"https://github.com/{repo_id}/archive/refs/heads/master.zip"
    ]
    
    last_err = None
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SkillManagerAgent"}
            )
            with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
                out_file.write(response.read())
            return
        except urllib.error.URLError as e:
            last_err = e
            
    if last_err:
        raise last_err


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
                            if m.endswith("/SKILL.md") and m.count('/') == 1:
                                prefix = m[:-len("SKILL.md")]
                                break
                    
                    # Extract files belonging to this skill directory
                    target_zip_dir_prefix = prefix + str(skill_parent_dir_rel) + "/"
                    for m in members:
                        if m.startswith(target_zip_dir_prefix):
                            relative_member = m[len(prefix):]
                            dest_file = library_dir / repo_id / relative_member
                            
                            # Zip Slip Prevention
                            dest_base = (library_dir / repo_id).resolve()
                            if not dest_file.resolve().is_relative_to(dest_base):
                                raise ValueError(f"Path traversal detected: {dest_file} is outside {dest_base}")
                            
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


def library_add(repo_id: str, config_path: Path, root_path: Path):
    # Pre-sync: download and find SKILL.md paths
    temp_zip = root_path / ".skills-repos" / f"temp_{repo_id.replace('/', '_')}.zip"
    temp_zip.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        download_repo_zip(repo_id, temp_zip)
    except Exception as e:
        print(f"Error downloading {repo_id}: {e}", file=sys.stderr)
        return
        
    skills_found = []
    with zipfile.ZipFile(temp_zip, 'r') as zf:
        for m in zf.namelist():
            if m.endswith("/SKILL.md"):
                # Extract skill path relative to repo root (excluding zipball root hash folder)
                parts = m.split('/')
                skill_path = "/".join(parts[1:])
                # Name is parent folder
                skill_name = parts[-2]
                skills_found.append({"name": skill_name, "path": skill_path})
            elif m.endswith("SKILL.md") and "/" not in m:
                # Skill at root
                skills_found.append({"name": repo_id.split('/')[-1], "path": "SKILL.md"})
                
    if temp_zip.exists():
        temp_zip.unlink()
        
    if not skills_found:
        print(f"No SKILL.md files found in repo {repo_id}.", file=sys.stderr)
        return

    # Update YAML config
    config = load_config(config_path)
    if "library" not in config:
        config["library"] = []
        
    # Find or update existing repoId
    found = False
    for r in config["library"]:
        if r["repoId"] == repo_id:
            r["skills"] = skills_found
            found = True
            break
    if not found:
        config["library"].append({
            "repoId": repo_id,
            "repoType": "github",
            "repoUrl": f"https://github.com/{repo_id}.git",
            "skills": skills_found
        })
        
    save_config(config, config_path)
    
    # Sync to finish the process
    sync(config_path, root_path)


def library_remove(repo_id: str, config_path: Path, root_path: Path):
    config = load_config(config_path)
    
    # Update YAML: remove from library
    if "library" in config:
        config["library"] = [r for r in config["library"] if r["repoId"] != repo_id]
        
    # Remove from workspace
    if "workspace" in config:
        config["workspace"] = [r for r in config["workspace"] if r["repoId"] != repo_id]
        
    save_config(config, config_path)
    
    # Sync
    sync(config_path, root_path)


