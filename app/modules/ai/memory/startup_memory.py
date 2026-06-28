from typing import Dict, Any, Optional

class StartupMemory:
    def __init__(self):
        self.profile_data: Dict[str, Any] = {}

    def set_profile(self, data: Dict[str, Any]):
        self.profile_data = dict(data)

    def update_field(self, key: str, value: Any):
        self.profile_data[key] = value

    def get_profile(self) -> Dict[str, Any]:
        return self.profile_data
