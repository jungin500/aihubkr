import base64
import json
import os
from typing import Dict, Optional

import requests
from aihubkr.core.config import AIHubConfig


class AIHubAuth:
    """
    Handles authentication for AIHub API.
    
    This class manages user credentials for authenticating with the AIHub API,
    including saving, loading, and clearing credentials from the configuration file.
    
    Attributes:
        BASE_URL (str): The base URL for the AIHub API.
        LOGIN_URL (str): The URL for the login endpoint.
        aihub_id (str): The user's AIHub ID.
        aihub_pw (str): The user's AIHub password.
        autosave_enabled (bool): Whether to automatically save credentials.
    """

    BASE_URL = "https://api.aihub.or.kr"
    LOGIN_URL = f"{BASE_URL}/api/loginProcess.do"

    def __init__(self, aihub_id: str, aihub_pw: str):
        """
        Initialize the AIHubAuth instance.
        
        Args:
            aihub_id (str): The user's AIHub ID.
            aihub_pw (str): The user's AIHub password.
        """
        self.aihub_id = aihub_id
        self.aihub_pw = aihub_pw
        self.autosave_enabled = False

    def clear_credential(self) -> None:
        """
        Clear the saved credentials from the configuration file.
        
        This method removes the authentication information from the configuration
        and resets the instance variables.
        """
        self.aihub_id = None
        self.aihub_pw = None
        self.autosave_enabled = False

        config_manager = AIHubConfig.get_instance()
        if "auth" in config_manager.config_db:
            config_manager.config_db.pop("auth")
        config_manager.save_to_disk()

    def save_credential(self) -> None:
        """
        Save the current credentials to the configuration file.
        
        This method stores the authentication information in the configuration
        for future use.
        """
        credential = {"id": self.aihub_id, "pass": self.aihub_pw}
        credential = json.dumps(credential)

        config_manager = AIHubConfig.get_instance()
        config_manager.config_db["auth"] = credential
        config_manager.save_to_disk()

    def load_credentials(self) -> Optional[Dict[str, str]]:
        """
        Load credentials from the configuration file.
        
        Returns:
            Optional[Dict[str, str]]: A dictionary containing the credentials if found,
                                     None otherwise.
        """
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
        """
        Authenticate with the AIHub API using the current credentials.
        
        Returns:
            Optional[Dict[str, str]]: A dictionary containing the authentication headers
                                     if authentication is successful, None otherwise.
        """
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