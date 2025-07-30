"""
CommandCore Launcher - Main Application Entry Point - ENHANCED VERSION

Modern, feature-rich launcher for the CommandCore application suite
with comprehensive fixes for startup, system tray, and theme management.
"""

import sys
import signal
import logging
import traceback
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QTabWidget, QStatusBar, QSystemTrayIcon,
    QMenu, QMessageBox, QSplashScreen, QLabel
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QAction

# Import application components
try:
    from splash_screen import ModernSplashScreen
    from config import ConfigManager
    from theme_manager import ThemeManager
    from app_state import AppStateManager, StateScope
    from notification_manager import NotificationManager
    from logging_setup import setup_logging
    from update_checker import UpdateChecker, initialize_update_checker
    
    # Import tab components
    from dashboard_tab import DashboardTab
    from application_manager_tab import ApplicationManagerTab
    from system_status_tab import SystemStatusTab
    from settings_tab import SettingsTab
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


@dataclass
class AppMetadata:
    """Application metadata and information."""
    name: str = "CommandCore Launcher"
    version: str = "2.0.0"
    description: str = "Modern Application Management Suite"
    author: str = "Outback Electronics"
    organization: str = "Outback Electronics"
    website: str = "https://outbackelectronics.com"
    copyright: str = "© 2024 Outback Electronics"
    license: str = "MIT"


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CommandCore Launcher - Modern Application Management Suite"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"CommandCore Launcher {AppMetadata().version}"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode with verbose logging"
    )
    
    parser.add_argument(
        "--no-splash", 
        action="store_true", 
        help="Skip splash screen on startup"
    )
    
    parser.add_argument(
        "--minimized", 
        action="store_true", 
        help="Start application minimized to system tray"
    )
    
    parser.add_argument(
        "--reset-config", 
        action="store_true", 
        help="Reset configuration to defaults"
    )
    
    parser.add_argument(
        "--config-dir", 
        type=str, 
        help="Specify custom configuration directory"
    )
    
    return parser.parse_args()


