# config/config_loader.py

import os
import sys
from typing import Optional, Set, Dict, Any
from dataclasses import dataclass
from logger import Logger


@dataclass(frozen=True)
class TradingConfig:
    """Immutable configuration data class with validation."""
    api_key: str
    api_secret: str
    mode: str
    timeframe: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.mode not in ConfigLoader.VALID_MODES:
            raise ValueError(f"Mode must be one of {ConfigLoader.VALID_MODES}")
        
        # Only validate API credentials for live mode
        if self.mode == "live":
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials cannot be empty for live mode")
        
        if self.mode == "backtest" and (not self.timeframe or self.timeframe not in ConfigLoader.VALID_TIMEFRAMES):
            raise ValueError(f"Backtest mode requires timeframe. Must be one of {ConfigLoader.VALID_TIMEFRAMES}")
    
    def get_masked_secrets(self) -> Dict[str, str]:
        """Return configuration with masked secrets for secure logging."""
        result = {
            "mode": self.mode,
        }
        
        # Only show API credentials for live mode
        if self.mode == "live":
            result.update({
                "api_key": self._mask_secret(self.api_key),
                "api_secret": self._mask_secret(self.api_secret),
            })
        
        result["timeframe"] = self.timeframe or "N/A"
        return result
    
    @staticmethod
    def _mask_secret(secret: str) -> str:
        """Mask a secret string for logging."""
        if len(secret) <= 8:
            return "***"
        return f"{secret[:4]}***{secret[-4:]}"

class ConfigLoader:
    """Optimized configuration loader for crypto trading application."""
    
    # Use frozenset for immutable, efficient lookups
    VALID_MODES: Set[str] = frozenset({"backtest", "live"})
    VALID_TIMEFRAMES: Set[str] = frozenset({"1", "5", "15", "30", "60", "240", "720", "1440"})
    
    def __init__(self, interactive: bool = True):
        """
        Initialize ConfigLoader.
        
        Args:
            interactive: Whether to prompt user for missing values (default: True)
        """
        self.logger = Logger(__name__, log_to_file=True)
        self.interactive = interactive
        self._config: Optional[TradingConfig] = None
        
        try:
            self._config = self._load_and_validate_config()
            self._log_configuration()
            
        except (ValueError, KeyboardInterrupt) as e:
            self._handle_configuration_error(e)
    
    @property
    def config(self) -> TradingConfig:
        """Get the validated configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not properly initialized")
        return self._config
    
    def _load_and_validate_config(self) -> TradingConfig:
        """Load and validate the complete configuration."""
        self.logger.info("🔧 Loading trading configuration...")
        
        # Load MODE first - always required
        mode = self._get_config_value("MODE", "⚙️  Enter MODE", 
                                    valid_values=self.VALID_MODES,
                                    transform=str.lower,
                                    required=True)
        
        # Initialize API credentials
        api_key = ""
        api_secret = ""
        
        # Only get API credentials for live mode
        if mode == "live":
            api_key = self._get_config_value("API_KEY", "🔑 Enter API_KEY", required=True)
            api_secret = self._get_config_value("API_SECRET", "🔐 Enter API_SECRET", required=True)
        
        # Get timeframe for backtest mode
        timeframe = None
        if mode == "backtest":
            timeframe = self._get_config_value("TIMEFRAME", "🕒 Enter TIMEFRAME",
                                             valid_values=self.VALID_TIMEFRAMES,
                                             required=True)
        
        return TradingConfig(
            api_key=api_key,
            api_secret=api_secret,
            mode=mode,
            timeframe=timeframe
        )
    
    def _get_config_value(self,
                         env_var: str,
                         prompt: str,
                         valid_values: Optional[Set[str]] = None,
                         transform: Optional[callable] = None,
                         required: bool = False) -> str:
        """
        Get configuration value from environment or user input with validation.
        
        Args:
            env_var: Environment variable name
            prompt: User prompt message
            valid_values: Set of valid values for validation
            transform: Function to transform the input value
            required: Whether the value is required
            
        Returns:
            The validated configuration value
            
        Raises:
            ValueError: If required value is missing or invalid
        """
        value = os.getenv(env_var)
        
        # Transform value if transformer provided
        if value and transform:
            value = transform(value)
        
        # Check if value is valid
        while not self._is_valid_value(value, valid_values, required):
            if not self.interactive:
                error_msg = f"Missing or invalid {env_var}"
                if valid_values:
                    error_msg += f". Expected one of: {', '.join(sorted(valid_values))}"
                raise ValueError(error_msg)
            
            # Prompt user for input
            value = self._prompt_user_input(prompt, valid_values)
            if transform:
                value = transform(value)
        
        return value
    
    def _is_valid_value(self, value: Optional[str], valid_values: Optional[Set[str]], required: bool) -> bool:
        """Check if a value is valid according to the criteria."""
        if required and not value:
            return False
        if valid_values and value and value not in valid_values:
            return False
        return True
    
    def _prompt_user_input(self, prompt: str, valid_values: Optional[Set[str]]) -> str:
        """Prompt user for input with validation hints."""
        try:
            if valid_values:
                full_prompt = f"{prompt} ({'/'.join(sorted(valid_values))}): "
            else:
                full_prompt = f"{prompt}: "
            
            return input(full_prompt).strip()
            
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt("Configuration cancelled by user")
    
    def _log_configuration(self) -> None:
        """Log the configuration with masked secrets."""
        if not self._config:
            return
        
        self.logger.info("✅ Configuration loaded successfully:")
        masked_config = self._config.get_masked_secrets()
        
        for key, value in masked_config.items():
            icon = self._get_config_icon(key)
            self.logger.info(f"{icon} {key.upper():<12} = {value}")
    
    @staticmethod
    def _get_config_icon(key: str) -> str:
        """Get appropriate emoji icon for configuration key."""
        icons = {
            "api_key": "🔑",
            "api_secret": "🔐",
            "mode": "⚙️ ",
            "timeframe": "🕒"
        }
        return icons.get(key, "�")
    
    def _handle_configuration_error(self, error: Exception) -> None:
        """Handle configuration errors appropriately."""
        if isinstance(error, KeyboardInterrupt):
            self.logger.info("🛑 Configuration cancelled by user")
            sys.exit(0)
        else:
            self.logger.error(f"❌ Configuration error: {error}")
            if not self.interactive:
                sys.exit(1)
            raise
    
    def reload(self) -> None:
        """Reload configuration from environment variables."""
        try:
            self.logger.info("� Reloading configuration...")
            self._config = self._load_and_validate_config()
            self._log_configuration()
            self.logger.info("✅ Configuration reloaded successfully")
            
        except (ValueError, KeyboardInterrupt) as e:
            self._handle_configuration_error(e)
    
    def validate_api_credentials(self) -> bool:
        """
        Validate API credentials format (placeholder for actual validation).
        
        Returns:
            True if credentials appear valid, False otherwise
        """
        if not self._config:
            return False
        
        # Skip validation for backtest mode
        if self._config.mode == "backtest":
            self.logger.info("📊 Backtest mode - API credentials not required")
            return True
        
        # Basic validation for live mode
        api_key_valid = len(self._config.api_key) >= 8
        api_secret_valid = len(self._config.api_secret) >= 8
        
        self.logger.info(f"🔐 API credentials format validation: {'✅' if api_key_valid and api_secret_valid else '❌'}")
        return api_key_valid and api_secret_valid
