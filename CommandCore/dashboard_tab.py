"""
Modern Dashboard Tab for CommandCore Launcher

Provides an overview of system status, running applications,
recent activity, and quick access to key functions.
"""

import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea,
    QGroupBox, QProgressBar, QListWidget, QListWidgetItem,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QPropertyAnimation, 
    QEasingCurve, QParallelAnimationGroup, QRect
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QPainter, QColor,
    QLinearGradient, QPainterPath, QBrush
)


@dataclass
class SystemMetrics:
    """Container for system performance metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    network_sent: int = 0
    network_recv: int = 0
    uptime_seconds: int = 0
    active_processes: int = 0


@dataclass
class AppStatus:
    """Container for application status information."""
    id: str
    name: str
    status: str
    pid: Optional[int] = None
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    start_time: Optional[datetime] = None


class MetricCard(QFrame):
    """Modern card widget for displaying system metrics."""
    
    clicked = Signal(str)  # metric_name
    
    def __init__(self, title: str, metric_name: str, icon_path: str = None, parent=None):
        super().__init__(parent)
        
        self.title = title
        self.metric_name = metric_name
        self.value = 0.0
        self.trend = 0.0  # Positive for increase, negative for decrease
        self.unit = "%"
        
        self._setup_ui()
        self._setup_style()
        self._setup_animations()
    
    def _setup_ui(self):
        """Setup the card UI components."""
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header with title and icon
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("cardTitle")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # TODO: Add icon support
        # if icon_path:
        #     icon_label = QLabel()
        #     icon_label.setPixmap(QPixmap(icon_path).scaled(20, 20, Qt.KeepAspectRatio))
        #     header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Value display
        self.value_label = QLabel("0%")
        self.value_label.setObjectName("cardValue")
        layout.addWidget(self.value_label)
        
        # Trend indicator
        self.trend_label = QLabel("No change")
        self.trend_label.setObjectName("cardTrend")
        layout.addWidget(self.trend_label)
        
        layout.addStretch()
    
    def _setup_style(self):
        """Setup card styling."""
        self.setObjectName("metricCard")
        self.setStyleSheet("""
            QFrame#metricCard {
                background-color: #2A2F42;
                border: 1px solid #37414F;
                border-radius: 12px;
                margin: 4px;
            }
            
            QFrame#metricCard:hover {
                border-color: #00A8FF;
                background-color: #2F3447;
            }
            
            QLabel#cardTitle {
                color: #B0BEC5;
                font-size: 12px;
                font-weight: 500;
            }
            
            QLabel#cardValue {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: bold;
            }
            
            QLabel#cardTrend {
                color: #78909C;
                font-size: 11px;
            }
        """)
    
    def _setup_animations(self):
        """Setup hover and value change animations."""
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def update_value(self, value: float, unit: str = "%", trend: float = 0.0):
        """Update the metric value with animation."""
        old_value = self.value
        self.value = value
        self.unit = unit
        self.trend = trend
        
        # Update value display
        if unit == "%":
            self.value_label.setText(f"{value:.1f}%")
        elif unit == "MB":
            self.value_label.setText(f"{value:.0f} MB")
        elif unit == "GB":
            self.value_label.setText(f"{value:.1f} GB")
        else:
            self.value_label.setText(f"{value:.1f} {unit}")
        
        # Update trend display
        if abs(trend) < 0.1:
            self.trend_label.setText("No change")
            self.trend_label.setStyleSheet("color: #78909C;")
        elif trend > 0:
            self.trend_label.setText(f"↑ +{trend:.1f}%")
            self.trend_label.setStyleSheet("color: #FF9800;")
        else:
            self.trend_label.setText(f"↓ {trend:.1f}%")
            self.trend_label.setStyleSheet("color: #4CAF50;")
        
        # Color coding based on value
        if value >= 90:
            self.value_label.setStyleSheet("color: #F44336; font-size: 28px; font-weight: bold;")
        elif value >= 70:
            self.value_label.setStyleSheet("color: #FF9800; font-size: 28px; font-weight: bold;")
        else:
            self.value_label.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: bold;")
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.metric_name)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter events."""
        # TODO: Add subtle hover animation
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        # TODO: Add subtle hover animation
        super().leaveEvent(event)


