import logging.config
import os
import yaml

from .utils.crew_io_utils import CrewInputOutputUtils


# Set up logging configuration
print("[INFO] Setting up logging configuration...")
config_file_path = CrewInputOutputUtils.find_folder_path('logging_config.yaml')
with open(config_file_path, 'rt') as f:
    config = yaml.safe_load(f.read())

# Configure the logging module with the config file.
logging.config.dictConfig(config)

# config_file_path = CrewInputOutputUtils.find_folder_path('logging_config.conf')
# logging.config.fileConfig(config_file_path)


def getLogger(name: str) -> logging.Logger:
    """
    Returns a logger with the specified name.
    
    :param name: The name of the logger.
    :return: A logging.Logger instance.
    """
    return logging.getLogger(name)
    
