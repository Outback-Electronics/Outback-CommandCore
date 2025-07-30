"""
Professional About Dialog for CommandCore Launcher

Provides comprehensive application information, system details,
credits, and licensing information with modern styling.
"""

import sys
import platform
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTabWidget, QTextEdit,
    QFrame, QScrollArea, QGroupBox, QApplication,
    QSizePolicy, QSpacerItem, QWidget
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import (
    QPixmap, QIcon, QPainter, QColor, QLinearGradient,
    QFont, QBrush, QPen, QDesktopServices, QCursor
)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from PySide6 import __version__ as pyside_version
except ImportError:
    pyside_version = "Unknown"


class AnimatedLogoLabel(QLabel):
    """Animated logo with subtle glow effect."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(120, 120)
        self.setAlignment(Qt.AlignCenter)
        
        # Animation properties
        self._glow_radius = 0
        self._setup_animation()
    
    def _setup_animation(self):
        """Setup the glow animation."""
        self.glow_animation = QPropertyAnimation(self, b"glow_radius")
        self.glow_animation.setDuration(2000)
        self.glow_animation.setStartValue(0)
        self.glow_animation.setEndValue(20)
        self.glow_animation.setLoopCount(-1)
        self.glow_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.glow_animation.start()
    
    def get_glow_radius(self):
        return self._glow_radius
    
    def set_glow_radius(self, radius):
        self._glow_radius = radius
        self.update()
    
    glow_radius = property(get_glow_radius, set_glow_radius)
    
    def paintEvent(self, event):
        """Paint the animated logo."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw background circle with glow
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 10
        
        # Glow effect
        if self._glow_radius > 0:
            glow_color = QColor(0, 168, 255, 30)
            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                center.x() - radius - self._glow_radius,
                center.y() - radius - self._glow_radius,
                (radius + self._glow_radius) * 2,
                (radius + self._glow_radius) * 2
            )
        
        # Main circle
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(0, 168, 255))
        gradient.setColorAt(1, QColor(0, 210, 211))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
        painter.drawEllipse(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2
        )
        
        # Draw "CC" text
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "CC")
        
        painter.end()


class ClickableLabel(QLabel):
    """Clickable label that opens URLs."""
    
    def __init__(self, text, url=None, parent=None):
        super().__init__(text, parent)
        
        self.url = url
        if url:
            self.setCursor(QCursor(Qt.PointingHandCursor))
            self.setStyleSheet("""
                QLabel {
                    color: #00A8FF;
                    text-decoration: underline;
                }
                QLabel:hover {
                    color: #42BFFF;
                }
            """)
    
    def mousePressEvent(self, event):
        """Handle mouse press to open URL."""
        if event.button() == Qt.LeftButton and self.url:
            QDesktopServices.openUrl(self.url)
        super().mousePressEvent(event)