class QuickActionButton(QPushButton):
    """Styled button for quick actions."""
    
    def __init__(self, text: str, icon_path: str = None, accent_color: str = "#00A8FF"):
        super().__init__(text)
        
        self.accent_color = accent_color
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #2A2F42;
                color: #FFFFFF;
                border: 1px solid #37414F;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                padding: 0 16px;
            }}
            
            QPushButton:hover {{
                background-color: {accent_color};
                border-color: {accent_color};
            }}
            
            QPushButton:pressed {{
                background-color: #0078CC;
            }}
        """)


class RecentActivityWidget(QWidget):
    """Widget for displaying recent system activity."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.activity_items = []
        self.max_items = 10
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the activity widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("Recent Activity")
        header.setStyleSheet("""
            color: #FFFFFF;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        """)
        layout.addWidget(header)
        
        # Activity list
        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            
            QListWidget::item {
                background-color: #2A2F42;
                border: 1px solid #37414F;
                border-radius: 6px;
                padding: 8px 12px;
                margin-bottom: 4px;
                color: #B0BEC5;
                font-size: 12px;
            }
            
            QListWidget::item:hover {
                background-color: #2F3447;
                border-color: #00A8FF;
            }
        """)
        layout.addWidget(self.activity_list)
    
    def add_activity(self, message: str, timestamp: datetime = None):
        """Add a new activity item."""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Format timestamp
        time_str = timestamp.strftime("%H:%M:%S")
        item_text = f"[{time_str}] {message}"
        
        # Add to list
        item = QListWidgetItem(item_text)
        self.activity_list.insertItem(0, item)
        
        # Limit number of items
        while self.activity_list.count() > self.max_items:
            self.activity_list.takeItem(self.activity_list.count() - 1)
        
        # Store in memory
        self.activity_items.insert(0, {
            'message': message,
            'timestamp': timestamp
        })
        
        if len(self.activity_items) > self.max_items:
            self.activity_items = self.activity_items[:self.max_items]


class ApplicationOverviewWidget(QWidget):
    """Widget for displaying application status overview."""
    
    app_action_requested = Signal(str, str)  # app_id, action
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.app_statuses: Dict[str, AppStatus] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the application overview UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Header with counts
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Applications")
        self.title_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 16px;
            font-weight: 600;
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.status_label = QLabel("0 running, 0 stopped")
        self.status_label.setStyleSheet("""
            color: #78909C;
            font-size: 12px;
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Applications list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setMaximumHeight(300)
        
        self.apps_widget = QWidget()
        self.apps_layout = QVBoxLayout(self.apps_widget)
        self.apps_layout.setContentsMargins(0, 0, 0, 0)
        self.apps_layout.setSpacing(4)
        
        scroll_area.setWidget(self.apps_widget)
        layout.addWidget(scroll_area)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        self.start_all_btn = QuickActionButton("Start All", accent_color="#4CAF50")
        self.start_all_btn.clicked.connect(lambda: self.app_action_requested.emit("all", "start"))
        actions_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QuickActionButton("Stop All", accent_color="#F44336")
        self.stop_all_btn.clicked.connect(lambda: self.app_action_requested.emit("all", "stop"))
        actions_layout.addWidget(self.stop_all_btn)
        
        layout.addLayout(actions_layout)
    
    def update_app_status(self, app_id: str, status: AppStatus):
        """Update the status of an application."""
        self.app_statuses[app_id] = status
        self._rebuild_app_list()
    
    def _rebuild_app_list(self):
        """Rebuild the applications list display."""
        # Clear existing items
        for i in reversed(range(self.apps_layout.count())):
            child = self.apps_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add current applications
        running_count = 0
        stopped_count = 0
        
        for app_id, status in self.app_statuses.items():
            app_widget = self._create_app_item(status)
            self.apps_layout.addWidget(app_widget)
            
            if status.status == "running":
                running_count += 1
            else:
                stopped_count += 1
        
        # Update status label
        self.status_label.setText(f"{running_count} running, {stopped_count} stopped")
        
        # Add stretch at the end
        self.apps_layout.addStretch()
    
    def _create_app_item(self, status: AppStatus) -> QWidget:
        """Create a widget for an application item."""
        item = QFrame()
        item.setFrameShape(QFrame.StyledPanel)
        item.setFixedHeight(48)
        
        # Status color
        status_color = "#4CAF50" if status.status == "running" else "#F44336"
        
        item.setStyleSheet(f"""
            QFrame {{
                background-color: #2A2F42;
                border: 1px solid #37414F;
                border-left: 3px solid {status_color};
                border-radius: 6px;
                margin: 1px;
            }}
            
            QFrame:hover {{
                background-color: #2F3447;
                border-color: #00A8FF;
                border-left-color: {status_color};
            }}
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # App name and status
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(status.name)
        name_label.setStyleSheet("color: #FFFFFF; font-weight: 500; font-size: 13px;")
        info_layout.addWidget(name_label)
        
        details = []
        if status.status == "running":
            if status.memory_usage > 0:
                details.append(f"RAM: {status.memory_usage:.0f}MB")
            if status.cpu_usage > 0:
                details.append(f"CPU: {status.cpu_usage:.1f}%")
        details.append(f"Status: {status.status}")
        
        status_label = QLabel(" • ".join(details))
        status_label.setStyleSheet("color: #78909C; font-size: 11px;")
        info_layout.addWidget(status_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Action button
        action_text = "Stop" if status.status == "running" else "Start"
        action_btn = QPushButton(action_text)
        action_btn.setFixedSize(60, 28)
        action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {status_color};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {"#45A049" if status.status == "running" else "#E53935"};
            }}
        """)
        
        action_btn.clicked.connect(
            lambda: self.app_action_requested.emit(
                status.id, 
                "stop" if status.status == "running" else "start"
            )
        )
        
        layout.addWidget(action_btn)
        
        return item


