from typing import Any, List, Optional, Dict
from pydantic import Field

from .base import BaseSchema, BaseEntity, Quantity


class DBImage(BaseEntity):
    """Database Image model for DynamoDB storage"""

    # partition
    product: str
    # data
    src: str
    hom: str


class DBProduct(BaseEntity):
    """Database Product model for DynamoDB storage"""

    class Name(BaseSchema):
        brand: Optional[str]
        series: Optional[str]
        model: Optional[str]

    class Category(BaseSchema):
        type: Optional[str]
        material: Optional[str]
        look: Optional[str]
        texture: Optional[str]

    class Format(BaseSchema):
        class Vendor(BaseEntity):
            store: str
            name: str
            price: Optional[Quantity]
            discontinued: Optional[bool]
            url: str

        length: Quantity
        width: Quantity
        thickness: Optional[Quantity]
        finish: Optional[str]
        edge: Optional[str]
        vendors: Optional[List[Vendor]] = Field(..., min_length=1)

    # data
    name: Name
    category: Category
    formats: List[Format] = Field(..., min_length=1)
    images: List[str] = Field(..., min_length=1)


class DBReport(BaseEntity):
    """Database Report model for DynamoDB storage"""

    # partition
    author: str
    # data
    title: str
    reference: str
    favorites: Optional[List[str]] = Field(None, min_length=1)


class DBUser(BaseEntity):
    """Database User model for DynamoDB storage"""

    # data
    name: str
    email: Optional[str]
    avatar: Optional[str]
    preferences: Dict[str, Any] = Field(default_factory=dict)
