"""
Application State Manager for CommandCore Launcher

Provides centralized state management with persistence,
event handling, and state synchronization across components.
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import threading
from contextlib import contextmanager

from PySide6.QtCore import QObject, Signal, QMutex, QTimer, QSettings
from PySide6.QtWidgets import QApplication


class StateScope(Enum):
    """State persistence scopes."""
    SESSION = "session"      # Lost when app closes
    PERSISTENT = "persistent"  # Saved to disk
    TEMPORARY = "temporary"   # Lost after timeout


@dataclass
class StateEntry:
    """Individual state entry with metadata."""
    key: str
    value: Any
    scope: StateScope = StateScope.SESSION
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateValidator:
    """Validates state values before setting."""
    
    def __init__(self):
        self.validators: Dict[str, Callable[[Any], bool]] = {}
        self.type_constraints: Dict[str, type] = {}
        self.value_constraints: Dict[str, Dict[str, Any]] = {}
    
    def add_validator(self, key: str, validator: Callable[[Any], bool]):
        """Add a custom validator function for a key."""
        self.validators[key] = validator
    
    def add_type_constraint(self, key: str, expected_type: type):
        """Add a type constraint for a key."""
        self.type_constraints[key] = expected_type
    
    def add_value_constraint(self, key: str, min_value=None, max_value=None, 
                           allowed_values=None):
        """Add value constraints for a key."""
        self.value_constraints[key] = {
            'min': min_value,
            'max': max_value,
            'allowed': allowed_values
        }
    
    def validate(self, key: str, value: Any) -> tuple[bool, str]:
        """Validate a value for a given key."""
        try:
            # Type validation
            if key in self.type_constraints:
                expected_type = self.type_constraints[key]
                if not isinstance(value, expected_type):
                    return False, f"Expected {expected_type.__name__}, got {type(value).__name__}"
            
            # Value constraints
            if key in self.value_constraints:
                constraints = self.value_constraints[key]
                
                if constraints['min'] is not None and value < constraints['min']:
                    return False, f"Value {value} is below minimum {constraints['min']}"
                
                if constraints['max'] is not None and value > constraints['max']:
                    return False, f"Value {value} is above maximum {constraints['max']}"
                
                if constraints['allowed'] is not None and value not in constraints['allowed']:
                    return False, f"Value {value} not in allowed values {constraints['allowed']}"
            
            # Custom validators
            if key in self.validators:
                validator = self.validators[key]
                if not validator(value):
                    return False, "Custom validation failed"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class AppStateManager(QObject):
    """
    Centralized application state manager with advanced features.
    
    Features:
    - Hierarchical state organization
    - Automatic persistence
    - State validation
    - Change notifications
    - State history/undo
    - Temporary state with expiration
    - Thread-safe operations
    - State synchronization
    """
    
    # Signals
    state_changed = Signal(str, object, object)  # key, new_value, old_value
    state_added = Signal(str, object)           # key, value
    state_removed = Signal(str)                 # key
    state_batch_changed = Signal(dict)          # changes dict
    
    def __init__(self, state_file: Optional[Path] = None):
        super().__init__()
        
        # State storage
        self.state: Dict[str, StateEntry] = {}
        self.state_history: List[Dict[str, Any]] = []
        self.max_history_size = 50
        
        # Thread safety
        self.mutex = QMutex()
        
        # State file management
        self.state_file = state_file or self._get_default_state_file()
        self.auto_save_enabled = True
        self.auto_save_interval = 30  # seconds
        
        # Validation
        self.validator = StateValidator()
        self._setup_default_validators()
        
        # Change tracking
        self.change_listeners: Dict[str, List[Callable]] = {}
        self.batch_mode = False
        self.batch_changes: Dict[str, Any] = {}
        
        # Cleanup timer for expired temporary state
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_expired_state)
        self.cleanup_timer.start(60000)  # Check every minute
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval * 1000)
        
        # Load existing state
        self.load_state()
        
        # Register app exit handler
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.save_state)
    
    def _get_default_state_file(self) -> Path:
        """Get the default state file path."""
        try:
            from PySide6.QtCore import QStandardPaths
            data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if data_dir:
                state_dir = Path(data_dir) / "CommandCore"
            else:
                state_dir = Path.home() / ".commandcore"
            
            state_dir.mkdir(parents=True, exist_ok=True)
            return state_dir / "app_state.json"
            
        except Exception:
            # Fallback
            return Path(__file__).parent.parent / "app_state.json"
    
    def _setup_default_validators(self):
        """Setup default validators for common state keys."""
        # Window geometry constraints
        self.validator.add_type_constraint("window.width", int)
        self.validator.add_type_constraint("window.height", int)
        self.validator.add_value_constraint("window.width", min_value=800, max_value=7680)
        self.validator.add_value_constraint("window.height", min_value=600, max_value=4320)
        
        # Theme constraints
        self.validator.add_type_constraint("ui.theme", str)
        self.validator.add_value_constraint("ui.theme", allowed_values=["dark", "light", "auto", "custom"])
        
        # Tab constraints - can be either int (index) or str (tab name)
        def validate_tab(value):
            return isinstance(value, (int, str))
        
        self.validator.add_validator("current_tab", validate_tab)
        
        # Performance constraints
        self.validator.add_type_constraint("performance.update_interval", int)
        self.validator.add_value_constraint("performance.update_interval", min_value=100, max_value=10000)
    
    @contextmanager
    def batch_update(self):
        """Context manager for batch state updates."""
        self.batch_mode = True
        self.batch_changes.clear()
        
        try:
            yield self
        finally:
            if self.batch_changes:
                self.state_batch_changed.emit(self.batch_changes.copy())
            
            self.batch_mode = False
            self.batch_changes.clear()
    
    def set_state(self, key: str, value: Any, scope: StateScope = StateScope.SESSION,
                  expires_in_seconds: Optional[int] = None, metadata: Dict[str, Any] = None) -> bool:
        """Set a state value with full options."""
        try:
            self.mutex.lock()
            
            # Validate the value
            is_valid, error_msg = self.validator.validate(key, value)
            if not is_valid:
                print(f"State validation failed for '{key}': {error_msg}")
                return False
            
            # Get old value for change notification
            old_value = self.state[key].value if key in self.state else None
            
            # Calculate expiration
            expires_at = None
            if expires_in_seconds is not None:
                from datetime import timedelta
                expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
            
            # Create state entry
            entry = StateEntry(
                key=key,
                value=value,
                scope=scope,
                timestamp=datetime.now(),
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            # Store state
            self.state[key] = entry
            
            # Track in history
            self._add_to_history(key, value, old_value)
            
            # Handle change notifications
            if self.batch_mode:
                self.batch_changes[key] = value
            else:
                self.state_changed.emit(key, value, old_value)
                if old_value is None:
                    self.state_added.emit(key, value)
                
                # Notify specific listeners
                self._notify_listeners(key, value, old_value)
            
            return True
            
        except Exception as e:
            print(f"Error setting state for '{key}': {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        try:
            self.mutex.lock()
            
            if key in self.state:
                entry = self.state[key]
                
                # Check if expired
                if entry.expires_at and datetime.now() > entry.expires_at:
                    del self.state[key]
                    return default
                
                return entry.value
            
            return default
            
        except Exception as e:
            print(f"Error getting state for '{key}': {e}")
            return default
        finally:
            self.mutex.unlock()
    
    def remove_state(self, key: str) -> bool:
        """Remove a state value."""
        try:
            self.mutex.lock()
            
            if key in self.state:
                del self.state[key]
                self.state_removed.emit(key)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error removing state for '{key}': {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def has_state(self, key: str) -> bool:
        """Check if a state key exists and is not expired."""
        try:
            self.mutex.lock()
            
            if key in self.state:
                entry = self.state[key]
                if entry.expires_at and datetime.now() > entry.expires_at:
                    del self.state[key]
                    return False
                return True
            
            return False
            
        finally:
            self.mutex.unlock()
    
    def get_state_info(self, key: str) -> Optional[StateEntry]:
        """Get full state entry information."""
        try:
            self.mutex.lock()
            return self.state.get(key)
        finally:
            self.mutex.unlock()
    
    def get_all_keys(self, scope: Optional[StateScope] = None) -> List[str]:
        """Get all state keys, optionally filtered by scope."""
        try:
            self.mutex.lock()
            
            keys = []
            for key, entry in self.state.items():
                # Check expiration
                if entry.expires_at and datetime.now() > entry.expires_at:
                    continue
                
                # Filter by scope
                if scope is None or entry.scope == scope:
                    keys.append(key)
            
            return keys
            
        finally:
            self.mutex.unlock()
    
    def clear_scope(self, scope: StateScope) -> int:
        """Clear all state in a specific scope."""
        try:
            self.mutex.lock()
            
            keys_to_remove = []
            for key, entry in self.state.items():
                if entry.scope == scope:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.state[key]
                self.state_removed.emit(key)
            
            return len(keys_to_remove)
            
        finally:
            self.mutex.unlock()
    
    def add_change_listener(self, key: str, callback: Callable[[str, Any, Any], None]):
        """Add a listener for changes to a specific key."""
        if key not in self.change_listeners:
            self.change_listeners[key] = []
        self.change_listeners[key].append(callback)
    
    def remove_change_listener(self, key: str, callback: Callable[[str, Any, Any], None]):
        """Remove a change listener."""
        if key in self.change_listeners:
            try:
                self.change_listeners[key].remove(callback)
                if not self.change_listeners[key]:
                    del self.change_listeners[key]
            except ValueError:
                pass
    
    def _notify_listeners(self, key: str, new_value: Any, old_value: Any):
        """Notify registered listeners of state changes."""
        if key in self.change_listeners:
            for callback in self.change_listeners[key]:
                try:
                    callback(key, new_value, old_value)
                except Exception as e:
                    print(f"Error in state change listener: {e}")
    
    def _add_to_history(self, key: str, new_value: Any, old_value: Any):
        """Add change to history for undo functionality."""
        if len(self.state_history) >= self.max_history_size:
            self.state_history.pop(0)
        
        self.state_history.append({
            'key': key,
            'new_value': new_value,
            'old_value': old_value,
            'timestamp': datetime.now()
        })
    
    def undo_last_change(self) -> bool:
        """Undo the last state change."""
        if not self.state_history:
            return False
        
        try:
            last_change = self.state_history.pop()
            key = last_change['key']
            old_value = last_change['old_value']
            
            if old_value is None:
                self.remove_state(key)
            else:
                # Temporarily disable history to avoid circular undo
                history_backup = self.state_history.copy()
                self.state_history.clear()
                
                self.set_state(key, old_value)
                
                self.state_history = history_backup
            
            return True
            
        except Exception as e:
            print(f"Error during undo: {e}")
            return False
    
    def get_history(self, key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get state change history, optionally filtered by key."""
        if key is None:
            return self.state_history.copy()
        
        return [change for change in self.state_history if change['key'] == key]
    
    def _cleanup_expired_state(self):
        """Clean up expired temporary state."""
        try:
            self.mutex.lock()
            
            current_time = datetime.now()
            expired_keys = []
            
            for key, entry in self.state.items():
                if entry.expires_at and current_time > entry.expires_at:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.state[key]
                self.state_removed.emit(key)
            
            if expired_keys:
                print(f"Cleaned up {len(expired_keys)} expired state entries")
                
        except Exception as e:
            print(f"Error during state cleanup: {e}")
        finally:
            self.mutex.unlock()
    
    def save_state(self) -> bool:
        """Save persistent state to file."""
        try:
            self.mutex.lock()
            
            # Filter persistent state
            persistent_state = {}
            for key, entry in self.state.items():
                if entry.scope == StateScope.PERSISTENT:
                    # Check expiration
                    if entry.expires_at is None or datetime.now() <= entry.expires_at:
                        persistent_state[key] = {
                            'value': entry.value,
                            'timestamp': entry.timestamp.isoformat(),
                            'expires_at': entry.expires_at.isoformat() if entry.expires_at else None,
                            'metadata': entry.metadata
                        }
            
            # Save to file
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(persistent_state, f, indent=2, default=str)
            
            print(f"Saved {len(persistent_state)} persistent state entries")
            return True
            
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def load_state(self) -> bool:
        """Load persistent state from file."""
        try:
            if not self.state_file.exists():
                return True  # No state file is okay
            
            self.mutex.lock()
            
            with open(self.state_file, 'r', encoding='utf-8') as f:
                persistent_state = json.load(f)
            
            current_time = datetime.now()
            loaded_count = 0
            
            for key, data in persistent_state.items():
                try:
                    # Parse timestamps
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    expires_at = None
                    if data.get('expires_at'):
                        expires_at = datetime.fromisoformat(data['expires_at'])
                        
                        # Skip if expired
                        if current_time > expires_at:
                            continue
                    
                    # Create state entry
                    entry = StateEntry(
                        key=key,
                        value=data['value'],
                        scope=StateScope.PERSISTENT,
                        timestamp=timestamp,
                        expires_at=expires_at,
                        metadata=data.get('metadata', {})
                    )
                    
                    self.state[key] = entry
                    loaded_count += 1
                    
                except Exception as e:
                    print(f"Error loading state entry '{key}': {e}")
                    continue
            
            print(f"Loaded {loaded_count} persistent state entries")
            return True
            
        except Exception as e:
            print(f"Error loading state: {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def _auto_save(self):
        """Auto-save persistent state."""
        if self.auto_save_enabled:
            self.save_state()
    
    def export_state(self, file_path: Path, include_session: bool = False) -> bool:
        """Export state to a file."""
        try:
            self.mutex.lock()
            
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'version': '1.0',
                    'include_session': include_session
                },
                'state': {}
            }
            
            for key, entry in self.state.items():
                # Skip expired entries
                if entry.expires_at and datetime.now() > entry.expires_at:
                    continue
                
                # Filter by scope
                if not include_session and entry.scope == StateScope.SESSION:
                    continue
                
                export_data['state'][key] = {
                    'value': entry.value,
                    'scope': entry.scope.value,
                    'timestamp': entry.timestamp.isoformat(),
                    'expires_at': entry.expires_at.isoformat() if entry.expires_at else None,
                    'metadata': entry.metadata
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error exporting state: {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def import_state(self, file_path: Path, overwrite: bool = False) -> bool:
        """Import state from a file."""
        try:
            self.mutex.lock()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'state' not in import_data:
                return False
            
            imported_count = 0
            current_time = datetime.now()
            
            for key, data in import_data['state'].items():
                try:
                    # Check if key exists and overwrite setting
                    if key in self.state and not overwrite:
                        continue
                    
                    # Parse data
                    scope = StateScope(data.get('scope', 'session'))
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    expires_at = None
                    if data.get('expires_at'):
                        expires_at = datetime.fromisoformat(data['expires_at'])
                        
                        # Skip if expired
                        if current_time > expires_at:
                            continue
                    
                    # Validate value
                    value = data['value']
                    is_valid, error_msg = self.validator.validate(key, value)
                    if not is_valid:
                        print(f"Skipping invalid imported value for '{key}': {error_msg}")
                        continue
                    
                    # Create state entry
                    entry = StateEntry(
                        key=key,
                        value=value,
                        scope=scope,
                        timestamp=timestamp,
                        expires_at=expires_at,
                        metadata=data.get('metadata', {})
                    )
                    
                    self.state[key] = entry
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Error importing state entry '{key}': {e}")
                    continue
            
            print(f"Imported {imported_count} state entries")
            return True
            
        except Exception as e:
            print(f"Error importing state: {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get state manager statistics."""
        try:
            self.mutex.lock()
            
            stats = {
                'total_entries': len(self.state),
                'by_scope': {},
                'expired_entries': 0,
                'history_size': len(self.state_history),
                'listeners_count': sum(len(listeners) for listeners in self.change_listeners.values()),
                'state_file': str(self.state_file),
                'auto_save_enabled': self.auto_save_enabled
            }
            
            current_time = datetime.now()
            
            for scope in StateScope:
                stats['by_scope'][scope.value] = 0
            
            for entry in self.state.values():
                stats['by_scope'][entry.scope.value] += 1
                
                if entry.expires_at and current_time > entry.expires_at:
                    stats['expired_entries'] += 1
            
            return stats
            
        finally:
            self.mutex.unlock()
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop timers
            if self.cleanup_timer.isActive():
                self.cleanup_timer.stop()
            
            if self.auto_save_timer.isActive():
                self.auto_save_timer.stop()
            
            # Save state one last time
            self.save_state()
            
            # Clear listeners
            self.change_listeners.clear()
            
            print("AppStateManager cleanup completed")
            
        except Exception as e:
            print(f"Error during AppStateManager cleanup: {e}")


# Global state manager instance
_state_manager: Optional[AppStateManager] = None

def get_state_manager() -> AppStateManager:
    """Get the global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = AppStateManager()
    return _state_manager

def cleanup_state_manager():
    """Clean up the global state manager."""
    global _state_manager
    if _state_manager is not None:
        _state_manager.cleanup()
        _state_manager = None
