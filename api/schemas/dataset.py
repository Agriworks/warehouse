from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from base.models.location import LocationHierarchy, LocationSpan
from base.models.time import TimePoint, TimeSpan


class DatasetCreate(BaseModel):
    """
    Schema to create dataset in the database.
    """
    
    title: str
    author: str
    column_labels: List[str]
    is_public: bool
    description: Optional[str] = None
    legend: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    locations: Optional[List[LocationHierarchy]] = None
    location_span: Optional[LocationSpan] = None
    timepoints: Optional[List[TimePoint]] = None
    time_span: Optional[TimeSpan] = None

    class Config:
        orm_mode = True


class DatasetUpdate(BaseModel):
    """
    Schema to update dataset in the database.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    legend: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    locations: Optional[List[LocationHierarchy]] = None
    location_span: Optional[LocationSpan] = None
    timepoints: Optional[List[TimePoint]] = None
    time_span: Optional[TimeSpan] = None

    class Config:
        orm_mode = True


class DatasetResponse(BaseModel):
    dataset_id: int
    title: str
    author: str
    date_created: datetime
    upload_date: datetime
    description: Optional[str] = None
    legend: Optional[Dict[str, str]] = None
    column_labels: List[str]
    is_public: bool
    tags: Optional[List[str]] = None
    locations: Optional[List[LocationHierarchy]] = None
    location_span: Optional[LocationSpan] = None
    timepoints: Optional[List[TimePoint]] = None
    time_span: Optional[TimeSpan] = None

    class Config:
        orm_mode = True
