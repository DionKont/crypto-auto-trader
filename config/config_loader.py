# config/config_loader.py

import os
import sys
import dotenv
from typing import Optional, Set, Dict, Any, List
from dataclasses import dataclass
from logger import Logger

# Load .env file at module import time
dotenv.load_dotenv()

@dataclass(frozen=True)
class TradingConfig:
    """Immutable configuration data class with validation."""
    # API Configuration
    api_key: str
    api_secret: str
    
    # Trading Configuration
    mode: str
    symbols: List[str]
    timeframes: List[str]
    history_count: int
    
    # Data Configuration
    max_candles: int
    cache_ttl: int
    
    # Application Configuration
    log_level: str
    log_to_file: bool
    
    # Legacy support
    timeframe: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.mode not in ConfigLoader.VALID_MODES:
            raise ValueError(f"Mode must be one of {ConfigLoader.VALID_MODES}")
        
        # Only validate API credentials for live mode
        if self.mode == "live":
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials cannot be empty for live mode")
        
        # Validate timeframes
        invalid_timeframes = [tf for tf in self.timeframes if tf not in ConfigLoader.VALID_TIMEFRAMES]
        if invalid_timeframes:
            raise ValueError(f"Invalid timeframes {invalid_timeframes}. Valid: {list(ConfigLoader.VALID_TIMEFRAMES)}")
        
        # Validate symbols
        if not self.symbols:
            raise ValueError("At least one symbol must be specified")
        
        # Validate numeric values
        if self.history_count <= 0:
            raise ValueError("History count must be positive")
        if self.max_candles <= 0:
            raise ValueError("Max candles must be positive")
        if self.cache_ttl < 0:
            raise ValueError("Cache TTL must be non-negative")
    
    def get_masked_secrets(self) -> Dict[str, Any]:
        """Return configuration with masked secrets for secure logging."""
        result = {
            "mode": self.mode,
            "symbols": self.symbols,
            "timeframes": self.timeframes,
            "history_count": self.history_count,
            "max_candles": self.max_candles,
            "cache_ttl": self.cache_ttl,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
        }
        
        # Only show API credentials for live mode
        if self.mode == "live":
            result.update({
                "api_key": self._mask_secret(self.api_key),
                "api_secret": self._mask_secret(self.api_secret),
            })
        
        return result
    
    @staticmethod
    def _mask_secret(secret: str) -> str:
        """Mask a secret string for logging."""
        if len(secret) <= 8:
            return "***"
        return f"{secret[:4]}***{secret[-4:]}"


