from pathlib import Path
import pytest
import manager as skill

@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SKILLS_DIR", str(tmp_path / "skills"))
    # Setup temporary directory structure mirroring project
    yaml_content = """# Test comments
library:
- repoId: obra/superpowers
  repoType: github
  repoUrl: https://github.com/obra/superpowers.git
  skills:
    - name: brainstorming
      path: skills/brainstorming/SKILL.md
workspace:
- repoId: obra/superpowers
  skills: 
  - name: brainstorming 
    source: obra/superpowers/brainstorming
    target: sp-brainstorming 
"""
    yaml_path = tmp_path / ".skills.yaml"
    yaml_path.write_text(yaml_content)
    return tmp_path

def test_load_save_config_preserves_comments(temp_env):
    yaml_path = temp_env / ".skills.yaml"
    config = skill.load_config(yaml_path)
    assert "library" in config
    assert "workspace" in config
    
    # Modify config and save
    config["library"].append({"repoId": "test-repo", "skills": []})
    skill.save_config(config, yaml_path)
    
    saved_content = yaml_path.read_text()
    assert "# Test comments" in saved_content
    assert "test-repo" in saved_content

def test_load_empty_config(tmp_path):
    yaml_path = tmp_path / ".skills.yaml"
    yaml_path.write_text("")
    config = skill.load_config(yaml_path)
    assert config == {"library": [], "workspace": []}

def test_load_only_comments_config(tmp_path):
    yaml_path = tmp_path / ".skills.yaml"
    yaml_path.write_text("# Only comments here\n")
    config = skill.load_config(yaml_path)
    assert config == {"library": [], "workspace": []}

def test_load_config_sanitizes_repo_id(tmp_path):
    yaml_path = tmp_path / ".skills.yaml"
    yaml_content = """
library:
- repoId: "obra/superpowers, "
  repoType: github
  repoUrl: https://github.com/obra/superpowers.git
  skills: []
workspace:
- repoId: "anthropics/skills,"
  skills: []
"""
    yaml_path.write_text(yaml_content)
    config = skill.load_config(yaml_path)
    assert config["library"][0]["repoId"] == "obra/superpowers"
    assert config["workspace"][0]["repoId"] == "anthropics/skills"



from unittest.mock import patch

@patch("manager.download_repo_zip")
def test_sync_rebuilds_links_and_library(mock_download, temp_env):
    import manager as skill
    
    # Mock download to write a dummy zip with a SKILL.md
    def side_effect(repo_id, dest_path, *args, **kwargs):
        import zipfile
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "# Brainstorming Skill")
            zf.writestr("superpowers-main/skills/other/SKILL.md", "# Other Skill")
    mock_download.side_effect = side_effect

    # Set paths in skill module dynamically or pass to sync
    skill.PROJECT_ROOT = temp_env
    skill.sync(temp_env / ".skills.yaml", temp_env)
    
    # Verify zip downloaded
    assert (temp_env / ".skills-repos/obra/superpowers.zip").exists()
    
    # Verify library extracted (should omit 'other' since it's not in library config)
    assert (temp_env / "skills-library/obra/superpowers/brainstorming/SKILL.md").exists()
    assert not (temp_env / "skills-library/obra/superpowers/other/SKILL.md").exists()
    
    # Verify workspace symlink created
    link_path = temp_env / "skills/sp-brainstorming"
    assert link_path.is_symlink()
    assert link_path.resolve() == (temp_env / "skills-library/obra/superpowers/brainstorming").resolve()


@patch("manager.download_repo_zip")
def test_sync_prunes_obsolete_and_idempotent(mock_download, temp_env):
    import manager as skill
    import shutil
    
    # 1. Prepare Zip
    def side_effect(repo_id, dest_path):
        import zipfile
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "# Brainstorming Skill")
    mock_download.side_effect = side_effect
    
    # Create some obsolete folders/files and symlinks
    # A stale zip in .skills-repos
    stale_zip = temp_env / ".skills-repos/obsolete/repo.zip"
    stale_zip.parent.mkdir(parents=True, exist_ok=True)
    stale_zip.write_text("dummy zip content")
    
    # A stale skill folder in skills-library with SKILL.md
    stale_lib_skill = temp_env / "skills-library/obra/superpowers/obsolete_skill"
    stale_lib_skill.mkdir(parents=True, exist_ok=True)
    (stale_lib_skill / "SKILL.md").write_text("# Obsolete Skill")
    (stale_lib_skill / "helper.py").write_text("print('stale')")
    
    # A stale symlink pointing inside this project's skills-library
    stale_link_managed = temp_env / "skills/stale-link-managed"
    stale_link_managed.parent.mkdir(parents=True, exist_ok=True)
    import os
    os.symlink(temp_env / "skills-library/obra/superpowers/stale", stale_link_managed)

    # A stale symlink pointing outside (unmanaged / other project)
    stale_link_unmanaged = temp_env / "skills/stale-link-unmanaged"
    (temp_env / "other-library/some-path").mkdir(parents=True, exist_ok=True)
    os.symlink(temp_env / "other-library/some-path", stale_link_unmanaged)

    # A stale directory
    stale_dir = temp_env / "skills/stale-dir"
    stale_dir.mkdir(parents=True, exist_ok=True)

    # A stale file
    stale_file = temp_env / "skills/stale-file"
    stale_file.write_text("file content")
    
    # Run sync
    skill.sync(temp_env / ".skills.yaml", temp_env)
    
    # Verify zip downloaded and old one pruned
    assert (temp_env / ".skills-repos/obra/superpowers.zip").exists()
    assert not stale_zip.exists()
    
    # Verify library extracted and stale library skill pruned
    assert (temp_env / "skills-library/obra/superpowers/brainstorming/SKILL.md").exists()
    assert not stale_lib_skill.exists()
    
    # Verify stale links are handled according to safe pruning
    assert not stale_link_managed.exists() and not stale_link_managed.is_symlink()
    assert stale_link_unmanaged.is_symlink()
    assert stale_dir.exists()
    assert stale_file.exists()
    assert (temp_env / "skills/sp-brainstorming").is_symlink()
    
    # Call sync again to verify idempotency (it shouldn't download or break anything)
    mock_download.reset_mock()
    skill.sync(temp_env / ".skills.yaml", temp_env)
    assert mock_download.call_count == 0
    assert (temp_env / "skills/sp-brainstorming").is_symlink()


