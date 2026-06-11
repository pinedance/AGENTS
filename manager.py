from pathlib import Path
import argparse
import os
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
import re
from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).parent.resolve()

DEFAULT_SKILLS_DIR = "~/.agents/skills"
DEFAULT_CONFIG_NAME = ".skills.yaml"
SKILL_FILENAME = "SKILL.md"
REPOS_DIR_NAME = ".skills-repos"
LIBRARY_DIR_NAME = "skills-library"
SKILLS_DIR_ENV_VAR = "SKILLS_DIR"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
GITHUB_ZIP_URL_TEMPLATES = [
    "https://github.com/{repo_id}/archive/refs/heads/main.zip",
    "https://github.com/{repo_id}/archive/refs/heads/master.zip"
]
GITHUB_REPO_URL_TEMPLATE = "https://github.com/{repo_id}.git"

def get_yaml_parser():
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=2, offset=0)
    return yaml

def _sanitize_config(data: dict) -> None:
    for key in ("library", "workspace"):
        if key in data and isinstance(data[key], list):
            for repo in data[key]:
                if isinstance(repo, dict) and "repoId" in repo and isinstance(repo["repoId"], str):
                    repo["repoId"] = repo["repoId"].strip(", ")

def prompt_selection(candidates, format_fn, title_label, prompt_label):
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
        
    print(f"Multiple {title_label} found:")
    for idx, item in enumerate(candidates, 1):
        print(f" [{idx}] {format_fn(item)}")
        
    while True:
        try:
            raw_val = input(f"Select {prompt_label} (1-{len(candidates)}): ").strip()
            if raw_val.lower() in ("q", "0", "cancel"):
                print("Operation canceled.")
                return None
            choice = int(raw_val)
            if 1 <= choice <= len(candidates):
                return candidates[choice - 1]
        except ValueError:
            pass
        except (KeyboardInterrupt, EOFError):
            print("Operation canceled.")
            return None

def load_config(path: Path) -> dict:
    yaml = get_yaml_parser()
    if not path.exists():
        return {"library": [], "workspace": []}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    if not data:
        return {"library": [], "workspace": []}
    
    _sanitize_config(data)
    return data

def save_config(config: dict, path: Path):
    yaml = get_yaml_parser()
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            yaml.dump(config, f)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise

