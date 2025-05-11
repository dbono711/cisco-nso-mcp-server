import logging
import os
from typing import Dict

class LoggerFactory:
    """
    Factory class for creating and configuring loggers.
    
    This class provides a centralized way to create and manage loggers
    with consistent formatting and behavior across the application.
    
    Logs will be sent to stdout by default, and optionally to a file if
    the LOG_FILE environment variable is set.
    """

    # dictionary to store created loggers
    _loggers: Dict[str, logging.Logger] = {}
    
    # standard log format
    _LOG_FORMAT = "%(asctime)s:%(levelname)s:%(message)s"
    _DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # map string log levels to logging constants
    _LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    @classmethod
    def __create_logger(cls, name: str, log_level: str) -> logging.Logger:
        """
        Create and configure a logger with the specified name and level.
        
        Args:
            name: The name for the logger
            log_level: The logging level (DEBUG, INFO, ERROR, etc.)
            
        Returns:
            A configured logger instance
        """
        # check if we've already created this logger
        if name in cls._loggers:
            return cls._loggers[name]

        # initialize a new logger
        logger = logging.getLogger(name)
        
        # only configure if not already configured
        if not logger.handlers:
            formatter = logging.Formatter(cls._LOG_FORMAT, datefmt=cls._DATE_FORMAT)
            
            # always add console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # add file handler only if LOG_FILE environment variable is set
            log_file_path = os.environ.get("LOG_FILE")
            if log_file_path:
                try:
                    file_handler = logging.FileHandler(log_file_path)
                    file_handler.setFormatter(formatter)
                    logger.addHandler(file_handler)
                except Exception as e:
                    console_handler.setLevel(logging.DEBUG)
                    logger.error(f"Failed to create file handler: {str(e)}")

            # set the logging level
            level = cls._LOG_LEVELS.get(log_level.upper(), logging.INFO)
            logger.setLevel(level)
                
            # store in our dictionary
            cls._loggers[name] = logger
            
        return logger

    @classmethod
    def get_logger(cls, name: str, log_level: str = "INFO") -> logging.Logger:
        """
        Get a configured logger with the specified name and level.
        
        Args:
            name: The name for the logger
            log_level: The logging level (default: INFO)
            
        Returns:
            A configured logger instance
        """
        return cls.__create_logger(name, log_level)

# create a default logger for simple imports
default_logger = LoggerFactory.get_logger("server", "INFO")

# log where logs are being sent
log_file_path = os.environ.get("LOG_FILE")
if log_file_path:
    default_logger.info(f"Logging to file: {log_file_path}")
else:
    default_logger.info("Logging to stdout only (no LOG_FILE environment variable set)")