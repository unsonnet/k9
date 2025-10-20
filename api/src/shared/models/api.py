from typing import Any, List, Optional, Dict
from pydantic import Field

from src.shared.utils import current_timestamp
from .base import BaseSchema, BaseEntity, Quantity


class APIImage(BaseSchema):
    """API Image model for API responses"""

    # data
    src: str
    hom: str


class APIProduct(BaseEntity):
    """API Product model for API responses"""

    class APIName(BaseSchema):
        brand: Optional[str] = None
        series: Optional[str] = None
        model: Optional[str] = None

    class APICategory(BaseSchema):
        type: Optional[str] = None
        material: Optional[str] = None
        look: Optional[str] = None
        texture: Optional[str] = None
        finish: Optional[str] = None
        edge: Optional[str] = None

    class Format(BaseSchema):
        class Vendor(BaseEntity):
            # data
            store: str
            name: str
            price: Optional[Quantity] = None
            discontinued: Optional[bool] = None
            url: str

        length: Quantity
        width: Quantity
        depth: Optional[Quantity] = None
        vendors: Optional[List[Vendor]] = Field(None, min_length=1)

    # data
    name: APIName
    category: APICategory
    formats: List[Format] = Field(..., min_length=1)
    images: List[APIImage] = Field(..., min_length=1)


class APIReport(BaseEntity):
    """API Report model for API responses"""

    title: str
    date: str
    reference: APIProduct
    favorites: Optional[List[str]] = Field(None, min_length=1)


class DBUser(BaseEntity):
    """Database User model for DynamoDB storage"""

    # data
    name: str
    email: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    # timestamp
    created_at: str = Field(default_factory=current_timestamp)
    updated_at: Optional[str] = None