class CommandCoreLauncher(QMainWindow):
    """
    Main application window with comprehensive functionality.
    Enhanced with proper system tray integration and error handling.
    """
    
    # Signals
    theme_changed = Signal(str)
    settings_saved = Signal()
    app_launch_requested = Signal(str)
    app_status_changed = Signal(str, str)
    
    def __init__(self, app_metadata: AppMetadata):
        super().__init__()
        
        self.app_metadata = app_metadata
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Core managers
        self.config_manager: Optional[ConfigManager] = None
        self.theme_manager: Optional[ThemeManager] = None
        self.state_manager: Optional[AppStateManager] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.update_checker: Optional[UpdateChecker] = None
        
        # UI components
        self.tab_widget: Optional[QTabWidget] = None
        self.status_bar: Optional[QStatusBar] = None
        self.system_tray: Optional[QSystemTrayIcon] = None
        
        # Tab references
        self.dashboard_tab: Optional[DashboardTab] = None
        self.applications_tab: Optional[ApplicationManagerTab] = None
        self.system_status_tab: Optional[SystemStatusTab] = None
        self.settings_tab: Optional[SettingsTab] = None
        
        # Initialize application
        try:
            self._initialize_core_systems()
            self._setup_ui()
            self._setup_system_tray()
            self._setup_connections()
            self._apply_initial_config()
            self._start_background_services()
            
            self.logger.info("CommandCore Launcher initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _initialize_core_systems(self):
        """Initialize core application systems."""
        try:
            # Configuration manager
            self.config_manager = ConfigManager()
            self.logger.info("Configuration manager initialized")
            
            # Theme manager
            self.theme_manager = ThemeManager()
            self.logger.info("Theme manager initialized")
            
            # State manager
            self.state_manager = AppStateManager()
            self.logger.info("State manager initialized")
            
            # Notification manager
            self.notification_manager = NotificationManager()
            self.logger.info("Notification manager initialized")
            
            # Update checker
            self.update_checker = initialize_update_checker(self.app_metadata.version)
            self.logger.info("Update checker initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing core systems: {e}")
            raise
    
    def _setup_ui(self):
        """Setup the main user interface."""
        try:
            # Window properties
            self.setWindowTitle(f"{self.app_metadata.name} v{self.app_metadata.version}")
            self.setMinimumSize(1200, 800)
            self.resize(1400, 900)
            
            # Set window icon
            icon_path = self._find_icon_file()
            if icon_path:
                self.setWindowIcon(QIcon(str(icon_path)))
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            layout = QVBoxLayout(central_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Tab widget
            self.tab_widget = QTabWidget()
            self.tab_widget.setTabPosition(QTabWidget.North)
            self.tab_widget.setMovable(False)
            self.tab_widget.setTabsClosable(False)
            
            # Create tabs
            self._create_tabs()
            
            layout.addWidget(self.tab_widget)
            
            # Status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("Ready", 2000)
            
            self.logger.info("Main UI setup completed")
            
        except Exception as e:
            self.logger.error(f"Error setting up UI: {e}")
            raise
    
    def _create_tabs(self):
        """Create and add all application tabs."""
        try:
            # Dashboard Tab
            self.dashboard_tab = DashboardTab(
                config=self.config_manager,
                parent=self
            )
            self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
            
            # Applications Tab
            self.applications_tab = ApplicationManagerTab(
                config=self.config_manager,
                parent=self
            )
            self.tab_widget.addTab(self.applications_tab, "Applications")
            
            # System Status Tab
            self.system_status_tab = SystemStatusTab(
                config=self.config_manager,
                parent=self
            )
            self.tab_widget.addTab(self.system_status_tab, "System Status")
            
            # Settings Tab
            self.settings_tab = SettingsTab(
                config=self.config_manager,
                theme_manager=self.theme_manager,
                parent=self
            )
            self.tab_widget.addTab(self.settings_tab, "Settings")
            
            self.logger.info("All tabs created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating tabs: {e}")
            raise
    
    def _find_icon_file(self) -> Optional[str]:
        """Find the application icon file with enhanced search."""
        icon_paths = [
            "CommandCore.png",
            "assets/CommandCore.png", 
            "assets/icons/CommandCore.png",
            "icon.png",
            "assets/icon.png",
            str(Path(__file__).parent / "CommandCore.png"),
            str(Path(__file__).parent / "assets" / "CommandCore.png"),
            str(Path(__file__).parent.parent / "CommandCore.png"),
            str(Path(__file__).parent.parent / "assets" / "CommandCore.png"),
            # Additional search locations
            str(Path.cwd() / "CommandCore.png"),
            str(Path.cwd() / "assets" / "CommandCore.png"),
        ]
        
        for icon_path in icon_paths:
            try:
                path = Path(icon_path)
                if path.exists() and path.is_file():
                    self.logger.info(f"Found icon at: {icon_path}")
                    return str(path.absolute())
            except Exception as e:
                self.logger.debug(f"Error checking icon path {icon_path}: {e}")
        
        self.logger.warning("No icon file found, will use system default")
        return None
    
    def _setup_system_tray(self):
        """Setup system tray with enhanced error handling and fallback icon."""
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                self.logger.warning("System tray not available")
                return
            
            # Create tray icon
            self.system_tray = QSystemTrayIcon(self)
            
            # Set icon with proper fallback
            icon_path = self._find_icon_file()
            if icon_path and Path(icon_path).exists():
                try:
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        self.system_tray.setIcon(icon)
                        self.logger.info(f"System tray icon set successfully: {icon_path}")
                    else:
                        self.logger.warning(f"Failed to load icon from {icon_path}")
                        self._create_fallback_tray_icon()
                except Exception as e:
                    self.logger.error(f"Error setting tray icon from {icon_path}: {e}")
                    self._create_fallback_tray_icon()
            else:
                self._create_fallback_tray_icon()
            
            # Create context menu
            tray_menu = QMenu(self)
            
            # Show/Hide action
            show_action = QAction("Show CommandCore Launcher", self)
            show_action.triggered.connect(self._show_from_tray)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            # Quick actions
            dashboard_action = QAction("Dashboard", self)
            dashboard_action.triggered.connect(lambda: self._show_and_switch_tab("Dashboard"))
            tray_menu.addAction(dashboard_action)
            
            apps_action = QAction("Applications", self)
            apps_action.triggered.connect(lambda: self._show_and_switch_tab("Applications"))
            tray_menu.addAction(apps_action)
            
            system_action = QAction("System Status", self)
            system_action.triggered.connect(lambda: self._show_and_switch_tab("System Status"))
            tray_menu.addAction(system_action)
            
            tray_menu.addSeparator()
            
            # Settings action
            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(lambda: self._show_and_switch_tab("Settings"))
            tray_menu.addAction(settings_action)
            
            tray_menu.addSeparator()
            
            # Exit action
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self._exit_application)
            tray_menu.addAction(exit_action)
            
            self.system_tray.setContextMenu(tray_menu)
            
            # Connect signals
            self.system_tray.activated.connect(self._on_tray_icon_activated)
            
            # Show tray icon
            self.system_tray.show()
            
            self.logger.info("System tray initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup system tray: {e}")
    
    def _create_fallback_tray_icon(self):
        """Create a simple fallback tray icon when PNG is not available."""
        try:
            # Create a simple 16x16 colored square as fallback
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(0, 168, 255))  # CommandCore blue
            
            # Add a simple pattern to make it recognizable
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))
            painter.drawRect(2, 2, 12, 12)
            painter.drawText(4, 12, "CC")
            painter.end()
            
            icon = QIcon(pixmap)
            self.system_tray.setIcon(icon)
            self.logger.info("Using fallback tray icon")
            
        except Exception as e:
            self.logger.error(f"Error creating fallback tray icon: {e}")
    
    def _setup_connections(self):
        """Setup signal/slot connections between components."""
        try:
            # Tab widget connections
            if self.tab_widget:
                self.tab_widget.currentChanged.connect(self._on_tab_changed)
            
            # Theme manager connections
            if self.theme_manager:
                self.theme_manager.theme_changed.connect(self._on_theme_applied)
            
            # Settings tab connections
            if self.settings_tab:
                self.settings_tab.theme_changed.connect(self._on_theme_changed)
                self.settings_tab.settings_saved.connect(self._on_settings_saved)
            
            # Application manager connections
            if self.applications_tab:
                self.applications_tab.app_launch_requested.connect(self._on_app_launch_requested)
                self.applications_tab.app_status_changed.connect(self._on_app_status_changed)
            
            # State manager connections
            if self.state_manager:
                self.state_manager.state_changed.connect(self._on_state_changed)
            
            # Update checker connections
            if self.update_checker:
                self.update_checker.update_available.connect(self._on_update_available)
                self.update_checker.error_occurred.connect(self._on_update_error)
            
            self.logger.info("Signal connections established")
            
        except Exception as e:
            self.logger.error(f"Error setting up connections: {e}")
    
    def _apply_initial_config(self):
        """Apply initial configuration from config manager."""
        try:
            if not self.config_manager:
                return
            
            # Apply theme
            theme_name = self.config_manager.get("ui.theme", "dark")
            if self.theme_manager:
                self.theme_manager.apply_theme(theme_name)
            
            # Apply window state
            if self.config_manager.get("ui.remember_window_state", True):
                self._restore_window_state()
            else:
                self.show()
            
            self.logger.info("Initial configuration applied")
            
        except Exception as e:
            self.logger.error(f"Error applying initial config: {e}")
    
    def _start_background_services(self):
        """Start background services and tasks."""
        try:
            # Start update checker
            if self.update_checker:
                # Check for updates after a delay
                QTimer.singleShot(5000, lambda: self.update_checker.check_for_updates(silent=True))
            
            # Start system monitoring
            if self.system_status_tab:
                self.system_status_tab.start_monitoring()
            
            self.logger.info("Background services started")
            
        except Exception as e:
            self.logger.error(f"Error starting background services: {e}")
    
    def _restore_window_state(self):
        """Restore window position and size from configuration."""
        try:
            # Get saved geometry
            geometry = self.config_manager.get("ui.window_geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            # Get saved state
            state = self.config_manager.get("ui.window_state")
            if state:
                self.restoreState(state)
                
        except Exception as e:
            self.logger.debug(f"Could not restore window state: {e}")
    
    def _save_window_state(self):
        """Save current window position and size to configuration."""
        try:
            if self.config_manager and self.config_manager.get("ui.remember_window_state", True):
                self.config_manager.set("ui.window_geometry", self.saveGeometry())
                self.config_manager.set("ui.window_state", self.saveState())
                
        except Exception as e:
            self.logger.debug(f"Could not save window state: {e}")
    
    # Event handlers
    def _on_tab_changed(self, index: int):
        """Handle tab change events."""
        try:
            if 0 <= index < self.tab_widget.count():
                tab_name = self.tab_widget.tabText(index)
                self.status_bar.showMessage(f"Switched to {tab_name}", 2000)
                
                # Update state
                if self.state_manager:
                    self.state_manager.set_state("ui.current_tab", tab_name, StateScope.SESSION)
                
        except Exception as e:
            self.logger.error(f"Error handling tab change: {e}")
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change event."""
        try:
            if self.theme_manager:
                self.theme_manager.set_theme(theme_name)  # Use the fixed method name
            
            # Update configuration
            if self.config_manager:
                self.config_manager.set("ui.theme", theme_name)
            
            # Emit signal
            self.theme_changed.emit(theme_name)
            
            self.status_bar.showMessage(f"Theme changed to {theme_name}", 3000)
            self.logger.info(f"Theme changed to: {theme_name}")
            
        except Exception as e:
            self.logger.error(f"Error changing theme: {e}")
    
    def _on_theme_applied(self, theme_name: str):
        """Handle theme applied event from theme manager."""
        try:
            self.logger.info(f"Theme applied: {theme_name}")
            
        except Exception as e:
            self.logger.error(f"Error handling theme applied: {e}")
    
    def _on_settings_saved(self):
        """Handle settings saved event."""
        try:
            self.status_bar.showMessage("Settings saved successfully", 3000)
            
            # Show notification
            if self.notification_manager:
                self.notification_manager.show_notification(
                    "Settings Saved",
                    "Your settings have been saved successfully.",
                    "success"
                )
            
        except Exception as e:
            self.logger.error(f"Error handling settings saved: {e}")
    
    def _on_app_launch_requested(self, app_name: str):
        """Handle application launch request."""
        try:
            self.status_bar.showMessage(f"Launching {app_name}...", 3000)
            self.logger.info(f"Launch requested for application: {app_name}")
            
        except Exception as e:
            self.logger.error(f"Error handling app launch request: {e}")
    
    def _on_app_status_changed(self, app_name: str, status: str):
        """Handle application status change."""
        try:
            self.logger.info(f"Application {app_name} status changed to: {status}")
            
        except Exception as e:
            self.logger.error(f"Error handling app status change: {e}")
    
    def _on_state_changed(self, key: str, value: Any, scope: StateScope):
        """Handle state change event."""
        try:
            self.logger.debug(f"State changed: {key} = {value} (scope: {scope})")
            
        except Exception as e:
            self.logger.error(f"Error handling state change: {e}")
    
    def _on_update_available(self, update_info):
        """Handle update available notification."""
        try:
            if update_info:
                version = getattr(update_info, 'version', 'Unknown')
                self.logger.info(f"Update available: version {version}")
                
                # Show notification
                if self.notification_manager:
                    self.notification_manager.show_notification(
                        "Update Available",
                        f"CommandCore Launcher v{version} is available for download.",
                        "info"
                    )
            
        except Exception as e:
            self.logger.error(f"Error handling update available: {e}")
    
    def _on_update_error(self, error_message: str):
        """Handle update check error."""
        try:
            self.logger.debug(f"Update check completed: {error_message}")
            
        except Exception as e:
            self.logger.error(f"Error handling update error: {e}")
    
    def _on_tray_icon_activated(self, reason):
        """Handle system tray icon activation."""
        try:
            if reason == QSystemTrayIcon.DoubleClick:
                self._show_from_tray()
            elif reason == QSystemTrayIcon.Trigger:
                # Single click - toggle visibility
                if self.isVisible() and not self.isMinimized():
                    self.hide()
                else:
                    self._show_from_tray()
                    
        except Exception as e:
            self.logger.error(f"Error handling tray icon activation: {e}")
    
    # Action methods
    def _show_from_tray(self):
        """Show window from system tray."""
        try:
            self.show()
            self.raise_()
            self.activateWindow()
            
            if self.isMinimized():
                self.showNormal()
                
        except Exception as e:
            self.logger.error(f"Error showing from tray: {e}")
    
    def _show_and_switch_tab(self, tab_name: str):
        """Show window and switch to specified tab."""
        try:
            self._show_from_tray()
            self.switch_to_tab(tab_name)
            
        except Exception as e:
            self.logger.error(f"Error showing and switching to tab {tab_name}: {e}")
    
    def switch_to_tab(self, tab_name: str):
        """Switch to the specified tab."""
        try:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == tab_name:
                    self.tab_widget.setCurrentIndex(i)
                    return True
            
            self.logger.warning(f"Tab not found: {tab_name}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error switching to tab {tab_name}: {e}")
            return False
    
    def _exit_application(self):
        """Exit the application gracefully."""
        try:
            self.logger.info("Application exit requested")
            
            # Disable all UI updates
            self.setEnabled(False)
            QApplication.processEvents()
            
            # Clean up resources first
            self._cleanup_resources()
            
            # Close all windows and dialogs
            for widget in QApplication.topLevelWidgets():
                if widget != self:
                    widget.close()
            
            # Process any pending events
            QApplication.processEvents()
            
            # Close the main window
            self.close()
            
            # Force quit the application after a short delay
            QTimer.singleShot(100, QApplication.quit)
            
        except Exception as e:
            self.logger.error(f"Error during application exit: {e}")
            # Ensure we still try to quit even if there's an error
            QTimer.singleShot(100, QApplication.quit)
    
    # Window event handlers
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Check if we should close to tray
            if (self.system_tray and 
                self.config_manager and 
                self.config_manager.get("ui.close_to_tray", False)):
                
                self.hide()
                event.ignore()
                return
            
            # Save window state
            self._save_window_state()
            
            # Disable the window to prevent further interaction
            self.setEnabled(False)
            QApplication.processEvents()
            
            # Cleanup resources
            self._cleanup_resources()
            
            # Ensure all pending events are processed
            QApplication.sendPostedEvents()
            QApplication.processEvents()
            
            # Stop any running timers
            for timer in self.findChildren(QTimer):
                if timer.isActive():
                    timer.stop()
            
            # Accept close event
            event.accept()
            
            self.logger.info("Window closed, requesting application quit")
            
            # Schedule application quit to ensure proper cleanup
            QTimer.singleShot(0, QApplication.quit)
            
        except Exception as e:
            self.logger.error(f"Error during window close: {e}")
            event.accept()
            QTimer.singleShot(0, QApplication.quit)
    
    def changeEvent(self, event):
        """Handle window state change events."""
        try:
            if (event.type() == event.Type.WindowStateChange and 
                self.isMinimized() and 
                self.system_tray and
                self.config_manager and
                self.config_manager.get("ui.minimize_to_tray", True)):
                
                self.hide()
                event.ignore()
                return
            
            super().changeEvent(event)
            
        except Exception as e:
            self.logger.error(f"Error handling window state change: {e}")
    
    def _cleanup_resources(self):
        """Clean up application resources."""
        try:
            # Stop system monitoring
            if (self.system_status_tab and 
                hasattr(self.system_status_tab, 'metrics_collector') and 
                self.system_status_tab.metrics_collector):
                
                self.logger.info("Stopping metrics collection...")
                collector = self.system_status_tab.metrics_collector
                collector.stop_collection()
                
                # Ensure the thread is properly finished
                if collector.isRunning():
                    if not collector.wait(3000):  # Wait up to 3 seconds
                        self.logger.warning("Forcing metrics thread to quit")
                        collector.terminate()
                        collector.wait()
                
                self.system_status_tab.metrics_collector = None
            
            # Cleanup update checker
            if self.update_checker:
                self.logger.info("Cleaning up update checker...")
                self.update_checker.cleanup()
            
            # Cleanup managers in reverse order of initialization
            managers_to_cleanup = [
                self.notification_manager,
                self.state_manager,
                self.config_manager
            ]
            
            for manager in managers_to_cleanup:
                if manager and hasattr(manager, 'cleanup'):
                    try:
                        self.logger.info(f"Cleaning up {manager.__class__.__name__}...")
                        manager.cleanup()
                    except Exception as e:
                        self.logger.error(f"Error cleaning up {manager.__class__.__name__}: {e}")
            
            # Force garbage collection to help with cleanup
            import gc
            gc.collect()
            
            self.logger.info("Resource cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {e}")
            raise  # Re-raise the exception to be handled by the caller


def main():
    """Enhanced main application entry point with proper splash timing."""
    
    # Set up application metadata
    app_metadata = AppMetadata()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging first with appropriate log level
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(
        name="CommandCore",
        level=log_level
    )
    
    logger = logging.getLogger("main")
    logger.info(f"Starting {app_metadata.name} v{app_metadata.version}")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName(app_metadata.name)
    app.setApplicationVersion(app_metadata.version)
    app.setOrganizationName(app_metadata.organization)
    app.setApplicationDisplayName(app_metadata.name)
    
    # Set application icon
    try:
        icon_paths = ["CommandCore.png", "assets/CommandCore.png"]
        for icon_path in icon_paths:
            if Path(icon_path).exists():
                app.setWindowIcon(QIcon(str(icon_path)))
                logger.info(f"Application icon set: {icon_path}")
                break
    except Exception as e:
        logger.debug(f"Could not set application icon: {e}")
    
    # Show splash screen IMMEDIATELY (unless disabled)
    splash = None
    if not args.no_splash:
        try:
            splash = ModernSplashScreen()
            splash.show()
            app.processEvents()  # Ensure splash is shown immediately
            
            # Give splash a moment to render
            QTimer.singleShot(100, lambda: app.processEvents())
            
            logger.info("Splash screen displayed")
            
        except Exception as e:
            logger.error(f"Failed to show splash screen: {e}")
    
    # Background loading function
    def load_main_window():
        try:
            logger.info("Creating main window...")
            
            # Create main window in background while splash is showing
            main_window = CommandCoreLauncher(app_metadata)
            
            # Handle reset config argument
            if args.reset_config:
                if main_window.config_manager:
                    main_window.config_manager.reset_to_defaults()
                    logger.info("Configuration reset to defaults")
            
            # Handle debug mode
            if args.debug:
                if main_window.config_manager:
                    main_window.config_manager.set("application.debug_mode", True)
                    main_window.config_manager.set("logging.level", "DEBUG")
            
            logger.info("Main window created successfully")
            return main_window
            
        except Exception as e:
            error_msg = f"Failed to create main window: {e}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(error_msg)
            
            if splash:
                splash.close()
            
            QMessageBox.critical(
                None,
                "Startup Error", 
                f"Failed to start CommandCore Launcher:\n\n{str(e)}\n\nPlease check the logs for more details."
            )
            
            return None
    
    # Load main window
    main_window = load_main_window()
    if not main_window:
        return 1
    
    try:
        # Finish splash screen (will wait for minimum time and loading completion)
        if splash:
            splash.finish(main_window)
        else:
            # Show main window immediately if no splash
            if args.minimized and main_window.system_tray:
                main_window.hide()
                logger.info("Started minimized to system tray")
            else:
                main_window.show()
                logger.info("Main window displayed")
        
        # Handle shutdown gracefully
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down gracefully...")
            main_window.close()
            app.quit()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Application startup completed successfully")
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        error_msg = f"Failed to start application: {e}\n\nTraceback:\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        if splash:
            splash.close()
        
        QMessageBox.critical(
            None,
            "Startup Error",
            f"Failed to start CommandCore Launcher:\n\n{str(e)}\n\nPlease check the logs for more details."
        )
        
        return 1


if __name__ == "__main__":
    sys.exit(main())