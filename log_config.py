import logging
import os
from datetime import datetime

def setup_logger(name, log_file):
    """Configura um logger com saída para arquivo e console"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Evita duplicação de handlers
    if not logger.handlers:
        # Handler para arquivo
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s - %(message)s')
        )
        logger.addHandler(console_handler)
    
    return logger
