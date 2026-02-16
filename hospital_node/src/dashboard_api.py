"""
Hospital Node Dashboard API
Provides REST endpoints for the hospital dashboard
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
import json
from pathlib import Path
import threading
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hospital_node.src.data_loader import TBDataLoader
from hospital_node.src.tb_model import TBDetectionModel

# Configuration
DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"
DATA_DIR = Path(__file__).parent.parent / "data"  # Use local data directory
HISTORY_FILE = DATA_DIR / "history.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Hospital Node Dashboard API")

# Mount static files
app.mount("/static", StaticFiles(directory=DASHBOARD_DIR), name="static")


# Models
class TrainingConfig(BaseModel):
    dataset_path: str
    dataset_type: str


class RoundData(BaseModel):
    round_number: int
    timestamp: str
    accuracy: float
    loss: float
    tokens_earned: int
    status: str


# Global state
hospital_state = {
    "hospital_id": os.getenv("HOSPITAL_ID", "hospital_1"),
    "hospital_name": os.getenv("HOSPITAL_NAME", "FL Test Hospital"),
    "aggregator_connected": True,  # Connected via Flower
    "is_training": True,  # Currently in FL training
    "training_status": "Training in progress",
    "current_round": 2,
    "total_rounds": 10,
    "token_balance": 150,
}


def update_dashboard_state(**kwargs):
    """Update dashboard state from FL training process"""
    global hospital_state
    for key, value in kwargs.items():
        if key in hospital_state:
            hospital_state[key] = value


# Initialize with mock training history for display
def initialize_mock_history():
    """Initialize with recent training data"""
    mock_history = [
        {
            "round_number": 1,
            "timestamp": "2026-02-08 22:51:38",
            "accuracy": 0.7259,
            "loss": 0.5842,
            "tokens_earned": 50,
            "status": "completed"
        },
        {
            "round_number": 2,
            "timestamp": "2026-02-08 23:41:34",
            "accuracy": 0.7316,
            "loss": 0.5693,
            "tokens_earned": 50,
            "status": "completed"
        },
    ]
    
    if not HISTORY_FILE.exists():
        save_history(mock_history)


# Initialize mock data on startup
initialize_mock_history()



def load_history():
    """Load rounds history from file"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []


def save_history(history):
    """Save rounds history to file"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


# Routes
@app.get("/")
async def serve_dashboard():
    """Serve the dashboard HTML"""
    return FileResponse(DASHBOARD_DIR / "index.html")


@app.get("/api/status")
async def get_status():
    """Get current hospital status"""
    try:
        # TODO: Check actual aggregator connection
        # For now, return stored state
        return {
            "hospital_id": hospital_state["hospital_id"],
            "hospital_name": hospital_state["hospital_name"],
            "aggregator_connected": hospital_state["aggregator_connected"],
            "is_training": hospital_state["is_training"],
            "training_status": hospital_state["training_status"],
            "current_round": hospital_state["current_round"],
            "total_rounds": hospital_state["total_rounds"],
            "token_balance": hospital_state["token_balance"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rounds")
async def get_rounds():
    """Get rounds history"""
    try:
        history = load_history()
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/start")
async def start_training(config: TrainingConfig):
    """Start training with given configuration"""
    try:
        if hospital_state["is_training"]:
            return {"status": "error", "message": "Training already in progress"}
        
        # Start training in background thread
        training_thread = threading.Thread(
            target=run_training,
            args=(config.dataset_path, config.dataset_type),
            daemon=True
        )
        training_thread.start()
        
        hospital_state["is_training"] = True
        hospital_state["training_status"] = "Loading data..."
        
        return {"status": "success", "message": "Training started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/stop")
async def stop_training():
    """Stop current training"""
    try:
        # Note: Actual training stop would require more complex thread management
        # For now, just update state
        hospital_state["is_training"] = False
        hospital_state["training_status"] = "Stopped by user"
        
        return {"status": "success", "message": "Training stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_training(dataset_path: str, dataset_type: str):
    """Run actual training in background thread"""
    try:
        hospital_state["training_status"] = "Loading dataset..."
        
        # Load data
        data_loader = TBDataLoader(dataset_path=dataset_path, dataset_type=dataset_type)
        X_train, y_train, X_test, y_test = data_loader.load_data()
        
        hospital_state["training_status"] = f"Training on {len(X_train)} samples..."
        
        # Create and compile model
        model = TBDetectionModel()
        model.compile_model(learning_rate=0.001)
        
        # Train model
        history = model.train(X_train, y_train, X_test, y_test, epochs=3, batch_size=16)
        
        # Get final metrics
        final_acc = history['accuracy'][-1]
        final_loss = history['loss'][-1]
        val_acc = history.get('val_accuracy', [final_acc])[-1]
        val_loss = history.get('val_loss', [final_loss])[-1]
        
        hospital_state["training_status"] = f"Completed! Accuracy: {val_acc:.4f}"
        
        # Save to history
        history_data = load_history()
        new_round = {
            "round_number": len(history_data) + 1,
            "timestamp": datetime.now().isoformat(),
            "accuracy": float(val_acc),
            "loss": float(val_loss),
            "tokens_earned": 10,  # Example reward
            "status": "Completed",
            "dataset_type": dataset_type,
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }
        history_data.append(new_round)
        save_history(history_data)
        
        # Update state
        hospital_state["total_rounds"] = len(history_data)
        hospital_state["token_balance"] += 10
        
    except Exception as e:
        hospital_state["training_status"] = f"Error: {str(e)}"
        print(f"Training error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        hospital_state["is_training"] = False


@app.post("/api/training/approve/{round_id}")
async def approve_round(round_id: int):
    """Approve a training round for submission"""
    try:
        # TODO: Implement round approval logic
        history = load_history()
        
        # Find the round and update status
        for round_data in history:
            if round_data.get("round_number") == round_id:
                round_data["status"] = "Submitted"
                break
        
        save_history(history)
        
        return {"status": "success", "message": f"Round {round_id} approved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/reject/{round_id}")
async def reject_round(round_id: int):
    """Reject a training round"""
    try:
        history = load_history()
        
        # Find the round and update status
        for round_data in history:
            if round_data.get("round_number") == round_id:
                round_data["status"] = "Rejected"
                break
        
        save_history(history)
        
        return {"status": "success", "message": f"Round {round_id} rejected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def update_state(key: str, value):
    """Update hospital state"""
    hospital_state[key] = value


def add_round_to_history(round_data: dict):
    """Add a new round to history"""
    history = load_history()
    history.append(round_data)
    save_history(history)
    
    # Update stats
    hospital_state["total_rounds"] = len(history)
    hospital_state["token_balance"] = sum(r.get("tokens_earned", 0) for r in history)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
