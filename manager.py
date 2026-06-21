from pathlib import Path
import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from ruamel.yaml import YAML, YAMLError

PROJECT_ROOT = Path(__file__).parent.resolve()

DEFAULT_SKILLS_DIR = "~/.agents/skills"
DEFAULT_CONFIG_NAME = ".skills.yaml"
SKILL_FILENAME = "SKILL.md"
COMMIT_FILENAME = ".commit"
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

def _get_zip_comment(zip_path: Path) -> str:
    """Extract comment from a zip file safely."""
    if not zip_path.exists():
        return ""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            return zf.comment.decode("utf-8").strip()
    except (zipfile.BadZipFile, OSError):
        pass
    return ""

def _prune_obsolete_zips(repos_dir: Path, active_zips: set):
    """Delete stale .zip files in the repos directory."""
    if not repos_dir.exists():
        return
    for root, dirs, files in os.walk(repos_dir):
        for f in files:
            p = Path(root) / f
            if p.suffix == ".zip" and p.resolve() not in active_zips:
                try:
                    p.unlink()
                except OSError as e:
                    print(f"Warning: Failed to delete stale zip {p}: {e}", file=sys.stderr)
                    continue
                try:
                    p.parent.rmdir()
                except OSError:
                    pass  # Non-empty dir — expected, skip

def _prune_obsolete_libs(library_dir: Path, active_libs: set):
    """Clean up obsolete extracted library directories."""
    if not library_dir.exists():
        return
    for root, dirs, files in os.walk(library_dir, topdown=False):
        for d in dirs:
            p = Path(root) / d
            if (p / SKILL_FILENAME).exists() and p.resolve() not in active_libs:
                try:
                    shutil.rmtree(p)
                except OSError as e:
                    print(f"Warning: Failed to remove stale library directory {p}: {e}", file=sys.stderr)
            else:
                try:
                    p.rmdir()
                except OSError:
                    pass  # Non-empty dir — expected, skip

def _rebuild_symlinks(skills_dir: Path, library_dir: Path, target_links: dict):
    """Rebuild symlinks in skills_dir pointing to library_dir."""
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
            except OSError:
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
                    if not real_link.exists() and real_link != source_abs:
                        print(f"Recreating broken symlink: {target} -> {source_abs}")
                        link_path.unlink()
                        os.symlink(source_abs, link_path)
                        continue
                except OSError as e:
                    try:
                        link_path.unlink()
                        os.symlink(source_abs, link_path)
                    except OSError:
                        raise OSError(f"Failed to recreate symlink '{target}' -> {source_abs}: {e}") from e
                    continue
                
                if real_link != source_abs:
                    raise ValueError(f"Collision: Symlink '{target}' already exists and points to different source: {real_link}")
            else:
                raise ValueError(f"Collision: Target '{target}' already exists and is not a symlink")
        else:
            print(f"Creating symlink: {target} -> {source_abs}")
            try:
                os.symlink(source_abs, link_path)
            except OSError as e:
                raise OSError(f"Failed to create symlink '{target}' -> {source_abs}: {e}") from e

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
            print(f"Invalid choice. Enter a number between 1 and {len(candidates)}, or 'q' to cancel.")
        except (KeyboardInterrupt, EOFError):
            print("Operation canceled.")
            return None

def load_config(path: Path) -> dict:
    yaml = get_yaml_parser()
    if not path.exists():
        return {"library": [], "workspace": []}
    with open(path, "r", encoding="utf-8-sig") as f:
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

def download_repo_zip(repo_id: str, dest_path: Path, commit_or_branch: str = None):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    # Avoid api.github.com due to strict rate limits.
    # Try downloading from specific commit/branch if provided, else main/master branch.
    if commit_or_branch and commit_or_branch != "latest":
        urls = [f"https://github.com/{repo_id}/archive/{commit_or_branch}.zip"]
    else:
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


