"""Logging setup"""
import logging
import colorlog


# pylint: disable=invalid-name
LOG_FORMAT = "{log_color}{levelname: <7}{reset} {purple}{name}{reset}: {bold}{message}{reset}"
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(LOG_FORMAT, style='{'))
logger = colorlog.getLogger('tfwrapper')
logger.addHandler(handler)
logger.setLevel(logging.INFO)
