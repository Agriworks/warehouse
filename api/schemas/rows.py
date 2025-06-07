from pydantic import BaseModel
from typing import Dict, Optional
from base.models.location import LocationHierarchy
from base.models.time import TimePoint


class RowCreate(BaseModel):
    """
    Schema for creating a new row. The required fields are:
    - data: Dictionary of column values (keys must match dataset's column labels)
    - location: LocationHierarchy object
    - time: TimePoint object
    """

    data: Dict[str]
    location: LocationHierarchy
    time: TimePoint

    class Config:
        orm_mode = True


class RowUpdate(BaseModel):
    """
    Schema for updating an existing row. All fields are optional:
    - data: Updated column values
    - location: Updated location
    - time: Updated time
    """

    data: Optional[Dict[str]] = None
    location: Optional[LocationHierarchy] = None
    time: Optional[TimePoint] = None

    class Config:
        orm_mode = True


class RowResponse(BaseModel):
    """
    Schema for returning a row's data. This schema will be used for the response.
    - data: The row's column data
    - location: The location data
    - time: The time data
    """

    id: str
    dataset_id: int
    data: Dict[str]
    location: LocationHierarchy
    time: TimePoint

    class Config:
        orm_mode = True
