"""Config API Routes

Endpoints:
- GET /api/config/categories - Get all categories
- GET /api/config/products/{category} - Get products for category
- GET /api/config/plans/{category}/{product} - Get plans for product
- GET /api/config/full - Get full product hierarchy
"""

from fastapi import APIRouter, HTTPException
import logging

from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])
config_service = ConfigService()


@router.get("/categories")
async def get_categories():
    """
    Get all available product categories.

    Returns:
        List of category IDs (MV4, MV2, PET, PA, TRAVEL)
    """
    try:
        categories = config_service.get_all_categories()
        logger.debug(f"Retrieved categories: {len(categories)}")
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Failed to get categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{category}")
async def get_products(category: str):
    """
    Get all products for a specific category.

    Args:
        category: Category ID (e.g., "MV4", "TRAVEL")

    Returns:
        List of products with product_id and product_name

    Raises:
        HTTPException: If category doesn't exist (404)
    """
    try:
        products = config_service.get_products_for_category(category)
        logger.debug(f"Retrieved products for {category}: {len(products)}")
        return {"category": category, "products": products}
    except ValueError as e:
        logger.warning(f"Category not found: {category}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get products for {category}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{category}/{product}")
async def get_plans(category: str, product: str):
    """
    Get all plans for a specific product.

    Args:
        category: Category ID (e.g., "MV4")
        product: Product ID (e.g., "TOKIO_MARINE")

    Returns:
        List of plans with plan_id and plan_name

    Raises:
        HTTPException: If category or product doesn't exist (404)
    """
    try:
        plans = config_service.get_plans_for_product(category, product)
        logger.debug(f"Retrieved plans for {category}/{product}: {len(plans)}")
        return {
            "category": category,
            "product_id": product,
            "plans": plans
        }
    except ValueError as e:
        logger.warning(f"Product not found: {category}/{product}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get plans for {category}/{product}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/full")
async def get_full_hierarchy():
    """
    Get complete product hierarchy.

    Returns:
        Full configuration with categories, products, and plans
    """
    try:
        hierarchy = config_service.get_full_hierarchy()
        logger.debug("Retrieved full product hierarchy")
        return hierarchy
    except Exception as e:
        logger.error(f"Failed to get full hierarchy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
