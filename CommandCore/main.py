#!/usr/bin/env python3
"""
CommandCore Launcher - Modernized Version - FIXED RESPONSIVE DESIGN

A modern, scalable launcher application for the CommandCore suite with improved
responsive design, proper window management, and better error handling.
"""

import sys
import os
import signal
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import traceback

# Ensure PySide6 is available before importing
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QWidget, 
        QTabWidget, QMessageBox, QSystemTrayIcon, QMenu,
        QSizePolicy, QSplashScreen
    )
    from PySide6.QtCore import (
        Qt, QTimer, QThread, Signal, QObject, QEvent,
        QPropertyAnimation, QEasingCurve, QSettings, QStandardPaths,
        QSize, QRect
    )
    from PySide6.QtGui import QIcon, QPixmap, QAction, QPalette, QColor, QScreen
except ImportError as e:
    print(f"Error: PySide6 not found. Please install with: pip install PySide6")
    print(f"Import error: {e}")
    sys.exit(1)

# Import local modules with error handling
try:
    from config import ConfigManager
    from splash_screen import ModernSplashScreen
    from theme_manager import ThemeManager
    from dashboard_tab import DashboardTab
    from application_manager_tab import ApplicationManagerTab
    from system_status_tab import SystemStatusTab
    from settings_tab import SettingsTab
    from app_state import AppStateManager, StateScope
    from notification_manager import NotificationManager
    from logging_setup import setup_logging
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all required files are present in the application directory.")
    sys.exit(1)


@dataclass
class AppMetadata:
    """Application metadata container."""
    name: str = "CommandCore Launcher"
    version: str = "2.0.0"
    organization: str = "Outback Electronics"
    description: str = "Modern launcher for CommandCore applications"


class ResponsiveWidget(QWidget):
    """Base widget class with responsive design capabilities."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_width = 800
        self.min_height = 600
        self.preferred_width = 1200
        self.preferred_height = 800
        
    def setSizePolicy(self, horizontal, vertical):
        """Override to set responsive size policy."""
        super().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def sizeHint(self):
        """Provide responsive size hint."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.availableGeometry().size()
            # Use 80% of screen size, but respect minimum
            width = max(self.min_width, min(self.preferred_width, int(screen_size.width() * 0.8)))
            height = max(self.min_height, min(self.preferred_height, int(screen_size.height() * 0.8)))
            return QSize(width, height)
        return QSize(self.preferred_width, self.preferred_height)
    
    def minimumSizeHint(self):
        """Provide minimum size hint."""
        return QSize(self.min_width, self.min_height)


