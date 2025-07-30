"""
CommandCore Launcher - Modern Edition

A comprehensive, modern application launcher and management suite for the
CommandCore ecosystem. Built with cutting-edge technologies and modern
design principles.

Features:
- Beautiful, modern UI with customizable themes
- Real-time system monitoring with advanced charts
- Comprehensive application management
- Intelligent configuration system
- Advanced logging and debugging
- Modern notification system
- State management with persistence
- Cross-platform compatibility

Author: Outback Electronics
License: MIT
Version: 2.0.0
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Version information
__version__ = "2.0.0"
__author__ = "Outback Electronics"
__email__ = "support@outbackelectronics.com"
__license__ = "MIT"
__description__ = "Modern launcher and manager for CommandCore applications"
__url__ = "https://github.com/outback-electronics/commandcore-launcher"

# Minimum Python version check
MIN_PYTHON_VERSION = (3, 8)
if sys.version_info < MIN_PYTHON_VERSION:
    raise RuntimeError(
        f"CommandCore Launcher requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} "
        f"or higher. You are running Python {sys.version_info[0]}.{sys.version_info[1]}."
    )

# Package information
__all__ = [
    # Version info
    '__version__', '__author__', '__email__', '__license__',
    '__description__', '__url__',
    
    # Main components
    'CommandCoreLauncher', 'main',
    
    # Configuration
    'ConfigManager', 'get_config',
    
    # State management
    'AppStateManager', 'get_state_manager',
    
    # Notifications
    'NotificationManager', 'get_notification_manager', 'show_notification',
    
    # Logging
    'setup_logging', 'get_logging_manager',
    
    # Theme management
    'ThemeManager',
    
    # Utilities
    'get_app_info', 'check_dependencies', 'get_system_info'
]

# Import main components (with error handling for missing dependencies)
try:
    from main import CommandCoreLauncher, main
except ImportError as e:
    print(f"Warning: Could not import main components: {e}")
    CommandCoreLauncher = None
    main = None

try:
    from config import ConfigManager, get_config
except ImportError as e:
    print(f"Warning: Could not import config components: {e}")
    ConfigManager = None
    get_config = None

try:
    from app_state import AppStateManager, get_state_manager
except ImportError as e:
    print(f"Warning: Could not import state management: {e}")
    AppStateManager = None
    get_state_manager = None

try:
    from notification_manager import (
        NotificationManager, get_notification_manager, show_notification
    )
except ImportError as e:
    print(f"Warning: Could not import notification system: {e}")
    NotificationManager = None
    get_notification_manager = None
    show_notification = None

try:
    from logging_setup import setup_logging, get_logging_manager
except ImportError as e:
    print(f"Warning: Could not import logging utilities: {e}")
    setup_logging = None
    get_logging_manager = None

try:
    from theme_manager import ThemeManager
except ImportError as e:
    print(f"Warning: Could not import theme manager: {e}")
    ThemeManager = None

# Application metadata
APP_INFO = {
    'name': 'CommandCore Launcher',
    'version': __version__,
    'description': __description__,
    'author': __author__,
    'license': __license__,
    'url': __url__,
    'python_requires': f'>={MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}',
    'platforms': ['Windows', 'macOS', 'Linux'],
    'gui_framework': 'PySide6',
    'architecture': 'Modern MVP with Qt integration'
}

def get_app_info() -> Dict[str, Any]:
    """Get comprehensive application information."""
    info = APP_INFO.copy()
    
    # Add runtime information
    info.update({
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': sys.platform,
        'executable': sys.executable,
        'installation_path': str(Path(__file__).parent.absolute()),
    })
    
    # Add Qt information if available
    try:
        from PySide6 import __version__ as pyside_version
        info['pyside6_version'] = pyside_version
    except ImportError:
        info['pyside6_version'] = 'Not available'
    
    # Add dependency versions
    dependencies = {}
    dep_modules = [
        ('psutil', 'System monitoring'),
        ('git', 'Git integration'),
        ('json', 'JSON handling'),
        ('pathlib', 'Path handling'),
        ('dataclasses', 'Data structures'),
        ('typing', 'Type hints'),
        ('enum', 'Enumerations'),
    ]
    
    for module_name, description in dep_modules:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'Unknown')
            dependencies[module_name] = {
                'version': version,
                'description': description,
                'available': True
            }
        except ImportError:
            dependencies[module_name] = {
                'version': None,
                'description': description,
                'available': False
            }
    
    info['dependencies'] = dependencies
    
    return info

def check_dependencies() -> Dict[str, Any]:
    """Check if all required dependencies are available."""
    results = {
        'all_available': True,
        'missing': [],
        'available': [],
        'warnings': []
    }
    
    # Required dependencies
    required_deps = [
        ('PySide6', 'GUI framework'),
        ('psutil', 'System monitoring'),
    ]
    
    # Optional dependencies
    optional_deps = [
        ('git', 'Version control integration'),
        ('matplotlib', 'Advanced charting'),
        ('plotly', 'Interactive charts'),
    ]
    
    # Check required dependencies
    for dep_name, description in required_deps:
        try:
            __import__(dep_name)
            results['available'].append({
                'name': dep_name,
                'description': description,
                'required': True
            })
        except ImportError:
            results['missing'].append({
                'name': dep_name,
                'description': description,
                'required': True
            })
            results['all_available'] = False
    
    # Check optional dependencies
    for dep_name, description in optional_deps:
        try:
            __import__(dep_name)
            results['available'].append({
                'name': dep_name,
                'description': description,
                'required': False
            })
        except ImportError:
            results['warnings'].append({
                'name': dep_name,
                'description': description,
                'message': f'Optional dependency {dep_name} not available. {description} features may be limited.'
            })
    
    return results

def get_system_info() -> Dict[str, Any]:
    """Get system information for diagnostics."""
    info = {
        'platform': {
            'system': sys.platform,
            'machine': None,
            'processor': None,
            'python_implementation': sys.implementation.name,
        },
        'memory': {},
        'disk': {},
        'environment': {},
    }
    
    # Platform details
    try:
        import platform
        info['platform'].update({
            'machine': platform.machine(),
            'processor': platform.processor(),
            'system_name': platform.system(),
            'system_release': platform.release(),
            'system_version': platform.version(),
        })
    except Exception:
        pass
    
    # Memory information
    try:
        import psutil
        memory = psutil.virtual_memory()
        info['memory'] = {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'used_percent': memory.percent,
        }
    except Exception:
        pass
    
    # Disk information
    try:
        import psutil
        disk = psutil.disk_usage('/')
        info['disk'] = {
            'total_gb': round(disk.total / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'used_percent': round((disk.used / disk.total) * 100, 1),
        }
    except Exception:
        pass
    
    # Environment variables (selective)
    env_vars = ['PATH', 'HOME', 'USER', 'USERPROFILE', 'APPDATA', 'XDG_CONFIG_HOME']
    for var in env_vars:
        if var in os.environ:
            info['environment'][var] = os.environ[var]
    
    return info

def print_info():
    """Print application information to console."""
    print(f"\n{'='*60}")
    print(f"  {APP_INFO['name']} v{APP_INFO['version']}")
    print(f"  {APP_INFO['description']}")
    print(f"{'='*60}")
    
    # Dependencies check
    deps = check_dependencies()
    if deps['all_available']:
        print("✓ All required dependencies are available")
    else:
        print("✗ Missing required dependencies:")
        for dep in deps['missing']:
            print(f"  - {dep['name']}: {dep['description']}")
    
    if deps['warnings']:
        print("\nWarnings:")
        for warning in deps['warnings']:
            print(f"  ! {warning['message']}")
    
    print(f"\nPython: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Installation: {Path(__file__).parent.absolute()}")
    print("")

def quick_start():
    """Quick start function for immediate application launch."""
    try:
        if main is not None:
            return main()
        else:
            print("Error: Main application not available. Check dependencies.")
            return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1

# Development and debugging utilities
if __name__ == "__main__":
    # When run as a module, print info and optionally start the app
    import argparse
    
    parser = argparse.ArgumentParser(description="CommandCore Launcher")
    parser.add_argument('--info', action='store_true', help='Show application information')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--system-info', action='store_true', help='Show system information')
    parser.add_argument('--start', action='store_true', help='Start the application')
    
    args = parser.parse_args()
    
    if args.info or not any(vars(args).values()):
        print_info()
    
    if args.check_deps:
        deps = check_dependencies()
        print("\nDependency Check Results:")
        print(f"Available: {len(deps['available'])}")
        print(f"Missing: {len(deps['missing'])}")
        print(f"Warnings: {len(deps['warnings'])}")
    
    if args.system_info:
        system_info = get_system_info()
        print("\nSystem Information:")
        print(f"Platform: {system_info['platform']['system_name']} {system_info['platform']['system_release']}")
        if system_info['memory']:
            print(f"Memory: {system_info['memory']['total_gb']} GB total, {system_info['memory']['available_gb']} GB available")
        if system_info['disk']:
            print(f"Disk: {system_info['disk']['total_gb']} GB total, {system_info['disk']['free_gb']} GB free")
    
    if args.start:
        sys.exit(quick_start())