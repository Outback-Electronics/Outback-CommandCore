"""
Notification Manager for CommandCore Launcher

Provides a modern notification system with custom styling,
multiple notification types, and configurable behavior.
"""

import sys
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtGui import QScreen
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect,
    QPoint, QSize, Signal, QObject, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QPainterPath, QBrush,
    QFont, QPixmap, QIcon, QPalette
)


class NotificationType(Enum):
    """Notification types with associated styling."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CUSTOM = "custom"


class NotificationPosition(Enum):
    """Notification display positions."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    enabled: bool = True
    position: NotificationPosition = NotificationPosition.BOTTOM_RIGHT
    duration: int = 5000  # milliseconds
    max_notifications: int = 5
    animation_duration: int = 300
    spacing: int = 10
    margin: int = 20
    opacity: float = 0.95
    show_close_button: bool = True
    auto_hide: bool = True
    play_sound: bool = False
    sound_file: Optional[str] = None


@dataclass
class NotificationData:
    """Data for a single notification."""
    id: str
    title: str
    message: str
    type: NotificationType
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[int] = None
    actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    callback: Optional[Callable] = None
    persistent: bool = False


class ModernNotificationWidget(QFrame):
    """Modern notification widget with animations and styling."""
    
    close_requested = Signal(str)  # notification_id
    action_clicked = Signal(str, str)  # notification_id, action_id
    
    def __init__(self, notification: NotificationData, config: NotificationConfig, parent=None):
        super().__init__(parent)
        
        self.notification = notification
        self.config = config
        self.is_closing = False
        
        # Widget properties
        self.setFixedWidth(350)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self._setup_ui()
        self._setup_style()
        self._setup_animations()
        
        # Auto-hide timer
        if self.config.auto_hide and not self.notification.persistent:
            duration = self.notification.duration or self.config.duration
            self.hide_timer = QTimer()
            self.hide_timer.setSingleShot(True)
            self.hide_timer.timeout.connect(self.start_close_animation)
            self.hide_timer.start(duration)
    
    def _setup_ui(self):
        """Setup the notification UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Icon (based on notification type)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self._set_icon()
        header_layout.addWidget(self.icon_label)
        
        # Title
        self.title_label = QLabel(self.notification.title)
        self.title_label.setObjectName("notificationTitle")
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Close button
        if self.config.show_close_button:
            self.close_btn = QPushButton("×")
            self.close_btn.setFixedSize(20, 20)
            self.close_btn.setObjectName("notificationCloseBtn")
            self.close_btn.clicked.connect(self.start_close_animation)
            header_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(header_layout)
        
        # Message
        if self.notification.message:
            self.message_label = QLabel(self.notification.message)
            self.message_label.setObjectName("notificationMessage")
            self.message_label.setWordWrap(True)
            self.message_label.setMaximumHeight(100)
            main_layout.addWidget(self.message_label)
        
        # Actions
        if self.notification.actions:
            actions_layout = QHBoxLayout()
            actions_layout.setSpacing(8)
            
            for action in self.notification.actions:
                action_btn = QPushButton(action.get('text', 'Action'))
                action_btn.setObjectName("notificationActionBtn")
                action_btn.clicked.connect(
                    lambda checked, aid=action.get('id'): self.action_clicked.emit(self.notification.id, aid)
                )
                actions_layout.addWidget(action_btn)
            
            actions_layout.addStretch()
            main_layout.addLayout(actions_layout)
        
        # Timestamp (for persistent notifications)
        if self.notification.persistent:
            time_str = self.notification.timestamp.strftime("%H:%M")
            self.time_label = QLabel(time_str)
            self.time_label.setObjectName("notificationTime")
            main_layout.addWidget(self.time_label)
        
        # Adjust height based on content
        self.adjustSize()
        self.setMaximumHeight(200)
    
    def _set_icon(self):
        """Set the notification icon based on type."""
        # Create a colored circle as icon
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Choose color based on notification type
        colors = {
            NotificationType.INFO: QColor(33, 150, 243),     # Blue
            NotificationType.SUCCESS: QColor(76, 175, 80),   # Green
            NotificationType.WARNING: QColor(255, 152, 0),   # Orange
            NotificationType.ERROR: QColor(244, 67, 54),     # Red
            NotificationType.CUSTOM: QColor(156, 39, 176)    # Purple
        }
        
        color = colors.get(self.notification.type, colors[NotificationType.INFO])
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 20, 20)
        
        # Add icon symbol
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        
        symbols = {
            NotificationType.INFO: "i",
            NotificationType.SUCCESS: "✓",
            NotificationType.WARNING: "!",
            NotificationType.ERROR: "×",
            NotificationType.CUSTOM: "•"
        }
        
        symbol = symbols.get(self.notification.type, "i")
        painter.drawText(QRect(2, 2, 20, 20), Qt.AlignCenter, symbol)
        painter.end()
        
        self.icon_label.setPixmap(pixmap)
    
    def _setup_style(self):
        """Setup notification styling."""
        # Choose colors based on notification type
        color_schemes = {
            NotificationType.INFO: {
                'bg': '#1A237E',
                'border': '#3F51B5',
                'title': '#FFFFFF',
                'message': '#E3F2FD'
            },
            NotificationType.SUCCESS: {
                'bg': '#1B5E20',
                'border': '#4CAF50',
                'title': '#FFFFFF',
                'message': '#E8F5E8'
            },
            NotificationType.WARNING: {
                'bg': '#E65100',
                'border': '#FF9800',
                'title': '#FFFFFF',
                'message': '#FFF3E0'
            },
            NotificationType.ERROR: {
                'bg': '#B71C1C',
                'border': '#F44336',
                'title': '#FFFFFF',
                'message': '#FFEBEE'
            },
            NotificationType.CUSTOM: {
                'bg': '#4A148C',
                'border': '#9C27B0',
                'title': '#FFFFFF',
                'message': '#F3E5F5'
            }
        }
        
        scheme = color_schemes.get(self.notification.type, color_schemes[NotificationType.INFO])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {scheme['bg']};
                border: 2px solid {scheme['border']};
                border-radius: 12px;
            }}
            
            QLabel#notificationTitle {{
                color: {scheme['title']};
                font-size: 14px;
                font-weight: bold;
                margin: 0px;
            }}
            
            QLabel#notificationMessage {{
                color: {scheme['message']};
                font-size: 12px;
                margin: 0px;
                line-height: 1.4;
            }}
            
            QLabel#notificationTime {{
                color: {scheme['message']};
                font-size: 10px;
                margin: 0px;
            }}
            
            QPushButton#notificationCloseBtn {{
                background-color: transparent;
                color: {scheme['title']};
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            
            QPushButton#notificationCloseBtn:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            
            QPushButton#notificationActionBtn {{
                background-color: {scheme['border']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            
            QPushButton#notificationActionBtn:hover {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def _setup_animations(self):
        """Setup show/hide animations."""
        # Slide in animation
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(self.config.animation_duration)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(self.config.animation_duration)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Combined animation group
        self.show_animation_group = QParallelAnimationGroup()
        self.show_animation_group.addAnimation(self.slide_animation)
        self.show_animation_group.addAnimation(self.fade_animation)
        
        # Hide animation
        self.hide_animation = QPropertyAnimation(self, b"windowOpacity")
        self.hide_animation.setDuration(self.config.animation_duration)
        self.hide_animation.setEasingCurve(QEasingCurve.InCubic)
        self.hide_animation.finished.connect(self._on_hide_finished)
    
    def show_notification(self, target_pos: QPoint):
        """Show the notification with animation."""
        # Set initial position (off-screen)
        screen_rect = QApplication.primaryScreen().availableGeometry()
        
        if self.config.position in [NotificationPosition.TOP_RIGHT, NotificationPosition.BOTTOM_RIGHT]:
            start_x = screen_rect.width()
        else:
            start_x = -self.width()
        
        self.move(start_x, target_pos.y())
        self.setWindowOpacity(0.0)
        self.show()
        
        # Animate to target position
        self.slide_animation.setStartValue(QRect(start_x, target_pos.y(), self.width(), self.height()))
        self.slide_animation.setEndValue(QRect(target_pos.x(), target_pos.y(), self.width(), self.height()))
        
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(self.config.opacity)
        
        self.show_animation_group.start()
    
    def start_close_animation(self):
        """Start the close animation."""
        if self.is_closing:
            return
        
        self.is_closing = True
        
        # Stop auto-hide timer
        if hasattr(self, 'hide_timer'):
            self.hide_timer.stop()
        
        # Start fade out
        self.hide_animation.setStartValue(self.windowOpacity())
        self.hide_animation.setEndValue(0.0)
        self.hide_animation.start()
    
    def _on_hide_finished(self):
        """Handle hide animation completion."""
        self.close_requested.emit(self.notification.id)
        self.close()
    
    def mousePressEvent(self, event):
        """Handle mouse press for interaction."""
        if event.button() == Qt.LeftButton:
            # Execute callback if present
            if self.notification.callback:
                try:
                    self.notification.callback(self.notification)
                except Exception as e:
                    print(f"Error in notification callback: {e}")
            
            # Close non-persistent notifications on click
            if not self.notification.persistent:
                self.start_close_animation()
        
        super().mousePressEvent(event)


class NotificationManager(QObject):
    """
    Modern notification manager with advanced features.
    
    Features:
    - Multiple notification types with custom styling
    - Configurable positioning and animations
    - Action buttons and callbacks
    - Persistent and temporary notifications
    - Sound notifications
    - Notification history
    - Batch operations
    """
    
    # Signals
    notification_shown = Signal(str)     # notification_id
    notification_closed = Signal(str)    # notification_id
    notification_clicked = Signal(str)   # notification_id
    action_triggered = Signal(str, str)  # notification_id, action_id
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        super().__init__()
        
        self.config = config or NotificationConfig()
        self.active_notifications: Dict[str, ModernNotificationWidget] = {}
        self.notification_history: List[NotificationData] = []
        self.max_history_size = 100
        
        # Position tracking
        self.position_tracker: Dict[NotificationPosition, List[QPoint]] = {
            pos: [] for pos in NotificationPosition
        }
        
        # Notification counter for unique IDs
        self.notification_counter = 0
    
    def show_notification(self, 
                         title: str, 
                         message: str = "", 
                         notification_type: NotificationType = NotificationType.INFO,
                         duration: Optional[int] = None,
                         actions: List[Dict[str, Any]] = None,
                         callback: Optional[Callable] = None,
                         persistent: bool = False,
                         metadata: Dict[str, Any] = None) -> str:
        """Show a new notification."""
        
        if not self.config.enabled:
            return ""
        
        # Generate unique ID
        self.notification_counter += 1
        notification_id = f"notification_{self.notification_counter}_{int(datetime.now().timestamp())}"
        
        # Create notification data
        notification = NotificationData(
            id=notification_id,
            title=title,
            message=message,
            type=notification_type,
            duration=duration,
            actions=actions or [],
            callback=callback,
            persistent=persistent,
            metadata=metadata or {}
        )
        
        # Add to history
        self._add_to_history(notification)
        
        # Check if we need to remove old notifications
        self._manage_notification_limit()
        
        # Create and show notification widget
        widget = ModernNotificationWidget(notification, self.config)
        widget.close_requested.connect(self._on_notification_closed)
        widget.action_clicked.connect(self._on_action_clicked)
        
        # Calculate position
        position = self._calculate_position(widget)
        
        # Store reference
        self.active_notifications[notification_id] = widget
        
        # Show with animation
        widget.show_notification(position)
        
        # Play sound if enabled
        if self.config.play_sound:
            self._play_notification_sound()
        
        self.notification_shown.emit(notification_id)
        return notification_id
    
    def show_info(self, title: str, message: str = "", **kwargs) -> str:
        """Show an info notification."""
        return self.show_notification(title, message, NotificationType.INFO, **kwargs)
    
    def show_success(self, title: str, message: str = "", **kwargs) -> str:
        """Show a success notification."""
        return self.show_notification(title, message, NotificationType.SUCCESS, **kwargs)
    
    def show_warning(self, title: str, message: str = "", **kwargs) -> str:
        """Show a warning notification."""
        return self.show_notification(title, message, NotificationType.WARNING, **kwargs)
    
    def show_error(self, title: str, message: str = "", **kwargs) -> str:
        """Show an error notification."""
        return self.show_notification(title, message, NotificationType.ERROR, **kwargs)
    
    def close_notification(self, notification_id: str) -> bool:
        """Close a specific notification."""
        if notification_id in self.active_notifications:
            widget = self.active_notifications[notification_id]
            widget.start_close_animation()
            return True
        return False
    
    def close_all_notifications(self):
        """Close all active notifications."""
        for notification_id in list(self.active_notifications.keys()):
            self.close_notification(notification_id)
    
    def close_notifications_by_type(self, notification_type: NotificationType):
        """Close all notifications of a specific type."""
        to_close = []
        for notification_id, widget in self.active_notifications.items():
            if widget.notification.type == notification_type:
                to_close.append(notification_id)
        
        for notification_id in to_close:
            self.close_notification(notification_id)
    
    def get_active_notifications(self) -> List[NotificationData]:
        """Get list of currently active notifications."""
        return [widget.notification for widget in self.active_notifications.values()]
    
    def get_notification_history(self, 
                                notification_type: Optional[NotificationType] = None,
                                limit: Optional[int] = None) -> List[NotificationData]:
        """Get notification history with optional filtering."""
        history = self.notification_history
        
        if notification_type:
            history = [n for n in history if n.type == notification_type]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def clear_history(self):
        """Clear notification history."""
        self.notification_history.clear()
    
    def update_config(self, config: NotificationConfig):
        """Update notification configuration."""
        self.config = config
        
        # Update existing notifications if needed
        for widget in self.active_notifications.values():
            widget.config = config
    
    def _calculate_position(self, widget: ModernNotificationWidget) -> QPoint:
        """Calculate position for a new notification."""
        screen_rect = QApplication.primaryScreen().availableGeometry()
        
        # Get notification dimensions
        widget_width = widget.width()
        widget_height = widget.height()
        
        # Calculate base position based on config
        if self.config.position == NotificationPosition.TOP_RIGHT:
            x = screen_rect.width() - widget_width - self.config.margin
            y = self.config.margin
        elif self.config.position == NotificationPosition.TOP_LEFT:
            x = self.config.margin
            y = self.config.margin
        elif self.config.position == NotificationPosition.BOTTOM_RIGHT:
            x = screen_rect.width() - widget_width - self.config.margin
            y = screen_rect.height() - widget_height - self.config.margin
        elif self.config.position == NotificationPosition.BOTTOM_LEFT:
            x = self.config.margin
            y = screen_rect.height() - widget_height - self.config.margin
        else:  # CENTER
            x = (screen_rect.width() - widget_width) // 2
            y = (screen_rect.height() - widget_height) // 2
        
        # Adjust for existing notifications
        positions = self.position_tracker[self.config.position]
        
        if self.config.position in [NotificationPosition.TOP_LEFT, NotificationPosition.TOP_RIGHT]:
            # Stack downward
            for pos in positions:
                if abs(pos.x() - x) < widget_width:
                    y = max(y, pos.y() + widget_height + self.config.spacing)
        elif self.config.position in [NotificationPosition.BOTTOM_LEFT, NotificationPosition.BOTTOM_RIGHT]:
            # Stack upward
            for pos in positions:
                if abs(pos.x() - x) < widget_width:
                    y = min(y, pos.y() - widget_height - self.config.spacing)
        
        position = QPoint(x, y)
        positions.append(position)
        
        return position
    
    def _manage_notification_limit(self):
        """Remove oldest notifications if limit exceeded."""
        if len(self.active_notifications) >= self.config.max_notifications:
            # Get oldest notification
            oldest_id = min(self.active_notifications.keys(), 
                          key=lambda nid: self.active_notifications[nid].notification.timestamp)
            self.close_notification(oldest_id)
    
    def _add_to_history(self, notification: NotificationData):
        """Add notification to history."""
        self.notification_history.append(notification)
        
        # Limit history size
        if len(self.notification_history) > self.max_history_size:
            self.notification_history = self.notification_history[-self.max_history_size:]
    
    def _on_notification_closed(self, notification_id: str):
        """Handle notification close event."""
        if notification_id in self.active_notifications:
            widget = self.active_notifications[notification_id]
            
            # Remove from position tracker
            positions = self.position_tracker[self.config.position]
            widget_pos = widget.pos()
            positions = [pos for pos in positions if pos != widget_pos]
            self.position_tracker[self.config.position] = positions
            
            # Remove from active notifications
            del self.active_notifications[notification_id]
            
            self.notification_closed.emit(notification_id)
    
    def _on_action_clicked(self, notification_id: str, action_id: str):
        """Handle notification action click."""
        self.action_triggered.emit(notification_id, action_id)
        
        # Close notification after action (unless persistent)
        if notification_id in self.active_notifications:
            widget = self.active_notifications[notification_id]
            if not widget.notification.persistent:
                self.close_notification(notification_id)
    
    def _play_notification_sound(self):
        """Play notification sound if configured."""
        try:
            if self.config.sound_file and Path(self.config.sound_file).exists():
                # TODO: Implement sound playback
                # This would require additional audio libraries
                pass
        except Exception as e:
            print(f"Error playing notification sound: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification manager statistics."""
        return {
            'active_notifications': len(self.active_notifications),
            'total_notifications_shown': self.notification_counter,
            'history_size': len(self.notification_history),
            'config': {
                'enabled': self.config.enabled,
                'position': self.config.position.value,
                'max_notifications': self.config.max_notifications,
                'auto_hide': self.config.auto_hide
            }
        }


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None

def get_notification_manager() -> NotificationManager:
    """Get the global notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

def show_notification(title: str, message: str = "", notification_type: str = "info", **kwargs) -> str:
    """Convenience function to show a notification."""
    manager = get_notification_manager()
    
    # Convert string type to enum
    type_map = {
        'info': NotificationType.INFO,
        'success': NotificationType.SUCCESS,
        'warning': NotificationType.WARNING,
        'error': NotificationType.ERROR,
        'custom': NotificationType.CUSTOM
    }
    
    ntype = type_map.get(notification_type.lower(), NotificationType.INFO)
    return manager.show_notification(title, message, ntype, **kwargs)