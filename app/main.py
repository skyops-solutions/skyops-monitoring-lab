import time
import random

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="SkyOps Monitoring Lab", version="1.0.0")

Instrumentator().instrument(app).expose(app)


@app.get("/")
def root():
    return {"app": "skyops-monitoring-lab", "status": "running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/api/items")
def list_items():
    return {"items": [{"id": i, "name": f"item-{i}"} for i in range(1, 6)]}


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    if item_id < 1 or item_id > 100:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, "name": f"item-{item_id}"}


@app.get("/api/slow")
def slow_endpoint():
    time.sleep(random.uniform(0.1, 0.5))
    return {"message": "slow response simulated"}