class SystemInfoWidget(QWidget):
    """Widget displaying comprehensive system information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._load_system_info()
    
    def _setup_ui(self):
        """Setup the system info UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Create info groups
        groups = [
            ("Operating System", self._get_os_info),
            ("Hardware", self._get_hardware_info),
            ("Python Environment", self._get_python_info),
            ("Application Environment", self._get_app_info)
        ]
        
        for group_name, info_func in groups:
            group = self._create_info_group(group_name, info_func())
            layout.addWidget(group)
        
        layout.addStretch()
    
    def _create_info_group(self, title: str, info_dict: Dict[str, str]) -> QGroupBox:
        """Create an information group."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
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
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(8)
        
        for row, (key, value) in enumerate(info_dict.items()):
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet("font-weight: 500; color: #B0BEC5;")
            layout.addWidget(key_label, row, 0)
            
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setStyleSheet("color: #FFFFFF;")
            layout.addWidget(value_label, row, 1)
        
        return group
    
    def _load_system_info(self):
        """Load system information."""
        pass  # Info is loaded in the getter methods
    
    def _get_os_info(self) -> Dict[str, str]:
        """Get operating system information."""
        info = {
            "Operating System": platform.system(),
            "OS Version": platform.release(),
            "OS Build": platform.version(),
            "Architecture": platform.machine(),
            "Hostname": platform.node(),
            "Platform": platform.platform()
        }
        
        if PSUTIL_AVAILABLE:
            try:
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.now() - boot_time
                days = uptime.days
                hours, remainder = divmod(uptime.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                if days > 0:
                    uptime_str = f"{days}d {hours}h {minutes}m"
                elif hours > 0:
                    uptime_str = f"{hours}h {minutes}m"
                else:
                    uptime_str = f"{minutes}m"
                
                info["System Uptime"] = uptime_str
            except Exception:
                pass
        
        return info
    
    def _get_hardware_info(self) -> Dict[str, str]:
        """Get hardware information."""
        info = {
            "Processor": platform.processor() or "Unknown"
        }
        
        if PSUTIL_AVAILABLE:
            try:
                # CPU information
                info["CPU Cores"] = f"{psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical"
                
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    info["CPU Frequency"] = f"{cpu_freq.current:.0f} MHz (max: {cpu_freq.max:.0f} MHz)"
                
                # Memory information
                memory = psutil.virtual_memory()
                info["Total Memory"] = f"{memory.total / (1024**3):.1f} GB"
                info["Available Memory"] = f"{memory.available / (1024**3):.1f} GB"
                info["Memory Usage"] = f"{memory.percent}%"
                
                # Disk information
                disk = psutil.disk_usage('/')
                info["Total Disk Space"] = f"{disk.total / (1024**3):.1f} GB"
                info["Free Disk Space"] = f"{disk.free / (1024**3):.1f} GB"
                info["Disk Usage"] = f"{(disk.used / disk.total * 100):.1f}%"
                
            except Exception as e:
                info["Hardware Info Error"] = str(e)
        else:
            info["Note"] = "Install psutil for detailed hardware information"
        
        return info
    
    def _get_python_info(self) -> Dict[str, str]:
        """Get Python environment information."""
        info = {
            "Python Version": platform.python_version(),
            "Python Implementation": platform.python_implementation(),
            "Python Compiler": platform.python_compiler(),
            "Python Executable": sys.executable,
            "PySide6 Version": pyside_version,
        }
        
        try:
            import pip
            info["Pip Version"] = pip.__version__
        except (ImportError, AttributeError):
            pass
        
        return info
    
    def _get_app_info(self) -> Dict[str, str]:
        """Get application environment information."""
        app_dir = Path(__file__).parent
        
        info = {
            "Application Directory": str(app_dir),
            "Configuration Directory": str(app_dir / "config"),
            "Data Directory": str(app_dir / "data"),
            "Current Working Directory": str(Path.cwd()),
        }
        
        # Check for Git information
        git_dir = app_dir / ".git"
        if git_dir.exists():
            try:
                import git
                repo = git.Repo(app_dir)
                info["Git Branch"] = repo.active_branch.name
                info["Git Commit"] = repo.head.commit.hexsha[:8]
                info["Git Remote"] = repo.remotes.origin.url if repo.remotes else "No remote"
            except Exception:
                info["Git"] = "Repository detected (GitPython not available)"
        
        return info


class AboutDialog(QDialog):
    """
    Professional About Dialog for CommandCore Launcher.
    
    Features:
    - Animated logo with glow effects
    - Comprehensive application information
    - System information display
    - Credits and acknowledgments
    - License information
    - Contact details and links
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("About CommandCore Launcher")
        self.setFixedSize(600, 700)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        self._setup_ui()
        self._apply_styles()
        self._center_on_parent()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header section
        header = self._create_header_section()
        main_layout.addWidget(header)
        
        # Tab widget
        tab_widget = QTabWidget()
        tab_widget.setObjectName("aboutTabs")
        
        # About tab
        about_tab = self._create_about_tab()
        tab_widget.addTab(about_tab, "About")
        
        # System info tab
        system_tab = SystemInfoWidget()
        tab_widget.addTab(system_tab, "System Info")
        
        # Credits tab
        credits_tab = self._create_credits_tab()
        tab_widget.addTab(credits_tab, "Credits")
        
        # License tab
        license_tab = self._create_license_tab()
        tab_widget.addTab(license_tab, "License")
        
        main_layout.addWidget(tab_widget)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(20, 10, 20, 20)
        
        buttons_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setFixedSize(100, 36)
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        buttons_layout.addWidget(close_button)
        
        main_layout.addLayout(buttons_layout)
    
    def _create_header_section(self) -> QWidget:
        """Create the header section with logo and basic info."""
        header = QFrame()
        header.setObjectName("aboutHeader")
        header.setFixedHeight(180)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        # Animated logo
        logo = AnimatedLogoLabel()
        layout.addWidget(logo)
        
        # App info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        # App name
        app_name = QLabel("CommandCore Launcher")
        app_name.setObjectName("appName")
        info_layout.addWidget(app_name)
        
        # Version
        version_label = QLabel("Version 2.0.0")
        version_label.setObjectName("appVersion")
        info_layout.addWidget(version_label)
        
        # Description
        description = QLabel(
            "Professional application management suite for\n"
            "launching, monitoring, and controlling CommandCore\n"
            "applications with modern interface and real-time\n"
            "system monitoring capabilities."
        )
        description.setObjectName("appDescription")
        description.setWordWrap(True)
        info_layout.addWidget(description)
        
        # Copyright
        copyright_label = QLabel(f"© {datetime.now().year} Outback Electronics. All rights reserved.")
        copyright_label.setObjectName("copyright")
        info_layout.addWidget(copyright_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        return header
    
    def _create_about_tab(self) -> QWidget:
        """Create the main about tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Key features
        features_group = QGroupBox("Key Features")
        features_layout = QVBoxLayout(features_group)
        
        features = [
            "• Modern, responsive user interface with customizable themes",
            "• Real-time system monitoring with performance charts",
            "• Comprehensive application management and control",
            "• Advanced configuration system with live preview",
            "• Professional notification system with custom styling",
            "• Cross-platform compatibility (Windows, macOS, Linux)",
            "• Centralized state management with persistence",
            "• Professional logging and debugging capabilities",
            "• Extensible architecture with plugin support",
            "• Built with modern Python and Qt technologies"
        ]
        
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setWordWrap(True)
            feature_label.setStyleSheet("color: #B0BEC5; margin: 2px 0;")
            features_layout.addWidget(feature_label)
        
        layout.addWidget(features_group)
        
        # Technical specifications
        tech_group = QGroupBox("Technical Specifications")
        tech_layout = QGridLayout(tech_group)
        
        tech_specs = {
            "Framework": "PySide6 (Qt for Python)",
            "Language": "Python 3.8+",
            "Architecture": "MVP with Signal-Slot Communication",
            "Minimum RAM": "512 MB",
            "Recommended RAM": "2 GB",
            "Disk Space": "100 MB",
            "Supported OS": "Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+)"
        }
        
        for row, (key, value) in enumerate(tech_specs.items()):
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet("font-weight: 500; color: #B0BEC5;")
            tech_layout.addWidget(key_label, row, 0)
            
            value_label = QLabel(value)
            value_label.setStyleSheet("color: #FFFFFF;")
            tech_layout.addWidget(value_label, row, 1)
        
        layout.addWidget(tech_group)
        
        # Contact information
        contact_group = QGroupBox("Contact & Support")
        contact_layout = QVBoxLayout(contact_group)
        
        contact_info = [
            ("Website:", "https://outbackelectronics.com", "https://outbackelectronics.com"),
            ("Support Email:", "support@outbackelectronics.com", "mailto:support@outbackelectronics.com"),
            ("Documentation:", "https://docs.commandcore.org", "https://docs.commandcore.org"),
            ("Issue Tracker:", "GitHub Issues", "https://github.com/outback-electronics/commandcore-launcher/issues"),
            ("Source Code:", "GitHub Repository", "https://github.com/outback-electronics/commandcore-launcher")
        ]
        
        for label_text, display_text, url in contact_info:
            contact_layout_row = QHBoxLayout()
            
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: 500; color: #B0BEC5;")
            label.setFixedWidth(120)
            contact_layout_row.addWidget(label)
            
            link = ClickableLabel(display_text, url)
            contact_layout_row.addWidget(link)
            
            contact_layout_row.addStretch()
            contact_layout.addLayout(contact_layout_row)
        
        layout.addWidget(contact_group)
        layout.addStretch()
        
        return tab
    
    def _create_credits_tab(self) -> QWidget:
        """Create the credits tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Development team
        dev_group = QGroupBox("Development Team")
        dev_layout = QVBoxLayout(dev_group)
        
        dev_credits = [
            ("Lead Developer", "Outback Electronics Development Team"),
            ("UI/UX Design", "Modern Interface Design Team"),
            ("System Integration", "CommandCore Architecture Team"),
            ("Quality Assurance", "Professional Testing Team"),
            ("Documentation", "Technical Writing Team")
        ]
        
        for role, name in dev_credits:
            credit_layout = QHBoxLayout()
            
            role_label = QLabel(f"{role}:")
            role_label.setStyleSheet("font-weight: 500; color: #B0BEC5;")
            role_label.setFixedWidth(150)
            credit_layout.addWidget(role_label)
            
            name_label = QLabel(name)
            name_label.setStyleSheet("color: #FFFFFF;")
            credit_layout.addWidget(name_label)
            
            credit_layout.addStretch()
            dev_layout.addLayout(credit_layout)
        
        layout.addWidget(dev_group)
        
        # Third-party libraries
        libs_group = QGroupBox("Third-Party Libraries & Acknowledgments")
        libs_layout = QVBoxLayout(libs_group)
        
        libraries = [
            ("PySide6", "Qt for Python - Cross-platform GUI framework", "https://pyside.org"),
            ("psutil", "System and process monitoring library", "https://github.com/giampaolo/psutil"),
            ("GitPython", "Git repository interaction library", "https://github.com/gitpython-developers/GitPython"),
            ("Python", "Programming language and runtime", "https://python.org"),
            ("Qt Framework", "Cross-platform application framework", "https://qt.io"),
        ]
        
        for name, description, url in libraries:
            lib_frame = QFrame()
            lib_frame.setStyleSheet("margin: 4px 0; padding: 8px; background-color: rgba(255,255,255,0.05); border-radius: 6px;")
            
            lib_layout = QVBoxLayout(lib_frame)
            lib_layout.setSpacing(4)
            
            name_link = ClickableLabel(name, url)
            name_link.setStyleSheet("font-weight: 600; color: #00A8FF; font-size: 12pt;")
            lib_layout.addWidget(name_link)
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #B0BEC5; font-size: 10pt;")
            desc_label.setWordWrap(True)
            lib_layout.addWidget(desc_label)
            
            libs_layout.addWidget(lib_frame)
        
        layout.addWidget(libs_group)
        
        # Special thanks
        thanks_group = QGroupBox("Special Thanks")
        thanks_layout = QVBoxLayout(thanks_group)
        
        thanks_text = QLabel(
            "Special thanks to the open-source community, Qt/PySide6 developers, "
            "Python core team, and all contributors who make professional software "
            "development possible. This application stands on the shoulders of giants "
            "in the software development community."
        )
        thanks_text.setWordWrap(True)
        thanks_text.setStyleSheet("color: #B0BEC5; font-style: italic; padding: 10px;")
        thanks_layout.addWidget(thanks_text)
        
        layout.addWidget(thanks_group)
        layout.addStretch()
        
        return tab
    
    def _create_license_tab(self) -> QWidget:
        """Create the license tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # License header
        license_header = QLabel("MIT License")
        license_header.setStyleSheet("font-size: 16pt; font-weight: bold; color: #00A8FF; margin-bottom: 10px;")
        layout.addWidget(license_header)
        
        # License text
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setStyleSheet("""
            QTextEdit {
                background-color: #1A1F2E;
                color: #B0BEC5;
                border: 1px solid #37414F;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 9pt;
                line-height: 1.4;
            }
        """)
        
        license_content = f"""MIT License

Copyright (c) {datetime.now().year} Outback Electronics

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

THIRD-PARTY LICENSES:

This software includes third-party libraries with their own licenses:

• PySide6: Licensed under LGPL/Commercial License
• psutil: Licensed under BSD License  
• GitPython: Licensed under BSD License
• Python: Licensed under Python Software Foundation License

For complete third-party license information, please refer to the respective
library documentation and license files.

DISCLAIMER:

This software is provided "as is" and any express or implied warranties,
including, but not limited to, the implied warranties of merchantability
and fitness for a particular purpose are disclaimed. In no event shall
Outback Electronics be liable for any direct, indirect, incidental, special,
exemplary, or consequential damages (including, but not limited to,
procurement of substitute goods or services; loss of use, data, or profits;
or business interruption) however caused and on any theory of liability,
whether in contract, strict liability, or tort (including negligence or
otherwise) arising in any way out of the use of this software, even if
advised of the possibility of such damage.
"""
        
        license_text.setPlainText(license_content)
        layout.addWidget(license_text)
        
        return tab
    
    def _apply_styles(self):
        """Apply custom styles to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1A1F2E;
                color: #FFFFFF;
            }
            
            QFrame#aboutHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2A2F42, stop:1 #353A4F);
                border-bottom: 1px solid #37414F;
            }
            
            QLabel#appName {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: bold;
            }
            
            QLabel#appVersion {
                color: #00A8FF;
                font-size: 16px;
                font-weight: 600;
            }
            
            QLabel#appDescription {
                color: #B0BEC5;
                font-size: 12px;
                line-height: 1.4;
            }
            
            QLabel#copyright {
                color: #78909C;
                font-size: 10px;
                font-style: italic;
            }
            
            QTabWidget#aboutTabs::pane {
                border: 1px solid #37414F;
                border-top: none;
            }
            
            QTabWidget#aboutTabs QTabBar::tab {
                background-color: #353A4F;
                color: #B0BEC5;
                padding: 10px 20px;
                border: 1px solid #37414F;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            
            QTabWidget#aboutTabs QTabBar::tab:selected {
                background-color: #1A1F2E;
                color: #FFFFFF;
                border-bottom: 1px solid #1A1F2E;
            }
            
            QTabWidget#aboutTabs QTabBar::tab:hover:!selected {
                background-color: #3E4358;
            }
            
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
                background-color: #1A1F2E;
            }
            
            QPushButton {
                background-color: #00A8FF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background-color: #42BFFF;
            }
            
            QPushButton:pressed {
                background-color: #0078CC;
            }
        """)
    
    def _center_on_parent(self):
        """Center the dialog on the parent window."""
        if self.parent():
            parent_rect = self.parent().geometry()
            dialog_rect = self.geometry()
            
            x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            
            self.move(x, y)
        else:
            # Center on screen
            screen = QApplication.primaryScreen().availableGeometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)


def show_about_dialog(parent=None):
    """Convenience function to show the about dialog."""
    dialog = AboutDialog(parent)
    return dialog.exec()


if __name__ == "__main__":
    # Test the about dialog
    app = QApplication(sys.argv)
    dialog = AboutDialog()
    dialog.show()
    sys.exit(app.exec())