class ConfigLoader:
    """Enhanced configuration loader for crypto trading application."""
    
    # Use frozenset for immutable, efficient lookups
    VALID_MODES: Set[str] = frozenset({"backtest", "live", "data"})
    VALID_TIMEFRAMES: Set[str] = frozenset({"1m", "5m", "15m", "30m", "1h", "4h", "1d"})
    VALID_SYMBOLS: Set[str] = frozenset({"BTC", "ETH", "ADA", "DOT", "LINK", "UNI", "AAVE", "MATIC", "SOL", "AVAX"})
    VALID_LOG_LEVELS: Set[str] = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
    
    # Default values
    DEFAULT_SYMBOLS = ["BTC"]
    DEFAULT_TIMEFRAMES = ["1m", "5m", "15m", "1h"]
    DEFAULT_HISTORY_COUNT = 1000
    DEFAULT_MAX_CANDLES = 2000
    DEFAULT_CACHE_TTL = 60
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_LOG_TO_FILE = True
    
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
        
        # Load symbols - comma-separated list
        symbols_str = self._get_config_value("SYMBOLS", "💰 Enter SYMBOLS (comma-separated)", 
                                           required=False, default=",".join(self.DEFAULT_SYMBOLS))
        symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
        
        # Validate symbols
        invalid_symbols = [s for s in symbols if s not in self.VALID_SYMBOLS]
        if invalid_symbols:
            self.logger.warning(f"⚠️  Unknown symbols: {invalid_symbols}. Proceeding anyway...")
        
        # Load timeframes - comma-separated list
        timeframes_str = self._get_config_value("TIMEFRAMES", "📊 Enter TIMEFRAMES (comma-separated)",
                                              required=False, default=",".join(self.DEFAULT_TIMEFRAMES))
        timeframes = [t.strip().lower() for t in timeframes_str.split(",") if t.strip()]
        
        # Load numeric configurations
        history_count = int(self._get_config_value("HISTORY_COUNT", "📈 Enter HISTORY_COUNT",
                                                 required=False, default=str(self.DEFAULT_HISTORY_COUNT)))
        
        max_candles = int(self._get_config_value("MAX_CANDLES", "📊 Enter MAX_CANDLES", 
                                               required=False, default=str(self.DEFAULT_MAX_CANDLES)))
        
        cache_ttl = int(self._get_config_value("CACHE_TTL", "⏰ Enter CACHE_TTL (seconds)",
                                             required=False, default=str(self.DEFAULT_CACHE_TTL)))
        
        # Load logging configuration
        log_level = self._get_config_value("LOG_LEVEL", "📝 Enter LOG_LEVEL",
                                         valid_values=self.VALID_LOG_LEVELS,
                                         transform=str.upper,
                                         required=False, default=self.DEFAULT_LOG_LEVEL)
        
        log_to_file_str = self._get_config_value("LOG_TO_FILE", "📁 Log to file (true/false)",
                                                required=False, default="true")
        log_to_file = log_to_file_str.lower() in ("true", "1", "yes", "on")
        
        return TradingConfig(
            api_key=api_key,
            api_secret=api_secret,
            mode=mode,
            symbols=symbols,
            timeframes=timeframes,
            history_count=history_count,
            max_candles=max_candles,
            cache_ttl=cache_ttl,
            log_level=log_level,
            log_to_file=log_to_file
        )
    
    def _get_config_value(self,
                         env_var: str,
                         prompt: str,
                         valid_values: Optional[Set[str]] = None,
                         transform: Optional[callable] = None,
                         required: bool = False,
                         default: Optional[str] = None) -> str:
        """
        Get configuration value from environment or user input with validation.
        
        Args:
            env_var: Environment variable name
            prompt: User prompt message
            valid_values: Set of valid values for validation
            transform: Function to transform the input value
            required: Whether the value is required
            default: Default value to use if not found and not required
            
        Returns:
            The validated configuration value
            
        Raises:
            ValueError: If required value is missing or invalid
        """
        value = os.getenv(env_var)
        
        # Use default if no value found and not required
        if not value and not required and default:
            value = default
        
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
            
            # Show current default if available
            prompt_text = prompt
            if default and not required:
                prompt_text += f" (default: {default})"
            
            # Prompt user for input
            user_input = self._prompt_user_input(prompt_text, valid_values)
            
            # Use default if user provides empty input and default exists
            if not user_input and default and not required:
                value = default
            else:
                value = user_input
                
            if transform and value:
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
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            self.logger.info(f"{icon} {key.upper():<15} = {value}")
    
    @staticmethod
    def _get_config_icon(key: str) -> str:
        """Get appropriate emoji icon for configuration key."""
        icons = {
            "api_key": "🔑",
            "api_secret": "🔐",
            "mode": "⚙️ ",
            "symbols": "💰",
            "timeframes": "📊",
            "history_count": "📈",
            "max_candles": "📊",
            "cache_ttl": "⏰",
            "log_level": "📝",
            "log_to_file": "📁"
        }
        return icons.get(key, "🔧")
    
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
            self.logger.info("🔄 Reloading configuration...")
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
        
        # Skip validation for non-live modes
        if self._config.mode != "live":
            self.logger.info(f"📊 {self._config.mode.title()} mode - API credentials not required")
            return True
        
        # Basic validation for live mode
        api_key_valid = len(self._config.api_key) >= 8
        api_secret_valid = len(self._config.api_secret) >= 8
        
        self.logger.info(f"🔐 API credentials format validation: {'✅' if api_key_valid and api_secret_valid else '❌'}")
        return api_key_valid and api_secret_valid
