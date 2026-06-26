import os
import hashlib
import yaml
from datetime import datetime
from typing import Any, Dict, Tuple


class PromptManager:
    _cache: Dict[Tuple[str, str], Dict[str, Any]] = {}

    @classmethod
    def load_prompt(cls, domain: str, version: str = "latest", use_cache: bool = True) -> Dict[str, Any]:
        """Loads the system.md, user.md, and metadata.yaml for a given domain and version."""
        # DEV_MODE bypasses cache for hot reloading
        dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"
        if dev_mode:
            use_cache = False

        cache_key = (domain, version)
        if use_cache and cache_key in cls._cache:
            return cls._cache[cache_key]

        base_dir = os.path.dirname(os.path.abspath(__file__))
        domain_dir = os.path.join(base_dir, domain)

        if not os.path.exists(domain_dir):
            raise FileNotFoundError(f"Domain folder '{domain}' does not exist.")

        # Resolve path based on version
        target_dir = domain_dir
        if version != "latest":
            version_dir = os.path.join(domain_dir, "versions", f"v{version}")
            if os.path.exists(version_dir):
                target_dir = version_dir
            else:
                # Fallback: check if root metadata version matches requested version
                meta_path = os.path.join(domain_dir, "metadata.yaml")
                if os.path.exists(meta_path):
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = yaml.safe_load(f)
                    if meta.get("version") != version:
                        raise FileNotFoundError(f"Version '{version}' for domain '{domain}' not found.")
                else:
                    raise FileNotFoundError(f"Version '{version}' for domain '{domain}' not found.")

        system_path = os.path.join(target_dir, "system.md")
        user_path = os.path.join(target_dir, "user.md")
        meta_path = os.path.join(target_dir, "metadata.yaml")

        if not os.path.exists(system_path) or not os.path.exists(user_path) or not os.path.exists(meta_path):
            raise FileNotFoundError(f"Prompt templates or metadata missing in {target_dir}")

        with open(system_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()

        with open(user_path, "r", encoding="utf-8") as f:
            user_prompt = f.read()

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = yaml.safe_load(f)

        # Compute hash
        combined = system_prompt + user_prompt
        prompt_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

        result = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "metadata": metadata,
            "prompt_name": metadata.get("name", f"{domain.capitalize()} Analysis Prompt"),
            "prompt_version": metadata.get("version", "1.0.0"),
            "prompt_hash": prompt_hash,
            "loaded_at": datetime.utcnow().isoformat() + "Z"
        }

        if use_cache:
            cls._cache[cache_key] = result

        return result

    _reporting_cache: Dict[str, str] = {}

    @classmethod
    def load_reporting_template(cls, template_name: str, use_cache: bool = True) -> str:
        """Loads a reporting template from app/modules/reporting/templates/ with caching."""
        dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"
        if dev_mode:
            use_cache = False

        if use_cache and template_name in cls._reporting_cache:
            return cls._reporting_cache[template_name]

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_path = os.path.join(base_dir, "reporting", "templates", f"{template_name}.md")

        if not os.path.exists(template_path):
            # Alternative layout fallback
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            template_path = os.path.join(base_dir, "app", "modules", "reporting", "templates", f"{template_name}.md")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Reporting template '{template_name}.md' not found")

        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        if use_cache:
            cls._reporting_cache[template_name] = content

        return content
