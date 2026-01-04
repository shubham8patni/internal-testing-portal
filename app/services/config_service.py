"""Config Service

Provides product configuration data from config/products.json.
Supports category, product, and plan hierarchy as defined in PRD.
"""

from typing import Dict, Any, List, Optional
import logging

from app.core.product_config import ProductConfigLoader

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for accessing product configuration."""

    def __init__(self):
        self.product_loader = ProductConfigLoader()
        self._load_config = self.product_loader.load_config

    def get_all_categories(self) -> List[str]:
        """
        Get all available categories.

        Returns:
            List of category IDs (MV4, MV2, PET, PA, TRAVEL)
        """
        try:
            hierarchy = self._load_config()
            categories_list = list(hierarchy.keys())
            logger.debug(f"Retrieved categories: {categories_list}")
            return categories_list
        except Exception as e:
            logger.error(f"Failed to get categories: {e}", exc_info=True)
            raise

    def get_products_for_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all products for a specific category.

        Args:
            category: Category ID (e.g., "MV4", "TRAVEL")

        Returns:
            List of product dictionaries with product_id and product_name

        Raises:
            ValueError: If category doesn't exist
        """
        try:
            hierarchy = self._load_config()

            if category not in hierarchy:
                logger.warning(f"Category not found: {category}")
                raise ValueError(f"Category not found: {category}")

            products = hierarchy.get(category, {}).get("products", {})
            product_list = [
                {"product_id": prod_id, **prod_data}
                for prod_id, prod_data in products.items()
            ]

            logger.debug(f"Retrieved products for {category}: {len(product_list)} products")
            return product_list

        except Exception as e:
            logger.error(f"Failed to get products for {category}: {e}", exc_info=True)
            raise

    def get_plans_for_product(
        self,
        category: str,
        product_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all plans for a specific product.

        Args:
            category: Category ID (e.g., "MV4")
            product_id: Product ID (e.g., "TOKIO_MARINE")

        Returns:
            List of plan dictionaries with plan_id and plan_name

        Raises:
            ValueError: If category or product doesn't exist
        """
        try:
            hierarchy = self._load_config()

            if category not in hierarchy:
                raise ValueError(f"Category not found: {category}")

            products = hierarchy.get(category, {}).get("products", {})

            if product_id not in products:
                raise ValueError(f"Product not found: {product_id} in category {category}")

            plans_data = products.get(product_id, {}).get("plans", [])

            plan_list = []
            if isinstance(plans_data, list):
                plan_list = [
                    {"plan_id": plan_id, "name": plan_id}
                    for plan_id in plans_data
                ]
            else:
                plan_list = [
                    {"plan_id": plan_id, **plan_data}
                    for plan_id, plan_data in plans_data.items()
                ]

            logger.debug(
                f"Retrieved plans for {category}/{product_id}: "
                f"{len(plan_list)} plans"
            )
            return plan_list

        except Exception as e:
            logger.error(
                f"Failed to get plans for {category}/{product_id}: {e}",
                exc_info=True
            )
            raise

    def get_full_hierarchy(self) -> Dict[str, Any]:
        """
        Get complete product hierarchy.

        Returns:
            Full configuration dictionary with categories, products, and plans
        """
        try:
            hierarchy = self._load_config()
            logger.debug("Retrieved full product hierarchy")
            return hierarchy
        except Exception as e:
            logger.error(f"Failed to get full hierarchy: {e}", exc_info=True)
            raise

    def get_all_combinations(self, categories: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Get all Category+Product+Plan combinations.

        Args:
            categories: Optional list of categories to filter. If None, returns all.

        Returns:
            List of combination dictionaries with category, product_id, plan_id
        """
        try:
            hierarchy = self._load_config()
            combinations = []

            categories_to_process = (
                categories if categories else list(hierarchy.keys())
            )

            for category in categories_to_process:
                if category not in hierarchy:
                    logger.warning(f"Skipping invalid category: {category}")
                    continue

                products = hierarchy.get(category, {}).get("products", {})

            for product_id, product_data in products.items():
                plans = product_data.get("plans", [])

                for plan_id in plans if isinstance(plans, list) else plans.keys():
                    combinations.append({
                        "category": category,
                        "product_id": product_id,
                        "plan_id": plan_id
                    })

            logger.info(f"Generated {len(combinations)} combinations for {len(categories_to_process)} categories")
            return combinations

        except Exception as e:
            logger.error(f"Failed to get combinations: {e}", exc_info=True)
            raise