class DashboardTab(QWidget):
    """
    Modern dashboard tab providing system overview and quick access.
    
    Features:
    - Real-time system metrics
    - Application status overview
    - Recent activity feed
    - Quick action buttons
    - Beautiful, responsive design
    """
    
    # Signals
    tab_requested = Signal(str)  # tab_name
    app_launch_requested = Signal(str)  # app_id
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.system_metrics = SystemMetrics()
        self.previous_metrics = SystemMetrics()
        
        # Components
        self.metric_cards: Dict[str, MetricCard] = {}
        self.activity_widget = RecentActivityWidget()
        self.app_overview = ApplicationOverviewWidget()
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_metrics)
        
        self._setup_ui()
        self._setup_connections()
        self._start_monitoring()
        
        # Add some initial activity
        self.activity_widget.add_activity("Dashboard initialized")
    
    def _setup_ui(self):
        """Setup the dashboard UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)
        
        # Welcome section
        welcome_section = self._create_welcome_section()
        main_layout.addWidget(welcome_section)
        
        # Metrics section
        metrics_section = self._create_metrics_section()
        main_layout.addWidget(metrics_section)
        
        # Content section with sidebar
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Main content area
        main_content = self._create_main_content()
        content_layout.addWidget(main_content, 2)
        
        # Sidebar
        sidebar = self._create_sidebar()
        content_layout.addWidget(sidebar, 1)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
    
    def _create_welcome_section(self) -> QWidget:
        """Create the welcome section."""
        section = QFrame()
        section.setObjectName("welcomeSection")
        section.setStyleSheet("""
            QFrame#welcomeSection {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2A2F42, stop:1 #353A4F);
                border: 1px solid #37414F;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Welcome to CommandCore")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("System Overview and Quick Access")
        subtitle.setStyleSheet("""
            color: #B0BEC5;
            font-size: 14px;
        """)
        layout.addWidget(subtitle)
        
        # Quick stats
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(24)
        
        uptime = self._get_system_uptime()
        stats = [
            ("System Uptime", uptime),
            ("Active Applications", "0"),
            ("Last Updated", datetime.now().strftime("%H:%M"))
        ]
        
        for label, value in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setSpacing(2)
            
            value_label = QLabel(value)
            value_label.setStyleSheet("color: #00A8FF; font-size: 18px; font-weight: bold;")
            stat_layout.addWidget(value_label)
            
            label_label = QLabel(label)
            label_label.setStyleSheet("color: #78909C; font-size: 11px;")
            stat_layout.addWidget(label_label)
            
            stats_layout.addWidget(stat_widget)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        return section
    
    def _create_metrics_section(self) -> QWidget:
        """Create the system metrics section."""
        section = QGroupBox("System Metrics")
        section.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 600;
                border: 1px solid #37414F;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 12px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                background-color: #1A1F2E;
            }
        """)
        
        layout = QGridLayout(section)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 20, 16, 16)
        
        # Create metric cards
        metrics = [
            ("CPU Usage", "cpu", "cpu_icon.svg"),
            ("Memory Usage", "memory", "memory_icon.svg"),
            ("Disk Usage", "disk", "disk_icon.svg"),
            ("Network Activity", "network", "network_icon.svg")
        ]
        
        for i, (title, metric_name, icon) in enumerate(metrics):
            card = MetricCard(title, metric_name, icon)
            card.clicked.connect(self._on_metric_card_clicked)
            self.metric_cards[metric_name] = card
            
            row = i // 2
            col = i % 2
            layout.addWidget(card, row, col)
        
        return section
    
    def _create_main_content(self) -> QWidget:
        """Create the main content area."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-size: 14px;
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
        """)
        
        actions_layout = QGridLayout(actions_group)
        actions_layout.setSpacing(12)
        actions_layout.setContentsMargins(12, 16, 12, 12)
        
        # Quick action buttons
        actions = [
            ("Applications", "View and manage applications", lambda: self.tab_requested.emit("Applications")),
            ("System Status", "Detailed system information", lambda: self.tab_requested.emit("System Status")),
            ("Settings", "Configure preferences", lambda: self.tab_requested.emit("Settings")),
            ("Refresh", "Update dashboard data", self._refresh_dashboard)
        ]
        
        for i, (title, description, callback) in enumerate(actions):
            btn = QuickActionButton(title)
            btn.setToolTip(description)
            btn.clicked.connect(callback)
            
            row = i // 2
            col = i % 2
            actions_layout.addWidget(btn, row, col)
        
        layout.addWidget(actions_group)
        
        # Application overview
        layout.addWidget(self.app_overview)
        
        return content
    
    def _create_sidebar(self) -> QWidget:
        """Create the sidebar with activity feed."""
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(16)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-size: 14px;
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
        """)
        
        activity_layout = QVBoxLayout(activity_group)
        activity_layout.setContentsMargins(12, 16, 12, 12)
        activity_layout.addWidget(self.activity_widget)
        
        layout.addWidget(activity_group)
        layout.addStretch()
        
        return sidebar
    
    def _setup_connections(self):
        """Setup signal connections."""
        self.app_overview.app_action_requested.connect(self._on_app_action_requested)
    
    def _start_monitoring(self):
        """Start the monitoring timer."""
        self.update_timer.start(2000)  # Update every 2 seconds
        self._update_metrics()  # Initial update
    
    def _update_metrics(self):
        """Update system metrics."""
        try:
            # Store previous metrics for trend calculation
            self.previous_metrics = SystemMetrics(
                cpu_percent=self.system_metrics.cpu_percent,
                memory_percent=self.system_metrics.memory_percent,
                disk_percent=self.system_metrics.disk_percent,
                network_sent=self.system_metrics.network_sent,
                network_recv=self.system_metrics.network_recv
            )
            
            # Get current metrics
            self.system_metrics.cpu_percent = psutil.cpu_percent(interval=None)
            
            memory = psutil.virtual_memory()
            self.system_metrics.memory_percent = memory.percent
            
            disk = psutil.disk_usage('/')
            self.system_metrics.disk_percent = disk.percent
            
            # Network stats
            network = psutil.net_io_counters()
            self.system_metrics.network_sent = network.bytes_sent
            self.system_metrics.network_recv = network.bytes_recv
            
            # System info
            self.system_metrics.uptime_seconds = int(psutil.boot_time())
            self.system_metrics.active_processes = len(psutil.pids())
            
            # Update metric cards
            self._update_metric_cards()
            
        except Exception as e:
            print(f"Error updating metrics: {e}")
            self.activity_widget.add_activity(f"Error updating metrics: {str(e)}")
    
    def _update_metric_cards(self):
        """Update the metric cards with current values."""
        # Calculate trends
        cpu_trend = self.system_metrics.cpu_percent - self.previous_metrics.cpu_percent
        memory_trend = self.system_metrics.memory_percent - self.previous_metrics.memory_percent
        disk_trend = self.system_metrics.disk_percent - self.previous_metrics.disk_percent
        
        # Update cards
        if "cpu" in self.metric_cards:
            self.metric_cards["cpu"].update_value(
                self.system_metrics.cpu_percent, "%", cpu_trend
            )
        
        if "memory" in self.metric_cards:
            self.metric_cards["memory"].update_value(
                self.system_metrics.memory_percent, "%", memory_trend
            )
        
        if "disk" in self.metric_cards:
            self.metric_cards["disk"].update_value(
                self.system_metrics.disk_percent, "%", disk_trend
            )
        
        if "network" in self.metric_cards:
            # Show network speed in MB/s (simplified)
            network_speed = (self.system_metrics.network_sent + self.system_metrics.network_recv) / (1024 * 1024)
            self.metric_cards["network"].update_value(network_speed, "MB", 0)
    
    def _get_system_uptime(self) -> str:
        """Get formatted system uptime."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception:
            return "Unknown"
    
    def _on_metric_card_clicked(self, metric_name: str):
        """Handle metric card click events."""
        self.activity_widget.add_activity(f"Viewed {metric_name} details")
        
        # Navigate to system status for detailed view
        self.tab_requested.emit("System Status")
    
    def _on_app_action_requested(self, app_id: str, action: str):
        """Handle application action requests."""
        if app_id == "all":
            self.activity_widget.add_activity(f"Requested to {action} all applications")
        else:
            self.activity_widget.add_activity(f"Requested to {action} {app_id}")
        
        # Emit signal for application manager to handle
        self.app_launch_requested.emit(app_id)
    
    def _refresh_dashboard(self):
        """Refresh dashboard data."""
        self.activity_widget.add_activity("Dashboard refreshed")
        self._update_metrics()
    
    def update_app_status(self, app_id: str, status: str):
        """Update application status from external source."""
        # Create or update app status
        if app_id in self.app_overview.app_statuses:
            app_status = self.app_overview.app_statuses[app_id]
            old_status = app_status.status
            app_status.status = status
            
            if old_status != status:
                self.activity_widget.add_activity(f"{app_status.name} {status}")
        else:
            # Create new app status
            app_status = AppStatus(
                id=app_id,
                name=app_id.replace('_', ' ').title(),
                status=status
            )
            
            self.activity_widget.add_activity(f"{app_status.name} {status}")
        
        self.app_overview.update_app_status(app_id, app_status)
    
    def cleanup(self):
        """Cleanup resources when tab is destroyed."""
        if self.update_timer.isActive():
            self.update_timer.stop()