@patch("urllib.request.urlopen")
def test_download_repo_zip_fallback(mock_urlopen, tmp_path):
    import urllib.error
    import manager as skill
    from unittest.mock import MagicMock
    
    response_mock = MagicMock()
    response_mock.__enter__.return_value = response_mock
    _data_187 = [b"zip-content", b""]
    response_mock.read.side_effect = lambda n=-1: _data_187.pop(0) if _data_187 else b""
    
    calls = []
    def urlopen_side_effect(req, *args, **kwargs):
        url = req.full_url
        calls.append(url)
        if "main.zip" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return response_mock
        
    mock_urlopen.side_effect = urlopen_side_effect
    
    dest = tmp_path / "repo.zip"
    skill.download_repo_zip("obra/superpowers", dest)
    
    assert dest.exists()
    assert dest.read_bytes() == b"zip-content"
    assert len(calls) == 2
    assert "main.zip" in calls[0]
    assert "master.zip" in calls[1]


@patch("urllib.request.urlopen")
def test_download_repo_zip_fails_both(mock_urlopen, tmp_path):
    import urllib.error
    import manager as skill
    
    def urlopen_side_effect(req, *args, **kwargs):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)
        
    mock_urlopen.side_effect = urlopen_side_effect
    
    dest = tmp_path / "repo.zip"
    with pytest.raises(urllib.error.HTTPError):
        skill.download_repo_zip("obra/superpowers", dest)


@patch("manager.download_repo_zip")
def test_sync_zip_slip_prevention(mock_download, temp_env):
    import manager as skill
    import pytest
    
    def side_effect(repo_id, dest_path):
        import zipfile
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "# Brainstorming Skill")
            zf.writestr("superpowers-main/skills/brainstorming/../../../traversal.txt", "evil")
    mock_download.side_effect = side_effect

    with pytest.raises(ValueError, match="Path traversal detected"):
        skill.sync(temp_env / ".skills.yaml", temp_env)


