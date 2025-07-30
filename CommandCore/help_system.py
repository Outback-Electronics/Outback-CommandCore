"""
Professional Help System for CommandCore Launcher

Provides comprehensive help functionality including context-sensitive help,
keyboard shortcuts, tooltips, and user guide integration.
"""

import sys
import json
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QTabWidget,
    QFrame, QScrollArea, QGroupBox, QApplication,
    QTreeWidget, QTreeWidgetItem, QSplitter, QLineEdit,
    QComboBox, QMessageBox, QWidget, QListWidget, QListWidgetItem
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QObject, QEvent,
    QUrl, QSize
)
from PySide6.QtGui import (
    QFont, QKeySequence, QIcon, QPixmap, QPainter,
    QColor, QDesktopServices, QCursor, QShortcut
)


class HelpTopicType(Enum):
    """Types of help topics."""
    OVERVIEW = "overview"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    FAQ = "faq"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class HelpTopic:
    """Individual help topic."""
    id: str
    title: str
    content: str
    type: HelpTopicType
    keywords: List[str]
    related_topics: List[str] = None
    shortcuts: List[str] = None
    
    def __post_init__(self):
        if self.related_topics is None:
            self.related_topics = []
        if self.shortcuts is None:
            self.shortcuts = []


class ContextualHelp(QObject):
    """Manages context-sensitive help for widgets."""
    
    def __init__(self):
        super().__init__()
        
        self.context_map: Dict[str, str] = {}
        self.widget_tooltips: Dict[QWidget, str] = {}
    
    def register_context(self, widget: QWidget, help_topic_id: str, tooltip: str = None):
        """Register a widget for contextual help."""
        widget_id = f"{widget.__class__.__name__}_{id(widget)}"
        self.context_map[widget_id] = help_topic_id
        
        if tooltip:
            self.widget_tooltips[widget] = tooltip
            widget.setToolTip(tooltip)
        
        # Install event filter for F1 key
        widget.installEventFilter(self)
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter events to catch F1 key presses."""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_F1:
            self.show_context_help(obj)
            return True
        return super().eventFilter(obj, event)
    
    def show_context_help(self, widget: QWidget):
        """Show contextual help for a widget."""
        widget_id = f"{widget.__class__.__name__}_{id(widget)}"
        help_topic_id = self.context_map.get(widget_id)
        
        if help_topic_id:
            help_system = HelpSystem.get_instance()
            if help_system:
                help_system.show_topic(help_topic_id)
        else:
            # Show general help if no specific context
            help_system = HelpSystem.get_instance()
            if help_system:
                help_system.show_help_dialog()


class KeyboardShortcutsWidget(QWidget):
    """Widget displaying keyboard shortcuts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._load_shortcuts()
    
    def _setup_ui(self):
        """Setup the shortcuts UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search shortcuts:")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search shortcuts...")
        self.search_edit.textChanged.connect(self._filter_shortcuts)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # Shortcuts list
        self.shortcuts_list = QListWidget()
        self.shortcuts_list.setAlternatingRowColors(True)
        layout.addWidget(self.shortcuts_list)
    
    def _load_shortcuts(self):
        """Load and display keyboard shortcuts."""
        shortcuts = [
            ("General", [
                ("F1", "Show context-sensitive help"),
                ("Ctrl+Q", "Quit application"),
                ("Ctrl+,", "Open settings"),
                ("Ctrl+R", "Refresh current view"),
                ("Ctrl+W", "Close current tab"),
                ("Ctrl+T", "New tab"),
                ("F11", "Toggle fullscreen"),
                ("Esc", "Cancel current operation")
            ]),
            ("Navigation", [
                ("Ctrl+1", "Switch to Dashboard tab"),
                ("Ctrl+2", "Switch to Applications tab"),
                ("Ctrl+3", "Switch to System Status tab"),
                ("Ctrl+4", "Switch to Settings tab"),
                ("Ctrl+Tab", "Next tab"),
                ("Ctrl+Shift+Tab", "Previous tab"),
                ("Alt+Left", "Back"),
                ("Alt+Right", "Forward")
            ]),
            ("Application Management", [
                ("Space", "Start/Stop selected application"),
                ("Ctrl+A", "Select all applications"),
                ("Delete", "Stop selected application"),
                ("F5", "Refresh application list"),
                ("Ctrl+F", "Find application"),
                ("Enter", "Open application details")
            ]),
            ("System Monitoring", [
                ("F5", "Refresh system information"),
                ("Ctrl+E", "Export performance data"),
                ("Ctrl+P", "Print system report"),
                ("Ctrl+S", "Save screenshot"),
                ("+", "Zoom in charts"),
                ("-", "Zoom out charts")
            ]),
            ("Help & Support", [
                ("F1", "Context help"),
                ("Ctrl+F1", "Show help dialog"),
                ("Shift+F1", "What's this? mode"),
                ("Ctrl+H", "Show keyboard shortcuts"),
                ("Ctrl+I", "Show about dialog")
            ])
        ]
        
        self.all_shortcuts = []
        
        for category, shortcut_list in shortcuts:
            # Add category header
            category_item = QListWidgetItem(category)
            category_item.setFont(QFont("", 0, QFont.Bold))
            category_item.setForeground(QColor("#00A8FF"))
            category_item.setData(Qt.UserRole, "category")
            self.shortcuts_list.addItem(category_item)
            
            # Add shortcuts in category
            for shortcut, description in shortcut_list:
                item_widget = self._create_shortcut_item(shortcut, description)
                item = QListWidgetItem()
                item.setSizeHint(item_widget.sizeHint())
                item.setData(Qt.UserRole, f"{shortcut}|{description}".lower())
                self.shortcuts_list.addItem(item)
                self.shortcuts_list.setItemWidget(item, item_widget)
                
                self.all_shortcuts.append((shortcut, description, item))
    
    def _create_shortcut_item(self, shortcut: str, description: str) -> QWidget:
        """Create a shortcut item widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20, 8, 8, 8)
        layout.setSpacing(16)
        
        # Shortcut key
        shortcut_label = QLabel(shortcut)
        shortcut_label.setStyleSheet("""
            QLabel {
                background-color: #353A4F;
                color: #FFFFFF;
                border: 1px solid #37414F;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                min-width: 80px;
            }
        """)
        shortcut_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(shortcut_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #B0BEC5;")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        return widget
    
    def _filter_shortcuts(self, text: str):
        """Filter shortcuts based on search text."""
        text = text.lower()
        
        for i in range(self.shortcuts_list.count()):
            item = self.shortcuts_list.item(i)
            
            # Always show category headers
            if item.data(Qt.UserRole) == "category":
                item.setHidden(False)
                continue
            
            # Filter shortcuts
            search_data = item.data(Qt.UserRole)
            if text in search_data:
                item.setHidden(False)
            else:
                item.setHidden(True)


class HelpContentWidget(QWidget):
    """Widget for displaying help content with rich formatting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self.current_topic = None
    
    def _setup_ui(self):
        """Setup the content widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Topic title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Topic content
        self.content_edit = QTextEdit()
        self.content_edit.setReadOnly(True)
        self.content_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2A2F42;
                color: #B0BEC5;
                border: 1px solid #37414F;
                border-radius: 8px;
                padding: 15px;
                font-size: 11pt;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.content_edit)
        
        # Related topics
        self.related_frame = QFrame()
        self.related_layout = QVBoxLayout(self.related_frame)
        
        related_title = QLabel("Related Topics:")
        related_title.setStyleSheet("color: #FFFFFF; font-weight: bold; margin-top: 10px;")
        self.related_layout.addWidget(related_title)
        
        self.related_list = QListWidget()
        self.related_list.setMaximumHeight(100)
        self.related_list.setStyleSheet("""
            QListWidget {
                background-color: #353A4F;
                border: 1px solid #37414F;
                border-radius: 6px;
                padding: 5px;
            }
            
            QListWidget::item {
                color: #00A8FF;
                padding: 4px;
                border-radius: 3px;
            }
            
            QListWidget::item:hover {
                background-color: #2A2F42;
                cursor: pointer;
            }
        """)
        self.related_list.itemClicked.connect(self._on_related_topic_clicked)
        self.related_layout.addWidget(self.related_list)
        
        layout.addWidget(self.related_frame)
        self.related_frame.hide()
    
    def show_topic(self, topic: HelpTopic):
        """Display a help topic."""
        self.current_topic = topic
        self.title_label.setText(topic.title)
        self.content_edit.setHtml(topic.content)
        
        # Show related topics
        if topic.related_topics:
            self.related_list.clear()
            for related_id in topic.related_topics:
                help_system = HelpSystem.get_instance()
                if help_system:
                    related_topic = help_system.get_topic(related_id)
                    if related_topic:
                        item = QListWidgetItem(related_topic.title)
                        item.setData(Qt.UserRole, related_id)
                        self.related_list.addItem(item)
            
            if self.related_list.count() > 0:
                self.related_frame.show()
            else:
                self.related_frame.hide()
        else:
            self.related_frame.hide()
    
    def _on_related_topic_clicked(self, item: QListWidgetItem):
        """Handle related topic click."""
        topic_id = item.data(Qt.UserRole)
        help_system = HelpSystem.get_instance()
        if help_system:
            help_system.show_topic(topic_id)


