import os

import yaml

# Config() with no path returns the instance already loaded by Config("../config.yaml").
_UNSET_PATH = object()


class Config:
    """Settings loaded from one YAML file.

    The first call that names a file loads it. A later call with no path
    returns that same instance. A later call with a different file reloads.
    """

    _instance = None

    def __new__(cls, config_path=_UNSET_PATH):
        if cls._instance is not None and config_path is _UNSET_PATH:
            return cls._instance

        path = "config.yaml" if config_path is _UNSET_PATH else config_path
        resolved = os.path.abspath(path)
        if cls._instance is not None and cls._instance._config_path == resolved:
            return cls._instance

        instance = super().__new__(cls)
        instance._initialize(path, resolved)
        cls._instance = instance
        return cls._instance

    def _initialize(self, config_path, resolved):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")

        try:
            with open(config_path, "r") as file:
                loaded = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            raise ValueError(f"Error parsing YAML file: {exc}") from exc

        self._config_path = resolved
        self._settings = loaded if isinstance(loaded, dict) else {}

    def __getattr__(self, name):
        """Attribute access for a top-level setting, such as config.plex_api."""
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
        if name in self._settings:
            value = self._settings[name]
            if isinstance(value, dict):
                return _DictWrapper(value)
            return value
        raise AttributeError(f"Config has no setting '{name}'")

    def _lookup(self, key, default):
        current = self._settings
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def get(self, key, default=None):
        """Return a dotted setting, or default when it is missing."""
        return self._lookup(key, default)

    def get_int(self, key, default=0):
        """Return a dotted setting as an int, or default when it is missing or not numeric."""
        value = self._lookup(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def get_bool(self, key, default=False):
        """Return a dotted setting as a bool.

        Strings accept 1/true/yes/y/on and 0/false/no/n/off. This replaces
        the old booler() helper, which evaluated the string as Python.
        """
        value = self._lookup(key, default)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off", ""}:
                return False
            return default
        return bool(value)


class _DictWrapper:
    """Attribute access for a nested mapping."""

    def __init__(self, data):
        self._data = data

    def __getattr__(self, name):
        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return _DictWrapper(value)
            return value
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
