"""
Modern Configuration Manager for CommandCore Launcher

Provides a robust, type-safe configuration system with validation,
schemas, and automatic backup/restore functionality.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Type
from dataclasses import dataclass, field, asdict
from datetime import datetime
import sys
import os
from contextlib import contextmanager
import shutil
import tempfile
import stat

from PySide6.QtCore import QObject, Signal, QSettings, QStandardPaths


@dataclass
class UIConfig:
    """UI-specific configuration settings."""
    theme: str = "dark"
    font_family: str = "Segoe UI"
    font_size: int = 10
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    animation_enabled: bool = True
    animation_duration: int = 200
    show_splash: bool = True
    minimize_to_tray: bool = True
    close_to_tray: bool = True
    confirm_exit: bool = True
    remember_window_state: bool = True
    auto_save_interval: int = 300


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class ApplicationConfig:
    """Application-specific configuration."""
    auto_start_monitoring: bool = False
    update_check_frequency: str = "weekly"
    update_check_enabled: bool = True
    monitor_interval: int = 1000
    crash_reporting: bool = True
    performance_mode: bool = False
    debug_mode: bool = False
    startup_tab: str = "Dashboard"
    background_monitoring: bool = True


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    require_admin_for_apps: bool = False
    allow_external_apps: bool = True
    sandbox_mode: bool = False
    log_sensitive_data: bool = False


@dataclass
class NotificationConfig:
    """Notification system configuration."""
    enabled: bool = True
    show_app_status: bool = True
    show_system_alerts: bool = True
    show_updates: bool = True
    duration: int = 5000
    position: str = "bottom_right"


@dataclass
class AppConfig:
    """Root configuration class containing all settings."""
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    application: ApplicationConfig = field(default_factory=ApplicationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    version: str = "2.0.0"
    first_run: bool = True
    last_updated: Optional[str] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigManager(QObject):
    """
    Modern configuration manager with comprehensive features:
    
    - Type-safe configuration using dataclasses
    - Automatic validation and schema enforcement
    - Backup and restore functionality
    - Hot-reloading of configuration changes
    - Migration support for config upgrades
    - Environment variable override support
    - Robust file handling with fallbacks
    """
    
    # Signals
    config_changed = Signal(str, object)
    config_loaded = Signal()
    config_saved = Signal()
    config_error = Signal(str)
    
    def __init__(self, config_dir: Optional[Path] = None):
        super().__init__()
        
        # Setup logging first
        self.logger = logging.getLogger(self.__class__.__name__)
        
        try:
            # Setup paths with comprehensive fallback logic
            self.app_dir = Path(__file__).parent
            self.config_dir = config_dir or self._get_default_config_dir()
            self.config_file = self.config_dir / "config.json"
            self.backup_dir = self.config_dir / "backups"
            
            # Configuration instance
            self._config = AppConfig()
            self._config_cache: Dict[str, Any] = {}
            self._watchers = []
            self._dirty = False
            
            # Ensure directories exist with robust error handling
            if not self._ensure_directories():
                raise ConfigValidationError("Failed to create configuration directories")
            
            # Load configuration
            self.load_config()
            
            # Setup auto-save
            self._setup_auto_save()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ConfigManager: {e}", exc_info=True)
            # Create minimal fallback configuration
            self._config = AppConfig()
            self._config_cache = {}
            # Don't raise - allow application to continue with defaults
    
    def _get_default_config_dir(self) -> Path:
        """Get the default configuration directory with proper fallbacks."""
        config_dirs = []
        
        try:
            # Primary: Use Qt's standard paths
            data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if data_dir:
                config_dirs.append(Path(data_dir) / "CommandCore")
        except Exception as e:
            self.logger.warning(f"Could not get Qt standard location: {e}")
        
        # Platform-specific fallbacks
        if sys.platform == "win32":
            app_data = os.getenv("APPDATA")
            if app_data:
                config_dirs.append(Path(app_data) / "CommandCore")
            
            local_app_data = os.getenv("LOCALAPPDATA") 
            if local_app_data:
                config_dirs.append(Path(local_app_data) / "CommandCore")
                
        elif sys.platform == "darwin":
            home = Path.home()
            config_dirs.extend([
                home / "Library" / "Application Support" / "CommandCore",
                home / ".commandcore"
            ])
        else:  # Linux and others
            xdg_config = os.getenv("XDG_CONFIG_HOME")
            if xdg_config:
                config_dirs.append(Path(xdg_config) / "commandcore")
            
            home = Path.home()
            config_dirs.extend([
                home / ".config" / "commandcore",
                home / ".commandcore"
            ])
        
        # Always add application directory as ultimate fallback
        config_dirs.append(self.app_dir / "config")
        
        # Try each directory in order
        for config_dir in config_dirs:
            try:
                if self._test_directory_access(config_dir):
                    self.logger.debug(f"Using config directory: {config_dir}")
                    return config_dir
            except Exception as e:
                self.logger.debug(f"Cannot use config directory {config_dir}: {e}")
        
        # If all else fails, use a temporary directory
        temp_dir = Path(tempfile.gettempdir()) / "commandcore_config"
        self.logger.warning(f"Using temporary config directory: {temp_dir}")
        return temp_dir
    
    def _test_directory_access(self, directory: Path) -> bool:
        """Test if we can read/write to a directory."""
        try:
            # Try to create the directory
            directory.mkdir(parents=True, exist_ok=True)
            
            # Test write access
            test_file = directory / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            
            return True
        except Exception:
            return False
    
    def _ensure_directories(self) -> bool:
        """Ensure all required directories exist with proper error handling."""
        directories = [self.config_dir, self.backup_dir]
        
        for directory in directories:
            try:
                self.logger.debug(f"Ensuring directory exists: {directory}")
                
                # Create directory with parents
                directory.mkdir(parents=True, exist_ok=True)
                
                # Set appropriate permissions (Unix-like systems)
                if sys.platform != "win32":
                    try:
                        os.chmod(directory, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
                    except (OSError, AttributeError):
                        # Permissions setting failed, but directory exists
                        pass
                
                # Verify we can write to the directory
                if not self._test_directory_access(directory):
                    self.logger.error(f"Cannot write to directory: {directory}")
                    return False
                
                self.logger.debug(f"Directory verified: {directory}")
                
            except Exception as e:
                self.logger.error(f"Failed to create/access directory {directory}: {e}")
                return False
        
        return True
    
    def _setup_auto_save(self):
        """Setup automatic configuration saving."""
        try:
            from PySide6.QtCore import QTimer
            
            self.auto_save_timer = QTimer()
            self.auto_save_timer.timeout.connect(self._auto_save)
            
            interval = self._config.ui.auto_save_interval * 1000
            self.auto_save_timer.start(interval)
        except Exception as e:
            self.logger.warning(f"Could not setup auto-save: {e}")
    
    def _auto_save(self):
        """Automatically save configuration if changes were made."""
        try:
            if self._dirty:
                self.save_config()
                self._dirty = False
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")
    
    def load_config(self) -> bool:
        """Load configuration from file with comprehensive error handling."""
        try:
            if not self.config_file.exists():
                self.logger.info("No configuration file found, using defaults")
                self._config = AppConfig()
                self.save_config()
                self.config_loaded.emit()
                return True
            
            # Validate file is readable and not empty
            if self.config_file.stat().st_size == 0:
                self.logger.warning("Configuration file is empty, using defaults")
                self._config = AppConfig()
                self.save_config()
                self.config_loaded.emit()
                return True
            
            # Load and parse JSON with encoding detection
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                # Try different encodings
                for encoding in ['utf-8-sig', 'latin1', 'cp1252']:
                    try:
                        with open(self.config_file, 'r', encoding=encoding) as f:
                            data = json.load(f)
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                else:
                    raise ValueError("Could not decode configuration file")
            
            # Validate and migrate if necessary
            data = self._migrate_config(data)
            data = self._validate_config_data(data)
            
            # Convert to config object
            self._config = self._dict_to_config(data)
            
            # Override with environment variables
            self._apply_env_overrides()
            
            # Cache flattened config for quick access
            self._rebuild_cache()
            
            self.logger.info("Configuration loaded successfully")
            self.config_loaded.emit()
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in config file: {e}"
            self.logger.error(error_msg)
            self._handle_config_error(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            self.logger.error(error_msg, exc_info=True)
            self._handle_config_error(error_msg)
            return False
    
    def save_config(self) -> bool:
        """Save configuration to file with atomic writes and backup."""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                self.logger.debug(f"Saving configuration (attempt {attempt + 1}/{max_attempts})")
                
                # Ensure directories exist
                if not self._ensure_directories():
                    raise IOError("Cannot access configuration directory")
                
                # Create backup if file exists
                if self.config_file.exists() and self.config_file.stat().st_size > 0:
                    try:
                        self._create_backup()
                    except Exception as e:
                        self.logger.warning(f"Backup creation failed: {e}")
                
                # Update metadata
                self._config.last_updated = datetime.now().isoformat()
                self._config.first_run = False
                
                # Convert to dictionary
                config_dict = asdict(self._config)
                
                # Atomic write using temporary file
                temp_file = self.config_file.with_suffix(f'.tmp.{os.getpid()}')
                
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(config_dict, f, indent=2, ensure_ascii=False, default=str)
                        f.flush()
                        os.fsync(f.fileno())
                    
                    # Atomic move (platform-specific)
                    if sys.platform == 'win32' and self.config_file.exists():
                        # Windows requires removing destination file first
                        backup_path = self.config_file.with_suffix('.bak')
                        if backup_path.exists():
                            backup_path.unlink()
                        self.config_file.rename(backup_path)
                        temp_file.rename(self.config_file)
                        if backup_path.exists():
                            backup_path.unlink()
                    else:
                        # POSIX systems support atomic replace
                        temp_file.replace(self.config_file)
                    
                    # Rebuild cache
                    self._rebuild_cache()
                    
                    self.logger.info("Configuration saved successfully")
                    self.config_saved.emit()
                    return True
                    
                finally:
                    # Clean up temp file if it still exists
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except Exception as e:
                            self.logger.warning(f"Could not clean up temp file: {e}")
                
            except Exception as e:
                self.logger.error(f"Save attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    error_msg = f"Failed to save configuration after {max_attempts} attempts: {e}"
                    self.logger.error(error_msg)
                    self.config_error.emit(error_msg)
                    return False
        
        return False
    
    def _create_backup(self):
        """Create a timestamped backup of the current configuration."""
        try:
            if not self.config_file.exists():
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_backup_{timestamp}.json"
            
            # Ensure backup directory exists
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(self.config_file, backup_file)
            
            # Clean old backups (keep last 10)
            backups = sorted(self.backup_dir.glob("config_backup_*.json"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    try:
                        old_backup.unlink()
                    except Exception as e:
                        self.logger.warning(f"Could not remove old backup {old_backup}: {e}")
                        
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")
    
    def _migrate_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate configuration from older versions."""
        config_version = data.get('version', '1.0.0')
        
        if config_version < '2.0.0':
            self.logger.info("Migrating configuration from v1.x to v2.0")
            
            # Example migrations
            if 'theme' in data:
                data.setdefault('ui', {})['theme'] = data.pop('theme')
            
            if 'log_level' in data:
                data.setdefault('logging', {})['level'] = data.pop('log_level')
            
            if 'window_width' in data:
                data.setdefault('ui', {})['window_width'] = data.pop('window_width')
            
            if 'window_height' in data:
                data.setdefault('ui', {})['window_height'] = data.pop('window_height')
            
            # Add new required fields
            data['version'] = '2.0.0'
        
        return data
    
    def _validate_config_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration data against schema."""
        # Define validation rules
        validation_rules = {
            'ui.font_size': (8, 72),
            'ui.window_width': (800, 7680),
            'ui.window_height': (600, 4320),
            'ui.animation_duration': (50, 2000),
            'logging.max_file_size_mb': (1, 1000),
            'logging.backup_count': (1, 50),
            'application.monitor_interval': (100, 60000),
            'notifications.duration': (1000, 30000),
        }
        
        # Validate and fix numeric values
        for key, (min_val, max_val) in validation_rules.items():
            try:
                value = self._get_nested_value(data, key)
                if value is not None:
                    if isinstance(value, (int, float)):
                        if value < min_val or value > max_val:
                            self.logger.warning(f"Invalid value for {key}: {value}, using default")
                            self._set_nested_value(data, key, min_val)
            except Exception:
                continue
        
        # Validate enum values
        enum_validations = {
            'ui.theme': ['dark', 'light', 'auto', 'high_contrast'],
            'logging.level': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'application.update_check_frequency': ['never', 'daily', 'weekly', 'monthly'],
            'notifications.position': ['bottom_right', 'bottom_left', 'top_right', 'top_left'],
        }
        
        for key, valid_values in enum_validations.items():
            try:
                value = self._get_nested_value(data, key)
                if value is not None and value not in valid_values:
                    self.logger.warning(f"Invalid value for {key}: {value}, using default")
                    self._set_nested_value(data, key, valid_values[0])
            except Exception:
                continue
        
        return data
    
    def _get_nested_value(self, data: Dict, key: str) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value
    
    def _set_nested_value(self, data: Dict, key: str, value: Any):
        """Set nested dictionary value using dot notation."""
        keys = key.split('.')
        current = data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig object with error handling."""
        try:
            # Create config sections with defaults for missing fields
            ui_data = data.get('ui', {})
            ui_config = UIConfig(
                theme=ui_data.get('theme', 'dark'),
                font_family=ui_data.get('font_family', 'Segoe UI'),
                font_size=ui_data.get('font_size', 10),
                window_width=ui_data.get('window_width', 1200),
                window_height=ui_data.get('window_height', 800),
                window_maximized=ui_data.get('window_maximized', False),
                animation_enabled=ui_data.get('animation_enabled', True),
                animation_duration=ui_data.get('animation_duration', 200),
                show_splash=ui_data.get('show_splash', True),
                minimize_to_tray=ui_data.get('minimize_to_tray', True),
                close_to_tray=ui_data.get('close_to_tray', True),
                confirm_exit=ui_data.get('confirm_exit', True),
                remember_window_state=ui_data.get('remember_window_state', True),
                auto_save_interval=ui_data.get('auto_save_interval', 300)
            )
            
            logging_data = data.get('logging', {})
            logging_config = LoggingConfig(
                level=logging_data.get('level', 'INFO'),
                file_enabled=logging_data.get('file_enabled', True),
                console_enabled=logging_data.get('console_enabled', True),
                max_file_size_mb=logging_data.get('max_file_size_mb', 10),
                backup_count=logging_data.get('backup_count', 5),
                format=logging_data.get('format', "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                date_format=logging_data.get('date_format', "%Y-%m-%d %H:%M:%S")
            )
            
            app_data = data.get('application', {})
            app_config = ApplicationConfig(
                auto_start_monitoring=app_data.get('auto_start_monitoring', False),
                update_check_frequency=app_data.get('update_check_frequency', 'weekly'),
                update_check_enabled=app_data.get('update_check_enabled', True),
                monitor_interval=app_data.get('monitor_interval', 1000),
                crash_reporting=app_data.get('crash_reporting', True),
                performance_mode=app_data.get('performance_mode', False),
                debug_mode=app_data.get('debug_mode', False),
                startup_tab=app_data.get('startup_tab', 'Dashboard'),
                background_monitoring=app_data.get('background_monitoring', True)
            )
            
            security_data = data.get('security', {})
            security_config = SecurityConfig(
                require_admin_for_apps=security_data.get('require_admin_for_apps', False),
                allow_external_apps=security_data.get('allow_external_apps', True),
                sandbox_mode=security_data.get('sandbox_mode', False),
                log_sensitive_data=security_data.get('log_sensitive_data', False)
            )
            
            notification_data = data.get('notifications', {})
            notification_config = NotificationConfig(
                enabled=notification_data.get('enabled', True),
                show_app_status=notification_data.get('show_app_status', True),
                show_system_alerts=notification_data.get('show_system_alerts', True),
                show_updates=notification_data.get('show_updates', True),
                duration=notification_data.get('duration', 5000),
                position=notification_data.get('position', 'bottom_right')
            )
            
            # Create main config
            config = AppConfig(
                ui=ui_config,
                logging=logging_config,
                application=app_config,
                security=security_config,
                notifications=notification_config,
                version=data.get('version', '2.0.0'),
                first_run=data.get('first_run', True),
                last_updated=data.get('last_updated'),
                custom_settings=data.get('custom_settings', {})
            )
            
            return config
            
        except Exception as e:
            self.logger.warning(f"Error converting config data: {e}")
            return AppConfig()  # Use defaults
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        env_prefix = "COMMANDCORE_"
        
        env_mappings = {
            f"{env_prefix}THEME": "ui.theme",
            f"{env_prefix}LOG_LEVEL": "logging.level",
            f"{env_prefix}DEBUG": "application.debug_mode",
            f"{env_prefix}PERFORMANCE_MODE": "application.performance_mode",
            f"{env_prefix}FONT_SIZE": "ui.font_size",
            f"{env_prefix}WINDOW_WIDTH": "ui.window_width",
            f"{env_prefix}WINDOW_HEIGHT": "ui.window_height",
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Convert boolean strings
                    if value.lower() in ('true', '1', 'yes', 'on'):
                        value = True
                    elif value.lower() in ('false', '0', 'no', 'off'):
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    
                    self.set(config_path, value)
                    self.logger.info(f"Applied environment override: {config_path} = {value}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to apply env override {env_var}: {e}")
    
    def _rebuild_cache(self):
        """Rebuild the flattened configuration cache."""
        def flatten_dict(d, parent_key='', sep='.'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        try:
            self._config_cache = flatten_dict(asdict(self._config))
        except Exception as e:
            self.logger.error(f"Failed to rebuild config cache: {e}")
            self._config_cache = {}
    
    def _handle_config_error(self, error_msg: str):
        """Handle configuration errors by restoring from backup or using defaults."""
        self.config_error.emit(error_msg)
        
        # Try to restore from latest backup
        try:
            backups = sorted(self.backup_dir.glob("config_backup_*.json"))
            if backups:
                latest_backup = backups[-1]
                self.logger.info(f"Attempting to restore from backup: {latest_backup}")
                shutil.copy2(latest_backup, self.config_file)
                if self.load_config():
                    return
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
        
        # Use default configuration
        self.logger.info("Using default configuration")
        self._config = AppConfig()
        self._rebuild_cache()
        self.save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        try:
            # Check cache first
            if key in self._config_cache:
                return self._config_cache[key]
            
            # Navigate through nested structure
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.warning(f"Error getting config value '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value using dot notation."""
        try:
            keys = key.split('.')
            obj = self._config
            
            # Navigate to parent object
            for k in keys[:-1]:
                if hasattr(obj, k):
                    obj = getattr(obj, k)
                else:
                    self.logger.error(f"Invalid configuration path: {key}")
                    return False
            
            # Set final value
            final_key = keys[-1]
            if hasattr(obj, final_key):
                old_value = getattr(obj, final_key)
                setattr(obj, final_key, value)
                
                # Update cache
                self._config_cache[key] = value
                
                # Mark as dirty for auto-save
                self._dirty = True
                
                # Emit change signal
                self.config_changed.emit(key, value)
                
                self.logger.debug(f"Config updated: {key} = {value} (was: {old_value})")
                return True
            else:
                self.logger.error(f"Invalid configuration key: {final_key}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting config value '{key}': {e}")
            return False
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update multiple configuration settings at once."""
        try:
            success = True
            for key, value in settings.items():
                if not self.set(key, value):
                    success = False
            
            if success:
                self.save_config()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values."""
        try:
            # Create backup first
            if self.config_file.exists():
                self._create_backup()
            
            # Reset to defaults
            self._config = AppConfig()
            self._rebuild_cache()
            
            success = self.save_config()
            if success:
                self.logger.info("Configuration reset to defaults")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False
    
    def export_config(self, file_path: Union[str, Path]) -> bool:
        """Export configuration to a file."""
        try:
            export_data = {
                **asdict(self._config),
                'export_timestamp': datetime.now().isoformat(),
                'export_version': self._config.version
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Configuration exported to: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, file_path: Union[str, Path]) -> bool:
        """Import configuration from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove export-specific fields
            data.pop('export_timestamp', None)
            data.pop('export_version', None)
            
            # Validate and migrate
            data = self._migrate_config(data)
            data = self._validate_config_data(data)
            
            # Create backup of current config
            self._create_backup()
            
            # Apply imported config
            self._config = self._dict_to_config(data)
            self._rebuild_cache()
            
            success = self.save_config()
            if success:
                self.logger.info(f"Configuration imported from: {file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about the current configuration."""
        try:
            file_size = self.config_file.stat().st_size if self.config_file.exists() else 0
            backup_count = len(list(self.backup_dir.glob("config_backup_*.json")))
        except Exception:
            file_size = 0
            backup_count = 0
        
        return {
            'config_file': str(self.config_file),
            'config_dir': str(self.config_dir),
            'version': self._config.version,
            'last_updated': self._config.last_updated,
            'first_run': self._config.first_run,
            'file_exists': self.config_file.exists(),
            'file_size': file_size,
            'backup_count': backup_count,
            'writable': self._test_directory_access(self.config_dir),
        }
    
    @property
    def config(self) -> AppConfig:
        """Get the current configuration object."""
        return self._config
    
    @contextmanager
    def batch_update(self):
        """Context manager for batch configuration updates."""
        old_auto_save = hasattr(self, 'auto_save_timer') and self.auto_save_timer.isActive()
        
        if old_auto_save:
            self.auto_save_timer.stop()
        
        try:
            yield self
        finally:
            if old_auto_save:
                self.auto_save_timer.start()
            self.save_config()


# Convenience function for quick config access
_config_manager: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager