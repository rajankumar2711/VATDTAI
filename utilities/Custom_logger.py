import logging
from datetime import datetime
import os
from utilities.common_utilities import get_current_test_method_name



class LogGen:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogGen, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if LogGen._initialized:
            return
        LogGen._initialized = True

        test_name = get_current_test_method_name()
        self.logger = logging.getLogger("CatalystLogger")
        self.logger.setLevel(logging.DEBUG)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_file_path = os.path.abspath(__file__)
        base_directory = os.path.dirname(os.path.dirname(current_file_path))
        log_directory = os.path.join(base_directory, 'reports/logs')
        os.makedirs(log_directory, exist_ok=True)
        log_file = f'{log_directory}/{test_name}_{timestamp}.log'

        # Prevent duplicate handlers
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(log_file) for h in self.logger.handlers):
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # Console handler removed to prevent logs from being captured in pytest-html report

    def log_step(self, message, level='info', **kwargs):
        """
        Logs a message with the given level and additional information.
        :param message: The message to log.
        :param level: The logging level (e.g., 'info', 'warning', 'error').
        :param kwargs: Additional information to log.
        """
        extra_info = ' '.join([f'{key}={value}' for key, value in kwargs.items()])
        full_message = f'{message} {extra_info}'

        # Log the message with the appropriate level
        getattr(self.logger, level.lower(), self.logger.info)(full_message)