def download_repo_zip(repo_id: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    # Avoid api.github.com due to strict rate limits.
    # Try downloading from main branch first, then fallback to master branch.
    urls = [tpl.format(repo_id=repo_id) for tpl in GITHUB_ZIP_URL_TEMPLATES]
    
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
    last_err = None
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(req) as response, open(temp_path, "wb") as out_file:
                # Stream in chunks to avoid loading entire ZIP into memory
                shutil.copyfileobj(response, out_file)
            temp_path.replace(dest_path)
            return
        except urllib.error.URLError as e:
            last_err = e
            temp_path.unlink(missing_ok=True)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    if last_err:
        raise last_err


def sync(config_path: Path, root_path: Path):
    print("Syncing skills...")
    config = load_config(config_path)
    repos_dir = root_path / REPOS_DIR_NAME
    library_dir = root_path / LIBRARY_DIR_NAME
    skills_dir = Path(os.environ.get(SKILLS_DIR_ENV_VAR, DEFAULT_SKILLS_DIR)).expanduser()
    
    repos_dir.mkdir(parents=True, exist_ok=True)
    library_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    active_zips = set()
    active_libs = set()
    config_changed = False
    
    # 1. Sync library (Downloads & Extractions)
    for repo in config.get("library", []):
        repo_id = repo.get("repoId", "")
        if not re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", repo_id):
            print(f"Warning: Skipping invalid repoId in config: {repo_id!r}", file=sys.stderr)
            continue
        zip_path = repos_dir / f"{repo_id}.zip"
        active_zips.add(zip_path.resolve())
        
        # Download zip if missing
        if not zip_path.exists():
            print(f"Downloading {repo_id}...")
            download_repo_zip(repo_id, zip_path)
            
        commit_hash = repo.get("commit", "")
        if not commit_hash and zip_path.exists():
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    extracted_hash = zf.comment.decode("utf-8").strip()
                    if extracted_hash:
                        commit_hash = extracted_hash
                        repo["commit"] = commit_hash
                        config_changed = True
            except Exception:
                pass

        # Extract files based on configured skills
        for skill_item in repo.get("skills", []):
            skill_path = skill_item["path"]  # e.g., 'skills/brainstorming/SKILL.md'
            skill_parent_dir_rel = Path(skill_path).parent # 'skills/brainstorming'
            skill_parent_dir_rel_posix = skill_parent_dir_rel.as_posix()
            
            # Destination path inside skills-library
            dest_skill_dir = library_dir / repo_id / skill_item["name"]
            active_libs.add(dest_skill_dir.resolve())
            
            commit_file = dest_skill_dir / ".commit"
            up_to_date = False
            if dest_skill_dir.exists() and commit_file.exists():
                try:
                    cached_commit = commit_file.read_text(encoding="utf-8").strip()
                    if cached_commit == commit_hash and commit_hash:
                        up_to_date = True
                except Exception:
                    pass

            # Extract if not up to date
            if not up_to_date:
                print(f"Extracting {skill_item['name']} from {repo_id}...")
                if dest_skill_dir.exists():
                    shutil.rmtree(dest_skill_dir)
                dest_skill_dir.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        # Find matching file in zip (GitHub zipballs prefix folders with hashes)
                        members = zf.namelist()
                        # We look for the folder structure ending in the skill_parent_dir_rel
                        prefix = ""
                        for m in members:
                            suffix_path = f"{skill_parent_dir_rel_posix}/{SKILL_FILENAME}"
                            if m.endswith(suffix_path):
                                prefix = m[:-len(suffix_path)]
                                break
                        
                        if not prefix:
                            # Fallback for SKILL.md directly at root
                            root_suffix = f"/{SKILL_FILENAME}"
                            for m in members:
                                if m.endswith(root_suffix) and m.count('/') == 1:
                                    prefix = m[:-len(SKILL_FILENAME)]
                                    break
                        
                        # Extract files belonging to this skill directory
                        if skill_parent_dir_rel_posix in (".", ""):
                            target_zip_dir_prefix = prefix
                        else:
                            target_zip_dir_prefix = prefix + skill_parent_dir_rel_posix + "/"
                        for m in members:
                            if m.startswith(target_zip_dir_prefix):
                                # Strip both prefix and original nested path within the zip
                                relative_member = m[len(target_zip_dir_prefix):]
                                if not relative_member:
                                    continue
                                dest_file = dest_skill_dir / relative_member
                                
                                # Zip Slip Prevention
                                dest_base = dest_skill_dir.resolve()
                                if not dest_file.resolve().is_relative_to(dest_base):
                                    raise ValueError(f"Path traversal detected: {dest_file} is outside {dest_base}")
                                
                                if m.endswith('/'):
                                    dest_file.mkdir(parents=True, exist_ok=True)
                                else:
                                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                                    with zf.open(m) as source_f, open(dest_file, "wb") as target_f:
                                        shutil.copyfileobj(source_f, target_f)
                                        
                    if commit_hash:
                        try:
                            commit_file.write_text(commit_hash, encoding="utf-8")
                        except Exception:
                            pass
                except zipfile.BadZipFile:
                    if zip_path.exists():
                        try:
                            zip_path.unlink()
                        except OSError:
                            pass
                    raise
            else:
                print(f"Skill '{skill_item['name']}' from {repo_id} is up to date.")

    if config_changed:
        save_config(config, config_path)

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

    # 3. Prune obsolete library folders and clean empty directories
    for root, dirs, files in os.walk(library_dir, topdown=False):
        for d in dirs:
            p = Path(root) / d
            if (p / SKILL_FILENAME).exists() and p.resolve() not in active_libs:
                try:
                    shutil.rmtree(p)
                except Exception:
                    pass
            else:
                try:
                    p.rmdir()
                except OSError:
                    pass

    # 4. Sync workspace links (symlinks inside ~/.agents/skills/)
    target_links = {} # target_name -> source_absolute_path
    
    # External workspace skills
    for repo in config.get("workspace", []):
        for skill_item in repo.get("skills", []):
            source = skill_item["source"] # 'obra/superpowers/skills/brainstorming'
            target = skill_item["target"] # 'sp-brainstorming'
            if target in target_links:
                raise ValueError(f"Duplicate target name: {target} in workspace configuration")
            target_links[target] = (library_dir / source).resolve()

    # Rebuild symlinks in skills_dir
    # Validate all target links point strictly inside library_dir
    resolved_lib = library_dir.resolve()
    for target, source_abs in target_links.items():
        resolved_src = source_abs.resolve()
        if not resolved_src.is_relative_to(resolved_lib) or resolved_src == resolved_lib:
            raise ValueError(f"Symlink target {resolved_src} is not strictly inside {resolved_lib}")

    # Delete stale links/files in skills_dir (safe pruning)
    for item in os.listdir(skills_dir):
        item_path = skills_dir / item
        if item_path.is_symlink():
            try:
                resolved_target = Path(os.readlink(item_path)).resolve()
                if resolved_target.is_relative_to(resolved_lib):
                    if item not in target_links or resolved_target != target_links[item]:
                        print(f"Pruning stale symlink: {item}")
                        item_path.unlink()
                elif not resolved_target.exists():
                    print(f"Pruning broken symlink: {item}")
                    item_path.unlink()
            except Exception:
                try:
                    item_path.unlink()
                except OSError:
                    pass
                
    # Create missing symlinks with collision check
    for target, source_abs in target_links.items():
        link_path = skills_dir / target
        if link_path.exists() or link_path.is_symlink():
            if link_path.is_symlink():
                try:
                    real_link = Path(os.readlink(link_path)).resolve()
                    if not real_link.exists():
                        print(f"Recreating broken symlink: {target} -> {source_abs}")
                        link_path.unlink()
                        os.symlink(source_abs, link_path)
                        continue
                except OSError:
                    link_path.unlink()
                    os.symlink(source_abs, link_path)
                    continue
                
                if real_link != source_abs:
                    raise ValueError(f"Collision: Symlink '{target}' already exists and points to different source: {real_link}")
            else:
                raise ValueError(f"Collision: Target '{target}' already exists and is not a symlink")
        else:
            print(f"Creating symlink: {target} -> {source_abs}")
            os.symlink(source_abs, link_path)
            
    print("Sync completed successfully.")


def library_add(repo_id: str, config_path: Path, root_path: Path, _do_sync: bool = True):
    if not re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", repo_id):
        raise ValueError(f"Invalid repo_id format: {repo_id}. Must match 'owner/repo'.")

    config = load_config(config_path)
    zip_path = root_path / REPOS_DIR_NAME / f"{repo_id}.zip"
    
    # Skip download if repo is already in config and zip already exists
    repo_in_config = any(r["repoId"] == repo_id for r in config.get("library", []))
    if repo_in_config and zip_path.exists():
        print(f"Repository {repo_id} already in library. Running sync.")
        sync(config_path, root_path)
        return

    print(f"Adding repository {repo_id} to library...")
    # Pre-sync: download and find SKILL.md paths
    temp_zip = root_path / REPOS_DIR_NAME / f"temp_{repo_id.replace('/', '_')}.zip"
    temp_zip.parent.mkdir(parents=True, exist_ok=True)
    
    skills_found = []
    commit_hash = ""
    try:
        download_repo_zip(repo_id, temp_zip)
        with zipfile.ZipFile(temp_zip, 'r') as zf:
            try:
                commit_hash = zf.comment.decode("utf-8").strip()
            except Exception:
                pass
            for m in zf.namelist():
                if m.endswith(f"/{SKILL_FILENAME}"):
                    # Extract skill path relative to repo root (excluding zipball root hash folder)
                    parts = m.split('/')
                    skill_path = "/".join(parts[1:])
                    # Name is parent folder
                    if len(parts) == 2:
                        skill_name = repo_id.split('/')[-1]
                    else:
                        skill_name = parts[-2]
                    skills_found.append({"name": skill_name, "path": skill_path})
                elif m.endswith(SKILL_FILENAME) and "/" not in m:
                    # Skill at root
                    skills_found.append({"name": repo_id.split('/')[-1], "path": SKILL_FILENAME})

        # Move temp_zip to final zip_path
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        if zip_path.exists():
            zip_path.unlink()
        temp_zip.replace(zip_path)
    except Exception:
        temp_zip.unlink(missing_ok=True)
        raise
        
    if not skills_found:
        raise ValueError(f"No {SKILL_FILENAME} files found in repo {repo_id}.")

    # Update YAML config
    if "library" not in config:
        config["library"] = []
        
    # Find or update existing repoId
    found = False
    for r in config["library"]:
        if r["repoId"] == repo_id:
            r["skills"] = skills_found
            r["commit"] = commit_hash
            found = True
            break
    if not found:
        config["library"].append({
            "repoId": repo_id,
            "repoType": "github",
            "repoUrl": GITHUB_REPO_URL_TEMPLATE.format(repo_id=repo_id),
            "commit": commit_hash,
            "skills": skills_found
        })
        
    save_config(config, config_path)
    print(f"Added repository {repo_id} to library.")
    
    # Sync to finish the process
    if _do_sync:
        sync(config_path, root_path)


def library_remove(repo_id: str, config_path: Path, root_path: Path):
    print(f"Removing repository {repo_id} from library...")
    config = load_config(config_path)
    
    # Update YAML: remove from library
    if "library" in config and isinstance(config["library"], list):
        lib = config["library"]
        for i in range(len(lib) - 1, -1, -1):
            if lib[i]["repoId"] == repo_id:
                del lib[i]
        
    # Remove from workspace
    if "workspace" in config and isinstance(config["workspace"], list):
        work = config["workspace"]
        for i in range(len(work) - 1, -1, -1):
            if work[i]["repoId"] == repo_id:
                del work[i]
        
    save_config(config, config_path)
    print(f"Removed repository {repo_id} from library.")
    
    # Sync
    sync(config_path, root_path)


def library_update(repo_id: str | None, config_path: Path, root_path: Path):
    config = load_config(config_path)
    repos_to_update = []
    if repo_id:
        repos_to_update = [r for r in config.get("library", []) if r["repoId"] == repo_id]
        if not repos_to_update:
            raise ValueError(f"Repository {repo_id} not found in library config")
        print(f"Updating repository {repo_id}...")
    else:
        repos_to_update = config.get("library", [])
        print("Updating all repositories in library...")
        
    repos_dir = root_path / REPOS_DIR_NAME
    for r in repos_to_update:
        r_id = r["repoId"]
        zip_path = repos_dir / f"{r_id}.zip"
        if zip_path.exists():
            try:
                zip_path.unlink()
            except OSError:
                pass
        library_add(r_id, config_path, root_path, _do_sync=False)

    # Single sync after all repos are updated — avoids O(N) redundant syncs
    # and prevents intermediate pruning from deleting not-yet-refreshed zips
    sync(config_path, root_path)


def workspace_add(skill_name: str, new_name: str | None, config_path: Path, root_path: Path):
    config = load_config(config_path)
    
    # Pre-sync: find matching skills in library
    candidates = []
    for repo in config.get("library", []):
        repo_id = repo["repoId"]
        for skill_item in repo.get("skills", []):
            if skill_item["name"] == skill_name:
                candidates.append((repo_id, skill_item))
                
    if not candidates:
        print(f"Skill '{skill_name}' not found in library. Run 'library add' first.", file=sys.stderr)
        return
        
    res = prompt_selection(
        candidates,
        format_fn=lambda x: f"{x[0]} ({x[1]['path']})",
        title_label="matches",
        prompt_label="repo"
    )
    if not res:
        return
    selected_repo_id, selected_skill = res
        
    target_name = new_name
    if target_name is None:
        try:
            raw_val = input(f"Enter target symlink name (default '{skill_name}'): ").strip()
            if raw_val.lower() in ("q", "0", "cancel"):
                print("Operation canceled.")
                return
            if not raw_val:
                target_name = skill_name
            else:
                target_name = raw_val
        except (KeyboardInterrupt, EOFError):
            print("Operation canceled.")
            return

    if not target_name or not re.match(r"^[a-zA-Z0-9._-]+$", target_name):
        raise ValueError(f"Invalid target name: {target_name!r}. Must match pattern: [a-zA-Z0-9._-]+")

    print(f"Adding skill {skill_name} to active workspace as {target_name}...")
            
    # Update YAML: add to workspace
    # 1. Globally remove any skill across all workspace repo blocks with the same target name
    if "workspace" in config and isinstance(config["workspace"], list):
        work = config["workspace"]
        for rw in work:
            if "skills" in rw and isinstance(rw["skills"], list):
                skills = rw["skills"]
                for i in range(len(skills) - 1, -1, -1):
                    if skills[i]["target"] == target_name:
                        del skills[i]
        # Clean up empty repo blocks in-place
        for i in range(len(work) - 1, -1, -1):
            if not work[i].get("skills"):
                del work[i]
        
    if "workspace" not in config:
        config["workspace"] = []
        
    repo_workspace = None
    for rw in config["workspace"]:
        if rw["repoId"] == selected_repo_id:
            repo_workspace = rw
            break
            
    if not repo_workspace:
        repo_workspace = {"repoId": selected_repo_id, "skills": []}
        config["workspace"].append(repo_workspace)
        
    # Source is repoId + skill_name
    source_path = f"{selected_repo_id}/{skill_name}"
    
    repo_workspace["skills"].append({
        "name": skill_name,
        "source": source_path,
        "target": target_name
    })
    
    save_config(config, config_path)
    print(f"Added skill {skill_name} to active workspace.")
    
    # Sync
    sync(config_path, root_path)


def workspace_remove(skill_name: str, config_path: Path, root_path: Path):
    config = load_config(config_path)
    
    # Find active workspace skills matching skill_name
    candidates = []
    for rw in config.get("workspace", []):
        for s in rw.get("skills", []):
            if s["name"] == skill_name:
                candidates.append((rw, s))
                
    if not candidates:
        print(f"Skill '{skill_name}' not active in workspace.", file=sys.stderr)
        return
        
    res = prompt_selection(
        candidates,
        format_fn=lambda x: f"{x[1]['target']} (from {x[0]['repoId']})",
        title_label="active skills",
        prompt_label="skill to remove"
    )
    if not res:
        return
    selected_rw, selected_skill = res
        
    print(f"Removing skill {skill_name} from active workspace...")
    # Update YAML
    selected_rw["skills"].remove(selected_skill)
    # Clean up empty repo blocks in-place
    if "workspace" in config and isinstance(config["workspace"], list):
        work = config["workspace"]
        for i in range(len(work) - 1, -1, -1):
            if not work[i].get("skills"):
                del work[i]
    
    save_config(config, config_path)
    print(f"Removed skill {skill_name} from active workspace.")
    
    # Sync
    sync(config_path, root_path)




def main(config_path: Path | None = None, root_path: Path | None = None):
    parser = argparse.ArgumentParser(description="Skill Manager CLI")
    parser.add_argument("--config", help="Path to config file", default=None)
    parser.add_argument("--root", help="Path to project root", default=None)
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # sync
    subparsers.add_parser("sync", help=f"Sync local file system with {DEFAULT_CONFIG_NAME}")
    
    # library
    lib_parser = subparsers.add_parser("library", help="Manage skill library")
    lib_sub = lib_parser.add_subparsers(dest="subcommand", required=True)
    lib_add = lib_sub.add_parser("add", help="Add remote repo to library")
    lib_add.add_argument("repoId", help="GitHub repository identifier, e.g. obra/superpowers")
    lib_rem = lib_sub.add_parser("remove", help="Remove repo from library")
    lib_rem.add_argument("repoId", help="GitHub repository identifier")
    lib_up = lib_sub.add_parser("update", help="Update remote repo in library")
    lib_up.add_argument("repoId", nargs="?", help="GitHub repository identifier, optional", default=None)
    
    # workspace
    work_parser = subparsers.add_parser("workspace", help="Manage active workspace skills")
    work_sub = work_parser.add_subparsers(dest="subcommand", required=True)
    work_add = work_sub.add_parser("add", help="Add skill from library to active workspace")
    work_add.add_argument("skill_name", help="Name of skill to add")
    work_add.add_argument("--name", help="Custom name for the symlink", default=None)
    work_rem = work_sub.add_parser("remove", help="Remove active workspace skill")
    work_rem.add_argument("skill_name", help="Name of skill to remove")
    

    
    args = parser.parse_args()
    
    cli_root = Path(args.root) if args.root else None
    root = cli_root or root_path or PROJECT_ROOT
    
    cli_cfg = Path(args.config) if args.config else None
    cfg = cli_cfg or config_path or (root / DEFAULT_CONFIG_NAME)
    
    if args.command == "sync":
        sync(cfg, root)
    elif args.command == "library":
        if args.subcommand == "add":
            library_add(args.repoId, cfg, root)
        elif args.subcommand == "remove":
            library_remove(args.repoId, cfg, root)
        elif args.subcommand == "update":
            library_update(args.repoId, cfg, root)
    elif args.command == "workspace":
        if args.subcommand == "add":
            workspace_add(args.skill_name, args.name, cfg, root)
        elif args.subcommand == "remove":
            workspace_remove(args.skill_name, cfg, root)



if __name__ == "__main__":
    main()






