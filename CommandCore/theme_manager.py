"""
Modern Theme Manager for CommandCore Launcher - FIXED VERSION

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
    custom color schemes, and dynamic theme switching - FIXED VERSION.
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
    
    def set_theme(self, theme_name: str) -> bool:
        """Apply a theme by name - FIXED METHOD NAME for backward compatibility."""
        return self.apply_theme(theme_name)
    
    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme by name."""
        try:
            if theme_name not in self.themes:
                print(f"Theme '{theme_name}' not found")
                return False
            
            theme_config = self.themes[theme_name]
            self.current_theme = theme_config
            
            # Apply to Qt application
            app = QApplication.instance()
            if app:
                self._apply_theme_to_app(app, theme_config)
            
            # Emit signals
            self.theme_changed.emit(theme_name)
            self.colors_updated.emit(self.get_colors_dict())
            self.font_changed.emit(theme_config.font_family, theme_config.font_size)
            
            print(f"Applied theme: {theme_config.display_name}")
            return True
            
        except Exception as e:
            print(f"Error applying theme: {e}")
            return False
    
    def get_current_theme_name(self) -> str:
        """Get the name of the currently active theme."""
        if self.current_theme:
            return self.current_theme.name
        return "dark"  # Default fallback
    
    def get_available_themes(self) -> List[Tuple[str, str]]:
        """Get list of available themes as (name, display_name) tuples."""
        return [(name, config.display_name) for name, config in self.themes.items()]
    
    def get_theme_config(self, theme_name: str) -> Optional[ThemeConfig]:
        """Get theme configuration by name."""
        return self.themes.get(theme_name)
    
    def _apply_theme_to_app(self, app: QApplication, theme_config: ThemeConfig):
        """Apply theme configuration to the Qt application."""
        try:
            # Apply palette colors
            palette = self._create_palette_from_theme(theme_config)
            app.setPalette(palette)
            
            # Apply font
            self._apply_font_to_app(app, theme_config)
            
            # Apply custom stylesheet
            stylesheet = self._generate_stylesheet(theme_config)
            app.setStyleSheet(stylesheet)
            
        except Exception as e:
            print(f"Error applying theme to app: {e}")
    
    def _create_palette_from_theme(self, theme_config: ThemeConfig) -> QPalette:
        """Create Qt palette from theme configuration."""
        palette = QPalette()
        colors = theme_config.colors
        
        # Window colors
        palette.setColor(QPalette.Window, QColor(colors.background))
        palette.setColor(QPalette.WindowText, QColor(colors.text_primary))
        
        # Base colors (input fields, etc.)
        palette.setColor(QPalette.Base, QColor(colors.surface))
        palette.setColor(QPalette.AlternateBase, QColor(colors.surface_light))
        
        # Text colors
        palette.setColor(QPalette.Text, QColor(colors.text_primary))
        palette.setColor(QPalette.BrightText, QColor(colors.text_primary))
        palette.setColor(QPalette.ButtonText, QColor(colors.text_primary))
        
        # Button colors
        palette.setColor(QPalette.Button, QColor(colors.surface))
        palette.setColor(QPalette.Highlight, QColor(colors.primary))
        palette.setColor(QPalette.HighlightedText, QColor(colors.text_primary))
        
        # Disabled colors
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors.text_disabled))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors.text_disabled))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors.text_disabled))
        
        return palette
    
    def _apply_font_to_app(self, app: QApplication, theme_config: ThemeConfig):
        """Apply font configuration to the application."""
        font = QFont(theme_config.font_family, theme_config.font_size)
        app.setFont(font)
    
    def _generate_stylesheet(self, theme_config: ThemeConfig) -> str:
        """Generate comprehensive stylesheet from theme configuration."""
        colors = theme_config.colors
        
        # Base stylesheet with theme colors
        stylesheet = f"""
        /* Main Application Styling */
        QMainWindow {{
            background-color: {colors.background};
            color: {colors.text_primary};
        }}
        
        /* Tabs */
        QTabWidget::pane {{
            border: 1px solid {colors.border};
            background-color: {colors.surface};
            border-radius: {theme_config.border_radius}px;
        }}
        
        QTabBar::tab {{
            background-color: {colors.background_light};
            color: {colors.text_secondary};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: {theme_config.border_radius}px;
            border-top-right-radius: {theme_config.border_radius}px;
            min-width: 120px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border-bottom: 2px solid {colors.primary};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors.surface_light};
            color: {colors.text_primary};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px 16px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background-color: {colors.surface_light};
            border-color: {colors.primary};
        }}
        
        QPushButton:pressed {{
            background-color: {colors.surface_dark};
        }}
        
        QPushButton:disabled {{
            background-color: {colors.background_dark};
            color: {colors.text_disabled};
            border-color: {colors.divider};
        }}
        
        /* Primary Buttons */
        QPushButton[class="primary"] {{
            background-color: {colors.primary};
            color: white;
            border-color: {colors.primary_dark};
        }}
        
        QPushButton[class="primary"]:hover {{
            background-color: {colors.primary_light};
        }}
        
        QPushButton[class="primary"]:pressed {{
            background-color: {colors.primary_dark};
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px;
            selection-background-color: {colors.primary};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {colors.primary};
        }}
        
        /* Combo Boxes */
        QComboBox {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px;
            min-width: 120px;
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
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors.text_secondary};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            selection-background-color: {colors.primary};
            border-radius: {theme_config.border_radius}px;
        }}
        
        /* List Widgets */
        QListWidget {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            alternate-background-color: {colors.surface_light};
        }}
        
        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {colors.divider};
        }}
        
        QListWidget::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        QListWidget::item:hover {{
            background-color: {colors.surface_light};
        }}
        
        /* Tree Widgets */
        QTreeWidget {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            alternate-background-color: {colors.surface_light};
        }}
        
        QTreeWidget::item {{
            padding: 4px;
            border-bottom: 1px solid {colors.divider};
        }}
        
        QTreeWidget::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        QTreeWidget::item:hover {{
            background-color: {colors.surface_light};
        }}
        
        /* Progress Bars */
        QProgressBar {{
            background-color: {colors.surface_dark};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            text-align: center;
            color: {colors.text_primary};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors.primary};
            border-radius: {theme_config.border_radius}px;
        }}
        
        /* Sliders */
        QSlider::groove:horizontal {{
            background-color: {colors.surface_dark};
            height: 6px;
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {colors.primary};
            width: 18px;
            height: 18px;
            border-radius: 9px;
            margin: -6px 0;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {colors.primary_light};
        }}
        
        /* Checkboxes */
        QCheckBox {{
            color: {colors.text_primary};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {colors.border};
            border-radius: 3px;
            background-color: {colors.surface};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors.primary};
            border-color: {colors.primary_dark};
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {colors.primary};
        }}
        
        /* Radio Buttons */
        QRadioButton {{
            color: {colors.text_primary};
            spacing: 8px;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {colors.border};
            border-radius: 9px;
            background-color: {colors.surface};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {colors.primary};
            border-color: {colors.primary_dark};
        }}
        
        QRadioButton::indicator:hover {{
            border-color: {colors.primary};
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {colors.background_dark};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors.surface_light};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors.primary};
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors.background_dark};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors.surface_light};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors.primary};
        }}
        
        /* Group Boxes */
        QGroupBox {{
            color: {colors.text_primary};
            font-weight: 600;
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            margin-top: 8px;
            padding-top: 8px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            background-color: {colors.surface};
        }}
        
        /* Menus */
        QMenu {{
            background-color: {colors.surface};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 16px;
            border-radius: {theme_config.border_radius}px;
        }}
        
        QMenu::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {colors.divider};
            margin: 4px 8px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {colors.background_light};
            color: {colors.text_secondary};
            border-top: 1px solid {colors.border};
        }}
        
        /* Tool Tips */
        QToolTip {{
            background-color: {colors.surface_dark};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: {theme_config.border_radius}px;
            padding: 8px;
        }}
        
        /* Splitters */
        QSplitter::handle {{
            background-color: {colors.border};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        """
        
        return stylesheet
    
    def _load_builtin_themes(self):
        """Load built-in theme configurations."""
        
        # Dark Theme (default)
        dark_colors = ColorScheme()  # Use defaults
        
        self.themes["dark"] = ThemeConfig(
            name="dark",
            display_name="Dark Theme",
            type=ThemeType.DARK,
            colors=dark_colors
        )
        
        # Light Theme
        light_colors = ColorScheme(
            primary="#1976D2",
            primary_light="#42A5F5",
            primary_dark="#1565C0",
            secondary="#00796B",
            secondary_light="#4DB6AC",
            secondary_dark="#00695C",
            background="#FAFAFA",
            background_light="#FFFFFF",
            background_dark="#F5F5F5",
            surface="#FFFFFF",
            surface_light="#F8F8F8",
            surface_dark="#F0F0F0",
            text_primary="#212121",
            text_secondary="#757575",
            text_disabled="#BDBDBD",
            text_hint="#9E9E9E",
            success="#388E3C",
            warning="#F57C00",
            error="#D32F2F",
            info="#1976D2",
            border="#E0E0E0",
            divider="#EEEEEE",
            online="#4CAF50",
            offline="#F44336",
            idle="#FF9800",
            busy="#9C27B0"
        )
        
        self.themes["light"] = ThemeConfig(
            name="light",
            display_name="Light Theme",
            type=ThemeType.LIGHT,
            colors=light_colors
        )
        
        # High Contrast Theme
        high_contrast_colors = ColorScheme(
            primary="#FFFF00",
            primary_light="#FFFF99",
            primary_dark="#CCCC00",
            secondary="#00FFFF",
            secondary_light="#99FFFF",
            secondary_dark="#00CCCC",
            background="#000000",
            background_light="#1A1A1A",
            background_dark="#0A0A0A",
            surface="#1A1A1A",
            surface_light="#2A2A2A",
            surface_dark="#0F0F0F",
            text_primary="#FFFFFF",
            text_secondary="#CCCCCC",
            text_disabled="#808080",
            text_hint="#999999",
            success="#00FF00",
            warning="#FFAA00",
            error="#FF0000",
            info="#0099FF",
            border="#FFFFFF",
            divider="#808080",
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
            display_name=data["display_name"],
            type=ThemeType(data["type"]),
            colors=colors,
            font_family=data.get("font_family", "Segoe UI"),
            font_size=data.get("font_size", 10),
            border_radius=data.get("border_radius", 8),
            shadow_enabled=data.get("shadow_enabled", True),
            animations_enabled=data.get("animations_enabled", True),
            custom_properties=data.get("custom_properties", {})
        )
    
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