class CommandCoreLauncher(QMainWindow):
    """
    Modern CommandCore Launcher with responsive design and improved functionality.
    
    Features:
    - Responsive UI that adapts to screen size
    - Improved window management
    - Better error handling
    - Resource-efficient operations
    """
    
    # Signals
    app_closing = Signal()
    theme_changed = Signal(str)
    tab_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components with error handling
        try:
            self.metadata = AppMetadata()
            self._is_closing = False
            self._force_quit = False  # Flag to force quit from system tray
            self._splash_screen: Optional[ModernSplashScreen] = None
            
            # Initialize managers with validation
            self.config = None
            self.state_manager = None
            self.theme_manager = None
            self.notification_manager = None
            
            # UI components
            self.tab_widget: Optional[QTabWidget] = None
            self.system_tray: Optional[QSystemTrayIcon] = None
            self.tabs: Dict[str, QWidget] = {}
            
            # Initialize components
            self._initialize_components()
            
            # Setup logging
            self.logger = setup_logging(
                name=self.__class__.__name__,
                level=self.config.get('logging.level', 'INFO') if self.config else 'INFO'
            )
            
            # Initialize application
            self._setup_application()
            self._setup_ui()
            self._setup_connections()
            self._setup_system_tray()
            
            # Apply initial theme
            if self.theme_manager:
                theme_name = self.config.get('ui.theme', 'dark') if self.config else 'dark'
                self.theme_manager.apply_theme(theme_name)
            
            self.logger.info("CommandCore Launcher initialized successfully")
            
        except Exception as e:
            print(f"Critical error during initialization: {e}")
            traceback.print_exc()
            self._show_critical_error("Initialization Error", 
                                    f"Failed to initialize application: {str(e)}")
    
    def _initialize_components(self):
        """Initialize core components with error handling."""
        try:
            # Initialize configuration manager
            self.config = ConfigManager()
            if not self.config:
                raise RuntimeError("Failed to initialize configuration manager")
            
            # Initialize state manager
            self.state_manager = AppStateManager()
            if not self.state_manager:
                raise RuntimeError("Failed to initialize state manager")
            
            # Initialize theme manager
            self.theme_manager = ThemeManager()
            if not self.theme_manager:
                raise RuntimeError("Failed to initialize theme manager")
            
            # Initialize notification manager
            self.notification_manager = NotificationManager()
            if not self.notification_manager:
                raise RuntimeError("Failed to initialize notification manager")
                
        except Exception as e:
            print(f"Error initializing components: {e}")
            # Create minimal fallback configuration
            self.config = None
            self.state_manager = None
            self.theme_manager = None
            self.notification_manager = None
    
    def _show_critical_error(self, title: str, message: str):
        """Show critical error message and exit."""
        try:
            QMessageBox.critical(None, title, message)
        except Exception:
            print(f"CRITICAL ERROR - {title}: {message}")
        sys.exit(1)
    
    def _setup_application(self):
        """Setup application properties and window configuration with responsive design."""
        try:
            self.setWindowTitle(f"{self.metadata.name} v{self.metadata.version}")
            
            # Get screen information for responsive sizing
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                screen_width = screen_geometry.width()
                screen_height = screen_geometry.height()
                
                # Calculate responsive dimensions
                if screen_width >= 1920 and screen_height >= 1080:
                    # Large screens - use larger default size
                    default_width = 1400
                    default_height = 900
                elif screen_width >= 1366 and screen_height >= 768:
                    # Medium screens - standard size
                    default_width = 1200
                    default_height = 800
                else:
                    # Small screens - compact size
                    default_width = min(1000, int(screen_width * 0.9))
                    default_height = min(700, int(screen_height * 0.9))
                
                # Set minimum size based on screen
                min_width = min(800, int(screen_width * 0.6))
                min_height = min(600, int(screen_height * 0.6))
                
                self.setMinimumSize(min_width, min_height)
                self.resize(default_width, default_height)
                
                # Check if we should start maximized
                start_maximized = self.config.get('ui.start_maximized', False) if self.config else False
                if start_maximized or (screen_width < 1366 or screen_height < 768):
                    # Start maximized on small screens or if configured
                    QTimer.singleShot(100, self.showMaximized)
            else:
                # Fallback if no screen info
                self.setMinimumSize(800, 600)
                self.resize(1200, 800)
            
            # Set window icon
            icon_paths = [
                Path(__file__).parent / 'assets' / 'icons' / 'app_icon.png',
                Path(__file__).parent / 'CommandCore.png',
                Path(__file__).parent / 'assets' / 'CommandCore.png'
            ]
            
            for icon_path in icon_paths:
                if icon_path.exists():
                    self.setWindowIcon(QIcon(str(icon_path)))
                    break
            
            # Center window if not maximized
            if not self.isMaximized():
                self._center_on_screen()
            
            # Setup window properties
            self.setWindowFlags(Qt.Window)
            self.setAttribute(Qt.WA_DeleteOnClose, True)
            
            # Restore window state if available
            self._restore_window_state()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error setting up application: {e}")
            else:
                print(f"Error setting up application: {e}")
    
    def _center_on_screen(self):
        """Center the window on the primary screen."""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                window_geometry = self.geometry()
                x = (screen_geometry.width() - window_geometry.width()) // 2
                y = (screen_geometry.height() - window_geometry.height()) // 2
                self.move(max(0, x), max(0, y))
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error centering window: {e}")
    
    def _restore_window_state(self):
        """Restore window state from previous session."""
        try:
            if not self.state_manager:
                return
                
            if self.config and self.config.get('ui.remember_window_state', True):
                # Restore window geometry
                geometry_data = self.state_manager.get_state('window_geometry')
                if geometry_data:
                    self.restoreGeometry(geometry_data)
                
                # Restore window state
                state_data = self.state_manager.get_state('window_state')
                if state_data:
                    self.restoreState(state_data)
                    
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not restore window state: {e}")
    
    def _setup_ui(self):
        """Setup the main user interface with responsive design."""
        try:
            # Create central widget with responsive properties
            central_widget = ResponsiveWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout with proper spacing
            layout = QVBoxLayout(central_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Create tab widget with responsive properties
            self.tab_widget = QTabWidget()
            self.tab_widget.setDocumentMode(True)
            self.tab_widget.setTabsClosable(False)
            self.tab_widget.setMovable(True)
            
            # Set responsive size policy
            self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Apply responsive styling
            self._apply_responsive_styling()
            
            layout.addWidget(self.tab_widget)
            
            # Load tabs
            self._load_tabs()
            
        except Exception as e:
            error_msg = f"Failed to setup UI: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            QMessageBox.critical(self, "Initialization Error", error_msg)
    
    def _apply_responsive_styling(self):
        """Apply responsive styling to the tab widget."""
        try:
            # Get screen size for responsive design
            screen = QApplication.primaryScreen()
            if screen:
                screen_width = screen.availableGeometry().width()
                
                # Adjust tab styling based on screen size
                if screen_width >= 1920:
                    # Large screens
                    tab_height = 45
                    font_size = 12
                    padding = "12px 20px"
                elif screen_width >= 1366:
                    # Medium screens
                    tab_height = 40
                    font_size = 11
                    padding = "10px 16px"
                else:
                    # Small screens
                    tab_height = 35
                    font_size = 10
                    padding = "8px 12px"
                
                self.tab_widget.setStyleSheet(f"""
                    QTabWidget::pane {{
                        border: 1px solid #37414F;
                        border-radius: 8px;
                        background-color: #2A2F42;
                        margin-top: 2px;
                    }}
                    
                    QTabBar::tab {{
                        background-color: #353A4F;
                        color: #B0BEC5;
                        padding: {padding};
                        border: 1px solid #37414F;
                        border-bottom: none;
                        border-top-left-radius: 6px;
                        border-top-right-radius: 6px;
                        margin-right: 2px;
                        min-width: 80px;
                        min-height: {tab_height}px;
                        font-size: {font_size}px;
                        font-weight: 500;
                    }}
                    
                    QTabBar::tab:selected {{
                        background-color: #2A2F42;
                        color: #FFFFFF;
                        border-bottom: 1px solid #2A2F42;
                        margin-bottom: -1px;
                    }}
                    
                    QTabBar::tab:hover:!selected {{
                        background-color: #3E4358;
                        color: #FFFFFF;
                    }}
                """)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error applying responsive styling: {e}")
    
    def _load_tabs(self):
        """Load and initialize all application tabs with responsive design."""
        tab_configs = [
            {
                'name': 'Dashboard',
                'class': DashboardTab,
                'icon': 'dashboard.svg',
                'tooltip': 'Main dashboard and overview'
            },
            {
                'name': 'Applications',
                'class': ApplicationManagerTab,
                'icon': 'apps.svg',
                'tooltip': 'Manage CommandCore applications'
            },
            {
                'name': 'System Status',
                'class': SystemStatusTab,
                'icon': 'system.svg',
                'tooltip': 'Monitor system resources'
            },
            {
                'name': 'Settings',
                'class': SettingsTab,
                'icon': 'settings.svg',
                'tooltip': 'Configure application settings'
            }
        ]
        
        for tab_config in tab_configs:
            try:
                # Create tab instance with proper error handling
                tab_class = tab_config['class']
                tab_instance = None
                
                if tab_class == SettingsTab:
                    if self.config and self.theme_manager:
                        tab_instance = tab_class(self.config, self.theme_manager)
                elif self.config:
                    tab_instance = tab_class(self.config)
                
                if tab_instance is None:
                    # Create fallback tab
                    tab_instance = ResponsiveWidget()
                    layout = QVBoxLayout(tab_instance)
                    error_label = QLabel(f"Error loading {tab_config['name']} tab")
                    error_label.setAlignment(Qt.AlignCenter)
                    error_label.setStyleSheet("""
                        QLabel {
                            color: #F44336;
                            font-size: 16px;
                            font-weight: bold;
                        }
                    """)
                    layout.addWidget(error_label)
                
                # Set responsive properties
                if hasattr(tab_instance, 'setSizePolicy'):
                    tab_instance.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                # Add to tab widget
                icon_paths = [
                    Path(__file__).parent / 'assets' / 'icons' / tab_config['icon'],
                    Path(__file__).parent / f"{tab_config['icon']}"
                ]
                
                icon = QIcon()
                for icon_path in icon_paths:
                    if icon_path.exists():
                        icon = QIcon(str(icon_path))
                        break
                
                index = self.tab_widget.addTab(tab_instance, icon, tab_config['name'])
                self.tab_widget.setTabToolTip(index, tab_config['tooltip'])
                
                # Store reference
                self.tabs[tab_config['name']] = tab_instance
                
                if self.logger:
                    self.logger.debug(f"Loaded tab: {tab_config['name']}")
                
            except Exception as e:
                error_msg = f"Error loading tab {tab_config['name']}: {e}"
                if self.logger:
                    self.logger.error(error_msg)
                
                # Add error placeholder tab
                placeholder = ResponsiveWidget()
                layout = QVBoxLayout(placeholder)
                error_label = QLabel(f"Failed to load {tab_config['name']}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
                layout.addWidget(error_label)
                
                index = self.tab_widget.addTab(placeholder, tab_config['name'])
                self.tabs[tab_config['name']] = placeholder
    
    def _setup_connections(self):
        """Setup signal connections between components."""
        try:
            # Tab widget connections
            if self.tab_widget:
                self.tab_widget.currentChanged.connect(self._on_tab_changed)
            
            # Dashboard connections
            if 'Dashboard' in self.tabs:
                dashboard = self.tabs['Dashboard']
                if hasattr(dashboard, 'tab_requested'):
                    dashboard.tab_requested.connect(self.switch_to_tab)
                if hasattr(dashboard, 'app_launch_requested'):
                    dashboard.app_launch_requested.connect(self._on_app_launch_requested)
            
            # Settings connections
            if 'Settings' in self.tabs:
                settings = self.tabs['Settings']
                if hasattr(settings, 'theme_changed'):
                    settings.theme_changed.connect(self._on_theme_changed)
                if hasattr(settings, 'settings_saved'):
                    settings.settings_saved.connect(self._on_settings_saved)
            
            # Application manager connections
            if 'Applications' in self.tabs:
                app_manager = self.tabs['Applications']
                if hasattr(app_manager, 'app_status_changed'):
                    app_manager.app_status_changed.connect(self._on_app_status_changed)
            
            # State manager connections
            if self.state_manager:
                self.state_manager.state_changed.connect(self._on_state_changed)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error setting up connections: {e}")
    
    def _setup_system_tray(self):
        """Setup system tray integration."""
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                if self.logger:
                    self.logger.warning("System tray not available")
                return
            
            # Create system tray icon
            self.system_tray = QSystemTrayIcon(self)
            
            # Set icon
            icon_paths = [
                Path(__file__).parent / 'assets' / 'icons' / 'tray_icon.png',
                Path(__file__).parent / 'CommandCore.png'
            ]
            
            icon_set = False
            for icon_path in icon_paths:
                if icon_path.exists():
                    self.system_tray.setIcon(QIcon(str(icon_path)))
                    icon_set = True
                    break
            
            if not icon_set:
                self.system_tray.setIcon(self.windowIcon())
            
            # Create context menu
            self._create_tray_menu()
            
            # Connect signals
            self.system_tray.activated.connect(self._on_tray_activated)
            
            # Show tray icon
            self.system_tray.show()
            
            if self.logger:
                self.logger.info("System tray setup completed")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error setting up system tray: {e}")
    
    def _create_tray_menu(self):
        """Create the system tray context menu."""
        try:
            tray_menu = QMenu()
            
            # Show/Hide action
            show_action = QAction("Show CommandCore", self)
            show_action.triggered.connect(self.show_normal)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            # Quick launch actions for apps
            if 'Applications' in self.tabs:
                app_manager = self.tabs['Applications']
                if hasattr(app_manager, 'get_installed_apps'):
                    try:
                        apps = app_manager.get_installed_apps()
                        for app in apps[:5]:  # Limit to first 5 apps
                            app_name = app.get('name', 'Unknown')
                            app_id = app.get('id')
                            if app_id:
                                action = QAction(f"Launch {app_name}", self)
                                action.triggered.connect(
                                    lambda checked, aid=app_id: self._launch_app_from_tray(aid)
                                )
                                tray_menu.addAction(action)
                        
                        if len(apps) > 5:
                            tray_menu.addSeparator()
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Error creating app launch menu: {e}")
            
            # Settings action
            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(lambda: self.switch_to_tab("Settings"))
            tray_menu.addAction(settings_action)
            
            tray_menu.addSeparator()
            
            # Quit action
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.system_tray.setContextMenu(tray_menu)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating tray menu: {e}")
    
    def _on_tab_changed(self, index: int):
        """Handle tab change events."""
        try:
            if self.tab_widget and index >= 0:
                tab_name = self.tab_widget.tabText(index)
                if self.logger:
                    self.logger.debug(f"Switched to tab: {tab_name}")
                self.tab_changed.emit(tab_name)
                
                # Update state
                if self.state_manager:
                    self.state_manager.set_state('current_tab', tab_name)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling tab change: {e}")
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change events."""
        try:
            if self.theme_manager:
                self.theme_manager.apply_theme(theme_name)
                self.theme_changed.emit(theme_name)
                
                # Reapply responsive styling
                self._apply_responsive_styling()
                
                if self.logger:
                    self.logger.info(f"Theme changed to: {theme_name}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error changing theme: {e}")
    
    def _on_settings_saved(self, settings: Dict[str, Any]):
        """Handle settings save events."""
        try:
            if self.config:
                self.config.update_settings(settings)
                
                # Check if font settings changed
                if any(key.startswith('ui.font') for key in settings.keys()):
                    # Force theme reapplication to update fonts
                    if self.theme_manager:
                        current_theme = self.theme_manager.get_current_theme_name()
                        self.theme_manager.apply_theme(current_theme)
                
                if self.notification_manager:
                    self.notification_manager.show_notification(
                        "Settings Saved",
                        "Your settings have been saved successfully.",
                        "success"
                    )
                if self.logger:
                    self.logger.info("Settings saved successfully")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving settings: {e}")
            if self.notification_manager:
                self.notification_manager.show_notification(
                    "Settings Error",
                    f"Failed to save settings: {str(e)}",
                    "error"
                )
    
    def _on_app_launch_requested(self, app_id: str):
        """Handle application launch requests."""
        try:
            if 'Applications' in self.tabs:
                app_manager = self.tabs['Applications']
                if hasattr(app_manager, 'launch_application'):
                    app_manager.launch_application(app_id)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error launching app {app_id}: {e}")
    
    def _on_app_status_changed(self, app_id: str, status: str):
        """Handle application status changes."""
        try:
            if self.logger:
                self.logger.info(f"App {app_id} status changed to: {status}")
            
            # Update dashboard if visible
            if 'Dashboard' in self.tabs:
                dashboard = self.tabs['Dashboard']
                if hasattr(dashboard, 'update_app_status'):
                    dashboard.update_app_status(app_id, status)
            
            # Show notification for important status changes
            if status in ['started', 'stopped', 'crashed'] and self.notification_manager:
                app_name = app_id.replace('_', ' ').title()
                notification_type = "info" if status == "started" else "warning"
                if status == "crashed":
                    notification_type = "error"
                
                self.notification_manager.show_notification(
                    f"Application {status.title()}",
                    f"{app_name} has {status}",
                    notification_type
                )
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling app status change: {e}")
    
    def _on_state_changed(self, key: str, value: Any):
        """Handle application state changes."""
        try:
            if self.logger:
                self.logger.debug(f"State changed: {key} = {value}")
            
            # Handle specific state changes
            if key == 'window_state':
                if (value == 'minimized' and self.config and 
                    self.config.get('ui.minimize_to_tray', True)):
                    self.hide()
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling state change: {e}")
    
    def _on_tray_activated(self, reason):
        """Handle system tray activation."""
        try:
            if reason == QSystemTrayIcon.Trigger:
                if self.isVisible():
                    self.hide()
                else:
                    self.show_normal()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling tray activation: {e}")
    
    def _launch_app_from_tray(self, app_id: str):
        """Launch application from system tray menu."""
        try:
            self._on_app_launch_requested(app_id)
            self.show_normal()  # Show window after launching
            self.switch_to_tab("Applications")  # Switch to applications tab
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error launching app from tray: {e}")
    
    def switch_to_tab(self, tab_name: str):
        """Switch to the specified tab."""
        try:
            if not self.tab_widget:
                return
                
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == tab_name:
                    self.tab_widget.setCurrentIndex(i)
                    break
            else:
                if self.logger:
                    self.logger.warning(f"Tab not found: {tab_name}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error switching to tab {tab_name}: {e}")
    
    def show_normal(self):
        """Show and activate the window."""
        try:
            self.show()
            self.raise_()
            self.activateWindow()
            if self.isMinimized():
                self.showNormal()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error showing window: {e}")
    
    def show_splash_screen(self) -> Optional[ModernSplashScreen]:
        """Show the splash screen during startup."""
        try:
            self._splash_screen = ModernSplashScreen()
            self._splash_screen.show()
            return self._splash_screen
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error showing splash screen: {e}")
            return None
    
    def hide_splash_screen(self):
        """Hide the splash screen."""
        try:
            if self._splash_screen:
                self._splash_screen.finish(self)
                self._splash_screen = None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error hiding splash screen: {e}")
    
    def resizeEvent(self, event):
        """Handle resize events to maintain responsive design."""
        try:
            super().resizeEvent(event)
            
            # Update tab styling based on new size
            self._apply_responsive_styling()
            
            # Notify tabs of resize if they have a resize method
            for tab in self.tabs.values():
                if hasattr(tab, 'on_window_resized'):
                    tab.on_window_resized(event.size())
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling resize event: {e}")
    
    def changeEvent(self, event):
        """Handle window state changes."""
        try:
            if event.type() == QEvent.WindowStateChange:
                if self.state_manager:
                    if self.isMinimized():
                        self.state_manager.set_state('window_state', 'minimized')
                    elif self.isMaximized():
                        self.state_manager.set_state('window_state', 'maximized')
                    else:
                        self.state_manager.set_state('window_state', 'normal')
            super().changeEvent(event)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling window state change: {e}")
    
    def quit_application(self):
        """Quit the application when triggered from system tray."""
        self._force_quit = True
        self.close()
    
    def closeEvent(self, event):
        """Handle application close event with proper cleanup."""
        try:
            if self._is_closing:
                event.accept()
                return
            
            self._is_closing = True
            
            # Check if should close to tray (only if not force quitting)
            if (not self._force_quit and 
                self.config and self.config.get('ui.close_to_tray', False) and 
                self.system_tray and self.system_tray.isVisible()):
                self.hide()
                if self.notification_manager:
                    self.notification_manager.show_notification(
                        "CommandCore Launcher",
                        "Application minimized to system tray",
                        "info"
                    )
                self._is_closing = False
                event.ignore()
                return
            
            # Ask for confirmation if configured
            if self.config and self.config.get('ui.confirm_exit', True):
                reply = QMessageBox.question(
                    self,
                    "Confirm Exit",
                    "Are you sure you want to exit CommandCore Launcher?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    self._is_closing = False
                    event.ignore()
                    return
            
            # Emit closing signal
            self.app_closing.emit()
            
            # Save current state
            self._save_state()
            
            # Cleanup tabs
            self._cleanup_tabs()
            
            # Cleanup system tray
            if self.system_tray:
                self.system_tray.hide()
                self.system_tray = None
            
            # Hide splash screen if still visible
            self.hide_splash_screen()
            
            if self.logger:
                self.logger.info("CommandCore Launcher shutting down")
            event.accept()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during close: {e}")
            event.accept()  # Force close even on error
    
    def _save_state(self):
        """Save application state before closing."""
        try:
            if not self.state_manager:
                return
                
            # Save window geometry
            self.state_manager.set_state(
                'window_geometry',
                self.saveGeometry(),
                scope=StateScope.PERSISTENT
            )
            
            # Save window state
            self.state_manager.set_state(
                'window_state',
                self.saveState(),
                scope=StateScope.PERSISTENT
            )
            
            # Save current tab
            if self.tab_widget:
                self.state_manager.set_state(
                    'current_tab',
                    self.tab_widget.currentIndex(),
                    scope=StateScope.PERSISTENT
                )
            
            # Save the state to disk
            self.state_manager.save_state()
            if self.logger:
                self.logger.debug("Application state saved")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving state: {e}")
    
    def _cleanup_tabs(self):
        """Cleanup all tab resources."""
        try:
            for tab_name, tab_widget in self.tabs.items():
                try:
                    if hasattr(tab_widget, 'cleanup'):
                        tab_widget.cleanup()
                    tab_widget.setParent(None)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error cleaning up tab {tab_name}: {e}")
            
            self.tabs.clear()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during tab cleanup: {e}")


def setup_signal_handlers(app: QApplication):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down gracefully...")
        app.quit()
    
    # Register signal handlers (Unix/Linux only)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, signal_handler)


def validate_environment():
    """Validate the runtime environment."""
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"Python 3.8+ required. Current version: {sys.version}")
        return False
    
    # Check critical paths
    app_dir = Path(__file__).parent
    if not app_dir.exists():
        print(f"Application directory not found: {app_dir}")
        return False
    
    return True


def main():
    """Main entry point for the CommandCore Launcher."""
    # Validate environment first
    if not validate_environment():
        return 1
    
    # Enable high DPI support
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except AttributeError:
        # Older Qt versions may not have this method
        pass
    
    app = QApplication(sys.argv)
    
    # Set application metadata
    metadata = AppMetadata()
    app.setApplicationName(metadata.name)
    app.setApplicationDisplayName(metadata.name)
    app.setApplicationVersion(metadata.version)
    app.setOrganizationName(metadata.organization)
    
    # Setup signal handlers
    setup_signal_handlers(app)
    
    # Handle uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"Uncaught exception:\n{error_msg}")
        
        try:
            QMessageBox.critical(
                None,
                "Critical Error",
                f"An unexpected error occurred:\n\n{str(exc_value)}\n\nThe application will now exit."
            )
        except Exception:
            pass
    
    sys.excepthook = handle_exception
    
    try:
        # Create main window
        launcher = CommandCoreLauncher()
        
        # Show splash screen
        splash = launcher.show_splash_screen()
        if splash:
            app.processEvents()
        
        # Show main window after splash
        QTimer.singleShot(4000, lambda: [
            launcher.hide_splash_screen(),
            launcher.show()
        ])
        
        # Start event loop
        return app.exec()
        
    except Exception as e:
        error_msg = f"Critical error in main: {e}"
        print(error_msg)
        traceback.print_exc()
        
        try:
            QMessageBox.critical(
                None,
                "Critical Error",
                f"A critical error occurred during startup:\n{str(e)}\n\nThe application will now exit."
            )
        except Exception:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())