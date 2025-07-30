# CommandCore Launcher - Modern Edition

<div align="center">

![CommandCore Logo](assets/logo.png)

**A modern, feature-rich launcher for the CommandCore application suite**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/outback-electronics/commandcore-launcher)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![Qt](https://img.shields.io/badge/Qt-PySide6-red.svg)](https://pyside.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

</div>

## 🚀 Overview

CommandCore Launcher is a completely modernized, centralized management hub for the entire CommandCore application ecosystem. Built with cutting-edge technologies and modern design principles, it provides an intuitive interface for launching, monitoring, and managing all CommandCore applications.

## ✨ Key Features

### 🎨 Modern User Interface
- **Beautiful Dark Theme** with customizable colors and fonts
- **Smooth Animations** and transitions throughout the interface
- **Responsive Design** that adapts to different screen sizes
- **Live Theme Preview** with real-time customization
- **System Tray Integration** for background operation

### 📊 Advanced System Monitoring
- **Real-time Performance Charts** for CPU, memory, disk, and network
- **Process Management** with detailed resource tracking
- **System Information** display with hardware details
- **Performance Analytics** with historical data
- **Customizable Monitoring Intervals**

### 🔧 Comprehensive Application Management
- **Visual Application Cards** with status indicators
- **Advanced Process Monitoring** with resource usage
- **Bulk Operations** (start all, stop all applications)
- **Auto-restart Capabilities** for critical applications
- **Dependency Management** and startup ordering

### ⚙️ Intelligent Configuration
- **Type-safe Configuration** using modern Python dataclasses
- **Live Settings Preview** with instant feedback
- **Configuration Validation** with helpful error messages
- **Import/Export Settings** for easy backup and sharing
- **Environment Variable Override** support

### 🔔 Modern Notification System
- **Beautiful Notifications** with custom styling
- **Multiple Notification Types** (info, success, warning, error)
- **Configurable Positioning** and duration
- **Action Buttons** for interactive notifications
- **Notification History** and management

### 📈 State Management & Persistence
- **Centralized State Management** with automatic persistence
- **Hierarchical State Organization** with scoped storage
- **State Validation** and type checking
- **Change History** with undo functionality
- **Temporary State** with automatic expiration

### 🔍 Advanced Logging & Debugging
- **Structured JSON Logging** for better analysis
- **Colored Console Output** for development
- **File Rotation** with size and count limits
- **Performance Tracking** with timing metrics
- **Error Context** and stack trace capture

## 🏗️ Architecture

### Modern Design Patterns
- **MVP Architecture** with clear separation of concerns
- **Signal-Slot Communication** for loose coupling
- **Dependency Injection** for testability
- **Observer Pattern** for state changes
- **Strategy Pattern** for configurable behavior

### Core Components

```
CommandCore/
├── CommandCore.png         # Application icon
├── README.md               # This file
├── __init__.py             # Package initialization
├── app_state.py            # Application state management
├── application_manager_tab.py  # Application management UI
├── commandcore-launcher.desktop  # Linux desktop entry
├── config.py               # Configuration management
├── dashboard_tab.py        # Dashboard UI
├── logging_setup.py        # Logging configuration
├── main.py                 # Application entry point
├── notification_manager.py # Notification system
├── requirements.txt        # Python dependencies
├── settings_tab.py         # Settings UI
├── setup.py                # Installation script
├── splash_screen.py        # Splash screen implementation
├── system_status_tab.py    # System monitoring UI
└── theme_manager.py        # Theme management
```

## 🚀 Installation

### Prerequisites
- **Python 3.8+** (3.10+ recommended)
- **Qt6** libraries (installed via PySide6)
- **Git** (for version detection)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/outback-electronics/commandcore-launcher.git
   cd commandcore-launcher
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

### Development Installation

For development with additional tools:
```bash
pip install -r requirements.txt
pip install pytest pytest-qt black flake8 mypy
```

## 🎯 Usage

### First Launch
1. The application will show a **modern splash screen** with loading animation
2. **Dashboard** opens by default with system overview
3. Navigate between tabs using the **tab bar** at the top
4. **System tray icon** allows quick access when minimized

### Managing Applications
- **Application Manager** tab shows all CommandCore applications
- **Click cards** to view detailed information
- **Start/Stop** applications with visual feedback
- **Monitor resource usage** in real-time
- **Configure auto-restart** and other advanced options

### Customizing Appearance
- Go to **Settings > Appearance** tab
- **Choose themes** from the dropdown
- **Customize colors** with the color picker
- **Adjust fonts** and animation settings
- **Live preview** shows changes instantly

### System Monitoring
- **System Status** tab provides detailed monitoring
- **Performance charts** update in real-time
- **Process table** shows running applications
- **Export data** for analysis (coming soon)

## ⚙️ Configuration

### Configuration File
Settings are stored in a platform-appropriate location:
- **Windows:** `%APPDATA%/CommandCore/config.json`
- **macOS:** `~/Library/Application Support/CommandCore/config.json`
- **Linux:** `~/.config/commandcore/config.json`

### Environment Variables
Override settings using environment variables:
```bash
export COMMANDCORE_THEME=dark
export COMMANDCORE_LOG_LEVEL=DEBUG

## 📁 Directory Structure

```
CommandCore/
├── CommandCore.png         # Application icon
├── README.md               # This file
├── __init__.py             # Package initialization
├── app_state.py            # Application state management
├── application_manager_tab.py  # Application management UI
├── commandcore-launcher.desktop  # Linux desktop entry
├── config.py               # Configuration management
├── dashboard_tab.py        # Dashboard UI
├── logging_setup.py        # Logging configuration
├── main.py                 # Application entry point
├── notification_manager.py # Notification system
├── requirements.txt        # Python dependencies
├── settings_tab.py         # Settings UI
├── setup.py                # Installation script
├── splash_screen.py        # Splash screen implementation
├── system_status_tab.py    # System monitoring UI
└── theme_manager.py        # Theme management
```
export COMMANDCORE_DEBUG=true
```

### Advanced Configuration
```json
{
  "ui": {
    "theme": "dark",
    "font_family": "Segoe UI",
    "font_size": 10,
    "animation_enabled": true
  },
  "logging": {
    "level": "INFO",
    "file_enabled": true,
    "max_file_size_mb": 10
  },
  "application": {
    "auto_start_monitoring": false,
    "update_check_frequency": "weekly"
  }
}
```

## 🔧 Development

### Project Structure
```
CommandCore/
├── CommandCore.png         # Application icon
├── README.md               # This file
├── __init__.py             # Package initialization
├── app_state.py            # Application state management
├── application_manager_tab.py  # Application management UI
├── commandcore-launcher.desktop  # Linux desktop entry
├── config.py               # Configuration management
├── dashboard_tab.py        # Dashboard UI
├── logging_setup.py        # Logging configuration
├── main.py                 # Application entry point
├── notification_manager.py # Notification system
├── requirements.txt        # Python dependencies
├── settings_tab.py         # Settings UI
├── setup.py                # Installation script
├── splash_screen.py        # Splash screen implementation
├── system_status_tab.py    # System monitoring UI
└── theme_manager.py        # Theme management
```

### Code Style
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking
- **Docstrings** for all public functions
- **Type hints** for better IDE support

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

### Building Executables
```bash
# Using PyInstaller (cross-platform)
pyinstaller --windowed --onefile main.py

# Using cx_Freeze (Windows)
python setup.py build

# Using py2app (macOS)
python setup.py py2app
```

## 🛠️ Troubleshooting

### Common Issues

**Application won't start:**
- Check Python version (3.8+ required)
- Verify all dependencies are installed
- Check log files in `logs/` directory

**UI appears corrupted:**
- Try resetting configuration: `--reset-config`
- Update graphics drivers
- Try different theme in settings

**Performance issues:**
- Enable performance mode in settings
- Reduce animation duration
- Increase monitoring intervals

**Applications not detected:**
- Verify CommandCore applications are installed
- Check file permissions
- Review application paths in settings

### Log Files
Logs are stored in:
- **Windows:** `%APPDATA%/CommandCore/logs/`
- **macOS:** `~/Library/Application Support/CommandCore/logs/`
- **Linux:** `~/.config/commandcore/logs/`

### Debug Mode
Enable debug mode for detailed logging:
```bash
python main.py --debug
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Guidelines
- Follow PEP 8 style guide
- Add type hints to new functions
- Include docstrings for public APIs
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Qt/PySide6** for the excellent GUI framework
- **PSUtil** for system monitoring capabilities
- **GitPython** for version control integration
- **The Python Community** for amazing libraries and tools

## 📞 Support

- **Documentation:** [docs.commandcore.org](https://docs.commandcore.org)
- **Issues:** [GitHub Issues](https://github.com/outback-electronics/commandcore-launcher/issues)
- **Discussions:** [GitHub Discussions](https://github.com/outback-electronics/commandcore-launcher/discussions)
- **Email:** support@outbackelectronics.com

## 🔄 Changelog

### Version 2.0.0 (Latest)
- Complete modernization with new architecture
- Advanced system monitoring with real-time charts
- Modern UI with theme customization
- Comprehensive application management
- Intelligent configuration system
- Advanced logging and debugging
- State management with persistence
- Modern notification system

### Version 1.0.0
- Initial release
- Basic application launching
- Simple system monitoring
- Configuration management

---

<div align="center">

**Built with ❤️ by Outback Electronics**

[Website](https://outbackelectronics.com) • [Documentation](https://docs.commandcore.org) • [Support](mailto:support@outbackelectronics.com)

</div>