from pathlib import Path
import pytest
import skill

@pytest.fixture
def temp_env(tmp_path):
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
    source: obra/superpowers/skills/brainstorming
    target: sp-brainstorming 
mine:
  - name: claude-video
    source: superpowers/writing-plan
    target: my-writing-plan
"""
    yaml_path = tmp_path / ".skills.yaml"
    yaml_path.write_text(yaml_content)
    return tmp_path

def test_load_save_config_preserves_comments(temp_env):
    yaml_path = temp_env / ".skills.yaml"
    config = skill.load_config(yaml_path)
    assert "library" in config
    assert "workspace" in config
    assert "mine" in config
    
    # Modify config and save
    config["mine"].append({"name": "test", "source": "test-src", "target": "test-tgt"})
    skill.save_config(config, yaml_path)
    
    saved_content = yaml_path.read_text()
    assert "# Test comments" in saved_content
    assert "test-tgt" in saved_content

def test_load_empty_config(tmp_path):
    yaml_path = tmp_path / ".skills.yaml"
    yaml_path.write_text("")
    config = skill.load_config(yaml_path)
    assert config == {"library": [], "workspace": [], "mine": []}

def test_load_only_comments_config(tmp_path):
    yaml_path = tmp_path / ".skills.yaml"
    yaml_path.write_text("# Only comments here\n")
    config = skill.load_config(yaml_path)
    assert config == {"library": [], "workspace": [], "mine": []}


from unittest.mock import patch

@patch("skill.download_repo_zip")
def test_sync_rebuilds_links_and_library(mock_download, temp_env):
    import skill
    
    # Mock download to write a dummy zip with a SKILL.md
    def side_effect(repo_id, dest_path):
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
    assert (temp_env / "skills-library/obra/superpowers/skills/brainstorming/SKILL.md").exists()
    assert not (temp_env / "skills-library/obra/superpowers/skills/other/SKILL.md").exists()
    
    # Verify workspace symlink created
    link_path = temp_env / "skills/sp-brainstorming"
    assert link_path.is_symlink()
    assert link_path.resolve() == (temp_env / "skills-library/obra/superpowers/skills/brainstorming").resolve()


@patch("skill.download_repo_zip")
def test_sync_prunes_obsolete_and_idempotent(mock_download, temp_env):
    import skill
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
    stale_lib_skill = temp_env / "skills-library/obra/superpowers/skills/obsolete_skill"
    stale_lib_skill.mkdir(parents=True, exist_ok=True)
    (stale_lib_skill / "SKILL.md").write_text("# Obsolete Skill")
    (stale_lib_skill / "helper.py").write_text("print('stale')")
    
    # A stale symlink or dir in skills/
    stale_link = temp_env / "skills/stale-link"
    stale_link.mkdir(parents=True, exist_ok=True) # as a directory
    
    stale_link_file = temp_env / "skills/stale-link-file"
    stale_link_file.write_text("file content") # as a file
    
    # Run sync
    skill.sync(temp_env / ".skills.yaml", temp_env)
    
    # Verify zip downloaded and old one pruned
    assert (temp_env / ".skills-repos/obra/superpowers.zip").exists()
    assert not stale_zip.exists()
    
    # Verify library extracted and stale library skill pruned
    assert (temp_env / "skills-library/obra/superpowers/skills/brainstorming/SKILL.md").exists()
    assert not stale_lib_skill.exists()
    
    # Verify stale links inside skills/ are removed, and new ones exist
    assert not stale_link.exists()
    assert not stale_link_file.exists()
    assert (temp_env / "skills/sp-brainstorming").is_symlink()
    
    # Call sync again to verify idempotency (it shouldn't download or break anything)
    mock_download.reset_mock()
    skill.sync(temp_env / ".skills.yaml", temp_env)
    assert mock_download.call_count == 0
    assert (temp_env / "skills/sp-brainstorming").is_symlink()


@patch("urllib.request.urlopen")
def test_download_repo_zip_fallback(mock_urlopen, tmp_path):
    import urllib.error
    import skill
    from unittest.mock import MagicMock
    
    response_mock = MagicMock()
    response_mock.__enter__.return_value = response_mock
    response_mock.read.return_value = b"zip-content"
    
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
    import skill
    
    def urlopen_side_effect(req, *args, **kwargs):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)
        
    mock_urlopen.side_effect = urlopen_side_effect
    
    dest = tmp_path / "repo.zip"
    with pytest.raises(urllib.error.HTTPError):
        skill.download_repo_zip("obra/superpowers", dest)


@patch("skill.download_repo_zip")
def test_sync_zip_slip_prevention(mock_download, temp_env):
    import skill
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


@patch("skill.download_repo_zip")
def test_library_add_and_remove(mock_download, temp_env):
    import skill
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
    assert (temp_env / "skills-library/obra/superpowers/skills/brainstorming/SKILL.md").exists()
    
    # 2. Test Library Remove
    # First ensure we have workspace entries for obra/superpowers
    assert any(r["repoId"] == "obra/superpowers" for r in config.get("workspace", []))
    
    skill.library_remove("obra/superpowers", yaml_path, temp_env)
    config = skill.load_config(yaml_path)
    assert not any(r["repoId"] == "obra/superpowers" for r in config["library"])
    assert not any(r["repoId"] == "obra/superpowers" for r in config.get("workspace", []))
    assert not (temp_env / "skills-library/obra/superpowers").exists()


@patch("skill.download_repo_zip")
def test_library_add_no_skills(mock_download, temp_env):
    import skill
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


@patch("skill.download_repo_zip")
def test_library_add_download_fails(mock_download, temp_env):
    import skill
    import urllib.error
    import pytest
    skill.PROJECT_ROOT = temp_env
    
    mock_download.side_effect = urllib.error.URLError("Connection refused")
    
    yaml_path = temp_env / ".skills.yaml"
    with pytest.raises(urllib.error.URLError, match="Connection refused"):
        skill.library_add("obra/superpowers", yaml_path, temp_env)


@patch("skill.download_repo_zip")
@patch("builtins.input", side_effect=[""])  # Simulates pressing Enter for prompt
def test_workspace_add_and_remove(mock_input, mock_download, temp_env):
    import skill
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
    
    skill_dir = temp_env / "skills-library/obra/superpowers/skills/brainstorming"
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


@patch("skill.download_repo_zip")
@patch("builtins.input")
def test_workspace_add_multiple_matches_and_interactive(mock_input, mock_download, temp_env):
    import skill
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
        skill_dir = temp_env / f"skills-library/{repo_id}/skills/brainstorming"
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
    import skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    skill.workspace_add("nonexistent", "some-target", yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "not found in library" in captured.err


def test_workspace_remove_not_active(temp_env, capsys):
    import skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    skill.workspace_remove("nonexistent", yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "not active in workspace" in captured.err


@patch("skill.download_repo_zip")
@patch("builtins.input")
def test_workspace_remove_multiple_active(mock_input, mock_download, temp_env):
    import skill
    import os
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
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
            "skills": [{"name": "brainstorming", "source": "obra/superpowers/skills/brainstorming", "target": "sp-brainstorming"}]
        },
        {
            "repoId": "other/superpowers",
            "skills": [{"name": "brainstorming", "source": "other/superpowers/skills/brainstorming", "target": "other-brainstorming"}]
        }
    ]
    skill.save_config(config, yaml_path)
    
    # Create library folders and symlinks
    for repo_id, target in [("obra/superpowers", "sp-brainstorming"), ("other/superpowers", "other-brainstorming")]:
        skill_dir = temp_env / f"skills-library/{repo_id}/skills/brainstorming"
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


@patch("skill.download_repo_zip")
@patch("builtins.input", side_effect=["1"])
def test_workspace_add_overwrites_global_duplicate_targets(mock_input, mock_download, temp_env):
    import skill
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
            "skills": [{"name": "brainstorming", "source": "other/superpowers/skills/brainstorming", "target": "sp-brainstorming"}]
        }
    ]
    skill.save_config(config, yaml_path)
    
    # Create library directory
    skill_dir = temp_env / "skills-library/obra/superpowers/skills/brainstorming"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Brainstorming")
    
    # Add from obra/superpowers with target 'sp-brainstorming'
    skill.workspace_add("brainstorming", "sp-brainstorming", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Check that other/superpowers repo block is cleaned up (since its only skill was removed)
    assert not any(w["repoId"] == "other/superpowers" for w in config.get("workspace", []))
    # Check that the new skill is registered under obra/superpowers
    assert any(w["repoId"] == "obra/superpowers" for w in config.get("workspace", []))


@patch("skill.download_repo_zip")
@patch("builtins.input", side_effect=[""])
def test_workspace_add_removes_mine_conflicts(mock_input, mock_download, temp_env):
    import skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed library config and mine config with target 'sp-brainstorming'
    config = skill.load_config(yaml_path)
    config["library"] = [{
        "repoId": "obra/superpowers",
        "repoType": "github",
        "repoUrl": "https://github.com/obra/superpowers.git",
        "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
    }]
    config["mine"] = [{"name": "some-mine-skill", "source": "local/mine", "target": "sp-brainstorming"}]
    skill.save_config(config, yaml_path)
    
    skill_dir = temp_env / "skills-library/obra/superpowers/skills/brainstorming"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Brainstorming")
    
    # Add from obra/superpowers with target 'sp-brainstorming'
    skill.workspace_add("brainstorming", "sp-brainstorming", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Check that mine entry was removed
    assert not any(m["target"] == "sp-brainstorming" for m in config.get("mine", []))
    # Check that the workspace has the skill
    assert any(w["repoId"] == "obra/superpowers" for w in config["workspace"])


@patch("skill.download_repo_zip")
@patch("builtins.input")
def test_workspace_add_and_remove_graceful_cancel(mock_input, mock_download, temp_env, capsys):
    import skill
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


@patch("skill.download_repo_zip")
@patch("builtins.input", side_effect=["my-brainstorming"])
def test_mine_add_and_remove(mock_input, mock_download, temp_env):
    import skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Mock download to write dummy zip
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed library, workspace and directory
    config = skill.load_config(yaml_path)
    config["library"] = [{
        "repoId": "obra/superpowers",
        "repoType": "github",
        "repoUrl": "https://github.com/obra/superpowers.git",
        "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
    }]
    config["workspace"] = [{
        "repoId": "obra/superpowers",
        "skills": [{"name": "brainstorming", "source": "obra/superpowers/skills/brainstorming", "target": "sp-brainstorming"}]
    }]
    skill.save_config(config, yaml_path)
    
    skill_dir = temp_env / "skills-library/obra/superpowers/skills/brainstorming"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Brainstorming")
    
    # 1. Test Mine Add
    skill.mine_add("brainstorming", "my-brainstorming", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Check removed from workspace
    assert not any(w["skills"] for w in config.get("workspace", []))
    # Check added in mine
    assert any(m["target"] == "my-brainstorming" for m in config.get("mine", []))
    # Check folder physical copy exists in skills-mine
    assert (temp_env / "skills-mine/obra/superpowers/skills/brainstorming/SKILL.md").exists()
    # Check symlink exists
    assert (temp_env / "skills/my-brainstorming").is_symlink()
    
    # 2. Test Mine Remove
    skill.mine_remove("brainstorming", yaml_path, temp_env)
    config = skill.load_config(yaml_path)
    assert not any(m["name"] == "brainstorming" for m in config.get("mine", []))
    assert not (temp_env / "skills/my-brainstorming").exists()


@patch("skill.download_repo_zip")
@patch("builtins.input")
def test_mine_add_interactive_and_multiple(mock_input, mock_download, temp_env):
    import skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Mock download to write dummy zip
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed library with two repos with same skill name
    config = skill.load_config(yaml_path)
    config["library"] = [
        {
            "repoId": "obra/superpowers",
            "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
        },
        {
            "repoId": "other/superpowers",
            "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
        }
    ]
    skill.save_config(config, yaml_path)
    
    # Create the library dir for the second one
    skill_dir = temp_env / "skills-library/other/superpowers/skills/brainstorming"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Brainstorming Other")
    
    # Mock input: "2" for other/superpowers, and "" for default target name "my-brainstorming"
    mock_input.side_effect = ["2", ""]
    
    skill.mine_add("brainstorming", None, yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Check added in mine with source 'other/superpowers/skills/brainstorming'
    mine_entry = next(m for m in config.get("mine", []) if m["name"] == "brainstorming")
    assert mine_entry["source"] == "other/superpowers/skills/brainstorming"
    assert mine_entry["target"] == "my-brainstorming"
    
    assert (temp_env / "skills-mine/other/superpowers/skills/brainstorming/SKILL.md").exists()
    assert (temp_env / "skills/my-brainstorming").is_symlink()


@patch("builtins.input")
def test_mine_remove_multiple(mock_input, temp_env):
    import skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Seed mine config with two entries for "brainstorming" but different targets
    config = skill.load_config(yaml_path)
    config["mine"] = [
        {"name": "brainstorming", "source": "obra/superpowers/skills/brainstorming", "target": "my-brainstorming"},
        {"name": "brainstorming", "source": "other/superpowers/skills/brainstorming", "target": "other-brainstorming"}
    ]
    skill.save_config(config, yaml_path)
    
    # Create the physical folders in skills-mine
    for source in ["obra/superpowers/skills/brainstorming", "other/superpowers/skills/brainstorming"]:
        (temp_env / "skills-mine" / source).mkdir(parents=True, exist_ok=True)
        (temp_env / "skills-mine" / source / "SKILL.md").write_text("# Brainstorming")
        
    skill.sync(yaml_path, temp_env)
    assert (temp_env / "skills/my-brainstorming").is_symlink()
    assert (temp_env / "skills/other-brainstorming").is_symlink()
    
    # Mock input: "2" to remove other-brainstorming
    mock_input.side_effect = ["2"]
    
    skill.mine_remove("brainstorming", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Check other-brainstorming was removed, but my-brainstorming remains
    assert any(m["target"] == "my-brainstorming" for m in config.get("mine", []))
    assert not any(m["target"] == "other-brainstorming" for m in config.get("mine", []))
    
    assert (temp_env / "skills/my-brainstorming").exists()
    assert not (temp_env / "skills/other-brainstorming").exists()


@patch("skill.download_repo_zip")
@patch("builtins.input")
def test_mine_add_and_remove_cancel(mock_input, mock_download, temp_env, capsys):
    import skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Mock download to write dummy zip
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed library config with two repos containing the same skill name
    config = skill.load_config(yaml_path)
    config["library"] = [
        {"repoId": "obra/superpowers", "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]},
        {"repoId": "other/superpowers", "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]}
    ]
    skill.save_config(config, yaml_path)
    
    # 1. Test KeyboardInterrupt on mine_add select repo
    mock_input.side_effect = KeyboardInterrupt
    skill.mine_add("brainstorming", None, yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled." in captured.out
    
    # 2. Test manual cancel 'q' on mine_add select repo
    mock_input.side_effect = ["q"]
    skill.mine_add("brainstorming", None, yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled." in captured.out
    
    # 3. Test EOFError on mine_add enter target name
    # Reset config to one repo so it skips select repo prompt, but prompt for target name is shown
    config = skill.load_config(yaml_path)
    config["library"] = [
        {"repoId": "obra/superpowers", "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]}
    ]
    skill.save_config(config, yaml_path)
    
    mock_input.side_effect = EOFError
    skill.mine_add("brainstorming", None, yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled." in captured.out
    
    # 4. Test manual cancel 'cancel' on mine_remove
    # Seed mine config with multiple items
    config = skill.load_config(yaml_path)
    config["mine"] = [
        {"name": "brainstorming", "source": "src1", "target": "my-brainstorming"},
        {"name": "brainstorming", "source": "src2", "target": "other-brainstorming"}
    ]
    skill.save_config(config, yaml_path)
    
    mock_input.side_effect = ["cancel"]
    skill.mine_remove("brainstorming", yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled." in captured.out


@patch("skill.download_repo_zip")
@patch("builtins.input")
def test_mine_add_existing_folder_abort_and_overwrite(mock_input, mock_download, temp_env, capsys):
    import skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Mock download to write dummy zip
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed library config
    config = skill.load_config(yaml_path)
    config["library"] = [{
        "repoId": "obra/superpowers",
        "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
    }]
    skill.save_config(config, yaml_path)
    
    # Library folder (source)
    src_dir = temp_env / "skills-library/obra/superpowers/skills/brainstorming"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "SKILL.md").write_text("Library Brainstorming")
    
    # Existing Mine folder (target)
    dest_dir = temp_env / "skills-mine/obra/superpowers/skills/brainstorming"
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "SKILL.md").write_text("Existing Custom Brainstorming")
    
    # 1. Test decline overwrite
    mock_input.side_effect = ["n"]
    skill.mine_add("brainstorming", "my-brainstorming", yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled. Existing custom skill preserved." in captured.out
    assert (dest_dir / "SKILL.md").read_text() == "Existing Custom Brainstorming"
    
    # 2. Test cancel/KeyboardInterrupt on overwrite prompt
    mock_input.side_effect = KeyboardInterrupt
    skill.mine_add("brainstorming", "my-brainstorming", yaml_path, temp_env)
    captured = capsys.readouterr()
    assert "Operation canceled. Existing custom skill preserved." in captured.out
    assert (dest_dir / "SKILL.md").read_text() == "Existing Custom Brainstorming"
    
    # 3. Test confirm overwrite
    mock_input.side_effect = ["y"]
    skill.mine_add("brainstorming", "my-brainstorming", yaml_path, temp_env)
    assert (dest_dir / "SKILL.md").read_text() == "Library Brainstorming"
    
    # Check YAML config updated
    config = skill.load_config(yaml_path)
    assert any(m["target"] == "my-brainstorming" for m in config.get("mine", []))


@patch("skill.download_repo_zip")
def test_mine_add_cleans_workspace_target_globally(mock_download, temp_env):
    import skill
    import zipfile
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Mock download to write dummy zip
    def side_effect(repo_id, dest_path):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest_path, "w") as zf:
            pass
    mock_download.side_effect = side_effect
    
    # Seed library config and workspace config
    config = skill.load_config(yaml_path)
    config["library"] = [{
        "repoId": "obra/superpowers",
        "skills": [{"name": "brainstorming", "path": "skills/brainstorming/SKILL.md"}]
    }]
    # Workspace has two entries matching target 'my-brainstorming'
    config["workspace"] = [
        {
            "repoId": "obra/superpowers",
            "skills": [{"name": "brainstorming", "source": "obra/superpowers/skills/brainstorming", "target": "my-brainstorming"}]
        },
        {
            "repoId": "other/superpowers",
            "skills": [{"name": "other-skill", "source": "other/superpowers/skills/other", "target": "my-brainstorming"}]
        }
    ]
    skill.save_config(config, yaml_path)
    
    # Create source directory
    src_dir = temp_env / "skills-library/obra/superpowers/skills/brainstorming"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "SKILL.md").write_text("# Brainstorming")
    
    # Add skill to mine
    skill.mine_add("brainstorming", "my-brainstorming", yaml_path, temp_env)
    
    config = skill.load_config(yaml_path)
    # Check that workspace is completely empty because all matching targets were cleaned up
    assert not any(w["skills"] for w in config.get("workspace", []))


def test_cli_arg_parsing(temp_env):
    import skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Test argparse parsing with library add
    with patch("skill.library_add") as mock_add:
        sys_args = ["skill.py", "library", "add", "obra/superpowers"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_add.assert_called_once_with("obra/superpowers", yaml_path, temp_env)


def test_cli_migration_and_other_subcommands(temp_env):
    import skill
    import shutil
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Test migration of skills-archive to skills-library
    archive_dir = temp_env / "skills-archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    # The new directory should not exist beforehand
    library_dir = temp_env / "skills-library"
    if library_dir.exists():
        shutil.rmtree(library_dir)
        
    with patch("skill.sync") as mock_sync:
        sys_args = ["skill.py", "sync"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_sync.assert_called_once_with(yaml_path, temp_env)
            
    assert not archive_dir.exists()
    assert library_dir.exists()
    
    # Test library remove subcommand
    with patch("skill.library_remove") as mock_lib_rem:
        sys_args = ["skill.py", "library", "remove", "obra/superpowers"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_lib_rem.assert_called_once_with("obra/superpowers", yaml_path, temp_env)

    # Test workspace add subcommand
    with patch("skill.workspace_add") as mock_work_add:
        sys_args = ["skill.py", "workspace", "add", "brainstorming", "--name", "custom-brain"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_work_add.assert_called_once_with("brainstorming", "custom-brain", yaml_path, temp_env)

    # Test workspace remove subcommand
    with patch("skill.workspace_remove") as mock_work_rem:
        sys_args = ["skill.py", "workspace", "remove", "brainstorming"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_work_rem.assert_called_once_with("brainstorming", yaml_path, temp_env)

    # Test mine add subcommand
    with patch("skill.mine_add") as mock_mine_add:
        sys_args = ["skill.py", "mine", "add", "brainstorming", "--name", "my-brain"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_mine_add.assert_called_once_with("brainstorming", "my-brain", yaml_path, temp_env)

    # Test mine remove subcommand
    with patch("skill.mine_remove") as mock_mine_rem:
        sys_args = ["skill.py", "mine", "remove", "brainstorming"]
        with patch("sys.argv", sys_args):
            skill.main(config_path=yaml_path, root_path=temp_env)
            mock_mine_rem.assert_called_once_with("brainstorming", yaml_path, temp_env)


def test_cli_config_root_overrides(temp_env):
    import skill
    skill.PROJECT_ROOT = temp_env
    
    custom_root = temp_env / "custom-root"
    custom_root.mkdir(parents=True, exist_ok=True)
    custom_cfg = custom_root / "custom-config.yaml"
    custom_cfg.write_text("library: []\nworkspace: []\nmine: []\n")
    
    with patch("skill.sync") as mock_sync:
        sys_args = [
            "skill.py",
            "--config", str(custom_cfg),
            "--root", str(custom_root),
            "sync"
        ]
        with patch("sys.argv", sys_args):
            skill.main()
            mock_sync.assert_called_once_with(custom_cfg, custom_root)


def test_cli_migration_oserror_warning(temp_env, capsys):
    import skill
    skill.PROJECT_ROOT = temp_env
    yaml_path = temp_env / ".skills.yaml"
    
    # Create the old archive directory
    archive_dir = temp_env / "skills-archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock rename to raise OSError
    with patch("pathlib.Path.rename", side_effect=OSError("Permission denied")):
        sys_args = ["skill.py", "sync"]
        with patch("sys.argv", sys_args):
            with patch("skill.sync") as mock_sync:
                skill.main(config_path=yaml_path, root_path=temp_env)
                mock_sync.assert_called_once_with(yaml_path, temp_env)
                
    captured = capsys.readouterr()
    assert "Warning: Failed to migrate skills-archive: Permission denied" in captured.err


def test_library_add_invalid_repo_id(temp_env):
    import skill
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


def test_workspace_mine_add_invalid_target(temp_env):
    import skill
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
    with patch("skill.download_repo_zip") as mock_download:
        def side_effect(repo_id, dest_path):
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
            with pytest.raises(ValueError, match="Invalid target name"):
                skill.mine_add("brainstorming", target, yaml_path, temp_env)


def test_sync_symlink_target_verification(temp_env):
    import skill
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
    import skill
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
    with patch("skill.download_repo_zip") as mock_download:
        with pytest.raises(zipfile.BadZipFile):
            skill.sync(yaml_path, temp_env)
        # Corrupt file must be deleted immediately
        assert not zip_path.exists()

    # 2. Test atomic download: when downloading, it writes to a .tmp file first.
    # Mock urllib.request.urlopen to check if temp file is written and renamed.
    from unittest.mock import MagicMock
    response_mock = MagicMock()
    response_mock.__enter__.return_value = response_mock
    response_mock.read.return_value = b"some zip content"
    
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





