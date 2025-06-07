from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from base.models.dataset import Dataset, DataRows
from schemas.rows import RowCreate, RowUpdate, RowResponse

router = APIRouter()

@router.post("/{dataset_id}/rows", response_model=List[RowResponse])
async def add_rows(
    dataset_id: int,
    rows: List[RowCreate],
    validate: bool = Query(True, description="Validate rows against dataset schema")
):
    """
    Add multiple rows to a dataset. Required for each row:
    - data: Dictionary of column values matching dataset's column_labels
    - location: LocationHierarchy object with at least country field
    - time: TimePoint object with at least year field
    """

    dataset = Dataset.objects(dataset_id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if validate:
        # Validate column names match dataset
        for row in rows:
            if not all(col in dataset.column_labels for col in row.data.keys()):
                raise HTTPException(status_code=400, detail="Invalid column names")
    
    try:
        inserted_rows = []
        for row in rows:
            row_dict = row.dict()
            row_dict['dataset_id'] = dataset_id
            new_row = DataRows(**row_dict)
            new_row.save()
            inserted_rows.append(RowResponse.model_validate(new_row))
        return inserted_rows
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/rows", response_model=List[RowResponse])
async def get_rows(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100,
    filters: Dict = Query(None)
):
    """
    Get rows from dataset with optional filtering:
    - spatial filters (country, state, etc.)
    - temporal filters (year, month, etc.)
    - data column filters
    """

    query = {'dataset_id': dataset_id}
    if filters:
        for key, value in filters.items():
            query[key] = value
    
    rows = DataRows.objects(**query).skip(skip).limit(limit)
    return [RowResponse.model_validate(row) for row in rows]


@router.put("/{dataset_id}/rows/{row_id}", response_model=RowResponse)
async def update_row(dataset_id: int, row_id: str, row: RowUpdate):
    """
    Update a single row. All fields are optional:
    - data: Updated column values
    - location: Updated location
    - time: Updated time
    """
    existing = DataRows.objects(id=row_id, dataset_id=dataset_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Row not found")
    
    update_data = row.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)
    
    existing.save()
    return RowResponse.model_validate(existing)

@router.delete("/{dataset_id}/rows")
async def delete_rows(dataset_id: int, row_ids: List[str] = Query(None)):
    """Delete multiple rows from a dataset"""
    query = {'dataset_id': dataset_id}
    if row_ids:
        query['id__in'] = row_ids
    
    result = DataRows.objects(**query).delete()
    return {"deleted_count": result}
