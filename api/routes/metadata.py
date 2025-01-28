from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from base.models.dataset import Dataset
from schemas.metadata import MetadataUpdate

router = APIRouter()

@router.put("/{dataset_id}/metadata", response_model=Dict[str, Any])
async def update_metadata(dataset_id: int, metadata: MetadataUpdate):
    """
    Update dataset metadata. Optional fields:
    - legend: Column name mappings
    - tags: Keywords
    """
    
    dataset = Dataset.objects(dataset_id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    update_data = metadata.dict(exclude_unset=True)
    
    # Update specific metadata fields
    if 'legend' in update_data:
        dataset.legend = update_data['legend']
    if 'tags' in update_data:
        dataset.tags = update_data['tags']
    
    dataset.save()
    return {
        "legend": dataset.legend,
        "tags": dataset.tags
    }

@router.get("/{dataset_id}/metadata")
async def get_metadata(dataset_id: int):
    """Get all metadata for a dataset"""
    dataset = Dataset.objects(dataset_id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "legend": dataset.legend,
        "tags": dataset.tags,
    }
