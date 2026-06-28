import pytest
import tempfile
import os
from app.modules.ai.prompts.registry import PromptRegistry

def test_prompt_template_loading_and_rendering():
    # Setup temporary templates directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple template file
        template_content = "Hello {name}, welcome to {platform}. {empty} is ignored."
        template_name = "test_greeting"
        
        with open(os.path.join(tmpdir, f"{template_name}.txt"), "w", encoding="utf-8") as f:
            f.write(template_content)
            
        # Create versioned template folder
        os.makedirs(os.path.join(tmpdir, "test_ver_agent"), exist_ok=True)
        with open(os.path.join(tmpdir, "test_ver_agent", "v_2.0.txt"), "w", encoding="utf-8") as f:
            f.write("Version 2.0 system prompt for {startup}")
            
        registry = PromptRegistry(templates_dir=tmpdir)
        
        # Test basic rendering
        rendered = registry.render(template_name, {"name": "Alice", "platform": "TIDES"})
        assert rendered == "Hello Alice, welcome to TIDES. {empty} is ignored."
        
        # Test versioned loading
        rendered_ver = registry.render("test_ver_agent", {"startup": "AgileCorp"}, version="2.0")
        assert rendered_ver == "Version 2.0 system prompt for AgileCorp"

def test_prompt_rendering_with_braces():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Template contains JSON-like curly brackets
        template_content = 'Greeting is {greeting}. Schema: {"name": "string", "id": {id_val}}'
        template_name = "test_braces"
        
        with open(os.path.join(tmpdir, f"{template_name}.txt"), "w", encoding="utf-8") as f:
            f.write(template_content)
            
        registry = PromptRegistry(templates_dir=tmpdir)
        rendered = registry.render(template_name, {"greeting": "Hello", "id_val": "123"})
        
        # Verify JSON curly brackets are intact and variables formatted correctly
        assert rendered == 'Greeting is Hello. Schema: {"name": "string", "id": 123}'
