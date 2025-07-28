"""
Modern Settings Tab for CommandCore Launcher - FIXED VERSION

Provides comprehensive settings management with live preview,
working font changes, and organized categories.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import asdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QGroupBox,
    QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QSlider, QTextEdit, QFileDialog, QMessageBox, QTabWidget,
    QColorDialog, QFontDialog, QButtonGroup, QRadioButton,
    QSizePolicy, QSpacerItem, QProgressBar, QSplitter
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve,
    QSettings, QSize
)
from PySide6.QtGui import (
    QFont, QColor, QPalette, QPixmap, QIcon, QPainter,
    QLinearGradient, QBrush
)


class SettingsGroup(QGroupBox):
    """Custom settings group with modern styling."""
    
    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(title, parent)
        
        self.description = description
        self._setup_style()
        self._setup_layout()
    
    def _setup_style(self):
        """Setup the group styling."""
        self.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
                border: 1px solid #37414F;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
                background-color: #2A2F42;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                background-color: #2A2F42;
                color: #00A8FF;
            }
        """)
    
    def _setup_layout(self):
        """Setup the group layout."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(12)
        self.main_layout.setContentsMargins(16, 20, 16, 16)
        
        # Add description if provided
        if self.description:
            desc_label = QLabel(self.description)
            desc_label.setStyleSheet("""
                color: #B0BEC5;
                font-size: 12px;
                font-weight: normal;
                margin-bottom: 8px;
            """)
            desc_label.setWordWrap(True)
            self.main_layout.addWidget(desc_label)
    
    def add_setting_row(self, label_text: str, widget: QWidget, description: str = ""):
        """Add a setting row to the group."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)
        
        # Label
        label = QLabel(label_text)
        label.setFixedWidth(150)
        label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 500;
        """)
        row_layout.addWidget(label)
        
        # Widget
        row_layout.addWidget(widget)
        row_layout.addStretch()
        
        self.main_layout.addWidget(row_widget)
        
        # Add description if provided
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("""
                color: #78909C;
                font-size: 11px;
                margin-left: 162px;
                margin-top: -8px;
                margin-bottom: 4px;
            """)
            desc_label.setWordWrap(True)
            self.main_layout.addWidget(desc_label)


class ColorPickerButton(QPushButton):
    """Custom color picker button with preview."""
    
    color_changed = Signal(QColor)
    
    def __init__(self, initial_color: QColor = QColor(0, 168, 255), parent=None):
        super().__init__(parent)
        
        self.current_color = initial_color
        self.setFixedSize(80, 32)
        self.clicked.connect(self._open_color_dialog)
        
        self._update_appearance()
    
    def _update_appearance(self):
        """Update button appearance with current color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                border: 1px solid #37414F;
                border-radius: 6px;
                color: {"#FFFFFF" if self.current_color.lightness() < 128 else "#000000"};
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                border-color: #00A8FF;
            }}
        """)
        self.setText(self.current_color.name().upper())
    
    def _open_color_dialog(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(self.current_color, self, "Choose Color")
        if color.isValid():
            self.set_color(color)
    
    def set_color(self, color: QColor):
        """Set the current color."""
        self.current_color = color
        self._update_appearance()
        self.color_changed.emit(color)
    
    def get_color(self) -> QColor:
        """Get the current color."""
        return self.current_color


class FontPickerButton(QPushButton):
    """Custom font picker button with preview."""
    
    font_changed = Signal(QFont)
    
    def __init__(self, initial_font: QFont = None, parent=None):
        super().__init__(parent)
        
        self.current_font = initial_font or QFont("Segoe UI", 10)
        self.setFixedHeight(32)
        self.clicked.connect(self._open_font_dialog)
        
        self._update_appearance()
    
    def _update_appearance(self):
        """Update button appearance with current font."""
        self.setStyleSheet("""
            QPushButton {
                background-color: #353A4F;
                color: #FFFFFF;
                border: 1px solid #37414F;
                border-radius: 6px;
                padding: 0 12px;
                text-align: left;
            }
            
            QPushButton:hover {
                background-color: #3E4358;
                border-color: #00A8FF;
            }
        """)
        
        font_text = f"{self.current_font.family()}, {self.current_font.pointSize()}pt"
        if self.current_font.bold():
            font_text += ", Bold"
        if self.current_font.italic():
            font_text += ", Italic"
        
        self.setText(font_text)
        self.setFont(self.current_font)
    
    def _open_font_dialog(self):
        """Open font picker dialog."""
        font, ok = QFontDialog.getFont(self.current_font, self, "Choose Font")
        if ok:
            self.set_font(font)
    
    def set_font(self, font: QFont):
        """Set the current font."""
        self.current_font = font
        self._update_appearance()
        self.font_changed.emit(font)
    
    def get_font(self) -> QFont:
        """Get the current font."""
        return self.current_font


class ThemePreviewWidget(QFrame):
    """Widget for previewing theme changes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedHeight(150)
        self.setFrameShape(QFrame.StyledPanel)
        self._setup_ui()
        self._setup_style()
    
    def _setup_ui(self):
        """Setup preview UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Theme Preview")
        self.title_label.setObjectName("previewTitle")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setObjectName("previewCloseBtn")
        header_layout.addWidget(self.close_btn)
        
        layout.addLayout(header_layout)
        
        # Content
        content_layout = QHBoxLayout()
        
        self.primary_btn = QPushButton("Primary Button")
        self.primary_btn.setObjectName("previewPrimaryBtn")
        content_layout.addWidget(self.primary_btn)
        
        self.secondary_btn = QPushButton("Secondary")
        self.secondary_btn.setObjectName("previewSecondaryBtn")
        content_layout.addWidget(self.secondary_btn)
        
        content_layout.addStretch()
        
        layout.addLayout(content_layout)
        
        # Sample text
        self.sample_text = QLabel("Sample text with different styling")
        self.sample_text.setObjectName("previewSampleText")
        layout.addWidget(self.sample_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(65)
        self.progress_bar.setObjectName("previewProgressBar")
        layout.addWidget(self.progress_bar)
    
    def _setup_style(self):
        """Setup preview styling."""
        self.setObjectName("themePreview")
        self.setStyleSheet("""
            QFrame#themePreview {
                background-color: #2A2F42;
                border: 1px solid #37414F;
                border-radius: 8px;
            }
            
            QLabel#previewTitle {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
            }
            
            QLabel#previewSampleText {
                color: #B0BEC5;
                font-size: 12px;
            }
            
            QPushButton#previewCloseBtn {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            
            QPushButton#previewPrimaryBtn {
                background-color: #00A8FF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 500;
            }
            
            QPushButton#previewSecondaryBtn {
                background-color: #353A4F;
                color: #FFFFFF;
                border: 1px solid #37414F;
                border-radius: 6px;
                padding: 6px 12px;
            }
            
            QProgressBar#previewProgressBar {
                background-color: #353A4F;
                border: 1px solid #37414F;
                border-radius: 8px;
                text-align: center;
                color: #FFFFFF;
            }
            
            QProgressBar#previewProgressBar::chunk {
                background-color: #00A8FF;
                border-radius: 7px;
            }
        """)
    
    def update_theme_preview(self, primary_color: QColor, font: QFont):
        """Update the preview with new theme settings."""
        # Update colors
        primary_hex = primary_color.name()
        
        # Update font for all elements
        for widget in [self.title_label, self.sample_text, self.primary_btn, self.secondary_btn, self.progress_bar]:
            new_font = QFont(font)
            if widget == self.title_label:
                new_font.setPointSize(font.pointSize() + 2)
                new_font.setBold(True)
            widget.setFont(new_font)
        
        self.setStyleSheet(f"""
            QFrame#themePreview {{
                background-color: #2A2F42;
                border: 1px solid #37414F;
                border-radius: 8px;
            }}
            
            QLabel#previewTitle {{
                color: #FFFFFF;
                font-weight: 600;
            }}
            
            QLabel#previewSampleText {{
                color: #B0BEC5;
            }}
            
            QPushButton#previewCloseBtn {{
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }}
            
            QPushButton#previewPrimaryBtn {{
                background-color: {primary_hex};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 500;
            }}
            
            QPushButton#previewSecondaryBtn {{
                background-color: #353A4F;
                color: #FFFFFF;
                border: 1px solid #37414F;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            
            QProgressBar#previewProgressBar {{
                background-color: #353A4F;
                border: 1px solid #37414F;
                border-radius: 8px;
                text-align: center;
                color: #FFFFFF;
            }}
            
            QProgressBar#previewProgressBar::chunk {{
                background-color: {primary_hex};
                border-radius: 7px;
            }}
        """)


class SettingsTab(QWidget):
    """
    Modern Settings Tab with comprehensive configuration options - FIXED VERSION.
    
    Features:
    - Working font changes that apply immediately
    - Organized categories with search
    - Live theme preview
    - Import/export functionality
    - Validation and error handling
    - Advanced customization options
    """
    
    # Signals
    theme_changed = Signal(str)
    settings_saved = Signal(dict)
    
    def __init__(self, config, theme_manager, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.theme_manager = theme_manager
        self.settings_widgets: Dict[str, QWidget] = {}
        self.has_unsaved_changes = False
        
        # Track original font settings
        self.original_font_family = self.config.get('ui.font_family', 'Segoe UI')
        self.original_font_size = self.config.get('ui.font_size', 10)
        
        self._setup_ui()
        self._load_current_settings()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Header
        header_section = self._create_header_section()
        main_layout.addWidget(header_section)
        
        # Settings content
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Settings tabs
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #37414F;
                border-radius: 8px;
                background-color: #2A2F42;
            }
            
            QTabBar::tab {
                background-color: #353A4F;
                color: #B0BEC5;
                padding: 8px 16px;
                border: 1px solid #37414F;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                min-width: 100px;
            }
            
            QTabBar::tab:selected {
                background-color: #2A2F42;
                color: #FFFFFF;
                border-bottom: 1px solid #2A2F42;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #3E4358;
            }
        """)
        
        # Create setting tabs
        self._create_appearance_tab()
        self._create_application_tab()
        self._create_system_tab()
        self._create_advanced_tab()
        
        content_splitter.addWidget(self.settings_tabs)
        
        # Preview panel
        preview_panel = self._create_preview_panel()
        content_splitter.addWidget(preview_panel)
        
        # Set splitter proportions
        content_splitter.setSizes([600, 300])
        
        main_layout.addWidget(content_splitter)
        
        # Action buttons
        buttons_section = self._create_buttons_section()
        main_layout.addWidget(buttons_section)
    
    def _create_header_section(self) -> QWidget:
        """Create the header section."""
        header = QFrame()
        header.setObjectName("headerSection")
        header.setStyleSheet("""
            QFrame#headerSection {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2A2F42, stop:1 #353A4F);
                border: 1px solid #37414F;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setSpacing(16)
        
        # Title and description
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        
        title = QLabel("Settings")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
        """)
        text_layout.addWidget(title)
        
        description = QLabel("Configure CommandCore Launcher preferences and behavior")
        description.setStyleSheet("""
            color: #B0BEC5;
            font-size: 14px;
        """)
        text_layout.addWidget(description)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Quick actions
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setFixedHeight(32)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        actions_layout.addWidget(self.reset_btn)
        
        import_export_layout = QHBoxLayout()
        import_export_layout.setSpacing(8)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.setFixedSize(60, 28)
        self.import_btn.clicked.connect(self._import_settings)
        import_export_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setFixedSize(60, 28)
        self.export_btn.clicked.connect(self._export_settings)
        import_export_layout.addWidget(self.export_btn)
        
        actions_layout.addLayout(import_export_layout)
        
        layout.addLayout(actions_layout)
        
        return header
    
    def _create_appearance_tab(self):
        """Create the appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Theme group
        theme_group = SettingsGroup(
            "Theme",
            "Customize the visual appearance of the application"
        )
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([display_name for _, display_name in self.theme_manager.get_available_themes()])
        self.theme_combo.setFixedWidth(200)
        theme_group.add_setting_row(
            "Theme:", 
            self.theme_combo,
            "Choose from available themes or create custom themes"
        )
        
        # Primary color
        primary_color_str = self.theme_manager.get_color("primary") or "#00A8FF"
        self.primary_color_btn = ColorPickerButton(QColor(primary_color_str))
        theme_group.add_setting_row(
            "Primary Color:",
            self.primary_color_btn,
            "Main accent color used throughout the interface"
        )
        
        scroll_layout.addWidget(theme_group)
        
        # Font group
        font_group = SettingsGroup(
            "Typography",
            "Configure fonts and text appearance"
        )
        
        # Font selection
        current_font = QFont(
            self.config.get("ui.font_family", "Segoe UI"),
            self.config.get("ui.font_size", 10)
        )
        self.font_btn = FontPickerButton(current_font)
        font_group.add_setting_row(
            "Application Font:",
            self.font_btn,
            "Font used throughout the application interface"
        )
        
        # Font size slider
        font_size_layout = QHBoxLayout()
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 18)
        self.font_size_slider.setValue(self.config.get("ui.font_size", 10))
        self.font_size_slider.setFixedWidth(150)
        font_size_layout.addWidget(self.font_size_slider)
        
        self.font_size_label = QLabel(f"{self.font_size_slider.value()}pt")
        self.font_size_label.setFixedWidth(30)
        self.font_size_label.setStyleSheet("color: #B0BEC5;")
        font_size_layout.addWidget(self.font_size_label)
        
        font_size_widget = QWidget()
        font_size_widget.setLayout(font_size_layout)
        
        font_group.add_setting_row(
            "Font Size:",
            font_size_widget,
            "Base font size for the application (8-18pt)"
        )
        
        scroll_layout.addWidget(font_group)
        
        # Animation group
        animation_group = SettingsGroup(
            "Animations",
            "Control visual effects and transitions"
        )
        
        # Enable animations
        self.animations_enabled_check = QCheckBox("Enable animations and transitions")
        self.animations_enabled_check.setChecked(self.config.get("ui.animation_enabled", True))
        animation_group.add_setting_row(
            "Animations:",
            self.animations_enabled_check,
            "Enable smooth transitions and visual effects"
        )
        
        # Animation speed
        speed_layout = QHBoxLayout()
        self.animation_speed_slider = QSlider(Qt.Horizontal)
        self.animation_speed_slider.setRange(50, 500)
        self.animation_speed_slider.setValue(self.config.get("ui.animation_duration", 200))
        self.animation_speed_slider.setFixedWidth(150)
        speed_layout.addWidget(self.animation_speed_slider)
        
        self.animation_speed_label = QLabel(f"{self.animation_speed_slider.value()}ms")
        self.animation_speed_label.setFixedWidth(40)
        self.animation_speed_label.setStyleSheet("color: #B0BEC5;")
        speed_layout.addWidget(self.animation_speed_label)
        
        speed_widget = QWidget()
        speed_widget.setLayout(speed_layout)
        
        animation_group.add_setting_row(
            "Animation Speed:",
            speed_widget,
            "Duration of animations in milliseconds"
        )
        
        scroll_layout.addWidget(animation_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.settings_tabs.addTab(tab, "Appearance")
    
    def _create_application_tab(self):
        """Create the application settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Startup group
        startup_group = SettingsGroup(
            "Startup",
            "Configure application startup behavior"
        )
        
        # Show splash screen
        self.show_splash_check = QCheckBox("Show splash screen on startup")
        self.show_splash_check.setChecked(self.config.get("ui.show_splash", True))
        startup_group.add_setting_row(
            "Splash Screen:",
            self.show_splash_check,
            "Display animated splash screen during application startup"
        )
        
        # Remember window state
        self.remember_window_check = QCheckBox("Remember window position and size")
        self.remember_window_check.setChecked(self.config.get("ui.remember_window_state", True))
        startup_group.add_setting_row(
            "Window State:",
            self.remember_window_check,
            "Restore window position and size from last session"
        )
        
        # Start maximized
        self.start_maximized_check = QCheckBox("Start maximized")
        self.start_maximized_check.setChecked(self.config.get("ui.start_maximized", False))
        startup_group.add_setting_row(
            "Start Maximized:",
            self.start_maximized_check,
            "Start the application in maximized window state"
        )
        
        # Default tab
        self.default_tab_combo = QComboBox()
        self.default_tab_combo.addItems(["Dashboard", "Applications", "System Status", "Settings"])
        self.default_tab_combo.setCurrentText(self.config.get("application.startup_tab", "Dashboard"))
        startup_group.add_setting_row(
            "Default Tab:",
            self.default_tab_combo,
            "Tab to show when the application starts"
        )
        
        scroll_layout.addWidget(startup_group)
        
        # System tray group
        tray_group = SettingsGroup(
            "System Tray",
            "Configure system tray integration"
        )
        
        # Minimize to tray
        self.minimize_to_tray_check = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_check.setChecked(self.config.get("ui.minimize_to_tray", True))
        tray_group.add_setting_row(
            "Minimize to Tray:",
            self.minimize_to_tray_check,
            "Hide window to system tray when minimized"
        )
        
        # Close to tray
        self.close_to_tray_check = QCheckBox("Close to system tray")
        self.close_to_tray_check.setChecked(self.config.get("ui.close_to_tray", False))
        tray_group.add_setting_row(
            "Close to Tray:",
            self.close_to_tray_check,
            "Hide to system tray instead of exiting when closed"
        )
        
        scroll_layout.addWidget(tray_group)
        
        # Notifications group
        notifications_group = SettingsGroup(
            "Notifications",
            "Configure notification preferences"
        )
        
        # Enable notifications
        self.notifications_enabled_check = QCheckBox("Enable notifications")
        self.notifications_enabled_check.setChecked(self.config.get("notifications.enabled", True))
        notifications_group.add_setting_row(
            "Notifications:",
            self.notifications_enabled_check,
            "Show desktop notifications for important events"
        )
        
        # Notification duration
        duration_layout = QHBoxLayout()
        self.notification_duration_spin = QSpinBox()
        self.notification_duration_spin.setRange(1000, 30000)
        self.notification_duration_spin.setValue(self.config.get("notifications.duration", 5000))
        self.notification_duration_spin.setSuffix(" ms")
        self.notification_duration_spin.setFixedWidth(100)
        duration_layout.addWidget(self.notification_duration_spin)
        
        duration_widget = QWidget()
        duration_widget.setLayout(duration_layout)
        
        notifications_group.add_setting_row(
            "Duration:",
            duration_widget,
            "How long notifications are displayed"
        )
        
        scroll_layout.addWidget(notifications_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.settings_tabs.addTab(tab, "Application")
    
    def _create_system_tab(self):
        """Create the system settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Monitoring group
        monitoring_group = SettingsGroup(
            "System Monitoring",
            "Configure system monitoring and performance tracking"
        )
        
        # Auto-start monitoring
        self.auto_start_monitoring_check = QCheckBox("Auto-start system monitoring")
        self.auto_start_monitoring_check.setChecked(self.config.get("application.auto_start_monitoring", False))
        monitoring_group.add_setting_row(
            "Auto-start:",
            self.auto_start_monitoring_check,
            "Automatically start monitoring when application launches"
        )
        
        # Monitor interval
        interval_layout = QHBoxLayout()
        self.monitor_interval_spin = QSpinBox()
        self.monitor_interval_spin.setRange(500, 10000)
        self.monitor_interval_spin.setValue(self.config.get("application.monitor_interval", 1000))
        self.monitor_interval_spin.setSuffix(" ms")
        self.monitor_interval_spin.setFixedWidth(100)
        interval_layout.addWidget(self.monitor_interval_spin)
        
        interval_widget = QWidget()
        interval_widget.setLayout(interval_layout)
        
        monitoring_group.add_setting_row(
            "Update Interval:",
            interval_widget,
            "How often to update system metrics"
        )
        
        scroll_layout.addWidget(monitoring_group)
        
        # Updates group
        updates_group = SettingsGroup(
            "Updates",
            "Configure automatic update checking"
        )
        
        # Update check enabled
        self.update_check_enabled_check = QCheckBox("Check for updates automatically")
        self.update_check_enabled_check.setChecked(self.config.get("application.update_check_enabled", True))
        updates_group.add_setting_row(
            "Auto-check:",
            self.update_check_enabled_check,
            "Automatically check for application updates"
        )
        
        # Update frequency
        self.update_frequency_combo = QComboBox()
        self.update_frequency_combo.addItems(["never", "daily", "weekly", "monthly"])
        self.update_frequency_combo.setCurrentText(self.config.get("application.update_check_frequency", "weekly"))
        updates_group.add_setting_row(
            "Check Frequency:",
            self.update_frequency_combo,
            "How often to check for updates"
        )
        
        scroll_layout.addWidget(updates_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.settings_tabs.addTab(tab, "System")
    
    def _create_advanced_tab(self):
        """Create the advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Logging group
        logging_group = SettingsGroup(
            "Logging",
            "Configure application logging and debugging"
        )
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText(self.config.get("logging.level", "INFO"))
        logging_group.add_setting_row(
            "Log Level:",
            self.log_level_combo,
            "Minimum level of messages to log"
        )
        
        # Enable file logging
        self.file_logging_check = QCheckBox("Enable file logging")
        self.file_logging_check.setChecked(self.config.get("logging.file_enabled", True))
        logging_group.add_setting_row(
            "File Logging:",
            self.file_logging_check,
            "Write log messages to files"
        )
        
        # Max log file size
        log_size_layout = QHBoxLayout()
        self.max_log_size_spin = QSpinBox()
        self.max_log_size_spin.setRange(1, 100)
        self.max_log_size_spin.setValue(self.config.get("logging.max_file_size_mb", 10))
        self.max_log_size_spin.setSuffix(" MB")
        self.max_log_size_spin.setFixedWidth(100)
        log_size_layout.addWidget(self.max_log_size_spin)
        
        log_size_widget = QWidget()
        log_size_widget.setLayout(log_size_layout)
        
        logging_group.add_setting_row(
            "Max File Size:",
            log_size_widget,
            "Maximum size of individual log files"
        )
        
        scroll_layout.addWidget(logging_group)
        
        # Performance group
        performance_group = SettingsGroup(
            "Performance",
            "Advanced performance and debugging options"
        )
        
        # Debug mode
        self.debug_mode_check = QCheckBox("Enable debug mode")
        self.debug_mode_check.setChecked(self.config.get("application.debug_mode", False))
        performance_group.add_setting_row(
            "Debug Mode:",
            self.debug_mode_check,
            "Enable additional debugging features and logging"
        )
        
        # Performance mode
        self.performance_mode_check = QCheckBox("Enable performance mode")
        self.performance_mode_check.setChecked(self.config.get("application.performance_mode", False))
        performance_group.add_setting_row(
            "Performance Mode:",
            self.performance_mode_check,
            "Reduce visual effects for better performance"
        )
        
        # Background monitoring
        self.background_monitoring_check = QCheckBox("Enable background monitoring")
        self.background_monitoring_check.setChecked(self.config.get("application.background_monitoring", True))
        performance_group.add_setting_row(
            "Background Monitoring:",
            self.background_monitoring_check,
            "Continue monitoring when application is minimized"
        )
        
        scroll_layout.addWidget(performance_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self.settings_tabs.addTab(tab, "Advanced")
    
    def _create_preview_panel(self) -> QWidget:
        """Create the live preview panel."""
        panel = QWidget()
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        
        # Preview header
        preview_header = QLabel("Live Preview")
        preview_header.setStyleSheet("""
            color: #FFFFFF;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        """)
        layout.addWidget(preview_header)
        
        # Theme preview widget
        self.theme_preview = ThemePreviewWidget()
        layout.addWidget(self.theme_preview)
        
        # Configuration info
        info_group = QGroupBox("Configuration Info")
        info_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-weight: 600;
                border: 1px solid #37414F;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background-color: #2A2F42;
            }
        """)
        
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)
        
        self.config_path_label = QLabel(f"Config: {str(self.config.config_file)}")
        self.config_path_label.setStyleSheet("color: #B0BEC5; font-size: 11px; font-weight: normal;")
        self.config_path_label.setWordWrap(True)
        info_layout.addWidget(self.config_path_label)
        
        self.last_saved_label = QLabel("Last saved: Never")
        self.last_saved_label.setStyleSheet("color: #78909C; font-size: 11px; font-weight: normal;")
        info_layout.addWidget(self.last_saved_label)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return panel
    
    def _create_buttons_section(self) -> QWidget:
        """Create the action buttons section."""
        buttons_section = QFrame()
        buttons_section.setStyleSheet("""
            QFrame {
                border-top: 1px solid #37414F;
                padding-top: 16px;
            }
        """)
        
        layout = QHBoxLayout(buttons_section)
        layout.setSpacing(12)
        
        # Status label
        self.status_label = QLabel("No changes")
        self.status_label.setStyleSheet("color: #78909C; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Action buttons
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.clicked.connect(self._cancel_changes)
        layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setFixedHeight(36)
        self.apply_btn.clicked.connect(self._apply_settings)
        layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:disabled {
                background-color: #2E7D32;
                opacity: 0.6;
            }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        layout.addWidget(self.save_btn)
        
        return buttons_section
    
    def _load_current_settings(self):
        """Load current settings into the UI."""
        try:
            # Update theme combo
            current_theme = self.config.get("ui.theme", "dark")
            for i in range(self.theme_combo.count()):
                theme_name, display_name = list(self.theme_manager.get_available_themes())[i]
                if theme_name == current_theme:
                    self.theme_combo.setCurrentIndex(i)
                    break
            
            # Update other settings are already loaded in UI creation
            self._update_preview()
            
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def _setup_connections(self):
        """Setup signal connections for live updates."""
        # Theme changes
        self.theme_combo.currentTextChanged.connect(self._on_setting_changed)
        self.primary_color_btn.color_changed.connect(self._on_setting_changed)
        
        # Font changes - these need immediate application
        self.font_btn.font_changed.connect(self._on_font_changed)
        self.font_size_slider.valueChanged.connect(self._on_font_size_changed)
        
        # Animation changes
        self.animation_speed_slider.valueChanged.connect(self._on_animation_speed_changed)
        
        # All checkboxes and combos
        checkboxes = [
            self.animations_enabled_check, self.show_splash_check,
            self.remember_window_check, self.start_maximized_check,
            self.minimize_to_tray_check, self.close_to_tray_check, 
            self.notifications_enabled_check, self.auto_start_monitoring_check, 
            self.update_check_enabled_check, self.file_logging_check, 
            self.debug_mode_check, self.performance_mode_check, 
            self.background_monitoring_check
        ]
        
        for checkbox in checkboxes:
            checkbox.toggled.connect(self._on_setting_changed)
        
        combos = [
            self.default_tab_combo, self.update_frequency_combo,
            self.log_level_combo
        ]
        
        for combo in combos:
            combo.currentTextChanged.connect(self._on_setting_changed)
        
        spinboxes = [
            self.notification_duration_spin, self.monitor_interval_spin,
            self.max_log_size_spin
        ]
        
        for spinbox in spinboxes:
            spinbox.valueChanged.connect(self._on_setting_changed)
    
    def _on_setting_changed(self):
        """Handle setting changes."""
        self.has_unsaved_changes = True
        self.status_label.setText("Unsaved changes")
        self.status_label.setStyleSheet("color: #FF9800; font-size: 12px;")
        
        # Update preview
        self._update_preview()
    
    def _on_font_changed(self, font: QFont):
        """Handle font picker changes - apply immediately."""
        self._apply_font_change(font.family(), font.pointSize())
        self._on_setting_changed()
    
    def _on_font_size_changed(self, value):
        """Handle font size slider changes - apply immediately."""
        self.font_size_label.setText(f"{value}pt")
        
        # Get current font family
        current_family = self.font_btn.get_font().family()
        self._apply_font_change(current_family, value)
        
        # Update font button to reflect size change
        new_font = QFont(current_family, value)
        self.font_btn.set_font(new_font)
        
        self._on_setting_changed()
    
    def _apply_font_change(self, family: str, size: int):
        """Apply font changes immediately to the application."""
        try:
            # Update the theme manager's current theme
            if self.theme_manager and self.theme_manager.current_theme:
                self.theme_manager.current_theme.font_family = family
                self.theme_manager.current_theme.font_size = size
                
                # Reapply the current theme to update fonts
                current_theme_name = self.theme_manager.get_current_theme_name()
                self.theme_manager.apply_theme(current_theme_name)
        except Exception as e:
            print(f"Error applying font change: {e}")
    
    def _on_animation_speed_changed(self, value):
        """Handle animation speed slider changes."""
        self.animation_speed_label.setText(f"{value}ms")
        self._on_setting_changed()
    
    def _update_preview(self):
        """Update the live preview."""
        try:
            primary_color = self.primary_color_btn.get_color()
            font = self.font_btn.get_font()
            font.setPointSize(self.font_size_slider.value())
            
            self.theme_preview.update_theme_preview(primary_color, font)
            
        except Exception as e:
            print(f"Error updating preview: {e}")
    
    def _apply_settings(self):
        """Apply settings without saving to file."""
        try:
            settings = self._collect_current_settings()
            
            # Apply theme changes
            if self.theme_combo.currentText():
                theme_names = [name for name, _ in self.theme_manager.get_available_themes()]
                if self.theme_combo.currentIndex() < len(theme_names):
                    theme_name = theme_names[self.theme_combo.currentIndex()]
                    self.theme_manager.apply_theme(theme_name)
                    self.theme_changed.emit(theme_name)
            
            self.status_label.setText("Settings applied")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            
        except Exception as e:
            print(f"Error applying settings: {e}")
            QMessageBox.warning(self, "Apply Failed", f"Failed to apply settings: {str(e)}")
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            settings = self._collect_current_settings()
            
            # Update config
            success = self.config.update_settings(settings)
            if success:
                self.has_unsaved_changes = False
                self.status_label.setText("Settings saved successfully")
                self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                
                # Update last saved time
                from datetime import datetime
                self.last_saved_label.setText(f"Last saved: {datetime.now().strftime('%H:%M:%S')}")
                
                # Emit signal
                self.settings_saved.emit(settings)
                
                # Apply settings
                self._apply_settings()
                
            else:
                QMessageBox.warning(self, "Save Failed", "Failed to save settings to file.")
                
        except Exception as e:
            print(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Save Error", f"Error saving settings: {str(e)}")
    
    def _cancel_changes(self):
        """Cancel unsaved changes."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Cancel Changes",
                "You have unsaved changes. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Restore original font settings
                self._apply_font_change(self.original_font_family, self.original_font_size)
                
                self._load_current_settings()
                self.has_unsaved_changes = False
                self.status_label.setText("Changes cancelled")
                self.status_label.setStyleSheet("color: #78909C; font-size: 12px;")
    
    def _collect_current_settings(self) -> Dict[str, Any]:
        """Collect current settings from UI controls."""
        # Get theme name
        theme_names = [name for name, _ in self.theme_manager.get_available_themes()]
        current_theme = "dark"
        if self.theme_combo.currentIndex() < len(theme_names):
            current_theme = theme_names[self.theme_combo.currentIndex()]
        
        settings = {
            # UI settings
            "ui.theme": current_theme,
            "ui.font_family": self.font_btn.get_font().family(),
            "ui.font_size": self.font_size_slider.value(),
            "ui.animation_enabled": self.animations_enabled_check.isChecked(),
            "ui.animation_duration": self.animation_speed_slider.value(),
            "ui.show_splash": self.show_splash_check.isChecked(),
            "ui.remember_window_state": self.remember_window_check.isChecked(),
            "ui.start_maximized": self.start_maximized_check.isChecked(),
            "ui.minimize_to_tray": self.minimize_to_tray_check.isChecked(),
            "ui.close_to_tray": self.close_to_tray_check.isChecked(),
            
            # Application settings
            "application.startup_tab": self.default_tab_combo.currentText(),
            "application.auto_start_monitoring": self.auto_start_monitoring_check.isChecked(),
            "application.monitor_interval": self.monitor_interval_spin.value(),
            "application.update_check_enabled": self.update_check_enabled_check.isChecked(),
            "application.update_check_frequency": self.update_frequency_combo.currentText(),
            "application.debug_mode": self.debug_mode_check.isChecked(),
            "application.performance_mode": self.performance_mode_check.isChecked(),
            "application.background_monitoring": self.background_monitoring_check.isChecked(),
            
            # Notification settings
            "notifications.enabled": self.notifications_enabled_check.isChecked(),
            "notifications.duration": self.notification_duration_spin.value(),
            
            # Logging settings
            "logging.level": self.log_level_combo.currentText(),
            "logging.file_enabled": self.file_logging_check.isChecked(),
            "logging.max_file_size_mb": self.max_log_size_spin.value(),
        }
        
        return settings
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.config.reset_to_defaults()
                if success:
                    # Reset font to defaults
                    self._apply_font_change("Segoe UI", 10)
                    
                    self._load_current_settings()
                    self.has_unsaved_changes = False
                    self.status_label.setText("Settings reset to defaults")
                    self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                else:
                    QMessageBox.warning(self, "Reset Failed", "Failed to reset settings to defaults.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Reset Error", f"Error resetting settings: {str(e)}")
    
    def _import_settings(self):
        """Import settings from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                success = self.config.import_config(file_path)
                if success:
                    self._load_current_settings()
                    self.has_unsaved_changes = False
                    self.status_label.setText("Settings imported successfully")
                    self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
                else:
                    QMessageBox.warning(self, "Import Failed", "Failed to import settings from file.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Error importing settings: {str(e)}")
    
    def _export_settings(self):
        """Export settings to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            "commandcore_settings.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                success = self.config.export_config(file_path)
                if success:
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Settings exported successfully to:\n{file_path}"
                    )
                else:
                    QMessageBox.warning(self, "Export Failed", "Failed to export settings to file.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Error exporting settings: {str(e)}")
    
    def cleanup(self):
        """Cleanup resources when tab is destroyed."""
        # Save unsaved changes if user wants
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self._save_settings()
            elif reply == QMessageBox.Cancel:
                return False  # Don't close
        
        return True