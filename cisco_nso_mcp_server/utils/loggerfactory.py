import logging

class LoggerFactory:
    """
    Factory class for creating and configuring loggers.
    """

    # Dictionary to store created loggers
    _loggers = {}

    @staticmethod
    def __create_logger(log_file: str, log_level: str) -> logging.Logger:
        """
        A private method that interacts with the python
        logging module to create a configured logger.
        """
        # Check if we've already created this logger
        if log_file in LoggerFactory._loggers:
            return LoggerFactory._loggers[log_file]

        # set the logging format
        log_format = "%(asctime)s:%(levelname)s:%(message)s"

        # Initialize a new logger
        logger = logging.getLogger(log_file)
        
        # Only configure if not already configured
        if not logger.handlers:
            # Configure file handler
            file_handler = logging.FileHandler(f"{log_file}.log")
            formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # set the logging level based on the user selection
            if log_level == "INFO":
                logger.setLevel(logging.INFO)
            elif log_level == "ERROR":
                logger.setLevel(logging.ERROR)
            elif log_level == "DEBUG":
                logger.setLevel(logging.DEBUG)
                
            # Store in our dictionary
            LoggerFactory._loggers[log_file] = logger
            
        return logger

    @staticmethod
    def get_logger(log_file: str, log_level: str = "INFO") -> logging.Logger:
        """
        A static method called by other modules to initialize logger in
        their own module.
        """
        return LoggerFactory.__create_logger(log_file, log_level)

# Create a default logger for simple imports
default_logger = LoggerFactory.get_logger("server", "INFO")