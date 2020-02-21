"""Common utilities"""

def error(message):
    """Raise a ValueError with an help message appended to the original message."""
    raise ValueError(f"{message}\n\nUse -h to show the help message")
