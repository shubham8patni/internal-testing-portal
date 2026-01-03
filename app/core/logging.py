"""Centralized Logging Configuration"""

import logging
import sys


def setup_logging(app_name: str = "InternalTestingPortal"):
    """Setup and configure application logging"""
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()
