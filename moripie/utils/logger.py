import logging


logging.basicConfig(level = logging.INFO, format = "[%(name)s][%(asctime)s][%(levelname)s]: %(message)s", datefmt = "%H:%M:%S")
Logger: logging.Logger = logging.getLogger("moripie")
