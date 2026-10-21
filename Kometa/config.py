import os

import yaml


class Config:
    """
    A class to handle configuration settings loaded from a YAML file.
    """
    _instance = None

    def __new__(cls, config_path="config.yaml"):
        if cls._instance is None:
            instance = super(Config, cls).__new__(cls)
            instance._initialize(config_path)
            cls._instance = instance
        return cls._instance

    def _initialize(self, config_path):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")

        try:
            with open(config_path, 'r') as file:
                self._settings = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")

    def __getattr__(self, name):
        """
        Allows accessing settings like attributes (e.g., config.database.host).
        """
        if name in self._settings:
            value = self._settings[name]
            if isinstance(value, dict):
                # Recursively wrap nested dictionaries
                return _DictWrapper(value)
            return value

        # Fallback to the default __getattr__ behavior
        return super().__getattr__(name)

    def get(self, key, default=None):
        """
        Provides a safe way to get a value with an optional default,
        similar to dictionary's .get() method.
        """
        keys = key.split('.')
        current_dict = self._settings
        for k in keys:
            if isinstance(current_dict, dict) and k in current_dict:
                current_dict = current_dict[k]
            else:
                return default
        return current_dict

    def get_int(self, key, default=0):
        """
        Provides a safe way to get a value with an optional default,
        similar to dictionary's .get() method.
        """
        keys = key.split('.')
        current_dict = self._settings
        for k in keys:
            if isinstance(current_dict, dict) and k in current_dict:
                current_dict = current_dict[k]
            else:
                return default
        return current_dict

    def get_bool(self, key, default=False):
        """
        Provides a safe way to get a value with an optional default,
        similar to dictionary's .get() method.
        """
        keys = key.split('.')
        current_dict = self._settings
        for k in keys:
            if isinstance(current_dict, dict) and k in current_dict:
                current_dict = current_dict[k]
            else:
                return default
        if isinstance(current_dict, str):
            normalized = current_dict.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", ""}:
                return False
            return default
        return bool(current_dict)


class _DictWrapper:
    """
    Helper class to enable attribute-style access for nested dictionaries.
    """
    def __init__(self, data):
        self._data = data

    def __getattr__(self, name):
        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return _DictWrapper(value)
            return value
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

# Example Usage:
if __name__ == "__main__":
    # Create a dummy config.yaml file for the example
    sample_config_content = """
    tvdb:
      apikey: "YOUR_TVDB_API_KEY" # Enter TVDb API Key (REQUIRED)

    omdb:
      apikey: "YOUR_OMDB_API_KEY" # Enter OMDb API Key (Optional)
    """
    with open("config.yaml", "w") as f:
        f.write(sample_config_content)

    try:
        config = Config()

        print("--- Attribute Access ---")
        print(f"tvdb key: {config.tvdb.apikey}")
        print(f"omdb key: {config.omdb.apikey}")

        print("\n--- 'get' Method Access ---")
        print(f"tvdb key: {config.get('tvdb.apikey')}")
        print(f"Default Value Test: {config.get('omdb.sproing', 'default_value')}")

    except (FileNotFoundError, ValueError) as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up the dummy file
        if os.path.exists("config.yaml"):
            os.remove("config.yaml")