@patch("manager.download_repo_zip")
def test_library_add_and_remove(mock_download, temp_env):
    import manager as skill
    skill.PROJECT_ROOT = temp_env
    
    # Mock download to write dummy zip
    def side_effect(repo_id, dest_path):
        import zipfile
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "# Brainstorming Skill")
            zf.writestr("superpowers-main/SKILL.md", "# Root Skill")
    mock_download.side_effect = side_effect
    
    # 1. Test Library Add
    yaml_path = temp_env / ".skills.yaml"
    skill.library_add("obra/superpowers", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Check added in YAML
    repo_entry = next(r for r in config["library"] if r["repoId"] == "obra/superpowers")
    skills = repo_entry["skills"]
    assert any(s["name"] == "brainstorming" and s["path"] == "skills/brainstorming/SKILL.md" for s in skills)
    assert any(s["name"] == "superpowers" and s["path"] == "SKILL.md" for s in skills)
    
    # Check library dir contains files
    assert (temp_env / "skills-library/obra/superpowers/brainstorming/SKILL.md").exists()
    assert (temp_env / "skills-library/obra/superpowers/superpowers/SKILL.md").exists()
    
    # 2. Test Library Remove
    # First ensure we have workspace entries for obra/superpowers
    assert any(r["repoId"] == "obra/superpowers" for r in config.get("workspace", []))
    
    skill.library_remove("obra/superpowers", yaml_path, temp_env)
    config = skill.load_config(yaml_path)
    assert not any(r["repoId"] == "obra/superpowers" for r in config["library"])
    assert not any(r["repoId"] == "obra/superpowers" for r in config.get("workspace", []))
    assert not (temp_env / "skills-library/obra/superpowers").exists()


@patch("manager.download_repo_zip")
def test_library_add_no_skills(mock_download, temp_env):
    import manager as skill
    import pytest
    skill.PROJECT_ROOT = temp_env
    
    def side_effect(repo_id, dest_path):
        import zipfile
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.writestr("superpowers-main/random.txt", "hello")
    mock_download.side_effect = side_effect
    
    yaml_path = temp_env / ".skills.yaml"
    with pytest.raises(ValueError, match="No SKILL.md files found in repo"):
        skill.library_add("obra/superpowers", yaml_path, temp_env)


@patch("manager.download_repo_zip")
def test_library_add_download_fails(mock_download, temp_env):
    import manager as skill
    import urllib.error
    import pytest
    skill.PROJECT_ROOT = temp_env
    
    mock_download.side_effect = urllib.error.URLError("Connection refused")
    
    yaml_path = temp_env / ".skills.yaml"
    with pytest.raises(urllib.error.URLError, match="Connection refused"):
        skill.library_add("obra/superpowers", yaml_path, temp_env)


@patch("manager.download_repo_zip")
@patch("builtins.input", side_effect=[""])  # Simulates pressing Enter for prompt
def test_workspace_add_and_remove(mock_input, mock_download, temp_env):
    import manager as skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed library config and library dir
    config = skill.load_config(yaml_path)
    config["library"] = [{
        "repoId": "obra/superpowers",
        "repoType": "github",
        "repoUrl": "https://github.com/obra/superpowers.git",
        "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
    }]
    skill.save_config(config, yaml_path)
    
    skill_dir = temp_env / "skills-library/obra/superpowers/brainstorming"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Brainstorming")
    
    # 1. Test Workspace Add
    skill.workspace_add("brainstorming", "sp-brainstorming", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    assert any(w["repoId"] == "obra/superpowers" for w in config["workspace"])
    assert (temp_env / "skills/sp-brainstorming").is_symlink()
    
    # 2. Test Workspace Remove
    skill.workspace_remove("brainstorming", yaml_path, temp_env)
    config = skill.load_config(yaml_path)
    assert not any(w["skills"] for w in config.get("workspace", []))
    assert not (temp_env / "skills/sp-brainstorming").exists()


@patch("manager.download_repo_zip")
@patch("builtins.input")
def test_workspace_add_multiple_matches_and_interactive(mock_input, mock_download, temp_env):
    import manager as skill
    import os
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed library config with two repos containing the same skill name
    config = skill.load_config(yaml_path)
    config["library"] = [
        {
            "repoId": "obra/superpowers",
            "repoType": "github",
            "repoUrl": "https://github.com/obra/superpowers.git",
            "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
        },
        {
            "repoId": "other/superpowers",
            "repoType": "github",
            "repoUrl": "https://github.com/other/superpowers.git",
            "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
        }
    ]
    skill.save_config(config, yaml_path)
    
    # Create library folders
    for repo_id in ["obra/superpowers", "other/superpowers"]:
        skill_dir = temp_env / f"skills-library/{repo_id}/brainstorming"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("# Brainstorming")

    # Mock input:
    # 1. "2" to select the second repo (other/superpowers)
    # 2. "custom-target" to name the target
    mock_input.side_effect = ["2", "custom-target"]
    
    skill.workspace_add("brainstorming", None, yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Verify the selected repo workspace has the skill
    other_workspace = next(w for w in config["workspace"] if w["repoId"] == "other/superpowers")
    assert any(s["target"] == "custom-target" for s in other_workspace["skills"])
    assert (temp_env / "skills/custom-target").is_symlink()


def test_workspace_add_not_found(temp_env, capsys):
    import manager as skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    skill.workspace_add("nonexistent", "some-target", yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "not found in library" in captured.err


def test_workspace_remove_not_active(temp_env, capsys):
    import manager as skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    skill.workspace_remove("nonexistent", yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "not active in workspace" in captured.err


@patch("manager.download_repo_zip")
@patch("builtins.input")
def test_workspace_remove_multiple_active(mock_input, mock_download, temp_env):
    import manager as skill
    import os
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "# Brainstorming Skill")
    mock_download.side_effect = side_effect
    
    # Seed library and active workspace config
    config = skill.load_config(yaml_path)
    config["library"] = [
        {
            "repoId": "obra/superpowers",
            "repoType": "github",
            "repoUrl": "https://github.com/obra/superpowers.git",
            "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
        },
        {
            "repoId": "other/superpowers",
            "repoType": "github",
            "repoUrl": "https://github.com/other/superpowers.git",
            "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
        }
    ]
    # Both active in workspace
    config["workspace"] = [
        {
            "repoId": "obra/superpowers",
            "skills": [{"name": "brainstorming", "source": "obra/superpowers/brainstorming", "target": "sp-brainstorming"}]
        },
        {
            "repoId": "other/superpowers",
            "skills": [{"name": "brainstorming", "source": "other/superpowers/brainstorming", "target": "other-brainstorming"}]
        }
    ]
    skill.save_config(config, yaml_path)
    
    # Create library folders and symlinks
    for repo_id, target in [("obra/superpowers", "sp-brainstorming"), ("other/superpowers", "other-brainstorming")]:
        skill_dir = temp_env / f"skills-library/{repo_id}/brainstorming"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("# Brainstorming")
        
        # Link in skills/
        link_path = temp_env / f"skills/{target}"
        link_path.parent.mkdir(parents=True, exist_ok=True)
        if not link_path.exists():
            os.symlink(skill_dir, link_path)
            
    # Mock input: "1" to remove the first candidate (obra/superpowers)
    mock_input.side_effect = ["1"]
    
    skill.workspace_remove("brainstorming", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # obra/superpowers workspace entry should be removed or cleaned up
    assert not any(w["repoId"] == "obra/superpowers" for w in config.get("workspace", []))
    assert any(w["repoId"] == "other/superpowers" for w in config.get("workspace", []))
    assert not (temp_env / "skills/sp-brainstorming").exists()
    assert (temp_env / "skills/other-brainstorming").exists()


@patch("manager.download_repo_zip")
@patch("builtins.input", side_effect=["1"])
def test_workspace_add_overwrites_global_duplicate_targets(mock_input, mock_download, temp_env):
    import manager as skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed config with another workspace block containing the same target 'sp-brainstorming'
    config = skill.load_config(yaml_path)
    config["library"] = [
        {
            "repoId": "obra/superpowers",
            "repoType": "github",
            "repoUrl": "https://github.com/obra/superpowers.git",
            "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
        },
        {
            "repoId": "other/superpowers",
            "repoType": "github",
            "repoUrl": "https://github.com/other/superpowers.git",
            "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
        }
    ]
    config["workspace"] = [
        {
            "repoId": "other/superpowers",
            "skills": [{"name": "brainstorming", "source": "other/superpowers/brainstorming", "target": "sp-brainstorming"}]
        }
    ]
    skill.save_config(config, yaml_path)
    
    # Create library directory
    skill_dir = temp_env / "skills-library/obra/superpowers/brainstorming"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Brainstorming")
    
    # Add from obra/superpowers with target 'sp-brainstorming'
    skill.workspace_add("brainstorming", "sp-brainstorming", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Check that other/superpowers repo block is cleaned up (since its only skill was removed)
    assert not any(w["repoId"] == "other/superpowers" for w in config.get("workspace", []))
    # Check that the new skill is registered under obra/superpowers
    assert any(w["repoId"] == "obra/superpowers" for w in config.get("workspace", []))





@patch("manager.download_repo_zip")
@patch("builtins.input")
def test_workspace_add_and_remove_graceful_cancel(mock_input, mock_download, temp_env, capsys):
    import manager as skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # 1. Test KeyboardInterrupt on workspace_add (select repo)
    config = skill.load_config(yaml_path)
    config["library"] = [
        {"repoId": "obra/superpowers", "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]},
        {"repoId": "other/superpowers", "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]}
    ]
    skill.save_config(config, yaml_path)
    
    mock_input.side_effect = KeyboardInterrupt
    skill.workspace_add("brainstorming", None, yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled." in captured.out
    
    # 2. Test manual cancel 'q' on workspace_add (select repo)
    mock_input.side_effect = ["q"]
    skill.workspace_add("brainstorming", None, yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled." in captured.out
    
    # 3. Test EOFError on workspace_add (enter target name)
    # Reset config to one repo so it skips select repo prompt, but prompt for target name is shown
    config = skill.load_config(yaml_path)
    config["library"] = [
        {"repoId": "obra/superpowers", "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]}
    ]
    skill.save_config(config, yaml_path)
    
    mock_input.side_effect = EOFError
    skill.workspace_add("brainstorming", None, yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled." in captured.out
    
    # 4. Test manual cancel 'cancel' on workspace_remove
    # Seed active workspace with multiple items
    config = skill.load_config(yaml_path)
    config["workspace"] = [
        {"repoId": "obra/superpowers", "skills": [{"name": "brainstorming", "source": "src1", "target": "sp-brainstorming"}]},
        {"repoId": "other/superpowers", "skills": [{"name": "brainstorming", "source": "src2", "target": "other-brainstorming"}]}
    ]
    skill.save_config(config, yaml_path)
    
    mock_input.side_effect = ["cancel"]
    skill.workspace_remove("brainstorming", yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled." in captured.out





def test_cli_arg_parsing(temp_env):
    import manager as skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Test argparse parsing with library add
    with patch("manager.library_add") as mock_add:
        sys_args = ["manager.py", "library", "add", "obra/superpowers"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_add.assert_called_once_with("obra/superpowers", yaml_path, temp_env)


def test_cli_subcommands(temp_env):
    import manager as skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    with patch("manager.sync") as mock_sync:
        sys_args = ["manager.py", "sync"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_sync.assert_called_once_with(yaml_path, temp_env, check_remote=False)
            
    # Test library remove subcommand
    with patch("manager.library_remove") as mock_lib_rem:
        sys_args = ["manager.py", "library", "remove", "obra/superpowers"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_lib_rem.assert_called_once_with("obra/superpowers", yaml_path, temp_env)

    # Test workspace add subcommand
    with patch("manager.workspace_add") as mock_work_add:
        sys_args = ["manager.py", "workspace", "add", "brainstorming", "--name", "custom-brain"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_work_add.assert_called_once_with("brainstorming", "custom-brain", yaml_path, temp_env)

    # Test workspace remove subcommand
    with patch("manager.workspace_remove") as mock_work_rem:
        sys_args = ["manager.py", "workspace", "remove", "brainstorming"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_work_rem.assert_called_once_with("brainstorming", yaml_path, temp_env)


def test_cli_config_root_overrides(temp_env):
    import manager as skill
    skill.PROJECT_ROOT = temp_env
    
    custom_root = temp_env / "custom-root"
    custom_root.mkdir(parents=True, exist_ok=True)
    custom_cfg = custom_root / "custom-config.yaml"
    custom_cfg.write_text("library: []\nworkspace: []\n")
    
    with patch("manager.sync") as mock_sync:
        sys_args = [
            "skill.py",
            "--config", str(custom_cfg),
            "--root", str(custom_root),
            "sync"
        ]
        with patch("sys.argv", sys_args):
            skill.main()
            mock_sync.assert_called_once_with(custom_cfg, custom_root, check_remote=False)



def test_library_add_invalid_repo_id(temp_env):
    import manager as skill
    import pytest
    yaml_path = temp_env / ".skills.yaml"
    
    invalid_repo_ids = [
        "invalid_id",          # No slash
        "owner/repo/sub",      # Too many slashes
        "owner/",              # Missing repo
        "/repo",               # Missing owner
        "owner/repo$",         # Invalid character
    ]
    for repo_id in invalid_repo_ids:
        with pytest.raises(ValueError, match="Invalid repo_id format"):
            skill.library_add(repo_id, yaml_path, temp_env)


def test_workspace_add_invalid_target(temp_env):
    import manager as skill
    import pytest
    from unittest.mock import patch
    yaml_path = temp_env / ".skills.yaml"
    
    invalid_targets = [
        "a/b",
        "a\\b",
        ".",
        "..",
        ""
    ]
    
    # Mock download to avoid network calls during library_add or workspace_add
    with patch("manager.download_repo_zip") as mock_download:
        def side_effect(repo_id, dest_path, *args, **kwargs):
            import zipfile
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(dest_path, "w") as zf:
                zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "# Brainstorming Skill")
        mock_download.side_effect = side_effect
        
        # Add to library first
        skill.library_add("obra/superpowers", yaml_path, temp_env)
        
        for target in invalid_targets:
            with pytest.raises(ValueError, match="Invalid target name"):
                skill.workspace_add("brainstorming", target, yaml_path, temp_env)


def test_sync_symlink_target_verification(temp_env):
    import manager as skill
    import pytest
    yaml_path = temp_env / ".skills.yaml"
    
    # Set workspace and mine entries with malicious/outside paths
    config = skill.load_config(yaml_path)
    config["workspace"] = [
        {
            "repoId": "obra/superpowers",
            "skills": [{"name": "brainstorming", "source": "../../outside-path", "target": "bad-workspace"}]
        }
    ]
    skill.save_config(config, yaml_path)
    
    with pytest.raises(ValueError, match="is not strictly inside"):
        skill.sync(yaml_path, temp_env)


def test_atomic_download_and_bad_zip_handling(temp_env):
    import manager as skill
    import pytest
    import zipfile
    from unittest.mock import patch
    
    yaml_path = temp_env / ".skills.yaml"
    zip_path = temp_env / ".skills-repos/obra/superpowers.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Test bad zip recovery: write corrupted content to zip file
    zip_path.write_text("corrupted content")
    assert zip_path.exists()
    
    # In sync, we mock download_repo_zip to raise if called, but since zip exists, sync tries to unzip it first.
    # BadZipFile should be raised, and corrupted file must be deleted.
    with patch("manager.download_repo_zip") as mock_download:
        with pytest.raises(zipfile.BadZipFile):
            skill.sync(yaml_path, temp_env)
        # Corrupt file must be deleted immediately
        assert not zip_path.exists()

    # 2. Test atomic download: when downloading, it writes to a .tmp file first.
    # Mock urllib.request.urlopen to check if temp file is written and renamed.
    from unittest.mock import MagicMock
    response_mock = MagicMock()
    response_mock.__enter__.return_value = response_mock
    _data_779 = [b"some zip content", b""]
    response_mock.read.side_effect = lambda n=-1: _data_779.pop(0) if _data_779 else b""
    
    # We patch open to see if the tmp file is created
    original_open = open
    tmp_file_created = False
    
    def mock_open(file, mode="r", *args, **kwargs):
        nonlocal tmp_file_created
        from pathlib import Path
        if isinstance(file, Path) and file.suffix == ".tmp":
            tmp_file_created = True
        return original_open(file, mode, *args, **kwargs)
        
    with patch("urllib.request.urlopen", return_value=response_mock), \
         patch("builtins.open", mock_open):
        skill.download_repo_zip("obra/superpowers", zip_path)
        
    assert tmp_file_created
    assert zip_path.exists()
    assert zip_path.read_bytes() == b"some zip content"


def test_workspace_collision_detection_internal(temp_env):
    import manager as skill
    import pytest
    yaml_path = temp_env / ".skills.yaml"
    config = skill.load_config(yaml_path)
    config["workspace"] = [
        {
            "repoId": "obra/superpowers",
            "skills": [
                {"name": "brainstorming", "source": "obra/superpowers/brainstorming", "target": "conflict-name"},
                {"name": "executing-plans", "source": "obra/superpowers/executing-plans", "target": "conflict-name"}
            ]
        }
    ]
    skill.save_config(config, yaml_path)
    with pytest.raises(ValueError, match="Duplicate target name: conflict-name in workspace configuration"):
        skill.sync(yaml_path, temp_env)


def test_workspace_collision_detection_external(temp_env):
    import manager as skill
    import pytest
    yaml_path = temp_env / ".skills.yaml"
    
    # 1. Create a plain file at conflict target
    conflict_path = temp_env / "skills/conflict-name"
    conflict_path.parent.mkdir(parents=True, exist_ok=True)
    conflict_path.write_text("plain file")
    
    config = skill.load_config(yaml_path)
    config["workspace"] = [
        {
            "repoId": "obra/superpowers",
            "skills": [
                {"name": "brainstorming", "source": "obra/superpowers/brainstorming", "target": "conflict-name"}
            ]
        }
    ]
    skill.save_config(config, yaml_path)
    
    with pytest.raises(ValueError, match="Collision: Target 'conflict-name' already exists and is not a symlink"):
        skill.sync(yaml_path, temp_env)
        
    # 2. Change to symlink pointing to a different folder
    conflict_path.unlink()
    import os
    diff_dir = temp_env / "different-folder"
    diff_dir.mkdir(parents=True, exist_ok=True)
    os.symlink(diff_dir, conflict_path)
    
    with pytest.raises(ValueError, match="Collision: Symlink 'conflict-name' already exists and points to different source"):
        skill.sync(yaml_path, temp_env)


def test_library_add_commit_hash(temp_env):
    import manager as skill
    import zipfile
    yaml_path = temp_env / ".skills.yaml"
    
    with patch("manager.download_repo_zip") as mock_download:
        def side_effect(repo_id, dest_path):
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(dest_path, "w") as zf:
                zf.comment = b"test-commit-hash-1234"
                zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "# Brainstorming Skill")
        mock_download.side_effect = side_effect
        
        skill.library_add("obra/superpowers", yaml_path, temp_env)
        
    config = skill.load_config(yaml_path)
    repo_entry = next(r for r in config["library"] if r["repoId"] == "obra/superpowers")
    assert repo_entry["commit"] == "test-commit-hash-1234"
    assert (temp_env / "skills-library/obra/superpowers/brainstorming/.commit").read_text(encoding="utf-8").strip() == "test-commit-hash-1234"


def test_sync_commit_hash_cache(temp_env):
    import manager as skill
    import zipfile
    yaml_path = temp_env / ".skills.yaml"
    
    # Pre-extract skill with .commit file
    dest_dir = temp_env / "skills-library/obra/superpowers/brainstorming"
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "SKILL.md").write_text("Old Brainstorming")
    (dest_dir / ".commit").write_text("test-commit-hash-1234", encoding="utf-8")
    
    # Pre-create the zip file
    zip_path = temp_env / ".skills-repos/obra/superpowers.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.comment = b"test-commit-hash-1234"
        zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "Old Brainstorming")
        
    config = skill.load_config(yaml_path)
    config["library"] = [{
        "repoId": "obra/superpowers",
        "commit": "test-commit-hash-1234",
        "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
    }]
    skill.save_config(config, yaml_path)
    
    # Mock download_repo_zip which should NOT be called if it is up to date and zip exists
    with patch("manager.download_repo_zip") as mock_download:
        skill.sync(yaml_path, temp_env)
        assert mock_download.call_count == 0
        
    # Content should be preserved (not deleted or overwritten)
    assert (dest_dir / "SKILL.md").read_text() == "Old Brainstorming"
    
    # Change config commit hash to simulate outdated cache, and delete zip file
    config["library"][0]["commit"] = "new-hash-5678"
    skill.save_config(config, yaml_path)
    if zip_path.exists():
        zip_path.unlink()
    
    with patch("manager.download_repo_zip") as mock_download:
        def side_effect(repo_id, dest_path):
            with zipfile.ZipFile(dest_path, "w") as zf:
                zf.comment = b"new-hash-5678"
                zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "New Brainstorming")
        mock_download.side_effect = side_effect
        
        skill.sync(yaml_path, temp_env)
        assert mock_download.call_count == 1
        
    assert (dest_dir / "SKILL.md").read_text() == "New Brainstorming"
    assert (dest_dir / ".commit").read_text(encoding="utf-8").strip() == "new-hash-5678"


def test_library_update_command(temp_env):
    import manager as skill
    import zipfile
    yaml_path = temp_env / ".skills.yaml"
    
    config = skill.load_config(yaml_path)
    config["library"] = [{
        "repoId": "obra/superpowers",
        "commit": "old-hash",
        "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
    }]
    skill.save_config(config, yaml_path)
    
    # Create the zip in .skills-repos
    zip_path = temp_env / ".skills-repos/obra/superpowers.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.comment = b"old-hash"
        zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "Old content")
        
    # Call library_update
    with patch("manager.download_repo_zip") as mock_download:
        def side_effect(repo_id, dest_path):
            with zipfile.ZipFile(dest_path, "w") as zf:
                zf.comment = b"updated-hash-999"
                zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "Updated content")
        mock_download.side_effect = side_effect
        
        # Test CLI dispatch for library update
        sys_args = ["manager.py", "library", "update", "obra/superpowers"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            
        assert mock_download.call_count == 1
        
    config = skill.load_config(yaml_path)
    repo_entry = next(r for r in config["library"] if r["repoId"] == "obra/superpowers")
    assert repo_entry["commit"] == "updated-hash-999"
    assert (temp_env / "skills-library/obra/superpowers/brainstorming/SKILL.md").read_text() == "Updated content"


def test_sync_broken_symlink_overwrite(temp_env):
    import manager as skill
    import os
    yaml_path = temp_env / ".skills.yaml"
    
    # 1. Create a broken symlink at conflict target
    conflict_path = temp_env / "skills/sp-brainstorming"
    conflict_path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(temp_env / "non-existent-directory", conflict_path)
    
    # Create the correct source directory
    src_dir = temp_env / "skills-library/obra/superpowers/brainstorming"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "SKILL.md").write_text("# Brainstorming")
    
    config = skill.load_config(yaml_path)
    config["workspace"] = [
        {
            "repoId": "obra/superpowers",
            "skills": [
                {"name": "brainstorming", "source": "obra/superpowers/brainstorming", "target": "sp-brainstorming"}
            ]
        }
    ]
    skill.save_config(config, yaml_path)
    
    # Sync should succeed by deleting the broken symlink and recreating it pointing to correct path
    skill.sync(yaml_path, temp_env)
    
    assert conflict_path.is_symlink()
    assert os.readlink(conflict_path) == str(src_dir.resolve())


def test_sync_unmanaged_broken_symlink_pruned(temp_env):
    import manager as skill
    import os
    yaml_path = temp_env / ".skills.yaml"
    
    # Create an unmanaged broken symlink in skills folder
    unmanaged_broken = temp_env / "skills/unmanaged-broken-link"
    unmanaged_broken.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(temp_env / "dead-path-somewhere", unmanaged_broken)
    
    config = skill.load_config(yaml_path)
    config["workspace"] = []
    skill.save_config(config, yaml_path)
    
    # Sync should run and prune the broken unmanaged symlink
    skill.sync(yaml_path, temp_env)
    
    assert not unmanaged_broken.exists()
    assert not unmanaged_broken.is_symlink()


@patch("manager.download_repo_zip")
def test_sync_saves_commit_from_zip_comment(mock_download, temp_env):
    import manager as skill
    import zipfile
    
    yaml_path = temp_env / ".skills.yaml"
    yaml_content = """
library:
- repoId: dummy/repo
  repoType: github
  repoUrl: https://github.com/dummy/repo.git
  skills:
    - name: dummy-skill
      path: dummy-skill/SKILL.md
workspace: []
"""
    yaml_path.write_text(yaml_content)
    
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.writestr("dummy-repo-main/dummy-skill/SKILL.md", "# Dummy Skill")
            zf.comment = b"a1b2c3d4e5f67890"
            
    mock_download.side_effect = side_effect
    
    skill.PROJECT_ROOT = temp_env
    skill.sync(yaml_path, temp_env)
    
    assert (temp_env / ".skills-repos/dummy/repo.zip").exists()
    
    config = skill.load_config(yaml_path)
    assert config["library"][0]["commit"] == "a1b2c3d4e5f67890"


@patch("manager.download_repo_zip")
@patch("subprocess.run")
def test_sync_resolves_dynamic_commit_on_empty(mock_run, mock_download, temp_env):
    import manager as skill
    from unittest.mock import MagicMock
    
    # Mock git ls-remote HEAD to return a specific mock hash
    mock_res = MagicMock()
    mock_res.stdout = "9999a9999b9999c9999d9999e9999f9999000000\tHEAD\n"
    mock_run.return_value = mock_res
    
    # Mock download to write dummy zip
    def side_effect(repo_id, dest_path):
        import zipfile
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.comment = b"9999a9999b9999c9999d9999e9999f9999000000"
            zf.writestr("superpowers-main/skills/brainstorming/SKILL.md", "# Brainstorming Skill")
    mock_download.side_effect = side_effect

    # Setup YAML with commit: latest
    yaml_content = """
library:
- repoId: obra/superpowers
  repoType: github
  repoUrl: https://github.com/obra/superpowers.git
  commit: latest
  skills:
    - name: brainstorming
      path: skills/brainstorming/SKILL.md
"""
    (temp_env / ".skills.yaml").write_text(yaml_content)
    
    skill.PROJECT_ROOT = temp_env
    skill.sync(temp_env / ".skills.yaml", temp_env)
    
    # Verify git ls-remote was called
    mock_run.assert_called_with(
        ["git", "ls-remote", "https://github.com/obra/superpowers.git", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Verify zip downloaded and .commit cached file created with dynamic hash
    assert (temp_env / "skills-library/obra/superpowers/brainstorming/.commit").read_text().strip() == "9999a9999b9999c9999d9999e9999f9999000000"


@patch("manager.sync")
@patch("subprocess.run")
def test_myskills_command_stages_commits_pushes_and_syncs(mock_run, mock_sync, temp_env):
    import manager as skill
    from unittest.mock import MagicMock
    
    # Mock subprocess.run outputs for git commands
    def run_side_effect(cmd, *args, **kwargs):
        res = MagicMock()
        if "remote" in cmd:
            res.stdout = "origin\thttps://github.com/pinedance/AGENTS.git (fetch)\n"
        elif "status" in cmd:
            res.stdout = " M skills/brainstorming/SKILL.md\n"
        elif "rev-parse" in cmd:
            res.stdout = "main\n"
        else:
            res.stdout = ""
        return res
    mock_run.side_effect = run_side_effect

    # Call myskills CLI logic
    skill.PROJECT_ROOT = temp_env
    skill.myskills(message="update brainstorming", config_path=temp_env / ".skills.yaml", root_path=temp_env)

    # Check that git status, add, commit, push were called in sequence targeting skills/
    called_cmds = [call[0][0] for call in mock_run.call_args_list]
    assert any(cmd[:4] == ["git", "status", "--porcelain", "skills/"] for cmd in called_cmds)
    assert any(cmd == ["git", "add", "skills/"] for cmd in called_cmds)
    assert any("commit" in cmd for cmd in called_cmds)
    assert any("push" in cmd for cmd in called_cmds)
    
    # Check that sync was triggered
    mock_sync.assert_called_once_with(temp_env / ".skills.yaml", temp_env)

def test_download_repo_zip_with_commit(tmp_path):
    import manager
    from unittest.mock import patch, MagicMock
    dest = tmp_path / "repo.zip"
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = b""
        mock_urlopen.return_value = mock_resp
        
        manager.download_repo_zip("foo/bar", dest, commit_or_branch="abcdef123456")
        
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        assert req.full_url == "https://github.com/foo/bar/archive/abcdef123456.zip"


def test_sync_cli_parser_check_remote():
    import sys
    from unittest.mock import patch
    import manager
    
    test_args = ["manager.py", "sync", "--check-remote"]
    with patch.object(sys, "argv", test_args), patch("manager.sync") as mock_sync:
        manager.main()
        mock_sync.assert_called_once()
        kwargs = mock_sync.call_args[1]
        assert kwargs.get("check_remote") is True


def test_sync_hash_verification(tmp_path, capsys):
    import manager
    from unittest.mock import patch
    config_path = tmp_path / ".skills.yaml"
    config_path.write_text("""
library:
- repoId: foo/bar
  repoType: github
  repoUrl: https://github.com/foo/bar.git
  commit: "commit1"
  skills: []
""")
    
    with patch("manager.download_repo_zip") as mock_download, \
         patch("manager.get_remote_commit_hash") as mock_remote:
        
        mock_remote.return_value = "commit2"
        
        zip_dir = tmp_path / ".skills-repos"
        zip_dir.mkdir()
        zip_path = zip_dir / "foo/bar.zip"
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        
        import zipfile
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.comment = b"commit3"
        
        manager.sync(config_path, tmp_path, check_remote=False)
        captured = capsys.readouterr()
        assert "Warning: Local file for foo/bar does not match .skills.yaml version (ID1: commit1, ID2: commit3)" in captured.out
        mock_download.assert_called_with("foo/bar", zip_path, "commit1")


def test_get_zip_comment(tmp_path):
    import manager
    import zipfile
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.comment = b"test-comment"
    assert manager._get_zip_comment(zip_path) == "test-comment"




