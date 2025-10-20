from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from src.shared.utils import current_timestamp, generate_id


class BaseSchema(BaseModel):
    """Base schema class with common configuration"""

    model_config = ConfigDict(
        str_strip_whitespace=True, validate_assignment=True, extra="forbid"
    )


class BaseEntity(BaseSchema):
    """Base entity class with id generator"""

    id: str = Field(default_factory=generate_id)
    created_at: str = Field(default_factory=current_timestamp)
    updated_at: Optional[str] = None


class Quantity(BaseSchema):
    """Quantity type"""

    val: float
    unit: str
