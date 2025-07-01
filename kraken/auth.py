# kraken/auth.py

import time
import base64
import hashlib
import hmac
import urllib.parse
from typing import Dict, Optional
from logger import Logger


class KrakenAuth:
    """
    Optimized Kraken API authentication handler.
    
    Handles request signing for Kraken's private API endpoints according to their
    official authentication scheme: https://docs.kraken.com/rest/#section/Authentication
    """
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Kraken authentication.
        
        Args:
            api_key: Kraken API public key
            api_secret: Kraken API private key (base64 encoded)
            
        Raises:
            ValueError: If api_key or api_secret is empty
            Exception: If api_secret is not valid base64
        """
        if not api_key or not api_secret:
            raise ValueError("API key and secret cannot be empty")
        
        self.api_key = api_key
        
        try:
            self.api_secret = base64.b64decode(api_secret)
        except Exception as e:
            raise ValueError(f"Invalid base64 API secret: {e}")
        
        self.logger = Logger(__name__, log_to_file=True)
        self._last_nonce = 0
        
    def sign_request(self, url_path: str, data: Optional[Dict] = None) -> Dict[str, str]:
        """
        Creates signed headers for a Kraken API private request.
        
        Args:
            url_path: API endpoint path (e.g. "/0/private/Balance")
            data: POST data payload as a dict (will be modified to add nonce)
            
        Returns:
            Dictionary containing API-Key and API-Sign headers
            
        Raises:
            ValueError: If url_path is empty or invalid
        """
        if not url_path:
            raise ValueError("URL path cannot be empty")
        
        if data is None:
            data = {}
        
        # Generate nonce - ensure it's always increasing
        nonce = self._generate_nonce()
        data["nonce"] = nonce
        
        try:
            # Create signature according to Kraken's specification
            signature = self._create_signature(url_path, data)
            
            headers = {
                "API-Key": self.api_key,
                "API-Sign": signature
            }
            
            self.logger.debug(f"🔑 Signed request for {url_path} with nonce {nonce}")
            return headers
            
        except Exception as e:
            self.logger.error(f"❌ Failed to sign request for {url_path}: {e}")
            raise
    
    def _generate_nonce(self) -> str:
        """
        Generate a nonce (number used once) for API requests.
        
        Kraken requires nonces to be increasing integers. Using microsecond
        precision timestamp ensures uniqueness and proper ordering.
        
        Returns:
            String representation of nonce
        """
        # Use microsecond precision to ensure uniqueness
        nonce = int(time.time() * 1_000_000)
        
        # Ensure nonce is always increasing (handle clock adjustments)
        if nonce <= self._last_nonce:
            nonce = self._last_nonce + 1
        
        self._last_nonce = nonce
        return str(nonce)
    
    def _create_signature(self, url_path: str, data: Dict) -> str:
        """
        Create HMAC-SHA512 signature for Kraken API request.
        
        Kraken signature algorithm:
        1. Create message: nonce + POST data (URL encoded)
        2. Hash message with SHA256
        3. Concatenate URL path + SHA256 hash
        4. Sign with HMAC-SHA512 using decoded secret
        5. Base64 encode the result
        
        Args:
            url_path: API endpoint path
            data: Request data including nonce
            
        Returns:
            Base64 encoded signature
        """
        # Get nonce as string
        nonce = str(data["nonce"])
        
        # URL encode the POST data
        post_data = urllib.parse.urlencode(data)
        
        # Create message: nonce + POST data
        message = (nonce + post_data).encode('utf-8')
        
        # Create SHA256 hash of the message
        sha256_hash = hashlib.sha256(message).digest()
        
        # Concatenate URL path + SHA256 hash
        path_bytes = url_path.encode('utf-8')
        hmac_data = path_bytes + sha256_hash
        
        # Create HMAC-SHA512 signature
        signature = hmac.new(
            self.api_secret,
            hmac_data,
            hashlib.sha512
        ).digest()
        
        # Base64 encode and return as string
        return base64.b64encode(signature).decode('utf-8')
    
    def validate_credentials(self) -> bool:
        """
        Validate API credentials format (basic checks).
        
        Returns:
            True if credentials appear to have valid format
        """
        try:
            # Basic validation checks
            if len(self.api_key) < 10:
                return False
            
            if len(self.api_secret) < 10:
                return False
            
            # Test if secret can be base64 decoded (already done in __init__)
            return True
            
        except Exception:
            return False
    
    @property
    def masked_api_key(self) -> str:
        """Get API key with masked middle section for logging."""
        if len(self.api_key) <= 8:
            return "***"
        return f"{self.api_key[:4]}***{self.api_key[-4:]}"
