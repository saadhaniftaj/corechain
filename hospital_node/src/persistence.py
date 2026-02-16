"""
Persistence layer for hospital node
Manages storage of rounds history and configuration
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class HospitalPersistence:
    """Handles persistent storage for hospital node"""
    
    def __init__(self, data_dir: str = "/hospital/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.data_dir / "history.json"
        self.config_file = self.data_dir / "config.json"
        self.state_file = self.data_dir / "state.json"
    
    def load_history(self) -> List[Dict]:
        """Load rounds history"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_history(self, history: List[Dict]):
        """Save rounds history"""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def add_round(self, round_data: Dict):
        """Add a new round to history"""
        history = self.load_history()
        
        # Add timestamp if not present
        if 'timestamp' not in round_data:
            round_data['timestamp'] = datetime.now().isoformat()
        
        history.append(round_data)
        self.save_history(history)
        
        return round_data
    
    def update_round_status(self, round_number: int, status: str):
        """Update the status of a specific round"""
        history = self.load_history()
        
        for round_data in history:
            if round_data.get('round_number') == round_number:
                round_data['status'] = status
                round_data['status_updated'] = datetime.now().isoformat()
                break
        
        self.save_history(history)
    
    def get_round(self, round_number: int) -> Optional[Dict]:
        """Get a specific round by number"""
        history = self.load_history()
        
        for round_data in history:
            if round_data.get('round_number') == round_number:
                return round_data
        
        return None
    
    def get_total_rounds(self) -> int:
        """Get total number of rounds"""
        return len(self.load_history())
    
    def get_total_tokens(self) -> int:
        """Get total tokens earned"""
        history = self.load_history()
        return sum(r.get('tokens_earned', 0) for r in history)
    
    def load_config(self) -> Dict:
        """Load configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self, config: Dict):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_state(self) -> Dict:
        """Load current state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_state(self, state: Dict):
        """Save current state"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def clear_history(self):
        """Clear all history (use with caution)"""
        if self.history_file.exists():
            self.history_file.unlink()
