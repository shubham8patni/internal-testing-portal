"""Product Configuration Loader"""

import json
from pathlib import Path
from typing import Dict, Any
from app.core.logging import logger


class ProductConfigLoader:
    """Loader for product hierarchy configuration."""

    def __init__(self):
        self.config_path = "config/products.json"

    def load_config(self) -> Dict[str, Any]:
        """
        Load product hierarchy configuration from JSON file.

        Returns:
            Configuration dictionary (unwrapped from "categories" key)
        """
        try:
            full_path = Path(self.config_path)
            if not full_path.exists():
                logger.warning(
                    f"Product config file not found: {self.config_path}, "
                    f"using empty config"
                )
                return {}

            with open(full_path, 'r') as f:
                config = json.load(f)

            if "categories" in config:
                config = config["categories"]

            logger.info(f"Loaded product configuration from {self.config_path}")
            return config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in product config: {e}")
            return {}

        except Exception as e:
            logger.error(f"Error loading product config: {e}")
            return {}

    def get_categories(self) -> list[str]:
        """
        Get all category IDs.

        Returns:
            List of category IDs
        """
        config = self.load_config()
        return list(config.keys())

    def get_products(self, category: str) -> Dict[str, Any]:
        """
        Get products for a category.

        Args:
            category: Category ID

        Returns:
            Products dictionary or empty dict
        """
        config = self.load_config()
        return config.get(category, {}).get("products", {})

    def get_plans(
        self,
        category: str,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Get plans for a product.

        Args:
            category: Category ID
            product_id: Product ID

        Returns:
            Plans dictionary or empty dict
        """
        products = self.get_products(category)
        return products.get(product_id, {}).get("plans", {})