def get_remote_commit_hash(repo_url: str) -> str:
    try:
        res = subprocess.run(
            ["git", "ls-remote", repo_url, "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        output = res.stdout.strip()
        if output:
            return output.split()[0]
    except FileNotFoundError:
        print("Error: git command line tool not found on system.", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching remote commit hash for {repo_url}: {e}", file=sys.stderr)
    return ""


def _resolve_commit_hash(
    repo: dict,
    zip_path: Path,
    check_remote: bool,
    resolved_hashes: dict,
) -> tuple[str, bool]:
    """Resolve the effective commit hash for a repo and flag if a re-download is needed.

    Returns (commit_hash, force_download).
    """
    repo_id = repo.get("repoId", "")
    repo_url = repo.get("repoUrl", "")
    commit_hash = repo.get("commit", "")

    # Support dynamic "latest" resolution with per-URL caching
    if commit_hash == "latest" and repo_url:
        if repo_url not in resolved_hashes:
            resolved_hashes[repo_url] = get_remote_commit_hash(repo_url)
        resolved_hash = resolved_hashes[repo_url]
        commit_hash = resolved_hash if resolved_hash else _get_zip_comment(zip_path)

    local_hash = _get_zip_comment(zip_path)

    # ID1 vs ID2: config hash vs local zip hash
    force_download = bool(
        zip_path.exists() and local_hash and commit_hash and commit_hash != local_hash
    )
    if force_download:
        print(f"Warning: Local file for {repo_id} does not match .skills.yaml version (ID1: {commit_hash}, ID2: {local_hash})")

    # ID1 vs ID3: config hash vs remote HEAD (--check-remote, informational only)
    if check_remote and repo_url:
        if repo_url not in resolved_hashes:
            resolved_hashes[repo_url] = get_remote_commit_hash(repo_url)
        remote_hash = resolved_hashes[repo_url]
        if commit_hash and remote_hash and commit_hash != remote_hash:
            print(f"Warning: {repo_id} is not up-to-date with remote latest (ID1: {commit_hash}, ID3: {remote_hash}). Update required.")

    return commit_hash, force_download


def _download_repo_if_needed(
    repo: dict,
    zip_path: Path,
    commit_hash: str,
    force_download: bool,
) -> bool:
    """Download the repo zip if missing or stale, and backfill commit hash into repo dict.

    Returns True if the config was changed.
    """
    configured_commit = repo.get("commit", "")
    config_changed = False

    if not zip_path.exists() or force_download:
        if zip_path.exists():
            try:
                zip_path.unlink()
            except OSError as e:
                print(f"Warning: Failed to delete stale zip {zip_path}: {e}", file=sys.stderr)
        if commit_hash:
            print(f"Downloading {repo['repoId']} (commit {commit_hash})...")
            download_repo_zip(repo["repoId"], zip_path, commit_hash)
        else:
            print(f"Downloading {repo['repoId']}...")
            download_repo_zip(repo["repoId"], zip_path)

        # Backfill commit hash from newly downloaded zip when it was previously unknown
        if not commit_hash and zip_path.exists():
            extracted_hash = _get_zip_comment(zip_path)
            if extracted_hash:
                commit_hash = extracted_hash
                if configured_commit != "latest":
                    repo["commit"] = commit_hash
                    config_changed = True
    else:
        local_hash = _get_zip_comment(zip_path)
        if not commit_hash and local_hash:
            # Zip exists but config has no commit — backfill from local zip
            commit_hash = local_hash
            if configured_commit != "latest":
                repo["commit"] = commit_hash
                config_changed = True

    return config_changed


def _resolve_and_download_repos(config: dict, repos_dir: Path, library_dir: Path, check_remote: bool, active_zips: set, active_libs: set) -> bool:
    """Orchestrate commit resolution, downloading, and skill extraction for all library repos."""
    config_changed = False
    resolved_hashes: dict = {}

    for repo in config.get("library", []):
        repo_id = repo.get("repoId", "")
        if not re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", repo_id):
            print(f"Warning: Skipping invalid repoId in config: {repo_id!r}", file=sys.stderr)
            continue

        zip_path = repos_dir / f"{repo_id}.zip"
        active_zips.add(zip_path.resolve())

        commit_hash, force_download = _resolve_commit_hash(repo, zip_path, check_remote, resolved_hashes)
        config_changed |= _download_repo_if_needed(repo, zip_path, commit_hash, force_download)

        # Reconcile commit_hash for skill extraction:
        # - If _download_repo_if_needed backfilled a real hash (commit was ""), use it.
        # - If config says "latest", keep the resolved hash from _resolve_commit_hash (not "latest").
        # - Otherwise (specific hash), repo["commit"] equals commit_hash already.
        stored_commit = repo.get("commit", "")
        if stored_commit and stored_commit != "latest":
            commit_hash = stored_commit

        for skill_item in repo.get("skills", []):
            dest_skill_dir = library_dir / repo_id / skill_item["name"]
            active_libs.add(dest_skill_dir.resolve())
            _extract_skill_if_needed(zip_path, skill_item, repo_id, commit_hash, dest_skill_dir)

    return config_changed


def _extract_skill_if_needed(zip_path: Path, skill_item: dict, repo_id: str, commit_hash: str, dest_skill_dir: Path):
    """Extract files belonging to this skill directory from the ZIP file if not up to date."""
    commit_file = dest_skill_dir / COMMIT_FILENAME
    up_to_date = False
    if dest_skill_dir.exists() and commit_file.exists():
        try:
            cached_commit = commit_file.read_text(encoding="utf-8-sig").strip()
            if cached_commit == commit_hash and commit_hash:
                up_to_date = True
        except OSError:
            pass

    if up_to_date:
        print(f"Skill '{skill_item['name']}' from {repo_id} is up to date.")
        return

    print(f"Extracting {skill_item['name']} from {repo_id}...")
    if dest_skill_dir.exists():
        try:
            shutil.rmtree(dest_skill_dir)
        except OSError as e:
            print(f"Warning: Failed to remove directory {dest_skill_dir}: {e}", file=sys.stderr)
            return

    dest_skill_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            _extract_zip_members(zf, skill_item, dest_skill_dir)
            
        if commit_hash:
            try:
                commit_file.write_text(commit_hash, encoding="utf-8")
            except OSError as e:
                print(f"Warning: Failed to write commit hash to {commit_file}: {e}", file=sys.stderr)
    except zipfile.BadZipFile:
        if zip_path.exists():
            try:
                zip_path.unlink()
            except OSError as e:
                print(f"Warning: Failed to delete bad zip {zip_path}: {e}", file=sys.stderr)
        raise


def _extract_zip_members(zf: zipfile.ZipFile, skill_item: dict, dest_skill_dir: Path):
    skill_path = skill_item["path"]
    skill_parent_dir_rel = Path(skill_path).parent
    skill_parent_dir_rel_posix = skill_parent_dir_rel.as_posix()
    
    members = zf.namelist()
    prefix = ""
    for m in members:
        suffix_path = f"{skill_parent_dir_rel_posix}/{SKILL_FILENAME}"
        if m.endswith(suffix_path):
            prefix = m[:-len(suffix_path)]
            break
            
    if not prefix:
        root_suffix = f"/{SKILL_FILENAME}"
        for m in members:
            if m.endswith(root_suffix) and m.count('/') == 1:
                prefix = m[:-len(SKILL_FILENAME)]
                break

    if skill_parent_dir_rel_posix in (".", ""):
        target_zip_dir_prefix = prefix
    else:
        target_zip_dir_prefix = prefix + skill_parent_dir_rel_posix + "/"
        
    for m in members:
        if m.startswith(target_zip_dir_prefix):
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


def _validate_active_workspaces(config: dict) -> bool:
    """Validate and auto-heal active workspace mapping entries."""
    library_skills = {}
    for repo in config.get("library", []):
        r_id = repo["repoId"]
        for s in repo.get("skills", []):
            library_skills[(r_id, s["name"])] = s["path"]

    valid_workspaces = []
    workspace_changed = False
    for rw in config.get("workspace", []):
        r_id = rw["repoId"]
        valid_skills = []
        for s in rw.get("skills", []):
            s_name = s["name"]
            if (r_id, s_name) in library_skills:
                valid_skills.append(s)
            else:
                # Try auto-healing substring match
                repo_skills = [lib_s for lib in config.get("library", []) if lib["repoId"] == r_id for lib_s in lib.get("skills", [])]
                matches = []
                for lib_s in repo_skills:
                    if lib_s["name"].lower() in s_name.lower() or s_name.lower() in lib_s["name"].lower():
                        matches.append(lib_s)
                        
                if len(matches) == 1:
                    match = matches[0]
                    new_name = match["name"]
                    print(f"Warning: Skill '{s_name}' from repo '{r_id}' was relocated/renamed. Auto-correcting workspace mapping to '{new_name}'.")
                    s["name"] = new_name
                    s["source"] = f"{r_id}/{new_name}"
                    valid_skills.append(s)
                    workspace_changed = True
                elif len(matches) > 1:
                    print(f"Warning: Skill '{s_name}' from repo '{r_id}' is ambiguous (matches: {[m['name'] for m in matches]}). Removing from active workspace.")
                    workspace_changed = True
                else:
                    print(f"Warning: Skill '{s_name}' from repo '{r_id}' is no longer available in the library. Removing from active workspace.")
                    workspace_changed = True
        if valid_skills:
            rw["skills"] = valid_skills
            valid_workspaces.append(rw)
        else:
            workspace_changed = True

    if workspace_changed:
        config["workspace"] = valid_workspaces
    return workspace_changed


def sync(config_path: Path, root_path: Path, check_remote: bool = False):
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
    
    config_changed = _resolve_and_download_repos(config, repos_dir, library_dir, check_remote, active_zips, active_libs)
    config_changed |= _validate_active_workspaces(config)
    
    if config_changed:
        save_config(config, config_path)
        
    _prune_obsolete_zips(repos_dir, active_zips)
    _prune_obsolete_libs(library_dir, active_libs)
    
    # Sync workspace links
    target_links = {}
    for repo in config.get("workspace", []):
        for skill_item in repo.get("skills", []):
            source = skill_item["source"]
            target = skill_item["target"]
            if target in target_links:
                raise ValueError(f"Duplicate target name: {target} in workspace configuration")
            target_links[target] = (library_dir / source).resolve()
            
    _rebuild_symlinks(skills_dir, library_dir, target_links)
    print("Sync completed successfully.")


def _extract_name_from_front_matter(content: str) -> str:
    content_clean = content.lstrip("\ufeff\n\r\t ")
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", content_clean, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        try:
            yaml = get_yaml_parser()
            data = yaml.load(yaml_content)
            if data and isinstance(data, dict) and "name" in data:
                return str(data["name"]).strip()
        except YAMLError:
            pass
    return ""


def _read_skill_name_from_zip(zf: zipfile.ZipFile, member: str) -> str:
    """Read and parse the skill name from a SKILL.md entry inside a zip file."""
    try:
        with zf.open(member) as f:
            content = f.read().decode("utf-8", errors="ignore")
            return _extract_name_from_front_matter(content)
    except (KeyError, OSError, UnicodeDecodeError):
        return ""


def _scan_zip_for_skills(zip_path: Path, repo_id: str) -> tuple[list, str]:
    """Scan a zip file for SKILL.md entries. Returns (skills_found, commit_hash)."""
    skills_found: list = []
    commit_hash = _get_zip_comment(zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for m in zf.namelist():
            if m.endswith(f"/{SKILL_FILENAME}"):
                # Extract skill path relative to repo root (excluding zipball root hash folder)
                parts = m.split("/")
                skill_path = "/".join(parts[1:])
                skill_name = _read_skill_name_from_zip(zf, m)
                # Fallback to parent folder name
                if not skill_name:
                    skill_name = repo_id.split("/")[-1] if len(parts) == 2 else parts[-2]
                skills_found.append({"name": skill_name, "path": skill_path})
            elif m.endswith(SKILL_FILENAME) and "/" not in m:
                # Skill at root
                skill_name = _read_skill_name_from_zip(zf, m) or repo_id.split("/")[-1]
                skills_found.append({"name": skill_name, "path": SKILL_FILENAME})
    return skills_found, commit_hash


def library_add(repo_id: str, config_path: Path, root_path: Path, _do_sync: bool = True):
    if not re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", repo_id):
        raise ValueError(f"Invalid repo_id format: {repo_id}. Must match 'owner/repo'.")

    config = load_config(config_path)
    zip_path = root_path / REPOS_DIR_NAME / f"{repo_id}.zip"

    skills_found: list = []
    commit_hash: str = ""

    if zip_path.exists():
        # Re-scan existing zip to pick up any new skills added upstream (no re-download)
        print(f"Repository {repo_id} already downloaded. Refreshing skill list...")
        try:
            skills_found, commit_hash = _scan_zip_for_skills(zip_path, repo_id)
        except zipfile.BadZipFile:
            zip_path.unlink(missing_ok=True)
            raise
    else:
        print(f"Adding repository {repo_id} to library...")
        temp_zip = root_path / REPOS_DIR_NAME / f"temp_{repo_id.replace('/', '_')}.zip"
        temp_zip.parent.mkdir(parents=True, exist_ok=True)
        try:
            download_repo_zip(repo_id, temp_zip)
            skills_found, commit_hash = _scan_zip_for_skills(temp_zip, repo_id)
            zip_path.parent.mkdir(parents=True, exist_ok=True)
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
            if r.get("commit") != "latest":
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

    if not target_name or target_name in (".", "..") or not re.match(r"^[a-zA-Z0-9._-]+$", target_name):
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


def _get_local_repo_id() -> str | None:
    try:
        res = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True)
        url = res.stdout.strip()
        match = re.search(r"github\.com[:/]([^/\s]+/[^/\s.]+)", url)
        if match:
            return match.group(1)
    except (FileNotFoundError, subprocess.CalledProcessError, AttributeError):
        pass
    return None


def _sync_library_to_source(lib_dir: Path, src_dir: Path):
    if not lib_dir.exists():
        return
    src_dir.mkdir(parents=True, exist_ok=True)
    comparison = filecmp.dircmp(lib_dir, src_dir)
    
    for name in comparison.left_only:
        if name == COMMIT_FILENAME:
            continue
        lib_path = lib_dir / name
        src_path = src_dir / name
        if lib_path.is_dir():
            shutil.copytree(lib_path, src_path)
            print(f"Copied directory: {name}")
        else:
            shutil.copy2(lib_path, src_path)
            print(f"Copied file: {name}")
            
    for name in comparison.diff_files:
        if name == COMMIT_FILENAME:
            continue
        shutil.copy2(lib_dir / name, src_dir / name)
        print(f"Updated file: {name}")
        
    for name in comparison.common_dirs:
        _sync_library_to_source(lib_dir / name, src_dir / name)
        
    for name in comparison.right_only:
        src_path = src_dir / name
        if src_path.is_dir():
            shutil.rmtree(src_path)
            print(f"Deleted directory: {name}")
        else:
            src_path.unlink()
            print(f"Deleted file: {name}")


def myskills(message: str | None, config_path: Path, root_path: Path):
    print("Checking repository status...")
    config = load_config(config_path)
    repos_dir = root_path / REPOS_DIR_NAME
    library_dir = root_path / LIBRARY_DIR_NAME

    local_repo_id = _get_local_repo_id()
    if local_repo_id:
        # Find matching repo in library config
        matching_repo = None
        for r in config.get("library", []):
            if r["repoId"] == local_repo_id:
                matching_repo = r
                break
                
        if matching_repo:
            print(f"Syncing modifications back from library extract for '{local_repo_id}' to source...")
            for skill_item in matching_repo.get("skills", []):
                s_name = skill_item["name"]
                s_path = skill_item["path"]
                
                lib_skill_dir = library_dir / local_repo_id / s_name
                src_skill_dir = root_path / Path(s_path).parent
                
                if lib_skill_dir.exists():
                    _sync_library_to_source(lib_skill_dir, src_skill_dir)
            
            # Revert library extract back to clean state
            lib_repo_dir = library_dir / local_repo_id
            if lib_repo_dir.exists():
                shutil.rmtree(lib_repo_dir)

    # 1. Get branch
    try:
        res_branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
        branch = res_branch.stdout.strip()
    except FileNotFoundError:
        print("Error: git command line tool not found on system.", file=sys.stderr)
        return
    except subprocess.CalledProcessError:
        print("Error: Not a git repository.", file=sys.stderr)
        return

    # 2. Check status
    try:
        res_status = subprocess.run(
            ["git", "status", "--porcelain", "skills/"],
            capture_output=True, text=True, check=True
        )
    except FileNotFoundError:
        print("Error: git command line tool not found on system.", file=sys.stderr)
        return
    except subprocess.CalledProcessError as e:
        print(f"Error: git status failed: {e}", file=sys.stderr)
        return

    if not res_status.stdout.strip():
        print("No changes in skills/ to publish. Syncing...")
        sync(config_path, root_path)
        return

    # 3. Add, commit, push
    msg = message or "Update skills"
    print(f"Staging, committing, and pushing changes on branch '{branch}'...")
    try:
        subprocess.run(["git", "add", "skills/"], check=True)
        subprocess.run(["git", "commit", "-m", msg], check=True)
        subprocess.run(["git", "push", "origin", branch], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: git operation failed: {e}", file=sys.stderr)
        return


    # 4. Sync
    print("Push complete. Updating active workspace...")
    sync(config_path, root_path)


def main(config_path: Path | None = None, root_path: Path | None = None):
    parser = argparse.ArgumentParser(description="Skill Manager CLI")
    parser.add_argument("--config", help="Path to config file", default=None)
    parser.add_argument("--root", help="Path to project root", default=None)
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # sync
    sync_parser = subparsers.add_parser("sync", help=f"Sync local file system with {DEFAULT_CONFIG_NAME}")
    sync_parser.add_argument("--check-remote", action="store_true", help="Compare with remote latest commit ID as well")
    
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
    
    # myskills
    myskills_parser = subparsers.add_parser("myskills", help="Stage, commit, push local skill changes and sync library")
    myskills_parser.add_argument("-m", "--message", help="Commit message", default=None)

    args = parser.parse_args()
    
    cli_root = Path(args.root) if args.root else None
    root = cli_root or root_path or PROJECT_ROOT
    
    cli_cfg = Path(args.config) if args.config else None
    cfg = cli_cfg or config_path or (root / DEFAULT_CONFIG_NAME)
    
    if args.command == "sync":
        sync(cfg, root, check_remote=args.check_remote)
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
    elif args.command == "myskills":
        myskills(args.message, cfg, root)


if __name__ == "__main__":
    main()
