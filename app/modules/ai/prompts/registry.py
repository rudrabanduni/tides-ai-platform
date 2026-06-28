import os
import re
from typing import Dict, Any, Optional

class PromptRegistry:
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            # Resolve relative to this module folder
            base_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(base_dir, "templates")
            
        self.templates_dir = templates_dir
        
        # Ensure templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)

    def _get_template_path(self, name: str, version: str) -> str:
        """Finds the template file path, supporting versioning folders or files."""
        # Check {templates_dir}/{name}/v_{version}.txt first
        path_ver = os.path.join(self.templates_dir, name, f"v_{version}.txt")
        if os.path.exists(path_ver):
            return path_ver
            
        # Check {templates_dir}/{name}.txt (fallback/default version)
        path_default = os.path.join(self.templates_dir, f"{name}.txt")
        if os.path.exists(path_default):
            return path_default
            
        # Check {templates_dir}/{name}.md (markdown version)
        path_md = os.path.join(self.templates_dir, f"{name}.md")
        if os.path.exists(path_md):
            return path_md
            
        # Also support yaml
        path_yaml = os.path.join(self.templates_dir, f"{name}.yaml")
        if os.path.exists(path_yaml):
            return path_yaml
            
        raise FileNotFoundError(f"Prompt template '{name}' (version: {version}) not found in registry.")

    def load_template(self, name: str, version: str = "latest") -> str:
        """Loads raw template string from external file."""
        path = self._get_template_path(name, version)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def render(self, name: str, variables: Dict[str, Any], version: str = "latest") -> str:
        """Loads prompt template and formats it with substitution variables."""
        template_str = self.load_template(name, version)
        
        # Safe format to prevent key errors with curly brackets in prompts (e.g. JSON schemas)
        # We only format matching standard placeholder format, e.g. {variable_name}
        def replacer(match):
            key = match.group(1)
            if key in variables:
                return str(variables[key])
            # Return original placeholder if variable is missing
            return match.group(0)
            
        # Find all {var_name} matches
        pattern = re.compile(r"\{([a-zA-Z0-9_]+)\}")
        rendered = pattern.sub(replacer, template_str)
        return rendered
