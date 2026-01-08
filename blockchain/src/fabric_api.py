"""
Blockchain API Server (Fabric-compatible)
Provides REST API for blockchain interaction
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from loguru import logger
import uvicorn
import os

from blockchain_core import Blockchain
from smart_contracts import ModelUpdateValidator, RewardDistributor, AuditLogger


# Pydantic models
class Transaction(BaseModel):
    type: str
    data: Dict


class BlockchainStats(BaseModel):
    total_blocks: int
    total_transactions: int
    pending_transactions: int
    difficulty: int
    is_valid: bool
    transaction_types: Dict[str, int]
    latest_block_hash: str


# Initialize FastAPI
app = FastAPI(
    title="CoreChain Blockchain API",
    description="Fabric-compatible blockchain API for CoreChain",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize blockchain and contracts
difficulty = int(os.getenv('DIFFICULTY', 4))
blockchain = Blockchain(difficulty=difficulty)
validator = ModelUpdateValidator(blockchain)
reward_distributor = RewardDistributor(blockchain)
audit_logger = AuditLogger(blockchain)

# Persistence
BLOCKCHAIN_FILE = '/app/data/blockchain.json'


@app.on_event("startup")
async def startup_event():
    """Load blockchain from file on startup"""
    logger.info("Starting Blockchain API server...")
    
    # Create data directory if it doesn't exist
    os.makedirs('/app/data', exist_ok=True)
    
    # Load existing blockchain
    blockchain.load_from_file(BLOCKCHAIN_FILE)
    
    logger.success("Blockchain API server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Save blockchain to file on shutdown"""
    logger.info("Shutting down Blockchain API server...")
    blockchain.save_to_file(BLOCKCHAIN_FILE)
    logger.success("Blockchain saved")


@app.get("/")
async def root():
    """API root"""
    return {
        "name": "CoreChain Blockchain API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/blockchain/transaction")
async def submit_transaction(transaction: Transaction):
    """Submit a new transaction to the blockchain"""
    try:
        tx_hash = blockchain.add_transaction({
            'type': transaction.type,
            **transaction.data
        })
        
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "message": "Transaction added to pending pool"
        }
    except Exception as e:
        logger.error(f"Transaction submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/blockchain/mine")
async def mine_block():
    """Manually trigger block mining"""
    try:
        if not blockchain.pending_transactions:
            return {
                "success": False,
                "message": "No pending transactions to mine"
            }
        
        blockchain.mine_pending_transactions()
        
        return {
            "success": True,
            "block_index": len(blockchain.chain) - 1,
            "block_hash": blockchain.get_latest_block().hash
        }
    except Exception as e:
        logger.error(f"Mining error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/blockchain/chain")
async def get_chain():
    """Get the entire blockchain"""
    return {
        "chain": blockchain.get_chain(),
        "length": len(blockchain.chain)
    }


@app.get("/api/blockchain/block/{index}")
async def get_block(index: int):
    """Get a specific block by index"""
    block = blockchain.get_block(index)
    
    if block is None:
        raise HTTPException(status_code=404, detail=f"Block {index} not found")
    
    return block


@app.get("/api/blockchain/validate")
async def validate_chain():
    """Validate the blockchain integrity"""
    is_valid = blockchain.is_chain_valid()
    
    return {
        "is_valid": is_valid,
        "message": "Blockchain is valid" if is_valid else "Blockchain is corrupted"
    }


@app.get("/api/blockchain/stats")
async def get_stats():
    """Get blockchain statistics"""
    return blockchain.get_stats()


@app.get("/api/blockchain/transactions/type/{tx_type}")
async def get_transactions_by_type(tx_type: str):
    """Get all transactions of a specific type"""
    transactions = blockchain.get_transactions_by_type(tx_type)
    
    return {
        "type": tx_type,
        "count": len(transactions),
        "transactions": transactions
    }


@app.get("/api/blockchain/hospital/{hospital_id}/transactions")
async def get_hospital_transactions(hospital_id: str):
    """Get all transactions for a specific hospital"""
    transactions = blockchain.get_transactions_by_hospital(hospital_id)
    
    return {
        "hospital_id": hospital_id,
        "count": len(transactions),
        "transactions": transactions
    }


@app.get("/api/blockchain/hospital/{hospital_id}/rewards")
async def get_hospital_rewards(hospital_id: str):
    """Get total rewards for a hospital"""
    total_rewards = blockchain.get_hospital_rewards(hospital_id)
    reward_txs = [
        tx for tx in blockchain.get_transactions_by_hospital(hospital_id)
        if tx.get('type') == 'REWARD_DISTRIBUTION'
    ]
    
    return {
        "hospital_id": hospital_id,
        "total_rewards": total_rewards,
        "reward_count": len(reward_txs),
        "reward_history": reward_txs
    }


@app.get("/api/blockchain/leaderboard")
async def get_leaderboard():
    """Get hospital leaderboard by rewards"""
    leaderboard = reward_distributor.get_leaderboard()
    
    return {
        "leaderboard": leaderboard,
        "count": len(leaderboard)
    }


@app.get("/api/blockchain/audit")
async def get_audit_trail(
    hospital_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
):
    """Get audit trail with optional filters"""
    audit_trail = audit_logger.get_audit_trail(
        hospital_id=hospital_id,
        event_type=event_type,
        limit=limit
    )
    
    return {
        "audit_trail": audit_trail,
        "count": len(audit_trail),
        "filters": {
            "hospital_id": hospital_id,
            "event_type": event_type,
            "limit": limit
        }
    }


@app.get("/api/blockchain/training/summary")
async def get_training_summary():
    """Get training activity summary"""
    summary = audit_logger.get_training_summary()
    
    return summary


@app.post("/api/blockchain/validate/update")
async def validate_update(update_data: Dict):
    """Validate a model update using smart contract"""
    is_valid, message = validator.execute(update_data)
    
    return {
        "is_valid": is_valid,
        "message": message
    }


def start_server(port: int = 7050):
    """Start the blockchain API server"""
    logger.info(f"Starting Blockchain API on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    port = int(os.getenv('BLOCKCHAIN_PORT', 7050))
    start_server(port)
