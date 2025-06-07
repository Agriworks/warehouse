from fastapi import FastAPI
from api.routes import datasets, metadata, rows, properties

app = FastAPI(
    title="AgriBase API",
    version="0.0.1"
)

# Include routers
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(metadata.router, prefix="/api/v1/metadata", tags=["metadata"])
app.include_router(rows.router, prefix="/api/v1/rows", tags=["rows"])
app.include_router(properties.router, prefix="/api/v1/properties", tags=["properties"])

@app.get("/")
async def root():
    return {"message": "Welcome to AgriBase API"}
