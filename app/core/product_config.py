"""Product Configuration Loader"""

import json
from pathlib import Path
from typing import Dict, Any
from app.core.logging import logger


def load_product_config(config_path: str = "config/products.json") -> Dict[str, Any]:
    """Load product hierarchy configuration from JSON file"""
    try:
        full_path = Path(config_path)
        if not full_path.exists():
            logger.warning(f"Product config file not found: {config_path}, using empty config")
            return {"categories": {}}
        
        with open(full_path, 'r') as f:
            config = json.load(f)
        
        logger.info(f"Loaded product configuration from {config_path}")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in product config: {e}")
        return {"categories": {}}
    except Exception as e:
        logger.error(f"Error loading product config: {e}")
        return {"categories": {}}


product_config = load_product_config()
