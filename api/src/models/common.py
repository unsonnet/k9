from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Name(BaseModel):
    brand: Optional[str] = None
    series: Optional[str] = None
    model: Optional[str] = None


class Currency(BaseModel):
    value: int
    unit: str


class Dimension(BaseModel):
    value: int
    unit: str


class Vendor(BaseModel):
    id: UUID
    sku: str
    store: str
    name: str
    price: Optional[Currency] = None
    discontinued: Optional[bool] = None
    url: Optional[str] = None


class Format(BaseModel):
    id: UUID
    aspect: str
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    thickness: Optional[Dimension] = None
    vendors: List[Vendor] = Field(default_factory=list)

    @field_validator("aspect")
    @classmethod
    def validate_aspect(cls, v: str) -> str:
        # Expect like "600:300"
        if ":" not in v:
            raise ValueError("aspect must be 'length:width'")
        return v


class Image(BaseModel):
    id: UUID
    url: str


class Product(BaseModel):
    id: UUID
    name: Name
    category: Dict[str, str]
    formats: List[Format] = Field(default_factory=list)
    images: List[Image] = Field(default_factory=list)


class ProductSummary(BaseModel):
    id: UUID
    name: Name
    image: Image


class ReportSummary(BaseModel):
    id: UUID
    author: UUID
    title: str
    date: str
    reference: ProductSummary


class Report(BaseModel):
    id: UUID
    author: UUID
    title: str
    date: str
    reference: Product
    favorites: Optional[List[Product]] = None


class Profile(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    preferences: Dict[str, str]
