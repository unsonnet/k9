from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from models.common import (
    Currency,
    Dimension,
    Format,
    Image,
    Name,
    Product,
    ProductSummary,
    Profile,
    Report,
    ReportSummary,
    Vendor,
)


# Auth
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    user: UUID
    accessToken: str
    refreshToken: str
    expiresIn: int


class RefreshRequest(BaseModel):
    refreshToken: str


class ForgotRequest(BaseModel):
    email: str


class ResetRequest(BaseModel):
    user: UUID
    session: str
    newPassword: str


# User
class CreateUserRequest(BaseModel):
    username: str
    email: str
    role: str
    preferences: Optional[Dict[str, str]] = None


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    preferences: Optional[Dict[str, Optional[str]]] = None


class PasswordUpdateRequest(BaseModel):
    currentPassword: str
    newPassword: str


# Product
class CreateProductRequest(BaseModel):
    name: Name
    category: Dict[str, str]


class UpdateProductRequest(BaseModel):
    name: Optional[Name] = None
    category: Optional[Dict[str, Optional[str]]] = None


class CreateFormatRequest(BaseModel):
    aspect: str
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    thickness: Optional[Dimension] = None


class UpdateFormatRequest(BaseModel):
    aspect: Optional[str] = None
    length: Optional[Optional[Dimension]] = None
    width: Optional[Optional[Dimension]] = None
    thickness: Optional[Optional[Dimension]] = None


class CreateVendorRequest(BaseModel):
    sku: str
    store: str
    name: str
    price: Optional[Currency] = None
    discontinued: Optional[bool] = None
    url: Optional[str] = None


class UpdateVendorRequest(BaseModel):
    sku: Optional[str] = None
    store: Optional[str] = None
    name: Optional[str] = None
    price: Optional[Optional[Currency]] = None
    discontinued: Optional[Optional[bool]] = None
    url: Optional[Optional[str]] = None


# Search
class DimensionRange(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    unit: str


class CurrencyRange(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    unit: str


class SearchNameFilter(BaseModel):
    brand: Optional[str] = None
    series: Optional[str] = None
    model: Optional[str] = None


class SearchFormatFilter(BaseModel):
    aspect: Optional[str] = None
    length: Optional[DimensionRange] = None
    width: Optional[DimensionRange] = None
    thickness: Optional[DimensionRange] = None


class SearchVendorFilter(BaseModel):
    sku: Optional[str] = None
    store: Optional[List[str]] = None
    name: Optional[str] = None
    price: Optional[CurrencyRange] = None
    discontinued: Optional[bool] = None


class SearchRequest(BaseModel):
    name: Optional[SearchNameFilter] = None
    category: Optional[Dict[str, List[str]]] = None
    format: Optional[SearchFormatFilter] = None
    vendor: Optional[SearchVendorFilter] = None
    colors: Optional[List[str]] = None
    references: Optional[List[UUID]] = None


# Pagination wrappers
class PageReportsResponse(BaseModel):
    total: int
    nextToken: Optional[str] = None
    reports: List[ReportSummary]


class PageUsersResponse(BaseModel):
    total: int
    nextToken: Optional[str] = None
    users: List[Profile]


class PageSearchResponse(BaseModel):
    total: int
    nextToken: Optional[str] = None
    results: List[ProductSummary]
