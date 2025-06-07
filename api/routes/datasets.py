from fastapi import APIRouter, HTTPException
from base.models.dataset import Dataset
from datetime import datetime
from schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse

router = APIRouter()

@router.post("/", response_model=DatasetResponse)
async def create_dataset(dataset: DatasetCreate):
    """
    Create a new dataset. Required fields:
    - title: Dataset title
    - author: User ID of creator
    - column_labels: List of column names
    - is_public: Boolean for public access
    
    Optional fields:
    - description: Dataset description
    - legend: Dictionary mapping column names to user-friendly names
    - tags: List of keywords
    """

    try:
        # Auto-generate dataset_id
        latest_dataset = Dataset.objects.order_by('-dataset_id').first()
        new_dataset_id = (latest_dataset.dataset_id + 1) if latest_dataset else 1
        
        dataset_dict = dataset.dict()
        dataset_dict['dataset_id'] = new_dataset_id
        dataset_dict['date_created'] = datetime.now()
        
        new_dataset = Dataset(**dataset_dict)
        new_dataset.save()
        return DatasetResponse.model_validate(new_dataset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: int):
    """Get dataset by ID"""

    dataset = Dataset.objects(dataset_id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse.model_validate(dataset)


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(dataset_id: int, dataset: DatasetUpdate):
    """
    Update dataset fields. All fields are optional:
    - title: New title
    - description: New description
    - legend: Updated column mappings
    - tags: Updated tags
    - is_public: Change visibility
    """

    existing = Dataset.objects(dataset_id=dataset_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    update_data = dataset.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)
    existing.save()
    return DatasetResponse.model_validate(existing)


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int):
    """Delete dataset and all associated data"""
    
    dataset = Dataset.objects(dataset_id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset.delete()
    return {"message": "Dataset deleted"}
