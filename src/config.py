from datetime import datetime


class Config:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.year = datetime.now().year
            Config._initialized = True

    @classmethod
    def get_year(cls):
        """Get the year from the configuration."""
        if cls._instance is None:
            cls()
        return cls._instance.year