class HelpDialog(QDialog):
    """Main help dialog with tabbed interface."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("CommandCore Launcher - Help")
        self.setMinimumSize(900, 700)
        self.setWindowFlags(Qt.Dialog | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        self._setup_ui()
        self._apply_styles()
        self._center_on_parent()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Help topics tree
        self.topics_tree = self._create_topics_tree()
        splitter.addWidget(self.topics_tree)
        
        # Tab widget for different help sections
        self.tab_widget = QTabWidget()
        
        # Help content tab
        self.content_widget = HelpContentWidget()
        self.tab_widget.addTab(self.content_widget, "Help Content")
        
        # Keyboard shortcuts tab
        self.shortcuts_widget = KeyboardShortcutsWidget()
        self.tab_widget.addTab(self.shortcuts_widget, "Keyboard Shortcuts")
        
        # FAQ tab
        faq_widget = self._create_faq_widget()
        self.tab_widget.addTab(faq_widget, "FAQ")
        
        splitter.addWidget(self.tab_widget)
        splitter.setSizes([250, 650])
        
        main_layout.addWidget(splitter)
        
        # Bottom buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(20, 10, 20, 20)
        
        online_help_btn = QPushButton("Online Help")
        online_help_btn.clicked.connect(self._open_online_help)
        buttons_layout.addWidget(online_help_btn)
        
        buttons_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        buttons_layout.addWidget(close_button)
        
        main_layout.addLayout(buttons_layout)
    
    def _create_header(self) -> QWidget:
        """Create the header section."""
        header = QFrame()
        header.setObjectName("helpHeader")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title = QLabel("CommandCore Launcher Help")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 20px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Search box
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #B0BEC5; font-weight: 500;")
        layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search help topics...")
        self.search_edit.setFixedWidth(200)
        self.search_edit.textChanged.connect(self._filter_topics)
        layout.addWidget(self.search_edit)
        
        return header
    
    def _create_topics_tree(self) -> QTreeWidget:
        """Create the help topics tree."""
        tree = QTreeWidget()
        tree.setHeaderLabel("Help Topics")
        tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2A2F42;
                border: 1px solid #37414F;
                border-radius: 8px;
                padding: 5px;
            }
            
            QTreeWidget::item {
                padding: 5px;
                border-radius: 4px;
            }
            
            QTreeWidget::item:selected {
                background-color: #00A8FF;
                color: white;
            }
            
            QTreeWidget::item:hover {
                background-color: #353A4F;
            }
        """)
        
        tree.itemClicked.connect(self._on_topic_selected)
        return tree
    
    def _create_faq_widget(self) -> QWidget:
        """Create the FAQ widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        faq_data = [
            ("How do I start an application?", 
             "Click on the application card in the Applications tab and press the 'Start' button, or use the Space key when the application is selected."),
            ("Why is an application not starting?", 
             "Check if the application path is correct in the settings, ensure you have proper permissions, and verify that all dependencies are installed."),
            ("How do I change the theme?", 
             "Go to Settings > Appearance and select a different theme from the dropdown menu. Changes are applied immediately."),
            ("Can I add custom applications?", 
             "Currently, applications are configured in the code. Future versions will support adding custom applications through the UI."),
            ("How do I view system performance?", 
             "Switch to the System Status tab to see real-time performance charts and detailed system information."),
            ("What keyboard shortcuts are available?", 
             "Press F1 for context help, or check the Keyboard Shortcuts tab in this help dialog for a complete list."),
            ("How do I export configuration?", 
             "Go to Settings and use the Export button to save your configuration to a file for backup or sharing."),
            ("Why are some features disabled?", 
             "Some features may require administrative privileges or specific system capabilities. Check the application logs for details."),
            ("How do I update the application?", 
             "The application will check for updates automatically. You can also check manually in the Settings tab."),
            ("Where are logs stored?", 
             "Logs are stored in the application data directory. The exact path is shown in the Settings > Advanced section.")
        ]
        
        for question, answer in faq_data:
            faq_item = self._create_faq_item(question, answer)
            layout.addWidget(faq_item)
        
        layout.addStretch()
        return widget
    
    def _create_faq_item(self, question: str, answer: str) -> QWidget:
        """Create a FAQ item widget."""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #353A4F;
                border: 1px solid #37414F;
                border-radius: 8px;
                margin: 5px 0;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(item)
        layout.setSpacing(8)
        
        # Question
        question_label = QLabel(f"Q: {question}")
        question_label.setStyleSheet("""
            color: #00A8FF;
            font-weight: bold;
            font-size: 12pt;
        """)
        question_label.setWordWrap(True)
        layout.addWidget(question_label)
        
        # Answer
        answer_label = QLabel(f"A: {answer}")
        answer_label.setStyleSheet("""
            color: #B0BEC5;
            font-size: 11pt;
            margin-left: 15px;
        """)
        answer_label.setWordWrap(True)
        layout.addWidget(answer_label)
        
        return item
    
    def _filter_topics(self, text: str):
        """Filter help topics based on search text."""
        # Implementation for filtering topics tree
        pass
    
    def _on_topic_selected(self, item: QTreeWidgetItem):
        """Handle topic selection."""
        topic_id = item.data(0, Qt.UserRole)
        if topic_id:
            help_system = HelpSystem.get_instance()
            if help_system:
                topic = help_system.get_topic(topic_id)
                if topic:
                    self.content_widget.show_topic(topic)
                    self.tab_widget.setCurrentIndex(0)  # Switch to content tab
    
    def _open_online_help(self):
        """Open online help documentation."""
        QDesktopServices.openUrl(QUrl("https://docs.commandcore.org"))
    
    def _apply_styles(self):
        """Apply custom styles to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1A1F2E;
                color: #FFFFFF;
            }
            
            QFrame#helpHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2A2F42, stop:1 #353A4F);
                border-bottom: 1px solid #37414F;
            }
            
            QTabWidget::pane {
                border: 1px solid #37414F;
                border-radius: 8px;
                background-color: #2A2F42;
            }
            
            QTabBar::tab {
                background-color: #353A4F;
                color: #B0BEC5;
                padding: 10px 20px;
                border: 1px solid #37414F;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: #2A2F42;
                color: #FFFFFF;
                border-bottom: 1px solid #2A2F42;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #3E4358;
            }
            
            QPushButton {
                background-color: #353A4F;
                color: #FFFFFF;
                border: 1px solid #37414F;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #3E4358;
                border-color: #00A8FF;
            }
            
            QPushButton:pressed {
                background-color: #2C3441;
            }
            
            QLineEdit {
                background-color: #353A4F;
                color: #FFFFFF;
                border: 1px solid #37414F;
                border-radius: 6px;
                padding: 6px 10px;
            }
            
            QLineEdit:focus {
                border-color: #00A8FF;
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


class HelpSystem(QObject):
    """
    Comprehensive help system for CommandCore Launcher.
    
    Features:
    - Context-sensitive help with F1 key
    - Comprehensive help topics database
    - Keyboard shortcuts reference
    - FAQ system
    - Online help integration
    - Tooltips management
    """
    
    _instance = None
    
    def __init__(self):
        super().__init__()
        
        if HelpSystem._instance is not None:
            raise RuntimeError("HelpSystem is a singleton")
        
        HelpSystem._instance = self
        
        self.topics: Dict[str, HelpTopic] = {}
        self.contextual_help = ContextualHelp()
        self.help_dialog: Optional[HelpDialog] = None
        
        self._load_help_topics()
        self._setup_global_shortcuts()
    
    @classmethod
    def get_instance(cls) -> Optional['HelpSystem']:
        """Get the singleton instance."""
        return cls._instance
    
    def _load_help_topics(self):
        """Load help topics from various sources."""
        # Built-in help topics
        topics_data = [
            {
                "id": "getting_started",
                "title": "Getting Started with CommandCore Launcher",
                "content": """
                <h2>Welcome to CommandCore Launcher</h2>
                <p>CommandCore Launcher is a professional application management suite that provides:</p>
                <ul>
                    <li><strong>Application Management:</strong> Launch, monitor, and control CommandCore applications</li>
                    <li><strong>System Monitoring:</strong> Real-time performance tracking and analytics</li>
                    <li><strong>Theme Customization:</strong> Professional themes with live preview</li>
                    <li><strong>Configuration Management:</strong> Comprehensive settings with validation</li>
                </ul>
                
                <h3>Quick Start</h3>
                <ol>
                    <li>Use the Dashboard tab for an overview of system status</li>
                    <li>Switch to Applications tab to manage your applications</li>
                    <li>Monitor system performance in the System Status tab</li>
                    <li>Customize appearance and behavior in Settings</li>
                </ol>
                
                <h3>Navigation Tips</h3>
                <p>Use <kbd>Ctrl+1-4</kbd> to quickly switch between tabs, or press <kbd>F1</kbd> anywhere for context-sensitive help.</p>
                """,
                "type": HelpTopicType.OVERVIEW,
                "keywords": ["getting started", "introduction", "overview", "quick start"],
                "related_topics": ["navigation", "applications", "settings"]
            },
            {
                "id": "navigation",
                "title": "Navigation and Interface",
                "content": """
                <h2>Interface Overview</h2>
                <p>The CommandCore Launcher interface consists of four main tabs:</p>
                
                <h3>Dashboard Tab</h3>
                <p>Provides an overview of system status, running applications, and quick access to key functions.</p>
                
                <h3>Applications Tab</h3>
                <p>Manage CommandCore applications with visual status cards, resource monitoring, and control options.</p>
                
                <h3>System Status Tab</h3>
                <p>Real-time system monitoring with performance charts, hardware information, and process management.</p>
                
                <h3>Settings Tab</h3>
                <p>Comprehensive configuration options including themes, notifications, and system preferences.</p>
                
                <h3>Keyboard Navigation</h3>
                <ul>
                    <li><kbd>Ctrl+1</kbd> - Dashboard</li>
                    <li><kbd>Ctrl+2</kbd> - Applications</li>
                    <li><kbd>Ctrl+3</kbd> - System Status</li>
                    <li><kbd>Ctrl+4</kbd> - Settings</li>
                    <li><kbd>Ctrl+Tab</kbd> - Next tab</li>
                    <li><kbd>F1</kbd> - Context help</li>
                </ul>
                """,
                "type": HelpTopicType.REFERENCE,
                "keywords": ["navigation", "interface", "tabs", "keyboard"],
                "related_topics": ["getting_started", "shortcuts"]
            },
            {
                "id": "applications",
                "title": "Application Management",
                "content": """
                <h2>Managing Applications</h2>
                <p>The Applications tab provides comprehensive management of CommandCore applications.</p>
                
                <h3>Application Cards</h3>
                <p>Each application is displayed as a modern card showing:</p>
                <ul>
                    <li>Application name and description</li>
                    <li>Current status (running, stopped, error)</li>
                    <li>Resource usage (CPU, memory when running)</li>
                    <li>Control buttons (start, stop, restart)</li>
                </ul>
                
                <h3>Starting Applications</h3>
                <ol>
                    <li>Click the "Start" button on an application card</li>
                    <li>Or select an application and press <kbd>Space</kbd></li>
                    <li>Watch the status change from "Stopped" to "Starting" to "Running"</li>
                </ol>
                
                <h3>Stopping Applications</h3>
                <ol>
                    <li>Click the "Stop" button on a running application</li>
                    <li>Or select a running application and press <kbd>Delete</kbd></li>
                    <li>Use "Force Stop" from the context menu if needed</li>
                </ol>
                
                <h3>Bulk Operations</h3>
                <p>Use the "Start All" and "Stop All" buttons to control multiple applications simultaneously.</p>
                
                <h3>Troubleshooting</h3>
                <p>If an application fails to start:</p>
                <ul>
                    <li>Check the error message displayed on the card</li>
                    <li>Verify the application path in settings</li>
                    <li>Ensure proper permissions and dependencies</li>
                    <li>Check the application logs for detailed error information</li>
                </ul>
                """,
                "type": HelpTopicType.TUTORIAL,
                "keywords": ["applications", "start", "stop", "management", "troubleshooting"],
                "related_topics": ["getting_started", "troubleshooting"]
            },
            {
                "id": "settings",
                "title": "Settings and Configuration",
                "content": """
                <h2>Configuring CommandCore Launcher</h2>
                <p>The Settings tab provides comprehensive configuration options organized into categories.</p>
                
                <h3>Appearance Settings</h3>
                <ul>
                    <li><strong>Theme:</strong> Choose from Dark, Light, High Contrast, or Blue themes</li>
                    <li><strong>Colors:</strong> Customize primary colors with live preview</li>
                    <li><strong>Fonts:</strong> Select font family and size</li>
                    <li><strong>Animations:</strong> Control animation speed and effects</li>
                </ul>
                
                <h3>Application Settings</h3>
                <ul>
                    <li><strong>Startup:</strong> Configure splash screen and window behavior</li>
                    <li><strong>System Tray:</strong> Minimize/close to tray options</li>
                    <li><strong>Notifications:</strong> Enable/disable and configure duration</li>
                </ul>
                
                <h3>System Settings</h3>
                <ul>
                    <li><strong>Monitoring:</strong> Auto-start and update intervals</li>
                    <li><strong>Updates:</strong> Automatic update checking frequency</li>
                </ul>
                
                <h3>Advanced Settings</h3>
                <ul>
                    <li><strong>Logging:</strong> Log level and file settings</li>
                    <li><strong>Performance:</strong> Debug and performance modes</li>
                </ul>
                
                <h3>Import/Export</h3>
                <p>Save your configuration settings to a file or import settings from a backup:</p>
                <ol>
                    <li>Click "Export" to save current settings</li>
                    <li>Click "Import" to load settings from file</li>
                    <li>Use "Reset to Defaults" to restore original settings</li>
                </ol>
                """,
                "type": HelpTopicType.REFERENCE,
                "keywords": ["settings", "configuration", "themes", "preferences"],
                "related_topics": ["themes", "troubleshooting"]
            },
            {
                "id": "troubleshooting",
                "title": "Troubleshooting Guide",
                "content": """
                <h2>Common Issues and Solutions</h2>
                
                <h3>Application Won't Start</h3>
                <p><strong>Problem:</strong> Application card shows error status</p>
                <p><strong>Solutions:</strong></p>
                <ul>
                    <li>Check that the application executable exists and is accessible</li>
                    <li>Verify file permissions (executable permission on Unix systems)</li>
                    <li>Ensure Python interpreter is available for Python applications</li>
                    <li>Check application dependencies are installed</li>
                    <li>Review error messages in the application logs</li>
                </ul>
                
                <h3>Performance Issues</h3>
                <p><strong>Problem:</strong> Slow interface or high resource usage</p>
                <p><strong>Solutions:</strong></p>
                <ul>
                    <li>Enable Performance Mode in Settings > Advanced</li>
                    <li>Reduce animation duration or disable animations</li>
                    <li>Increase monitoring intervals in System Settings</li>
                    <li>Close unnecessary applications to free resources</li>
                </ul>
                
                <h3>Theme or Display Issues</h3>
                <p><strong>Problem:</strong> UI appears corrupted or colors are wrong</p>
                <p><strong>Solutions:</strong></p>
                <ul>
                    <li>Try switching to a different theme in Settings</li>
                    <li>Reset settings to defaults if theme is corrupted</li>
                    <li>Update graphics drivers</li>
                    <li>Restart the application</li>
                </ul>
                
                <h3>Configuration Problems</h3>
                <p><strong>Problem:</strong> Settings not saving or loading incorrectly</p>
                <p><strong>Solutions:</strong></p>
                <ul>
                    <li>Check write permissions in configuration directory</li>
                    <li>Export settings as backup before making changes</li>
                    <li>Delete corrupted configuration files to restore defaults</li>
                    <li>Run as administrator if permission issues persist</li>
                </ul>
                
                <h3>Getting Help</h3>
                <p>If problems persist:</p>
                <ul>
                    <li>Check the application logs in the logs directory</li>
                    <li>Enable debug mode in Settings > Advanced</li>
                    <li>Visit the online documentation</li>
                    <li>Contact support with log files and error descriptions</li>
                </ul>
                """,
                "type": HelpTopicType.TROUBLESHOOTING,
                "keywords": ["troubleshooting", "problems", "errors", "issues", "solutions"],
                "related_topics": ["applications", "settings", "support"]
            }
        ]
        
        # Create help topics
        for topic_data in topics_data:
            topic = HelpTopic(
                id=topic_data["id"],
                title=topic_data["title"],
                content=topic_data["content"],
                type=HelpTopicType(topic_data["type"]),
                keywords=topic_data["keywords"],
                related_topics=topic_data.get("related_topics", [])
            )
            self.topics[topic.id] = topic
    
    def _setup_global_shortcuts(self):
        """Setup global keyboard shortcuts."""
        try:
            app = QApplication.instance()
            if app:
                # F1 for help dialog
                help_shortcut = QShortcut(QKeySequence("F1"), app.activeWindow())
                help_shortcut.activated.connect(self.show_help_dialog)
                
                # Ctrl+F1 for help dialog
                help_shortcut2 = QShortcut(QKeySequence("Ctrl+F1"), app.activeWindow())
                help_shortcut2.activated.connect(self.show_help_dialog)
                
                # Ctrl+H for shortcuts
                shortcuts_shortcut = QShortcut(QKeySequence("Ctrl+H"), app.activeWindow())
                shortcuts_shortcut.activated.connect(self.show_shortcuts)
        except Exception as e:
            print(f"Error setting up global shortcuts: {e}")
    
    def register_context_help(self, widget: QWidget, topic_id: str, tooltip: str = None):
        """Register a widget for context-sensitive help."""
        self.contextual_help.register_context(widget, topic_id, tooltip)
    
    def show_help_dialog(self, topic_id: str = None):
        """Show the main help dialog."""
        try:
            if not self.help_dialog:
                app = QApplication.instance()
                main_window = None
                
                # Find main window
                for widget in app.topLevelWidgets():
                    if widget.objectName() == "MainWindow" or "MainWindow" in str(type(widget)):
                        main_window = widget
                        break
                
                self.help_dialog = HelpDialog(main_window)
            
            if topic_id and topic_id in self.topics:
                topic = self.topics[topic_id]
                self.help_dialog.content_widget.show_topic(topic)
                self.help_dialog.tab_widget.setCurrentIndex(0)
            
            self.help_dialog.show()
            self.help_dialog.raise_()
            self.help_dialog.activateWindow()
            
        except Exception as e:
            print(f"Error showing help dialog: {e}")
    
    def show_topic(self, topic_id: str):
        """Show a specific help topic."""
        self.show_help_dialog(topic_id)
    
    def show_shortcuts(self):
        """Show keyboard shortcuts."""
        self.show_help_dialog()
        if self.help_dialog:
            self.help_dialog.tab_widget.setCurrentIndex(1)  # Shortcuts tab
    
    def get_topic(self, topic_id: str) -> Optional[HelpTopic]:
        """Get a help topic by ID."""
        return self.topics.get(topic_id)
    
    def search_topics(self, query: str) -> List[HelpTopic]:
        """Search help topics by keywords."""
        query = query.lower()
        results = []
        
        for topic in self.topics.values():
            # Search in title, keywords, and content
            if (query in topic.title.lower() or 
                any(query in keyword for keyword in topic.keywords) or
                query in topic.content.lower()):
                results.append(topic)
        
        return results
    
    def add_custom_topic(self, topic: HelpTopic):
        """Add a custom help topic."""
        self.topics[topic.id] = topic
    
    def cleanup(self):
        """Clean up help system resources."""
        if self.help_dialog:
            self.help_dialog.close()
            self.help_dialog = None
        
        HelpSystem._instance = None


# Global functions
def initialize_help_system():
    """Initialize the global help system."""
    return HelpSystem()

def get_help_system() -> Optional[HelpSystem]:
    """Get the global help system instance."""
    return HelpSystem.get_instance()

def show_help(topic_id: str = None):
    """Show help dialog with optional topic."""
    help_system = get_help_system()
    if help_system:
        help_system.show_help_dialog(topic_id)

def register_help_context(widget: QWidget, topic_id: str, tooltip: str = None):
    """Register widget for context-sensitive help."""
    help_system = get_help_system()
    if help_system:
        help_system.register_context_help(widget, topic_id, tooltip)


if __name__ == "__main__":
    # Test the help system
    app = QApplication(sys.argv)
    help_system = initialize_help_system()
    help_system.show_help_dialog()
    sys.exit(app.exec())