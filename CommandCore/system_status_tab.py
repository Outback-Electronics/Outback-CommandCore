"""
Modern System Status Tab for CommandCore Launcher

Provides comprehensive system monitoring with real-time charts,
detailed hardware information, and performance analytics with proper
resource management and error handling.
"""

import platform
import psutil
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
import threading

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QProgressBar, QFrame, QScrollArea, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QTextEdit, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QSizePolicy, QSpacerItem, QMessageBox
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QThread, QMutex, QPropertyAnimation,
    QEasingCurve, QSize, QRect, QPointF
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QPainter, QColor, QPen, QBrush,
    QLinearGradient, QPainterPath, QPolygonF
)


@dataclass
class SystemInfo:
    """System information container."""
    os_name: str = ""
    os_version: str = ""
    hostname: str = ""
    architecture: str = ""
    processor: str = ""
    python_version: str = ""
    total_memory: int = 0
    total_disk: int = 0
    cpu_cores: int = 0
    cpu_freq_max: float = 0.0
    boot_time: Optional[datetime] = None


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics."""
    timestamp: datetime
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used: int = 0
    memory_available: int = 0
    disk_percent: float = 0.0
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    network_sent: int = 0
    network_recv: int = 0
    cpu_freq: float = 0.0
    cpu_temp: Optional[float] = None
    active_processes: int = 0


class RealTimeChart(QWidget):
    """Real-time chart widget for displaying performance metrics with proper error handling."""
    
    def __init__(self, title: str, max_points: int = 60, parent=None):
        super().__init__(parent)
        
        self.title = title
        self.max_points = max_points
        self.data_points: deque = deque(maxlen=max_points)
        self.timestamps: deque = deque(maxlen=max_points)
        self._lock = threading.Lock()
        
        self.setMinimumHeight(200)
        self.setMinimumWidth(300)
        
        # Chart styling
        self.background_color = QColor(26, 31, 46)
        self.grid_color = QColor(55, 65, 79)
        self.line_color = QColor(0, 168, 255)
        self.fill_color = QColor(0, 168, 255, 30)
        self.text_color = QColor(176, 190, 197)
        
        self.max_value = 100.0
        self.min_value = 0.0
        self.show_grid = True
        self.show_fill = True
        
        # Error handling
        self._last_error = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{title}")
    
    def add_data_point(self, value: float, timestamp: datetime = None):
        """Add a new data point to the chart safely."""
        try:
            with self._lock:
                if timestamp is None:
                    timestamp = datetime.now()
                
                # Validate the value
                if not isinstance(value, (int, float)) or value < 0:
                    self.logger.warning(f"Invalid data point: {value}")
                    return
                
                self.data_points.append(float(value))
                self.timestamps.append(timestamp)
                
            self.update()
        except Exception as e:
            self.logger.error(f"Error adding data point: {e}")
    
    def set_colors(self, line_color: QColor, fill_color: QColor = None):
        """Set chart colors safely."""
        try:
            self.line_color = line_color
            if fill_color:
                self.fill_color = fill_color
            else:
                self.fill_color = QColor(line_color.red(), line_color.green(), line_color.blue(), 30)
        except Exception as e:
            self.logger.error(f"Error setting colors: {e}")
    
    def set_range(self, min_value: float, max_value: float):
        """Set the chart value range safely."""
        try:
            if min_value < max_value:
                self.min_value = min_value
                self.max_value = max_value
            else:
                self.logger.warning(f"Invalid range: min={min_value}, max={max_value}")
        except Exception as e:
            self.logger.error(f"Error setting range: {e}")
    
    def paintEvent(self, event):
        """Paint the chart with comprehensive error handling."""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            
            # Fill background
            painter.fillRect(self.rect(), self.background_color)
            
            # Calculate drawing area
            margin = 40
            chart_rect = QRect(
                margin, margin,
                max(1, self.width() - 2 * margin),
                max(1, self.height() - 2 * margin)
            )
            
            # Draw grid if enabled
            if self.show_grid:
                self._draw_grid(painter, chart_rect)
            
            # Draw chart border
            painter.setPen(QPen(self.grid_color, 1))
            painter.drawRect(chart_rect)
            
            # Draw title
            self._draw_title(painter)
            
            # Draw data if available
            with self._lock:
                data_points_copy = list(self.data_points)
            
            if len(data_points_copy) > 1:
                self._draw_data(painter, chart_rect, data_points_copy)
            
            # Draw current value
            if data_points_copy:
                self._draw_current_value(painter, data_points_copy[-1])
            
        except Exception as e:
            self.logger.error(f"Error in paint event: {e}")
            # Draw error message
            painter.setPen(QPen(QColor(255, 0, 0)))
            painter.drawText(self.rect(), Qt.AlignCenter, f"Chart Error: {str(e)[:50]}")
        finally:
            painter.end()
    
    def _draw_title(self, painter: QPainter):
        """Draw the chart title."""
        try:
            painter.setPen(QPen(self.text_color))
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(10, 20, self.title)
        except Exception as e:
            self.logger.error(f"Error drawing title: {e}")
    
    def _draw_current_value(self, painter: QPainter, current_value: float):
        """Draw the current value display."""
        try:
            value_text = f"{current_value:.1f}"
            if self.max_value <= 100:
                value_text += "%"
            
            font = painter.font()
            font.setPointSize(16)
            painter.setFont(font)
            painter.setPen(QPen(self.line_color))
            painter.drawText(self.width() - 80, 25, value_text)
        except Exception as e:
            self.logger.error(f"Error drawing current value: {e}")
    
    def _draw_grid(self, painter: QPainter, rect: QRect):
        """Draw the chart grid."""
        try:
            painter.setPen(QPen(self.grid_color, 1, Qt.DotLine))
            
            # Horizontal grid lines
            for i in range(1, 5):
                y = rect.top() + (rect.height() * i / 5)
                painter.drawLine(rect.left(), y, rect.right(), y)
            
            # Vertical grid lines
            for i in range(1, 6):
                x = rect.left() + (rect.width() * i / 6)
                painter.drawLine(x, rect.top(), x, rect.bottom())
        except Exception as e:
            self.logger.error(f"Error drawing grid: {e}")
    
    def _draw_data(self, painter: QPainter, rect: QRect, data_points: List[float]):
        """Draw the data line and fill."""
        try:
            if len(data_points) < 2 or rect.width() <= 0 or rect.height() <= 0:
                return
            
            # Create points for the line
            points = []
            value_range = max(0.1, self.max_value - self.min_value)  # Avoid division by zero
            
            for i, value in enumerate(data_points):
                x = rect.left() + (rect.width() * i / max(1, self.max_points - 1))
                y_ratio = (value - self.min_value) / value_range
                y_ratio = max(0, min(1, y_ratio))  # Clamp to [0, 1]
                y = rect.bottom() - (rect.height() * y_ratio)
                points.append(QPointF(x, y))
            
            if not points:
                return
            
            # Draw fill area if enabled
            if self.show_fill and len(points) > 1:
                self._draw_fill_area(painter, rect, points)
            
            # Draw line
            if len(points) > 1:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(self.line_color, 2))
                polygon = QPolygonF(points)
                painter.drawPolyline(polygon)
                
        except Exception as e:
            self.logger.error(f"Error drawing data: {e}")
    
    def _draw_fill_area(self, painter: QPainter, rect: QRect, points: List[QPointF]):
        """Draw the fill area under the line."""
        try:
            fill_polygon = QPolygonF()
            fill_polygon.append(QPointF(points[0].x(), rect.bottom()))
            for point in points:
                fill_polygon.append(point)
            fill_polygon.append(QPointF(points[-1].x(), rect.bottom()))
            
            painter.setBrush(QBrush(self.fill_color))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(fill_polygon)
        except Exception as e:
            self.logger.error(f"Error drawing fill area: {e}")


class MetricsCollector(QThread):
    """Thread for collecting system metrics with comprehensive error handling."""
    
    metrics_updated = Signal(PerformanceMetrics)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        self._running = True
        self.update_interval = 1.0  # seconds
        self.previous_disk_io = None
        self.previous_network_io = None
        self.previous_time = None
        
        # Error handling
        self.error_count = 0
        self.max_errors = 10
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Thread safety
        self._lock = threading.Lock()
        
    def run(self):
        """Main collection loop with error recovery."""
        self.logger.info("Starting metrics collection thread")
        
        while self._running:
            try:
                metrics = self._collect_metrics()
                if metrics:
                    self.metrics_updated.emit(metrics)
                    self.error_count = 0  # Reset error count on success
                
                self.msleep(int(self.update_interval * 1000))
                
            except Exception as e:
                self.error_count += 1
                error_msg = f"Error collecting metrics: {e}"
                self.logger.error(error_msg)
                
                if self.error_count <= self.max_errors:
                    self.error_occurred.emit(error_msg)
                
                # Increase sleep time on repeated errors
                sleep_time = min(30000, 5000 * self.error_count)  # Max 30 seconds
                self.msleep(sleep_time)
        
        self.logger.info("Metrics collection thread stopped")
    
    def _collect_metrics(self) -> Optional[PerformanceMetrics]:
        """Collect current system metrics with error handling."""
        try:
            with self._lock:
                current_time = datetime.now()
                
                # Basic metrics
                cpu_percent = self._safe_get_cpu_percent()
                memory = self._safe_get_memory_info()
                disk = self._safe_get_disk_info()
                
                # CPU frequency
                cpu_freq = self._safe_get_cpu_freq()
                
                # CPU temperature
                cpu_temp = self._safe_get_cpu_temp()
                
                # Disk I/O
                disk_read_bytes, disk_write_bytes = self._safe_get_disk_io(current_time)
                
                # Network I/O
                network_sent, network_recv = self._safe_get_network_io(current_time)
                
                # Process count
                active_processes = self._safe_get_process_count()
                
                self.previous_time = current_time
                
                return PerformanceMetrics(
                    timestamp=current_time,
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent if memory else 0.0,
                    memory_used=memory.used if memory else 0,
                    memory_available=memory.available if memory else 0,
                    disk_percent=disk.percent if disk else 0.0,
                    disk_read_bytes=disk_read_bytes,
                    disk_write_bytes=disk_write_bytes,
                    network_sent=network_sent,
                    network_recv=network_recv,
                    cpu_freq=cpu_freq,
                    cpu_temp=cpu_temp,
                    active_processes=active_processes
                )
                
        except Exception as e:
            self.logger.error(f"Error in _collect_metrics: {e}")
            return None
    
    def _safe_get_cpu_percent(self) -> float:
        """Safely get CPU percentage."""
        try:
            return psutil.cpu_percent(interval=None)
        except Exception as e:
            self.logger.warning(f"Error getting CPU percent: {e}")
            return 0.0
    
    def _safe_get_memory_info(self):
        """Safely get memory information."""
        try:
            return psutil.virtual_memory()
        except Exception as e:
            self.logger.warning(f"Error getting memory info: {e}")
            return None
    
    def _safe_get_disk_info(self):
        """Safely get disk information."""
        try:
            return psutil.disk_usage('/')
        except Exception as e:
            self.logger.warning(f"Error getting disk info: {e}")
            return None
    
    def _safe_get_cpu_freq(self) -> float:
        """Safely get CPU frequency."""
        try:
            freq_info = psutil.cpu_freq()
            return freq_info.current if freq_info else 0.0
        except Exception as e:
            self.logger.warning(f"Error getting CPU frequency: {e}")
            return 0.0
    
    def _safe_get_cpu_temp(self) -> Optional[float]:
        """Safely get CPU temperature."""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries and entries[0].current:
                        return entries[0].current
        except (AttributeError, Exception) as e:
            self.logger.debug(f"CPU temperature not available: {e}")
        return None
    
    def _safe_get_disk_io(self, current_time: datetime) -> Tuple[int, int]:
        """Safely get disk I/O rates."""
        try:
            disk_io = psutil.disk_io_counters()
            if not disk_io:
                return 0, 0
            
            if self.previous_disk_io and self.previous_time:
                time_delta = (current_time - self.previous_time).total_seconds()
                if time_delta > 0:
                    read_rate = (disk_io.read_bytes - self.previous_disk_io.read_bytes) / time_delta
                    write_rate = (disk_io.write_bytes - self.previous_disk_io.write_bytes) / time_delta
                    self.previous_disk_io = disk_io
                    return int(max(0, read_rate)), int(max(0, write_rate))
            
            self.previous_disk_io = disk_io
            return 0, 0
            
        except Exception as e:
            self.logger.warning(f"Error getting disk I/O: {e}")
            return 0, 0
    
    def _safe_get_network_io(self, current_time: datetime) -> Tuple[int, int]:
        """Safely get network I/O rates."""
        try:
            network_io = psutil.net_io_counters()
            if not network_io:
                return 0, 0
            
            if self.previous_network_io and self.previous_time:
                time_delta = (current_time - self.previous_time).total_seconds()
                if time_delta > 0:
                    sent_rate = (network_io.bytes_sent - self.previous_network_io.bytes_sent) / time_delta
                    recv_rate = (network_io.bytes_recv - self.previous_network_io.bytes_recv) / time_delta
                    self.previous_network_io = network_io
                    return int(max(0, sent_rate)), int(max(0, recv_rate))
            
            self.previous_network_io = network_io
            return 0, 0
            
        except Exception as e:
            self.logger.warning(f"Error getting network I/O: {e}")
            return 0, 0
    
    def _safe_get_process_count(self) -> int:
        """Safely get process count."""
        try:
            return len(psutil.pids())
        except Exception as e:
            self.logger.warning(f"Error getting process count: {e}")
            return 0
    
    def stop_collection(self):
        """Stop the metrics collection safely."""
        with self._lock:
            self._running = False
        self.quit()
        self.wait(5000)  # Wait up to 5 seconds for thread to finish


class ProcessTableWidget(QTableWidget):
    """Custom table widget for displaying running processes with error handling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Process", "PID", "CPU %", "Memory", "Status", "User"
        ])
        
        # Configure table
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.verticalHeader().setVisible(False)
        
        # Configure column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Process name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # PID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # CPU
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Memory
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # User
        
        # Style the table
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #37414F;
                background-color: #2A2F42;
                alternate-background-color: #2F3447;
                color: #FFFFFF;
                selection-background-color: #00A8FF;
            }
            
            QHeaderView::section {
                background-color: #353A4F;
                color: #FFFFFF;
                padding: 8px;
                border: 1px solid #37414F;
                font-weight: 600;
            }
        """)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_processes)
        self.update_timer.setSingleShot(False)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Error tracking
        self.update_errors = 0
        self.max_update_errors = 5
        
        # Initial update
        self.update_processes()
    
    def update_processes(self):
        """Update the process list with error handling."""
        try:
            processes = []
            
            # Get process information safely
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'username']):
                try:
                    info = proc.info
                    if info and info.get('memory_info'):
                        memory_mb = info['memory_info'].rss / (1024 * 1024)
                        processes.append({
                            'name': info.get('name', 'Unknown')[:50],  # Limit name length
                            'pid': info.get('pid', 0),
                            'cpu_percent': info.get('cpu_percent', 0.0) or 0.0,
                            'memory_mb': memory_mb,
                            'status': info.get('status', 'unknown'),
                            'username': (info.get('username') or 'Unknown')[:20]  # Limit username length
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    continue
                except Exception as e:
                    self.logger.debug(f"Error getting process info: {e}")
                    continue
            
            # Sort by CPU usage (descending)
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            # Update table safely
            self._update_table_content(processes[:50])  # Show top 50 processes
            
            # Reset error count on success
            self.update_errors = 0
            
        except Exception as e:
            self.update_errors += 1
            self.logger.error(f"Error updating process table: {e}")
            
            if self.update_errors >= self.max_update_errors:
                self.update_timer.stop()
                self.logger.error("Too many process table update errors, stopping updates")
    
    def _update_table_content(self, processes: List[Dict]):
        """Update table content safely."""
        try:
            self.setRowCount(len(processes))
            
            for row, proc in enumerate(processes):
                # Process name
                name_item = QTableWidgetItem(str(proc.get('name', 'Unknown')))
                self.setItem(row, 0, name_item)
                
                # PID
                pid_item = QTableWidgetItem(str(proc.get('pid', 0)))
                self.setItem(row, 1, pid_item)
                
                # CPU usage with color coding
                cpu_percent = proc.get('cpu_percent', 0.0)
                cpu_item = QTableWidgetItem(f"{cpu_percent:.1f}%")
                if cpu_percent > 50:
                    cpu_item.setForeground(QColor("#F44336"))
                elif cpu_percent > 25:
                    cpu_item.setForeground(QColor("#FF9800"))
                else:
                    cpu_item.setForeground(QColor("#4CAF50"))
                self.setItem(row, 2, cpu_item)
                
                # Memory
                memory_mb = proc.get('memory_mb', 0.0)
                memory_item = QTableWidgetItem(f"{memory_mb:.1f} MB")
                self.setItem(row, 3, memory_item)
                
                # Status
                status_item = QTableWidgetItem(str(proc.get('status', 'unknown')))
                self.setItem(row, 4, status_item)
                
                # User
                user_item = QTableWidgetItem(str(proc.get('username', 'Unknown')))
                self.setItem(row, 5, user_item)
                
        except Exception as e:
            self.logger.error(f"Error updating table content: {e}")
    
    def cleanup(self):
        """Clean up table resources."""
        try:
            if self.update_timer:
                self.update_timer.stop()
                self.update_timer = None
        except Exception as e:
            self.logger.error(f"Error cleaning up process table: {e}")


class SystemStatusTab(QWidget):
    """
    Modern System Status Tab providing comprehensive system monitoring.
    
    Features:
    - Real-time performance charts with error handling
    - Detailed system information
    - Process monitoring with resource management
    - Hardware information display
    - Performance analytics with data validation
    """
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Data containers
        self.system_info = SystemInfo()
        self.metrics_history: List[PerformanceMetrics] = []
        self._lock = threading.Lock()
        
        # Components
        self.metrics_collector = None
        self.charts: Dict[str, RealTimeChart] = {}
        self.info_labels: Dict[str, QLabel] = {}
        self.progress_bars: Dict[str, QProgressBar] = {}
        self.process_table = None
        
        try:
            self._setup_ui()
            self._load_system_info()
            self._setup_connections()
            
            # Start metrics collection
            self._start_metrics_collection()
            
        except Exception as e:
            self.logger.error(f"Error initializing SystemStatusTab: {e}")
            self._show_error_message("Initialization Error", str(e))
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        try:
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(24, 24, 24, 24)
            main_layout.setSpacing(20)
            
            # Header
            header_section = self._create_header_section()
            main_layout.addWidget(header_section)
            
            # Create tab widget for different views
            self.tab_widget = QTabWidget()
            self.tab_widget.setStyleSheet("""
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
            
            # Performance tab
            performance_tab = self._create_performance_tab()
            self.tab_widget.addTab(performance_tab, "Performance")
            
            # System info tab
            system_tab = self._create_system_info_tab()
            self.tab_widget.addTab(system_tab, "System Info")
            
            # Processes tab
            processes_tab = self._create_processes_tab()
            self.tab_widget.addTab(processes_tab, "Processes")
            
            main_layout.addWidget(self.tab_widget)
            
        except Exception as e:
            self.logger.error(f"Error setting up UI: {e}")
            raise
    
    def _create_header_section(self) -> QWidget:
        """Create the header section with quick stats."""
        try:
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
            
            layout = QVBoxLayout(header)
            layout.setSpacing(12)
            
            # Title
            title_layout = QHBoxLayout()
            
            title = QLabel("System Status")
            title.setStyleSheet("""
                color: #FFFFFF;
                font-size: 24px;
                font-weight: bold;
            """)
            title_layout.addWidget(title)
            
            title_layout.addStretch()
            
            # Quick stats
            stats_layout = QHBoxLayout()
            
            # Create quick stat widgets
            quick_stats = [
                ("CPU", "cpu_quick"),
                ("Memory", "memory_quick"),
                ("Disk", "disk_quick"),
                ("Network", "network_quick")
            ]
            
            for stat_name, stat_key in quick_stats:
                stat_widget = self._create_quick_stat_widget(stat_name, stat_key)
                stats_layout.addWidget(stat_widget)
            
            title_layout.addLayout(stats_layout)
            layout.addLayout(title_layout)
            
            # Description and uptime
            desc_layout = QHBoxLayout()
            
            description = QLabel("Real-time system monitoring and performance analytics")
            description.setStyleSheet("""
                color: #B0BEC5;
                font-size: 14px;
            """)
            desc_layout.addWidget(description)
            
            desc_layout.addStretch()
            
            self.uptime_label = QLabel("Uptime: --")
            self.uptime_label.setStyleSheet("""
                color: #78909C;
                font-size: 12px;
            """)
            desc_layout.addWidget(self.uptime_label)
            
            layout.addLayout(desc_layout)
            
            return header
            
        except Exception as e:
            self.logger.error(f"Error creating header section: {e}")
            return QFrame()  # Return empty frame on error
    
    def _create_quick_stat_widget(self, name: str, key: str) -> QWidget:
        """Create a quick stat widget."""
        try:
            widget = QFrame()
            widget.setFixedSize(100, 60)
            widget.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid #37414F;
                    border-radius: 8px;
                }
            """)
            
            layout = QVBoxLayout(widget)
            layout.setSpacing(2)
            layout.setContentsMargins(8, 6, 8, 6)
            
            # Value label
            value_label = QLabel("0%")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet("""
                color: #00A8FF;
                font-size: 16px;
                font-weight: bold;
            """)
            self.info_labels[f"{key}_value"] = value_label
            layout.addWidget(value_label)
            
            # Name label
            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("""
                color: #78909C;
                font-size: 10px;
            """)
            layout.addWidget(name_label)
            
            return widget
            
        except Exception as e:
            self.logger.error(f"Error creating quick stat widget: {e}")
            return QFrame()
    
    def _create_performance_tab(self) -> QWidget:
        """Create the performance monitoring tab."""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setSpacing(16)
            
            # Charts grid
            charts_layout = QGridLayout()
            charts_layout.setSpacing(16)
            
            # Create performance charts
            chart_configs = [
                ("CPU Usage", "cpu_chart", QColor(0, 168, 255)),
                ("Memory Usage", "memory_chart", QColor(76, 175, 80)),
                ("Disk Usage", "disk_chart", QColor(255, 152, 0)),
                ("Network Activity", "network_chart", QColor(156, 39, 176))
            ]
            
            for i, (title, key, color) in enumerate(chart_configs):
                chart = RealTimeChart(title)
                chart.set_colors(color)
                self.charts[key] = chart
                
                row = i // 2
                col = i % 2
                charts_layout.addWidget(chart, row, col)
            
            layout.addLayout(charts_layout)
            
            # Resource usage bars
            usage_group = self._create_usage_bars_section()
            layout.addWidget(usage_group)
            
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating performance tab: {e}")
            return QWidget()
    
    def _create_usage_bars_section(self) -> QGroupBox:
        """Create the resource usage bars section."""
        try:
            usage_group = QGroupBox("Current Resource Usage")
            usage_group.setStyleSheet("""
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
            
            usage_layout = QVBoxLayout(usage_group)
            usage_layout.setSpacing(12)
            
            # Create usage bars
            usage_items = [
                ("CPU", "cpu_bar"),
                ("Memory", "memory_bar"),
                ("Disk", "disk_bar")
            ]
            
            for name, key in usage_items:
                item_layout = QHBoxLayout()
                
                label = QLabel(name)
                label.setFixedWidth(80)
                label.setStyleSheet("color: #B0BEC5; font-weight: 500;")
                item_layout.addWidget(label)
                
                progress_bar = QProgressBar()
                progress_bar.setFixedHeight(20)
                progress_bar.setRange(0, 100)
                progress_bar.setStyleSheet("""
                    QProgressBar {
                        background-color: #353A4F;
                        border: 1px solid #37414F;
                        border-radius: 10px;
                        text-align: center;
                        color: #FFFFFF;
                        font-size: 11px;
                    }
                    
                    QProgressBar::chunk {
                        background-color: #00A8FF;
                        border-radius: 9px;
                    }
                """)
                self.progress_bars[key] = progress_bar
                item_layout.addWidget(progress_bar)
                
                usage_layout.addLayout(item_layout)
            
            return usage_group
            
        except Exception as e:
            self.logger.error(f"Error creating usage bars section: {e}")
            return QGroupBox()
    
    def _create_system_info_tab(self) -> QWidget:
        """Create the system information tab."""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setSpacing(16)
            
            # Create info groups
            groups = [
                ("Operating System", ["os_name", "os_version", "hostname", "architecture"]),
                ("Hardware", ["processor", "cpu_cores", "cpu_freq_max", "total_memory", "total_disk"]),
                ("Software", ["python_version", "boot_time"])
            ]
            
            for group_name, fields in groups:
                group = self._create_info_group(group_name, fields)
                layout.addWidget(group)
            
            layout.addStretch()
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating system info tab: {e}")
            return QWidget()
    
    def _create_info_group(self, group_name: str, fields: List[str]) -> QGroupBox:
        """Create an information group."""
        try:
            group = QGroupBox(group_name)
            group.setStyleSheet("""
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
            
            group_layout = QGridLayout(group)
            group_layout.setSpacing(12)
            
            for i, field in enumerate(fields):
                label = QLabel(field.replace('_', ' ').title() + ":")
                label.setStyleSheet("color: #B0BEC5; font-weight: 500;")
                group_layout.addWidget(label, i, 0)
                
                value_label = QLabel("Loading...")
                value_label.setStyleSheet("color: #FFFFFF;")
                self.info_labels[field] = value_label
                group_layout.addWidget(value_label, i, 1)
            
            return group
            
        except Exception as e:
            self.logger.error(f"Error creating info group {group_name}: {e}")
            return QGroupBox()
    
    def _create_processes_tab(self) -> QWidget:
        """Create the processes monitoring tab."""
        try:
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.setSpacing(16)
            
            # Process controls
            controls_layout = QHBoxLayout()
            
            refresh_btn = QPushButton("Refresh")
            refresh_btn.setFixedHeight(32)
            refresh_btn.clicked.connect(self._refresh_processes)
            controls_layout.addWidget(refresh_btn)
            
            controls_layout.addStretch()
            
            info_label = QLabel("Showing top 50 processes by CPU usage")
            info_label.setStyleSheet("color: #78909C; font-size: 12px;")
            controls_layout.addWidget(info_label)
            
            layout.addLayout(controls_layout)
            
            # Process table
            self.process_table = ProcessTableWidget()
            layout.addWidget(self.process_table)
            
            return tab
            
        except Exception as e:
            self.logger.error(f"Error creating processes tab: {e}")
            return QWidget()
    
    def _load_system_info(self):
        """Load static system information safely."""
        try:
            # Operating system
            self.system_info.os_name = platform.system()
            self.system_info.os_version = platform.release()
            self.system_info.hostname = platform.node()
            self.system_info.architecture = platform.machine()
            
            # Processor
            try:
                processor_info = platform.processor()
                self.system_info.processor = processor_info if processor_info else "Unknown"
            except Exception:
                self.system_info.processor = "Unknown"
            
            # Python version
            self.system_info.python_version = platform.python_version()
            
            # Hardware info
            self.system_info.cpu_cores = psutil.cpu_count(logical=True)
            
            try:
                cpu_freq = psutil.cpu_freq()
                self.system_info.cpu_freq_max = cpu_freq.max if cpu_freq else 0.0
            except Exception:
                self.system_info.cpu_freq_max = 0.0
            
            try:
                memory = psutil.virtual_memory()
                self.system_info.total_memory = memory.total
            except Exception:
                self.system_info.total_memory = 0
            
            try:
                disk = psutil.disk_usage('/')
                self.system_info.total_disk = disk.total
            except Exception:
                self.system_info.total_disk = 0
            
            # Boot time
            try:
                self.system_info.boot_time = datetime.fromtimestamp(psutil.boot_time())
            except Exception:
                self.system_info.boot_time = None
            
            # Update info labels
            self._update_system_info_display()
            
        except Exception as e:
            self.logger.error(f"Error loading system info: {e}")
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Connections will be set up when metrics collector is created
        pass
    
    def _start_metrics_collection(self):
        """Start the metrics collection thread."""
        try:
            self.metrics_collector = MetricsCollector()
            self.metrics_collector.metrics_updated.connect(self._on_metrics_updated)
            self.metrics_collector.error_occurred.connect(self._on_collector_error)
            self.metrics_collector.start()
            
            self.logger.info("Started metrics collection")
            
        except Exception as e:
            self.logger.error(f"Error starting metrics collection: {e}")
    
    def _update_system_info_display(self):
        """Update the system information display."""
        try:
            # Update info labels safely
            info_updates = {
                "os_name": self.system_info.os_name,
                "os_version": self.system_info.os_version,
                "hostname": self.system_info.hostname,
                "architecture": self.system_info.architecture,
                "processor": self.system_info.processor,
                "python_version": self.system_info.python_version,
                "cpu_cores": f"{self.system_info.cpu_cores} cores",
                "cpu_freq_max": f"{self.system_info.cpu_freq_max:.0f} MHz" if self.system_info.cpu_freq_max > 0 else "Unknown",
                "total_memory": self._format_bytes(self.system_info.total_memory),
                "total_disk": self._format_bytes(self.system_info.total_disk),
                "boot_time": self.system_info.boot_time.strftime("%Y-%m-%d %H:%M:%S") if self.system_info.boot_time else "Unknown"
            }
            
            for key, value in info_updates.items():
                if key in self.info_labels:
                    self.info_labels[key].setText(str(value))
            
        except Exception as e:
            self.logger.error(f"Error updating system info display: {e}")
    
    def _on_metrics_updated(self, metrics: PerformanceMetrics):
        """Handle updated metrics from the collector."""
        try:
            with self._lock:
                # Store metrics
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > 300:  # Keep last 5 minutes
                    self.metrics_history = self.metrics_history[-300:]
            
            # Update charts
            self._update_charts(metrics)
            
            # Update progress bars
            self._update_progress_bars(metrics)
            
            # Update quick stats
            self._update_quick_stats(metrics)
            
            # Update uptime
            self._update_uptime()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics display: {e}")
    
    def _update_charts(self, metrics: PerformanceMetrics):
        """Update chart displays."""
        try:
            if "cpu_chart" in self.charts:
                self.charts["cpu_chart"].add_data_point(metrics.cpu_percent, metrics.timestamp)
            
            if "memory_chart" in self.charts:
                self.charts["memory_chart"].add_data_point(metrics.memory_percent, metrics.timestamp)
            
            if "disk_chart" in self.charts:
                self.charts["disk_chart"].add_data_point(metrics.disk_percent, metrics.timestamp)
            
            # Network chart (show KB/s)
            if "network_chart" in self.charts:
                network_total = (metrics.network_sent + metrics.network_recv) / 1024
                self.charts["network_chart"].add_data_point(network_total, metrics.timestamp)
                self.charts["network_chart"].set_range(0, max(1000, network_total * 1.2))
                
        except Exception as e:
            self.logger.error(f"Error updating charts: {e}")
    
    def _update_progress_bars(self, metrics: PerformanceMetrics):
        """Update progress bar displays."""
        try:
            if "cpu_bar" in self.progress_bars:
                self.progress_bars["cpu_bar"].setValue(int(metrics.cpu_percent))
            
            if "memory_bar" in self.progress_bars:
                self.progress_bars["memory_bar"].setValue(int(metrics.memory_percent))
            
            if "disk_bar" in self.progress_bars:
                self.progress_bars["disk_bar"].setValue(int(metrics.disk_percent))
                
        except Exception as e:
            self.logger.error(f"Error updating progress bars: {e}")
    
    def _update_quick_stats(self, metrics: PerformanceMetrics):
        """Update quick stats display."""
        try:
            if "cpu_quick_value" in self.info_labels:
                self.info_labels["cpu_quick_value"].setText(f"{metrics.cpu_percent:.1f}%")
            
            if "memory_quick_value" in self.info_labels:
                self.info_labels["memory_quick_value"].setText(f"{metrics.memory_percent:.1f}%")
            
            if "disk_quick_value" in self.info_labels:
                self.info_labels["disk_quick_value"].setText(f"{metrics.disk_percent:.1f}%")
            
            # Network display
            if "network_quick_value" in self.info_labels:
                network_mb = (metrics.network_sent + metrics.network_recv) / (1024 * 1024)
                if network_mb < 1:
                    network_kb = (metrics.network_sent + metrics.network_recv) / 1024
                    self.info_labels["network_quick_value"].setText(f"{network_kb:.0f}KB/s")
                else:
                    self.info_labels["network_quick_value"].setText(f"{network_mb:.1f}MB/s")
                    
        except Exception as e:
            self.logger.error(f"Error updating quick stats: {e}")
    
    def _update_uptime(self):
        """Update system uptime display."""
        try:
            if self.system_info.boot_time:
                uptime = datetime.now() - self.system_info.boot_time
                days = uptime.days
                hours, remainder = divmod(uptime.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                if days > 0:
                    uptime_str = f"Uptime: {days}d {hours}h {minutes}m"
                elif hours > 0:
                    uptime_str = f"Uptime: {hours}h {minutes}m"
                else:
                    uptime_str = f"Uptime: {minutes}m"
                
                self.uptime_label.setText(uptime_str)
                
        except Exception as e:
            self.logger.error(f"Error updating uptime: {e}")
    
    def _on_collector_error(self, error_message: str):
        """Handle collector error messages."""
        self.logger.warning(f"Metrics collector error: {error_message}")
    
    def _refresh_processes(self):
        """Manually refresh the process list."""
        try:
            if self.process_table:
                self.process_table.update_processes()
        except Exception as e:
            self.logger.error(f"Error refreshing processes: {e}")
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable format."""
        try:
            if bytes_value == 0:
                return "0 B"
            
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024:
                    if unit == 'B':
                        return f"{bytes_value} {unit}"
                    else:
                        return f"{bytes_value:.2f} {unit}"
                bytes_value /= 1024
            return f"{bytes_value:.2f} PB"
        except Exception:
            return "Unknown"
    
    def _show_error_message(self, title: str, message: str):
        """Show error message to user."""
        try:
            QMessageBox.warning(self, title, message)
        except Exception:
            self.logger.error(f"Could not show error dialog: {title} - {message}")
    
    def cleanup(self):
        """Cleanup resources when tab is destroyed."""
        try:
            self.logger.info("Starting SystemStatusTab cleanup")
            
            # Stop metrics collection
            if self.metrics_collector and self.metrics_collector.isRunning():
                self.metrics_collector.stop_collection()
                self.metrics_collector = None
            
            # Clean up process table
            if self.process_table:
                self.process_table.cleanup()
                self.process_table = None
            
            # Clear charts
            for chart in self.charts.values():
                if hasattr(chart, 'cleanup'):
                    chart.cleanup()
            self.charts.clear()
            
            self.logger.info("SystemStatusTab cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")