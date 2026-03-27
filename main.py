# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from graph_engine import ApexGraphEngine

app = FastAPI(title="Apex Fraud Detection API")

# Initialize the engine once so it stays in memory
apex = ApexGraphEngine()

# Define the exact data contract your partner must follow
class Transaction(BaseModel):
    txn_id: str
    src: str
    dst: str
    amount: float
    device_id: str

@app.get("/")
def read_root():
    return {"status": "Apex Engine is Online"}

@app.post("/ingest")
def ingest_data(transactions: List[Transaction]):
    """Endpoint for your partner to stream data into the graph."""
    # Convert incoming API data to the dictionary format our engine expects
    txn_dicts = [txn.model_dump() for txn in transactions]
    apex.ingest_data(txn_dicts)
    
    return {"message": f"Successfully ingested {len(transactions)} transactions into the graph."}

@app.get("/analyze")
def run_analysis():
    """Endpoint to trigger the rules and get the JSON report."""
    report = apex.generate_risk_report()
    return report