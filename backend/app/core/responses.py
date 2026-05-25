from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API Response wrapper. 
    Wrap your router response models in this for consistency.
    """
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None