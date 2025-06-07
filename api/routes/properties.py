from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from base.models.dataset import Dataset
from schemas.properties import PropertyUpdate

router = APIRouter()

@router.put("/{dataset_id}/properties", response_model=Dict[str, Any])
async def update_properties(dataset_id: int, properties: PropertyUpdate):
    """
    Update dataset properties. Optional fields:
    - is_public: Change visibility
    - column_labels: Update column definitions
    - description: Update description
    """

    dataset = Dataset.objects(dataset_id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    update_data = properties.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dataset, key, value)
    
    dataset.save()
    return update_data


@router.get("/{dataset_id}/properties")
async def get_properties(dataset_id: int):
    """Get dataset properties"""
    
    dataset = Dataset.objects(dataset_id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "is_public": dataset.is_public,
        "column_labels": dataset.column_labels,
        "description": dataset.description
    }
