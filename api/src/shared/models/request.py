from typing import Any, List, Optional, Dict, Tuple, Union
from pydantic import Field

from .base import BaseSchema, BaseEntity, Quantity
from . import database


class Image(BaseSchema):
    """Request Image model from REST API"""

    class Affine(BaseSchema):
        shape: Dict[str, float]  # { width: number; height: number }
        position: Dict[str, float]  # { x: number; y: number; z: number }
        rotation: Dict[str, float]  # { x: number; y: number; z: number; w: number }

        def to_db(self) -> database.DBImage.Affine:
            return database.DBImage.Affine(
                shape=self.shape,
                position=self.position,
                rotation=self.rotation,
            )

    image: str
    mask: Optional[str] = None
    grid: Optional[Affine] = None

    def to_db(self, product: str) -> database.DBImage:
        return database.DBImage(
            image=self.image,
            mask=self.mask,
            grid=self.grid.to_db() if self.grid else None,
            product=product,
        )


class Product(BaseSchema):
    """Request Product model from REST API"""

    class Category(BaseSchema):
        type: Optional[str] = None
        material: Optional[str] = None
        look: Optional[str] = None
        texture: Optional[str] = None
        finish: Optional[str] = None
        edge: Optional[str] = None

        def to_db(self) -> database.DBProduct.Category:
            return database.DBProduct.Category(
                type=self.type,
                material=self.material,
                look=self.look,
                texture=self.texture,
                finish=self.finish,
                edge=self.edge,
            )

    class Format(BaseSchema):
        class Vendor(BaseSchema):
            sku: str
            store: str
            name: str
            price: Optional[Quantity] = None
            discontinued: Optional[bool] = None
            url: str

            def to_db(self) -> database.DBProduct.Format.Vendor:
                return database.DBProduct.Format.Vendor(
                    sku=self.sku,
                    store=self.store,
                    name=self.name,
                    price=self.price,
                    discontinued=self.discontinued,
                    url=self.url,
                )

        length: Optional[Quantity] = None
        width: Optional[Quantity] = None
        thickness: Optional[Quantity] = None
        vendors: Optional[List[Vendor]] = Field(None, min_length=1)

        def to_db(self) -> database.DBProduct.Format:
            return database.DBProduct.Format(
                length=self.length,
                width=self.width,
                thickness=self.thickness,
                vendors=(
                    [vendor.to_db() for vendor in self.vendors]
                    if self.vendors
                    else None
                ),
            )

    brand: Optional[str] = None
    series: Optional[str] = None
    model: str
    images: Optional[List[Image]] = Field(None, min_length=1)
    category: Optional[Category] = None
    formats: Optional[List[Format]] = Field(None, min_length=1)

    def to_db(self) -> Tuple[database.DBProduct, List[database.DBImage]]:
        images = [img.to_db(product="") for img in self.images]
        product = database.DBProduct(
            brand=self.brand,
            series=self.series,
            model=self.model,
            images=[img.image for img in self.images],
            category=(
                self.category.to_db()
                if self.category is not None
                else database.DBProduct.Category()
            ),
            formats=(
                [fmt.to_db() for fmt in self.formats]
                if self.formats is not None
                else [database.DBProduct.Format()]
            ),
        )
        for img in images:
            img.product = product.id

        return product, images


class Report(BaseSchema):
    """Request Report model from REST API"""

    title: str
    reference: Product
    favorites: Optional[List[str]] = Field(None, min_length=1)

    def to_db(
        self, author: str
    ) -> Tuple[database.DBReport, database.DBProduct, List[database.DBImage]]:
        reference, images = self.reference.to_db()

        return (
            database.DBReport(
                title=self.title,
                author=author,
                reference=reference.id,
                favorites=self.favorites,
            ),
            reference,
            images,
        )


class User(BaseSchema):
    """Request User model from REST API"""

    id: str
    username: Optional[str] = None
    email: Optional[str] = None
    name: str

    def to_db(self) -> database.DBUser:
        return database.DBUser(
            id=self.id,  # Override the default factory with the provided id
            name=self.name,
            email=self.email,
            avatar=None,  # Not provided in request model
            preferences={},  # Use default empty dict
            # created_at has default factory in database model
        )


class ReportList(BaseSchema):
    """Request Report List model from REST API"""

    reports: List[Report]
    total: int
    limit: int
    next_cursor: Optional[Dict[str, Any]] = None
    has_more: bool

    def to_db(self, author: str) -> List[database.DBReport]:
        """Convert list of request reports to database reports"""
        # Note: This assumes reference IDs are available or need to be generated
        # In practice, you might need additional logic to handle the Product references
        return [
            report.to_db(author=author)  # reference_id would need to be provided
            for report in self.reports
        ]
