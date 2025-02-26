import base64
import json
import os


class AIHubConfig:
    """
    Configuration manager for AIHub CLI and GUI applications.
    
    This class manages the configuration settings for the AIHub applications,
    including loading, saving, and clearing configuration data from disk.
    It follows the Singleton pattern to ensure only one instance exists.
    
    Attributes:
        CONFIG_PATH (str): The path to the configuration file.
        _instance (AIHubConfig): The singleton instance of the class.
        config_db (dict): The configuration database.
    """

    CONFIG_PATH = os.path.expanduser("~/.aihubkr-cli/config.json")
    _instance = None

    @staticmethod
    def get_instance():
        """
        Get the singleton instance of the AIHubConfig class.
        
        Returns:
            AIHubConfig: The singleton instance.
        """
        return AIHubConfig._instance

    def __init__(self):
        """Initialize the AIHubConfig instance with an empty configuration database."""
        self.config_db = {}

    def load_from_disk(self) -> dict:
        """
        Load configuration from disk.
        
        This method loads the configuration from the CONFIG_PATH file,
        decoding the base64-encoded values.
        
        Returns:
            dict: The loaded configuration database.
            
        Raises:
            RuntimeError: If called on an instance other than the singleton.
        """
        if self != AIHubConfig._instance:
            raise RuntimeError("Singleton class. Use get_instance() instead.")

        if not os.path.exists(AIHubConfig.CONFIG_PATH):
            return {}

        try:
            with open(AIHubConfig.CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            config_db = {}
            for key in data.keys():
                config_db[key] = base64.b64decode(data.get(key)).decode()
            return config_db
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(
                f"Failed to load credential file at {AIHubConfig.CONFIG_PATH}: {e}"
            )
            return {}

    def save_to_disk(self) -> None:
        """
        Save configuration to disk.
        
        This method saves the configuration to the CONFIG_PATH file,
        encoding the values with base64.
        
        Raises:
            RuntimeError: If called on an instance other than the singleton.
        """
        if self != AIHubConfig._instance:
            raise RuntimeError("Singleton class. Use get_instance() instead.")

        os.makedirs(os.path.dirname(AIHubConfig.CONFIG_PATH), exist_ok=True)

        save_config = {}
        for key in self.config_db.keys():
            save_config[key] = base64.b64encode(
                self.config_db.get(key).encode()
            ).decode()

        with open(AIHubConfig.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(save_config, f)

    def clear(self, save: bool = True) -> None:
        """
        Clear the configuration database.
        
        Args:
            save (bool, optional): Whether to remove the configuration file from disk.
                                  Defaults to True.
                                  
        Raises:
            RuntimeError: If called on an instance other than the singleton.
        """
        if self != AIHubConfig._instance:
            raise RuntimeError("Singleton class. Use get_instance() instead.")

        if save and os.path.exists(AIHubConfig.CONFIG_PATH):
            os.remove(AIHubConfig.CONFIG_PATH)
        self.config_db = {}


# Initialize the singleton instance
if AIHubConfig._instance is None:
    AIHubConfig._instance = AIHubConfig()
    AIHubConfig._instance.config_db = AIHubConfig._instance.load_from_disk()