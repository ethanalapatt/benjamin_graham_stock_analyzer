"""API key management with rotation support - TEMPLATE FILE"""

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


# Alpha Vantage API keys - ADD YOUR KEYS HERE
# To use this file:
# 1. Copy this file to src/api_keys.py
# 2. Add your actual Alpha Vantage API keys to the list below
# 3. Never commit api_keys.py to version control (it's in .gitignore)

ALPHA_VANTAGE_KEYS = [
    "YOUR_ALPHA_VANTAGE_KEY_1",
    "YOUR_ALPHA_VANTAGE_KEY_2", 
    "YOUR_ALPHA_VANTAGE_KEY_3",
    # Add more keys as needed...
    # Get free keys from: https://www.alphavantage.co/support/#api-key
]

# Create global key manager
alpha_vantage_key_manager = APIKeyManager(ALPHA_VANTAGE_KEYS)