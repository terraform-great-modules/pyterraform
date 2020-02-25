"""Logging setup"""
import os
import logging
import colorlog


# pylint: disable=invalid-name
LOG_FORMAT = "{log_color}{levelname: <7}{reset} {purple}{name}{reset}: {bold}{message}{reset}"
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(LOG_FORMAT, style='{'))
logger = colorlog.getLogger('tfwrapper')
logger.addHandler(handler)
logger.setLevel(logging.INFO)



def set_root_logger(log_to_file=None, log_to_stream=None):
    """Set root logger for more verbose analisys"""
    rootlog = logging.getLogger()
    handlers = getattr(rootlog, 'handlers', list())
    formatter = logging.Formatter(
        fmt=set_root_logger.message_format,
        datefmt=set_root_logger.date_format)
    if log_to_file:
        import logging.handlers as handlers_  # pylint: disable=import-outside-toplevel
        file_ = handlers_.RotatingFileHandler(log_to_file, backupCount=10, maxBytes=20*2**100)
        file_.doRollover()
        handlers.append(file_)
    if log_to_stream:  # like sys.stdout
        handlers.append(logging.StreamHandler(log_to_stream))
    for _handler in handlers:
        _handler.setFormatter(formatter)

set_root_logger.message_format = (
    '%(asctime)s.%(msecs)03d %(process)d-%(thread)d %(name)-8s:'
    '[%(levelname)6s]:[%(filename)s:%(lineno)d]: %(message)s')
set_root_logger.date_format = '%Y-%m-%d %H:%M:%S'

# Logger Factory
def get_logger(logger_name=None, level=None):
    """Generate a logger.

    Usage:
    >>> logger = get_logger()
    >>> logger = get_logger(__name__, "DEBUG")

    parameters
    ----------
    :param str logger_name: the name of the logger, if none the root logger will be used
    :param str level: the logger level, if not set it will be user DEBUG or INFO according to the
        DEBUG_MODE environment variable
    :return logging:
    """
    # Get the requested logger
    logger_ = logging.getLogger(logger_name)

    # Set the logger level
    level = getattr(logging, os.environ.get('LOG_LEVEL', 'NOTDEF'),
                    logging.INFO if not level else getattr(logging, level, logging.INFO))
    logger_.setLevel(level)

    return logger_

if os.environ.get("VERBOSE_AWS"):
    # pylint: disable=invalid-name,missing-docstring,too-few-public-methods
    class OnlySessionInfos(logging.Filter):
        def filter(self, record):
            msg = record.getMessage()
            return msg.startswith("Response body") or msg.startswith("Making request for")

    boto_parser = logging.getLogger("botocore.parsers")
    boto_endpoint = logging.getLogger("botocore.endpoint")
    boto_parser.setLevel(logging.DEBUG)
    boto_endpoint.setLevel(logging.DEBUG)
    boto_parser.addFilter(OnlySessionInfos())
    boto_endpoint.addFilter(OnlySessionInfos())
