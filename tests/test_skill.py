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
