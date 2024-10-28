import base64
import json
import os
from typing import Dict, Optional

import requests
from core.config import AIHubConfig


class AIHubAuth:
    """Handles authentication for AIHub API."""

    BASE_URL = "https://api.aihub.or.kr"
    LOGIN_URL = f"{BASE_URL}/api/loginProcess.do"

    def __init__(self, aihub_id: str, aihub_pw: str):
        self.aihub_id = aihub_id
        self.aihub_pw = aihub_pw
        self.autosave_enabled = False

    def clear_credential(self) -> None:
        self.aihub_id = None
        self.aihub_pw = None
        self.autosave_enabled = False

        config_manager = AIHubConfig.get_instance()
        if "auth" in config_manager.config_db:
            config_manager.config_db.pop("auth")
        config_manager.save_to_disk()

    def save_credential(self) -> None:
        credential = {"id": self.aihub_id, "pass": self.aihub_pw}
        credential = json.dumps(credential)

        config_manager = AIHubConfig.get_instance()
        config_manager.config_db["auth"] = credential
        config_manager.save_to_disk()

    def load_credentials(self) -> Optional[Dict[str, str]]:
        config_manager = AIHubConfig.get_instance()
        config_manager.load_from_disk()

        if config_manager.config_db.get("auth") is None:
            return None

        credential = config_manager.config_db.get("auth")
        credential = json.loads(credential)

        self.aihub_id = credential.get("id")
        self.aihub_pw = credential.get("pass")

        # Enable autosave while previously used credentials.json is loaded
        self.autosave_enabled = True
        return credential

    def authenticate(self) -> Optional[Dict[str, str]]:
        response = requests.post(
            self.LOGIN_URL, headers={"id": self.aihub_id, "pass": self.aihub_pw}
        )

        if response.status_code == 200:
            try:
                data = response.json()
                code = int(
                    data.get("code", 0)
                )  # Convert to int and default to 0 if not present
                if code == 200:
                    return {"id": self.aihub_id, "pass": self.aihub_pw}
                else:
                    # print(f"Authentication failed. Code: {code}")
                    return None
            except (ValueError, KeyError) as e:
                print(f"Failed to parse authentication response: {e}")
        else:
            print(f"Authentication request failed. Status code: {response.status_code}")

        return None
