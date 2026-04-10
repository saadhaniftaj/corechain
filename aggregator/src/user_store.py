"""
User Store for CoreChain
Stores users in JSON file (persistent across restarts)
"""
import json
import os
import bcrypt
from datetime import datetime
from typing import Optional, Dict, List
from loguru import logger

USER_FILE = os.getenv('USER_DB_PATH', '/app/data/users.json')


def _load() -> Dict:
    if os.path.exists(USER_FILE):
        with open(USER_FILE) as f:
            return json.load(f)
    return {}


def _save(users: Dict):
    os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def seed_default_users():
    """Create default admin/researcher if no users exist"""
    users = _load()
    if users:
        return
    defaults = [
        {'user_id': 'admin', 'password': 'admin123', 'role': 'admin', 'name': 'System Admin'},
        {'user_id': 'researcher1', 'password': 'research123', 'role': 'researcher', 'name': 'Lead Researcher'},
    ]
    for u in defaults:
        users[u['user_id']] = {
            'user_id': u['user_id'],
            'name': u['name'],
            'role': u['role'],
            'password_hash': _hash(u['password']),
            'created_at': datetime.utcnow().isoformat()
        }
    _save(users)
    logger.info("Default users seeded (admin/admin123, researcher1/research123)")


def authenticate(user_id: str, password: str) -> Optional[Dict]:
    users = _load()
    user = users.get(user_id)
    if not user:
        return None
    if not _check(password, user['password_hash']):
        return None
    return {k: v for k, v in user.items() if k != 'password_hash'}


def create_user(user_id: str, password: str, role: str, name: str) -> Dict:
    users = _load()
    if user_id in users:
        raise ValueError(f'User {user_id} already exists')
    if role not in ('admin', 'researcher', 'institution'):
        raise ValueError(f'Invalid role: {role}')
    users[user_id] = {
        'user_id': user_id,
        'name': name,
        'role': role,
        'password_hash': _hash(password),
        'created_at': datetime.utcnow().isoformat()
    }
    _save(users)
    return {k: v for k, v in users[user_id].items() if k != 'password_hash'}


def list_users() -> List[Dict]:
    users = _load()
    return [{k: v for k, v in u.items() if k != 'password_hash'} for u in users.values()]


def get_user(user_id: str) -> Optional[Dict]:
    users = _load()
    u = users.get(user_id)
    if not u:
        return None
    return {k: v for k, v in u.items() if k != 'password_hash'}


def delete_user(user_id: str) -> bool:
    users = _load()
    if user_id not in users:
        return False
    del users[user_id]
    _save(users)
    return True
