from pydantic import BaseModel
from typing import Optional, Dict, List


class MetadataUpdate(BaseModel):
    """
    Schema to update metadata fields in the dataset. Both fields are optional.
    - legend: Dictionary mapping column names to user-friendly names.
    - tags: List of tags (keywords) describing the dataset.
    """
    
    legend: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None

    class Config:
        orm_mode = True


class MetadataResponse(BaseModel):
    """
    Schema for the response when querying metadata for a dataset.
    - legend: The current column name mappings.
    - tags: The current tags (keywords) for the dataset.
    """

    legend: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None

    class Config:
        orm_mode = True
