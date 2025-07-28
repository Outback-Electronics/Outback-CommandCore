"""
Modern Theme Manager for CommandCore Launcher - IMPROVED VERSION

Provides comprehensive theming support with multiple color schemes,
custom styling, and dynamic theme switching with improved light theme.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QColor, QPalette, QFont
from PySide6.QtWidgets import QApplication, QWidget


class ThemeType(Enum):
    """Available theme types."""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"
    CUSTOM = "custom"


@dataclass
class ColorScheme:
    """Defines a complete color scheme for the application."""
    # Primary colors
    primary: str = "#00A8FF"
    primary_light: str = "#42BFFF"
    primary_dark: str = "#0078CC"
    
    # Secondary colors
    secondary: str = "#00D2D3"
    secondary_light: str = "#4DD8D9"
    secondary_dark: str = "#00A5A6"
    
    # Background colors
    background: str = "#1A1F2E"
    background_light: str = "#262B3D"
    background_dark: str = "#0F1419"
    
    # Surface colors
    surface: str = "#2A2F42"
    surface_light: str = "#353A4F"
    surface_dark: str = "#1F2435"
    
    # Text colors
    text_primary: str = "#FFFFFF"
    text_secondary: str = "#B0BEC5"
    text_disabled: str = "#546E7A"
    text_hint: str = "#78909C"
    
    # Accent colors
    success: str = "#4CAF50"
    warning: str = "#FF9800"
    error: str = "#F44336"
    info: str = "#2196F3"
    
    # Border and divider colors
    border: str = "#37414F"
    divider: str = "#2C3441"
    
    # Status colors
    online: str = "#4CAF50"
    offline: str = "#F44336"
    idle: str = "#FF9800"
    busy: str = "#9C27B0"


@dataclass
class ThemeConfig:
    """Complete theme configuration."""
    name: str
    display_name: str
    type: ThemeType
    colors: ColorScheme
    font_family: str = "Segoe UI"
    font_size: int = 10
    border_radius: int = 8
    shadow_enabled: bool = True
    animations_enabled: bool = True
    custom_properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_properties is None:
            self.custom_properties = {}


class ThemeManager(QObject):
    """
    Advanced theme manager with support for multiple themes,
    custom color schemes, and dynamic theme switching.
    """
    
    # Signals
    theme_changed = Signal(str)  # theme_name
    colors_updated = Signal(dict)  # color_dict
    font_changed = Signal(str, int)  # family, size
    
    def __init__(self):
        super().__init__()
        
        # Initialize built-in themes
        self.themes: Dict[str, ThemeConfig] = {}
        self.current_theme: Optional[ThemeConfig] = None
        self.custom_themes_dir = Path(__file__).parent.parent / "themes"
        
        # Create themes directory
        self.custom_themes_dir.mkdir(exist_ok=True)
        
        # Load built-in themes
        self._load_builtin_themes()
        
        # Load custom themes
        self._load_custom_themes()
        
        # Set default theme
        self.apply_theme("dark")
    
    def _load_builtin_themes(self):
        """Load built-in theme configurations."""
        
        # Dark Theme (Default)
        dark_colors = ColorScheme(
            primary="#00A8FF",
            primary_light="#42BFFF",
            primary_dark="#0078CC",
            secondary="#00D2D3",
            secondary_light="#4DD8D9",
            secondary_dark="#00A5A6",
            background="#1A1F2E",
            background_light="#262B3D",
            background_dark="#0F1419",
            surface="#2A2F42",
            surface_light="#353A4F",
            surface_dark="#1F2435",
            text_primary="#FFFFFF",
            text_secondary="#B0BEC5",
            text_disabled="#546E7A",
            text_hint="#78909C",
            success="#4CAF50",
            warning="#FF9800",
            error="#F44336",
            info="#2196F3",
            border="#37414F",
            divider="#2C3441",
            online="#4CAF50",
            offline="#F44336",
            idle="#FF9800",
            busy="#9C27B0"
        )
        
        self.themes["dark"] = ThemeConfig(
            name="dark",
            display_name="Dark Theme",
            type=ThemeType.DARK,
            colors=dark_colors,
            font_family="Segoe UI",
            font_size=10,
            border_radius=8,
            shadow_enabled=True,
            animations_enabled=True
        )
        
        # Improved Light Theme with better contrast
        light_colors = ColorScheme(
            primary="#1565C0",
            primary_light="#1976D2",
            primary_dark="#0D47A1",
            secondary="#00838F",
            secondary_light="#0097A7",
            secondary_dark="#006064",
            background="#F8F9FA",
            background_light="#FFFFFF",
            background_dark="#F0F2F5",
            surface="#FFFFFF",
            surface_light="#F5F7FA",
            surface_dark="#E8EBF0",
            text_primary="#212121",
            text_secondary="#424242",
            text_disabled="#9E9E9E",
            text_hint="#757575",
            success="#2E7D32",
            warning="#EF6C00",
            error="#C62828",
            info="#1565C0",
            border="#D1D5DB",
            divider="#E5E7EB",
            online="#2E7D32",
            offline="#C62828",
            idle="#EF6C00",
            busy="#7B1FA2"
        )
        
        self.themes["light"] = ThemeConfig(
            name="light",
            display_name="Light Theme",
            type=ThemeType.LIGHT,
            colors=light_colors,
            font_family="Segoe UI",
            font_size=10,
            border_radius=8,
            shadow_enabled=True,
            animations_enabled=True
        )
        
        # High Contrast Dark Theme
        high_contrast_colors = ColorScheme(
            primary="#00FFFF",
            primary_light="#66FFFF",
            primary_dark="#00CCCC",
            secondary="#FFFF00",
            secondary_light="#FFFF66",
            secondary_dark="#CCCC00",
            background="#000000",
            background_light="#1A1A1A",
            background_dark="#000000",
            surface="#1A1A1A",
            surface_light="#2A2A2A",
            surface_dark="#0A0A0A",
            text_primary="#FFFFFF",
            text_secondary="#CCCCCC",
            text_disabled="#666666",
            text_hint="#888888",
            success="#00FF00",
            warning="#FFAA00",
            error="#FF0000",
            info="#0099FF",
            border="#666666",
            divider="#444444",
            online="#00FF00",
            offline="#FF0000",
            idle="#FFAA00",
            busy="#FF00FF"
        )
        
        self.themes["high_contrast"] = ThemeConfig(
            name="high_contrast",
            display_name="High Contrast",
            type=ThemeType.DARK,
            colors=high_contrast_colors,
            font_family="Segoe UI",
            font_size=11,
            border_radius=4,
            shadow_enabled=False,
            animations_enabled=False
        )
        
        # Blue Theme
        blue_colors = ColorScheme(
            primary="#1E88E5",
            primary_light="#42A5F5",
            primary_dark="#1565C0",
            secondary="#26C6DA",
            secondary_light="#4DD0E1",
            secondary_dark="#00ACC1",
            background="#0D1421",
            background_light="#1A2332",
            background_dark="#050A0F",
            surface="#1A2332",
            surface_light="#253244",
            surface_dark="#0F1B28",
            text_primary="#E3F2FD",
            text_secondary="#90CAF9",
            text_disabled="#42A5F5",
            text_hint="#64B5F6",
            success="#00C853",
            warning="#FF8F00",
            error="#D32F2F",
            info="#1E88E5",
            border="#1976D2",
            divider="#1565C0",
            online="#00C853",
            offline="#D32F2F",
            idle="#FF8F00",
            busy="#7B1FA2"
        )
        
        self.themes["blue"] = ThemeConfig(
            name="blue",
            display_name="Blue Theme",
            type=ThemeType.DARK,
            colors=blue_colors,
            font_family="Segoe UI",
            font_size=10,
            border_radius=8,
            shadow_enabled=True,
            animations_enabled=True
        )
    
    def _load_custom_themes(self):
        """Load custom themes from the themes directory."""
        for theme_file in self.custom_themes_dir.glob("*.json"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                
                theme_config = self._dict_to_theme_config(theme_data)
                self.themes[theme_config.name] = theme_config
                
            except Exception as e:
                print(f"Error loading custom theme {theme_file}: {e}")
    
    def _dict_to_theme_config(self, data: Dict[str, Any]) -> ThemeConfig:
        """Convert dictionary to ThemeConfig object."""
        colors_data = data.get("colors", {})
        colors = ColorScheme(**colors_data)
        
        return ThemeConfig(
            name=data["name"],
            display_name=data.get("display_name", data["name"]),
            type=ThemeType(data.get("type", "custom")),
            colors=colors,
            font_family=data.get("font_family", "Segoe UI"),
            font_size=data.get("font_size", 10),
            border_radius=data.get("border_radius", 8),
            shadow_enabled=data.get("shadow_enabled", True),
            animations_enabled=data.get("animations_enabled", True),
            custom_properties=data.get("custom_properties", {})
        )
    
    def get_available_themes(self) -> List[Tuple[str, str]]:
        """Get list of available themes as (name, display_name) tuples."""
        return [(name, config.display_name) for name, config in self.themes.items()]
    
    def get_current_theme_name(self) -> str:
        """Get the name of the current theme."""
        return self.current_theme.name if self.current_theme else "dark"
    
    def get_theme_config(self, theme_name: str) -> Optional[ThemeConfig]:
        """Get theme configuration by name."""
        return self.themes.get(theme_name)
    
    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme to the application."""
        try:
            if theme_name not in self.themes:
                print(f"Theme '{theme_name}' not found")
                return False
            
            theme_config = self.themes[theme_name]
            self.current_theme = theme_config
            
            # Apply Qt palette
            self._apply_qt_palette(theme_config)
            
            # Apply custom stylesheets
            self._apply_custom_styles(theme_config)
            
            # Apply fonts
            self._apply_fonts(theme_config)
            
            # Emit signals
            self.theme_changed.emit(theme_name)
            self.colors_updated.emit(asdict(theme_config.colors))
            self.font_changed.emit(theme_config.font_family, theme_config.font_size)
            
            print(f"Applied theme: {theme_config.display_name}")
            return True
            
        except Exception as e:
            print(f"Error applying theme {theme_name}: {e}")
            return False
    
    def _apply_qt_palette(self, theme_config: ThemeConfig):
        """Apply color palette to Qt application."""
        app = QApplication.instance()
        if not app:
            return
        
        palette = QPalette()
        colors = theme_config.colors
        
        # Window colors
        palette.setColor(QPalette.Window, QColor(colors.background))
        palette.setColor(QPalette.WindowText, QColor(colors.text_primary))
        
        # Base colors (for input fields, etc.)
        palette.setColor(QPalette.Base, QColor(colors.surface))
        palette.setColor(QPalette.AlternateBase, QColor(colors.surface_light))
        
        # Text colors
        palette.setColor(QPalette.Text, QColor(colors.text_primary))
        palette.setColor(QPalette.BrightText, QColor(colors.text_primary))
        palette.setColor(QPalette.PlaceholderText, QColor(colors.text_hint))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor(colors.surface))
        palette.setColor(QPalette.ButtonText, QColor(colors.text_primary))
        
        # Highlight colors
        palette.setColor(QPalette.Highlight, QColor(colors.primary))
        palette.setColor(QPalette.HighlightedText, QColor(colors.text_primary))
        
        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors.text_disabled))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors.text_disabled))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors.text_disabled))
        
        app.setPalette(palette)
    
    def _apply_custom_styles(self, theme_config: ThemeConfig):
        """Apply custom stylesheets to the application."""
        app = QApplication.instance()
        if not app:
            return
        
        colors = theme_config.colors
        
        # Generate comprehensive stylesheet
        stylesheet = f"""
        /* Global Application Styles */
        QMainWindow {{
            background-color: {colors.background};
            color: {colors.text_primary};
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QWidget {{
            background-color: {colors.background};
            color: {colors.text_primary};
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        /* Tab Widget Styles */
        QTabWidget::pane {{
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            background-color: {colors.surface};
            margin-top: 2px;
        }}
        
        QTabBar::tab {{
            background-color: {colors.surface_dark};
            color: {colors.text_secondary};
            padding: 8px 16px;
            border: 1px solid {colors.border};
            border-bottom: none;
            border-top-left-radius: {theme_config.border_radius}px;
            border-top-right-radius: {theme_config.border_radius}px;
            margin-right: 2px;
            min-width: 80px;
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border-bottom: 1px solid {colors.surface};
            margin-bottom: -1px;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {colors.surface};
            color: {colors.text_primary};
        }}
        
        /* Button Styles */
        QPushButton {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px 16px;
            font-weight: 500;
            min-width: 80px;
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QPushButton:hover {{
            background-color: {colors.surface_light};
            border-color: {colors.primary};
        }}
        
        QPushButton:pressed {{
            background-color: {colors.surface_dark};
        }}
        
        QPushButton:disabled {{
            background-color: {colors.surface_dark};
            color: {colors.text_disabled};
            border-color: {colors.border};
        }}
        
        QPushButton.primary {{
            background-color: {colors.primary};
            color: {colors.text_primary if theme_config.type == ThemeType.DARK else '#FFFFFF'};
            border: none;
        }}
        
        QPushButton.primary:hover {{
            background-color: {colors.primary_light};
        }}
        
        QPushButton.primary:pressed {{
            background-color: {colors.primary_dark};
        }}
        
        QPushButton.success {{
            background-color: {colors.success};
            color: {colors.text_primary if theme_config.type == ThemeType.DARK else '#FFFFFF'};
            border: none;
        }}
        
        QPushButton.warning {{
            background-color: {colors.warning};
            color: {colors.text_primary if theme_config.type == ThemeType.DARK else '#FFFFFF'};
            border: none;
        }}
        
        QPushButton.error {{
            background-color: {colors.error};
            color: {colors.text_primary if theme_config.type == ThemeType.DARK else '#FFFFFF'};
            border: none;
        }}
        
        /* Input Field Styles */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px 12px;
            selection-background-color: {colors.primary};
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {colors.primary};
            outline: none;
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {colors.surface_dark};
            color: {colors.text_disabled};
        }}
        
        /* ComboBox Styles */
        QComboBox {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px 12px;
            min-width: 100px;
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QComboBox:hover {{
            border-color: {colors.primary};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {colors.text_secondary};
            margin-right: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors.surface};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            outline: none;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            color: {colors.text_primary};
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background-color: {colors.primary};
            color: {colors.text_primary if theme_config.type == ThemeType.DARK else '#FFFFFF'};
        }}
        
        /* List Widget Styles */
        QListWidget {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 8px 12px;
            border-bottom: 1px solid {colors.divider};
        }}
        
        QListWidget::item:selected {{
            background-color: {colors.primary};
            color: {colors.text_primary if theme_config.type == ThemeType.DARK else '#FFFFFF'};
        }}
        
        QListWidget::item:hover {{
            background-color: {colors.surface_light};
        }}
        
        /* GroupBox Styles */
        QGroupBox {{
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            margin-top: 12px;
            padding-top: 8px;
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px 0 8px;
            color: {colors.text_primary};
            font-weight: 600;
        }}
        
        /* Label Styles */
        QLabel {{
            color: {colors.text_primary};
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
            background-color: transparent;
        }}
        
        QLabel.secondary {{
            color: {colors.text_secondary};
        }}
        
        QLabel.hint {{
            color: {colors.text_hint};
        }}
        
        QLabel.success {{
            color: {colors.success};
        }}
        
        QLabel.warning {{
            color: {colors.warning};
        }}
        
        QLabel.error {{
            color: {colors.error};
        }}
        
        /* Progress Bar Styles */
        QProgressBar {{
            background-color: {colors.surface_dark};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            text-align: center;
            color: {colors.text_primary};
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors.primary};
            border-radius: {theme_config.border_radius - 1}px;
        }}
        
        /* Slider Styles */
        QSlider::groove:horizontal {{
            background-color: {colors.surface_dark};
            height: 6px;
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {colors.primary};
            border: 2px solid {colors.primary_light};
            width: 16px;
            height: 16px;
            border-radius: 8px;
            margin: -8px 0;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {colors.primary_light};
        }}
        
        /* CheckBox and RadioButton Styles */
        QCheckBox, QRadioButton {{
            color: {colors.text_primary};
            spacing: 8px;
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}
        
        QCheckBox::indicator:unchecked {{
            background-color: {colors.surface};
            border: 1px solid {colors.border};
            border-radius: 3px;
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors.primary};
            border: 1px solid {colors.primary};
            border-radius: 3px;
        }}
        
        QRadioButton::indicator:unchecked {{
            background-color: {colors.surface};
            border: 1px solid {colors.border};
            border-radius: 8px;
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {colors.primary};
            border: 1px solid {colors.primary};
            border-radius: 8px;
        }}
        
        /* SpinBox Styles */
        QSpinBox, QDoubleSpinBox {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px 12px;
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {colors.primary};
        }}
        
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            background-color: {colors.surface_light};
            border: 1px solid {colors.border};
            width: 16px;
        }}
        
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: {colors.primary};
        }}
        
        /* ScrollBar Styles */
        QScrollBar:vertical {{
            background-color: {colors.surface_dark};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors.border};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors.text_hint};
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors.surface_dark};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors.border};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors.text_hint};
        }}
        
        QScrollBar::add-line, QScrollBar::sub-line {{
            border: none;
            background: none;
        }}
        
        /* Menu and MenuBar Styles */
        QMenuBar {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border-bottom: 1px solid {colors.border};
        }}
        
        QMenuBar::item {{
            padding: 8px 12px;
            background-color: transparent;
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors.surface_light};
        }}
        
        QMenu {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
        }}
        
        QMenu::item {{
            padding: 8px 16px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors.primary};
            color: {colors.text_primary if theme_config.type == ThemeType.DARK else '#FFFFFF'};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {colors.divider};
            margin: 4px 0;
        }}
        
        /* ToolTip Styles */
        QToolTip {{
            background-color: {colors.surface_dark};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px 12px;
            font-size: {theme_config.font_size - 1}pt;
            font-family: '{theme_config.font_family}';
        }}
        
        /* Table Widget Styles */
        QTableWidget {{
            gridline-color: {colors.border};
            background-color: {colors.surface};
            alternate-background-color: {colors.surface_light};
            color: {colors.text_primary};
            selection-background-color: {colors.primary};
            font-family: '{theme_config.font_family}';
            font-size: {theme_config.font_size}pt;
        }}
        
        QHeaderView::section {{
            background-color: {colors.surface_light};
            color: {colors.text_primary};
            padding: 8px;
            border: 1px solid {colors.border};
            font-weight: 600;
        }}
        
        /* Status Colors */
        .status-online {{
            color: {colors.online};
        }}
        
        .status-offline {{
            color: {colors.offline};
        }}
        
        .status-idle {{
            color: {colors.idle};
        }}
        
        .status-busy {{
            color: {colors.busy};
        }}
        """
        
        app.setStyleSheet(stylesheet)
    
    def _apply_fonts(self, theme_config: ThemeConfig):
        """Apply font settings to the application."""
        app = QApplication.instance()
        if not app:
            return
        
        font = QFont(theme_config.font_family, theme_config.font_size)
        app.setFont(font)
    
    def create_custom_theme(self, name: str, display_name: str, base_theme: str, 
                          color_overrides: Dict[str, str]) -> bool:
        """Create a custom theme based on an existing theme with color overrides."""
        try:
            if base_theme not in self.themes:
                print(f"Base theme '{base_theme}' not found")
                return False
            
            # Copy base theme
            base_config = self.themes[base_theme]
            colors_dict = asdict(base_config.colors)
            
            # Apply color overrides
            colors_dict.update(color_overrides)
            custom_colors = ColorScheme(**colors_dict)
            
            # Create custom theme config
            custom_config = ThemeConfig(
                name=name,
                display_name=display_name,
                type=ThemeType.CUSTOM,
                colors=custom_colors,
                font_family=base_config.font_family,
                font_size=base_config.font_size,
                border_radius=base_config.border_radius,
                shadow_enabled=base_config.shadow_enabled,
                animations_enabled=base_config.animations_enabled
            )
            
            # Save theme
            self.themes[name] = custom_config
            self.save_custom_theme(custom_config)
            
            print(f"Created custom theme: {display_name}")
            return True
            
        except Exception as e:
            print(f"Error creating custom theme: {e}")
            return False
    
    def save_custom_theme(self, theme_config: ThemeConfig) -> bool:
        """Save a custom theme to file."""
        try:
            theme_file = self.custom_themes_dir / f"{theme_config.name}.json"
            theme_data = asdict(theme_config)
            
            with open(theme_file, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving custom theme: {e}")
            return False
    
    def delete_custom_theme(self, theme_name: str) -> bool:
        """Delete a custom theme."""
        try:
            if theme_name not in self.themes:
                return False
            
            theme_config = self.themes[theme_name]
            if theme_config.type != ThemeType.CUSTOM:
                print("Cannot delete built-in theme")
                return False
            
            # Remove from memory
            del self.themes[theme_name]
            
            # Remove file
            theme_file = self.custom_themes_dir / f"{theme_name}.json"
            if theme_file.exists():
                theme_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error deleting custom theme: {e}")
            return False
    
    def get_color(self, color_name: str) -> Optional[str]:
        """Get a color value from the current theme."""
        if not self.current_theme:
            return None
        
        return getattr(self.current_theme.colors, color_name, None)
    
    def get_colors_dict(self) -> Dict[str, str]:
        """Get all colors from the current theme as a dictionary."""
        if not self.current_theme:
            return {}
        
        return asdict(self.current_theme.colors)
    
    def update_theme_property(self, property_name: str, value: Any) -> bool:
        """Update a property of the current theme."""
        try:
            if not self.current_theme:
                return False
            
            if hasattr(self.current_theme, property_name):
                setattr(self.current_theme, property_name, value)
                
                # Re-apply theme if it's a visual property
                if property_name in ['font_family', 'font_size', 'border_radius']:
                    self.apply_theme(self.current_theme.name)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating theme property: {e}")
            return False