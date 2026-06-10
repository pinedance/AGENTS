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



