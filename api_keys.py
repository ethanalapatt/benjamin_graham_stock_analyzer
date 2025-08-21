"""API key management with rotation support"""

import random
from typing import List, Optional


class APIKeyManager:
    """Manages multiple API keys with rotation"""
    
    def __init__(self, keys: List[str]):
        self.keys = [key.strip() for key in keys if key.strip()]
        self.current_index = 0
        
    def get_current_key(self) -> Optional[str]:
        """Get the current API key"""
        if not self.keys:
            return None
        return self.keys[self.current_index]
    
    def rotate_key(self):
        """Rotate to the next API key"""
        if len(self.keys) > 1:
            self.current_index = (self.current_index + 1) % len(self.keys)
    
    def get_random_key(self) -> Optional[str]:
        """Get a random API key"""
        if not self.keys:
            return None
        return random.choice(self.keys)
    
    def get_key_count(self) -> int:
        """Get total number of available keys"""
        return len(self.keys)


# Alpha Vantage API keys provided
ALPHA_VANTAGE_KEYS = [
]

# Create global key manager
alpha_vantage_key_manager = APIKeyManager(ALPHA_VANTAGE_KEYS)
