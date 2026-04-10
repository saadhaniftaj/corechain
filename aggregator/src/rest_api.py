"""
REST API for Dashboard
Provides training metrics, blockchain data, and auth endpoints
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from loguru import logger
import uvicorn
import os

from blockchain_client import BlockchainClient
from auth import create_token, get_current_user, require_role
from user_store import seed_default_users, authenticate, create_user, list_users, get_user, delete_user


# --- Pydantic models ---
class LoginRequest(BaseModel):
    user_id: str
    password: str

class CreateUserRequest(BaseModel):
    user_id: str
    password: str
    role: str
    name: str

# Initialize FastAPI
app = FastAPI(
    title="CoreChain Aggregator API",
    description="REST API for CoreChain dashboard",
    version="1.0.0"
)

@app.on_event('startup')
async def startup():
    seed_default_users()
    logger.info('CoreChain API started, default users seeded')

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize blockchain client
blockchain_url = os.getenv('BLOCKCHAIN_URL', 'http://localhost:7050')
blockchain_client = BlockchainClient(blockchain_url)

# Global state (will be updated by gRPC server)
training_state = {
    'current_round': 0,
    'total_rounds': int(os.getenv('FL_ROUNDS', 10)),
    'global_accuracy': 0.0,
    'global_loss': 0.0,
    'is_training': False,
    'connected_hospitals': 0,
    'accuracy_history': [],
    'loss_history': []
}

registered_hospitals = {}


@app.get("/")
async def root():
    return {"name": "CoreChain Aggregator API", "version": "1.0.0", "status": "running"}


# --- AUTH ROUTES ---
@app.post("/auth/login")
async def login(req: LoginRequest):
    """Login and receive JWT token"""
    user = authenticate(req.user_id, req.password)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_token(user['user_id'], user['role'])
    return {'token': token, 'user': user, 'expires_in': 86400}


@app.get("/auth/me")
async def me(current_user=Depends(get_current_user)):
    """Get current user info"""
    return current_user


@app.get("/auth/users")
async def get_users(current_user=Depends(require_role('admin'))):
    """List all users (admin only)"""
    return {'users': list_users()}


@app.post("/auth/users")
async def add_user(req: CreateUserRequest, current_user=Depends(require_role('admin'))):
    """Create a new user (admin only)"""
    try:
        user = create_user(req.user_id, req.password, req.role, req.name)
        return {'success': True, 'user': user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/auth/users/{user_id}")
async def remove_user(user_id: str, current_user=Depends(require_role('admin'))):
    """Delete a user (admin only)"""
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail='User not found')
    return {'success': True}


# Alias /api/status -> /api/training/status for dashboard compatibility
@app.get("/api/status")
async def get_status():
    """Alias for training status"""
    return {
        "current_round": training_state['current_round'],
        "total_rounds": training_state['total_rounds'],
        "global_accuracy": training_state['global_accuracy'],
        "global_loss": training_state['global_loss'],
        "is_training": training_state['is_training'],
        "connected_hospitals": len(registered_hospitals),
        "total_hospitals": len(registered_hospitals),
        "progress_percentage": (training_state['current_round'] / training_state['total_rounds']) * 100 if training_state['total_rounds'] > 0 else 0
    }


@app.get("/api/training/status")
async def get_training_status():
    """Get current training status"""
    return {
        "current_round": training_state['current_round'],
        "total_rounds": training_state['total_rounds'],
        "global_accuracy": training_state['global_accuracy'],
        "global_loss": training_state['global_loss'],
        "is_training": training_state['is_training'],
        "connected_hospitals": len(registered_hospitals),
        "progress_percentage": (training_state['current_round'] / training_state['total_rounds']) * 100
    }


@app.get("/api/hospitals")
async def get_hospitals():
    """Get list of registered hospitals"""
    return {
        "hospitals": list(registered_hospitals.values()),
        "count": len(registered_hospitals)
    }


@app.get("/api/hospitals/{hospital_id}")
async def get_hospital(hospital_id: str):
    """Get specific hospital details"""
    if hospital_id not in registered_hospitals:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    hospital = registered_hospitals[hospital_id]
    
    # Get rewards from blockchain
    rewards = blockchain_client.get_hospital_rewards(hospital_id)
    
    return {
        **hospital,
        "total_rewards": rewards
    }


@app.get("/api/metrics/history")
async def get_metrics_history():
    """Get historical accuracy and loss data"""
    return {
        "accuracy_history": training_state['accuracy_history'],
        "loss_history": training_state['loss_history'],
        "rounds": list(range(len(training_state['accuracy_history'])))
    }


@app.get("/api/blockchain/transactions")
async def get_recent_transactions(limit: int = 50):
    """Get recent blockchain transactions"""
    chain = blockchain_client.get_chain()
    
    # Extract all transactions
    transactions = []
    for block in chain:
        for tx in block.get('transactions', []):
            transactions.append({
                **tx,
                'block_index': block['index'],
                'block_hash': block['hash']
            })
    
    # Sort by timestamp (newest first)
    transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return {
        "transactions": transactions[:limit],
        "total": len(transactions)
    }


@app.get("/api/blockchain/chain")
async def get_blockchain():
    """Get the entire blockchain"""
    chain = blockchain_client.get_chain()
    
    return {
        "chain": chain,
        "length": len(chain)
    }


@app.get("/api/rewards")
async def get_rewards():
    """Get reward distribution for all hospitals"""
    leaderboard = blockchain_client.get_leaderboard()
    
    return {
        "leaderboard": leaderboard,
        "total_hospitals": len(leaderboard)
    }


@app.get("/api/rewards/{hospital_id}")
async def get_hospital_rewards(hospital_id: str):
    """Get rewards for specific hospital"""
    rewards = blockchain_client.get_hospital_rewards(hospital_id)
    
    return {
        "hospital_id": hospital_id,
        "total_rewards": rewards
    }


@app.get("/api/training/summary")
async def get_training_summary():
    """Get comprehensive training summary"""
    blockchain_summary = blockchain_client.get_training_summary()
    
    return {
        **blockchain_summary,
        "current_round": training_state['current_round'],
        "total_rounds": training_state['total_rounds'],
        "current_accuracy": training_state['global_accuracy'],
        "current_loss": training_state['global_loss'],
        "is_training": training_state['is_training']
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check blockchain connectivity
    blockchain_valid = blockchain_client.validate_chain()
    
    return {
        "status": "healthy",
        "blockchain_connected": blockchain_valid,
        "training_active": training_state['is_training']
    }


def start_api_server(port: int = 8000):
    """Start the REST API server"""
    logger.info(f"Starting REST API on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    port = int(os.getenv('REST_PORT', 8000))
    start_api_server(port)
