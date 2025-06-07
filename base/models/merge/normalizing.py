from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, date
import calendar
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
import requests


def get_mongo_client(uri: str = "mongodb://localhost:27017") -> MongoClient:
    """
    Returns a MongoClient instance.
    """
    return MongoClient(uri)


def get_collection(db_name: str, collection_name: str, uri: str = None):
    """
    Retrieves a MongoDB collection.
    """
    client = get_mongo_client(uri) if uri else get_mongo_client()
    return client[db_name][collection_name]


class MergeRequest(BaseModel):
    left_db: str = Field(..., description="Database name for left (daily) collection")
    left_collection: str = Field(..., description="Collection name for daily data")
    right_db: str = Field(
        ..., description="Database name for right (monthly) collection"
    )
    right_collection: str = Field(..., description="Collection name for monthly data")
    left_time_col: str = Field(
        ..., description="Field name for date in left collection"
    )
    right_time_col: str = Field(
        ..., description="Field name for month in right collection (YYYY-MM)"
    )
    target_resolution: Literal["daily", "monthly"] = Field(
        ..., description="Join resolution: 'daily' or 'monthly'"
    )
    aggregation: Optional[Literal["sum", "avg", "max", "min"]] = Field(
        None, description="Aggregation for down-sampling"
    )
    join_type: Literal["inner", "left", "right", "outer"] = Field(
        "inner", description="Join type"
    )


def extract_month(date_obj: date) -> str:
    return date_obj.strftime("%Y-%m")


def group_by_month(
    rows: List[Dict[str, Any]], date_col: str
) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        dt = row[date_col]
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt).date()
        ym = extract_month(dt)
        grouped.setdefault(ym, []).append(row)
    return grouped


def aggregate_monthly(
    grouped: Dict[str, List[Dict[str, Any]]], value_cols: List[str], agg: str
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for ym, items in grouped.items():
        agg_row: Dict[str, Any] = {}
        for col in value_cols:
            vals = [item.get(col, 0) for item in items]
            if agg == "sum":
                agg_row[f"{col}_sum"] = sum(vals)
            elif agg == "avg":
                agg_row[f"{col}_avg"] = sum(vals) / len(vals) if vals else None
            elif agg == "max":
                agg_row[f"{col}_max"] = max(vals)
            elif agg == "min":
                agg_row[f"{col}_min"] = min(vals)
        result[ym] = agg_row
    return result


def merge_monthly(
    A: List[Dict[str, Any]],
    B: List[Dict[str, Any]],
    date_col: str,
    month_col: str,
    agg: str,
    join_type: str,
) -> List[Dict[str, Any]]:
    # Group A by month
    grouped = group_by_month(A, date_col)
    # Determine numeric columns in A to aggregate
    if A:
        sample = A[0]
        numeric_cols = [
            k
            for k, v in sample.items()
            if isinstance(v, (int, float)) and k != date_col
        ]
    else:
        numeric_cols = []
    # Aggregate A
    monthly_A = aggregate_monthly(grouped, numeric_cols, agg)

    # Build key sets
    keys_A = set(monthly_A.keys())
    keys_B = set(row[month_col] for row in B)
    if join_type == "inner":
        keys = keys_A & keys_B
    elif join_type == "left":
        keys = keys_A
    elif join_type == "right":
        keys = keys_B
    else:  # outer
        keys = keys_A | keys_B

    # Create lookup for B
    B_lookup = {row[month_col]: row for row in B}

    # Merge
    result: List[Dict[str, Any]] = []
    for ym in sorted(keys):
        row: Dict[str, Any] = {month_col: ym}
        row.update(monthly_A.get(ym, {}))
        row.update(B_lookup.get(ym, {}))
        result.append(row)
    return result


def merge_daily(
    A: List[Dict[str, Any]],
    B: List[Dict[str, Any]],
    date_col: str,
    month_col: str,
    join_type: str,
) -> List[Dict[str, Any]]:
    # Create lookup for B
    B_lookup = {row[month_col]: row for row in B}
    result: List[Dict[str, Any]] = []
    used_dates = set()

    # Merge on existing days
    for a in A:
        dt = a[date_col]
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt).date()
        ym = extract_month(dt)
        b = B_lookup.get(ym)
        if b or join_type in ("left", "outer"):
            merged = {**a, **(b or {})}
            result.append(merged)
            used_dates.add(dt)

    # Handle right or outer joins: add missing days
    if join_type in ("right", "outer"):
        for ym, b in B_lookup.items():
            year, month = map(int, ym.split("-"))
            days = calendar.monthrange(year, month)[1]
            for d in range(1, days + 1):
                dt = date(year, month, d)
                if dt not in used_dates:
                    row = {date_col: dt, **b}
                    result.append(row)
    # Sort by date if daily
    return sorted(result, key=lambda r: r[date_col])


app = FastAPI(title="Time Series Merge API")


@app.post("/merge")
def merge_timeseries(req: MergeRequest):
    # Fetch data from MongoDB
    left_coll = get_collection(req.left_db, req.left_collection)
    right_coll = get_collection(req.right_db, req.right_collection)
    A = list(left_coll.find({}, {req.left_time_col: 1, "_id": 0, **{}}))
    B = list(right_coll.find({}, {req.right_time_col: 1, "_id": 0, **{}}))
    if req.target_resolution == "monthly":
        if not req.aggregation:
            raise HTTPException(
                status_code=400, detail="Aggregation is required for monthly resolution"
            )
        merged = merge_monthly(
            A,
            B,
            date_col=req.left_time_col,
            month_col=req.right_time_col,
            agg=req.aggregation,
            join_type=req.join_type,
        )
    else:
        merged = merge_daily(
            A,
            B,
            date_col=req.left_time_col,
            month_col=req.right_time_col,
            join_type=req.join_type,
        )
    return {"merged": merged}


if __name__ == "__main__":
    payload = {
        "left_db": "analytics",
        "left_collection": "daily_metrics",
        "right_db": "analytics",
        "right_collection": "monthly_targets",
        "left_time_col": "date",
        "right_time_col": "month",
        "target_resolution": "monthly",
        "aggregation": "sum",
        "join_type": "outer",
    }
    resp = requests.post("http://localhost:8000/merge", json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print("Merged rows:", len(data["merged"]))
        print(data["merged"][:5])  # print first 5 rows
    else:
        print("Error:", resp.status_code, resp.text)
