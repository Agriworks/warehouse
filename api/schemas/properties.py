from pydantic import BaseModel
from typing import Optional, List


class PropertyUpdate(BaseModel):
    """
    Schema to update dataset properties. All fields are optional.
    - is_public: Boolean for visibility status.
    - column_labels: List of updated column definitions.
    - description: Updated description of the dataset.
    """
    
    is_public: Optional[bool] = None
    column_labels: Optional[List[str]] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True


class PropertyResponse(BaseModel):
    """
    Schema for the response when querying dataset properties.
    - is_public: The visibility status of the dataset.
    - column_labels: The current column definitions.
    - description: The current description of the dataset.
    """

    is_public: bool
    column_labels: List[str]
    description: Optional[str] = None

    class Config:
        orm_mode = True
