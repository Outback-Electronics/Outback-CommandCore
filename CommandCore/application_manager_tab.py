"""
Modern Application Manager Tab for CommandCore Launcher

Provides comprehensive application management with modern UI,
process monitoring, and advanced controls.
"""

import os
import sys
import subprocess
import psutil
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import shutil
import stat

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QGroupBox,
    QListWidget, QListWidgetItem, QProgressBar, QMenu,
    QMessageBox, QDialog, QTextEdit, QSplitter, QTabWidget,
    QHeaderView, QTreeWidget, QTreeWidgetItem, QSizePolicy,
    QComboBox, QLineEdit, QCheckBox, QSpinBox, QFileDialog
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QThread, QMutex, QProcess,
    QPropertyAnimation, QEasingCurve, QSize, QRect, QStandardPaths
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QPainter, QColor, QAction,
    QLinearGradient, QPainterPath, QBrush, QContextMenuEvent
)


class AppStatus(Enum):
    """Application status enumeration."""
    UNKNOWN = "unknown"
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    NOT_INSTALLED = "not_installed"


@dataclass
class ApplicationInfo:
    """Comprehensive application information."""
    id: str
    name: str
    description: str
    executable_path: str
    working_directory: str
    version: str = "unknown"
    status: AppStatus = AppStatus.STOPPED
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    log_file: Optional[str] = None
    auto_restart: bool = False
    dependencies: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    command_args: List[str] = field(default_factory=list)
    icon_path: Optional[str] = None
    category: str = "General"
    priority: int = 0
    validated: bool = False
    last_error: Optional[str] = None


class ProcessMonitor(QThread):
    """Advanced process monitoring with resource tracking and error handling."""
    
    process_status_changed = Signal(str, AppStatus, dict)
    resource_stats_updated = Signal(str, dict)
    
    def __init__(self):
        super().__init__()
        
        self.monitored_apps: Dict[str, ApplicationInfo] = {}
        self.processes: Dict[str, QProcess] = {}
        self.mutex = QMutex()
        self._running = True
        
        # Performance tracking
        self.previous_stats: Dict[str, Dict] = {}
        
        # Logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def add_application(self, app_info: ApplicationInfo):
        """Add an application to monitoring with validation."""
        self.mutex.lock()
        try:
            # Validate application before adding
            if self._validate_application(app_info):
                self.monitored_apps[app_info.id] = app_info
                self.logger.info(f"Added application to monitoring: {app_info.name}")
            else:
                self.logger.warning(f"Application validation failed: {app_info.name}")
        finally:
            self.mutex.unlock()
    
    def _validate_application(self, app_info: ApplicationInfo) -> bool:
        """Validate application configuration and paths."""
        try:
            # Check if executable exists and is executable
            exec_path = Path(app_info.executable_path)
            if not exec_path.exists():
                app_info.last_error = f"Executable not found: {exec_path}"
                app_info.status = AppStatus.NOT_INSTALLED
                return False
            
            # Check if it's a valid executable file
            if not exec_path.is_file():
                app_info.last_error = f"Executable path is not a file: {exec_path}"
                app_info.status = AppStatus.NOT_INSTALLED
                return False
            
            # Check permissions on Unix-like systems
            if sys.platform != "win32":
                if not os.access(exec_path, os.X_OK):
                    app_info.last_error = f"Executable not executable: {exec_path}"
                    app_info.status = AppStatus.ERROR
                    return False
            
            # Check working directory
            work_dir = Path(app_info.working_directory)
            if not work_dir.exists() or not work_dir.is_dir():
                app_info.last_error = f"Working directory not found: {work_dir}"
                app_info.status = AppStatus.ERROR
                return False
            
            # Validate Python scripts specifically
            if exec_path.suffix.lower() == '.py':
                if not shutil.which('python') and not shutil.which('python3'):
                    app_info.last_error = "Python interpreter not found"
                    app_info.status = AppStatus.NOT_INSTALLED
                    return False
            
            app_info.validated = True
            app_info.last_error = None
            return True
            
        except Exception as e:
            app_info.last_error = f"Validation error: {str(e)}"
            app_info.status = AppStatus.ERROR
            self.logger.error(f"Error validating application {app_info.name}: {e}")
            return False
    
    def remove_application(self, app_id: str):
        """Remove an application from monitoring."""
        self.mutex.lock()
        try:
            if app_id in self.monitored_apps:
                # Stop the application if running
                if app_id in self.processes:
                    self.stop_application(app_id, force=True)
                
                del self.monitored_apps[app_id]
                self.logger.info(f"Removed application from monitoring: {app_id}")
        finally:
            self.mutex.unlock()
    
    def start_application(self, app_id: str) -> bool:
        """Start an application with comprehensive error handling."""
        self.mutex.lock()
        try:
            if app_id not in self.monitored_apps:
                self.logger.error(f"Application not found: {app_id}")
                return False
            
            app_info = self.monitored_apps[app_id]
            
            # Re-validate before starting
            if not self._validate_application(app_info):
                self.logger.error(f"Application validation failed for {app_id}: {app_info.last_error}")
                return False
            
            # Check if already running
            if app_id in self.processes:
                process = self.processes[app_id]
                if process.state() != QProcess.NotRunning:
                    self.logger.warning(f"Application {app_id} is already running")
                    return False
            
            # Create new process
            process = QProcess()
            
            # Set working directory
            try:
                process.setWorkingDirectory(app_info.working_directory)
            except Exception as e:
                self.logger.error(f"Failed to set working directory for {app_id}: {e}")
                return False
            
            # Set environment variables
            env = process.processEnvironment()
            
            # Copy current environment safely
            for key, value in os.environ.items():
                if self._is_safe_env_var(key):
                    env.insert(key, value)
            
            # Add application-specific environment variables
            for key, value in app_info.environment_vars.items():
                if self._is_safe_env_var(key):
                    env.insert(key, str(value))
            
            # Set PYTHONPATH for Python applications
            if app_info.executable_path.endswith('.py'):
                python_path = env.value('PYTHONPATH', '')
                project_root = str(Path(app_info.executable_path).parent.absolute())
                if python_path:
                    python_path = f"{project_root}{os.pathsep}{python_path}"
                else:
                    python_path = project_root
                env.insert('PYTHONPATH', python_path)
            
            process.setProcessEnvironment(env)
            
            # Connect signals
            process.started.connect(lambda: self._on_process_started(app_id))
            process.finished.connect(
                lambda exit_code, exit_status: self._on_process_finished(app_id, exit_code, exit_status)
            )
            process.errorOccurred.connect(lambda error: self._on_process_error(app_id, error))
            
            # Capture output
            process.readyReadStandardOutput.connect(
                lambda: self._handle_stdout(app_id, process)
            )
            process.readyReadStandardError.connect(
                lambda: self._handle_stderr(app_id, process)
            )
            
            # Prepare command
            program, arguments = self._prepare_command(app_info)
            if not program:
                return False
            
            # Update status
            app_info.status = AppStatus.STARTING
            self.process_status_changed.emit(app_id, AppStatus.STARTING, {})
            
            # Log the command
            cmd_str = f"{program} {' '.join(arguments)}" if arguments else program
            self.logger.info(f"Starting {app_id}: {cmd_str}")
            
            try:
                # Start the process
                process.start(program, arguments)
                
                # Wait a moment to see if it starts successfully
                if not process.waitForStarted(5000):  # 5 second timeout
                    error_msg = f"Process failed to start within timeout: {process.errorString()}"
                    self.logger.error(f"Failed to start {app_id}: {error_msg}")
                    app_info.status = AppStatus.ERROR
                    app_info.last_error = error_msg
                    self.process_status_changed.emit(app_id, AppStatus.ERROR, {"error": error_msg})
                    return False
                
                self.processes[app_id] = process
                self.logger.info(f"Successfully started {app_id} with PID {process.processId()}")
                return True
                
            except Exception as e:
                error_msg = f"Failed to start process: {str(e)}"
                self.logger.error(f"Error starting {app_id}: {error_msg}")
                app_info.status = AppStatus.ERROR
                app_info.last_error = error_msg
                self.process_status_changed.emit(app_id, AppStatus.ERROR, {"error": error_msg})
                return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error starting application {app_id}: {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def _is_safe_env_var(self, key: str) -> bool:
        """Check if an environment variable is safe to pass to child processes."""
        # Block potentially dangerous environment variables
        dangerous_vars = {
            'LD_PRELOAD', 'LD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES',
            'DYLD_LIBRARY_PATH', 'PATH_INFO', 'SCRIPT_NAME'
        }
        
        # Block Qt debug variables that might cause issues
        qt_debug_vars = {
            'QT_DEBUG_PLUGINS', 'QT_LOGGING_RULES', 'QT_LOGGING_TO_CONSOLE'
        }
        
        return key not in dangerous_vars and key not in qt_debug_vars
    
    def _prepare_command(self, app_info: ApplicationInfo) -> Tuple[Optional[str], List[str]]:
        """Prepare command and arguments for process execution."""
        try:
            exec_path = Path(app_info.executable_path)
            
            if exec_path.suffix.lower() == '.py':
                # Python script - find appropriate interpreter
                python_interpreters = ['python3', 'python']
                python_cmd = None
                
                for interpreter in python_interpreters:
                    if shutil.which(interpreter):
                        python_cmd = interpreter
                        break
                
                if not python_cmd:
                    app_info.last_error = "No Python interpreter found"
                    return None, []
                
                program = python_cmd
                arguments = [str(exec_path)] + app_info.command_args
                
            else:
                # Regular executable
                program = str(exec_path)
                arguments = app_info.command_args.copy()
            
            return program, arguments
            
        except Exception as e:
            app_info.last_error = f"Error preparing command: {str(e)}"
            self.logger.error(f"Error preparing command for {app_info.id}: {e}")
            return None, []
    
    def stop_application(self, app_id: str, force: bool = False) -> bool:
        """Stop an application with proper cleanup."""
        self.mutex.lock()
        try:
            if app_id not in self.monitored_apps:
                return False
            
            app_info = self.monitored_apps[app_id]
            app_info.status = AppStatus.STOPPING
            self.process_status_changed.emit(app_id, AppStatus.STOPPING, {})
            
            stopped = False
            
            # Try to stop QProcess first
            if app_id in self.processes:
                process = self.processes[app_id]
                if process.state() != QProcess.NotRunning:
                    if force:
                        process.kill()
                    else:
                        process.terminate()
                    
                    # Wait for process to finish
                    if process.waitForFinished(5000):  # 5 second timeout
                        stopped = True
                    elif force:
                        process.kill()
                        stopped = process.waitForFinished(2000)
            
            # Try to kill by PID if we have it and QProcess method failed
            if not stopped and app_info.pid:
                try:
                    psutil_process = psutil.Process(app_info.pid)
                    if force:
                        psutil_process.kill()
                    else:
                        psutil_process.terminate()
                    stopped = True
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self.logger.warning(f"Could not stop process {app_info.pid}: {e}")
            
            if stopped:
                self.logger.info(f"Successfully stopped {app_id}")
            else:
                self.logger.warning(f"Could not confirm {app_id} was stopped")
            
            return stopped
            
        except Exception as e:
            self.logger.error(f"Error stopping application {app_id}: {e}")
            return False
        finally:
            self.mutex.unlock()
    
    def _on_process_started(self, app_id: str):
        """Handle process started signal."""
        self.mutex.lock()
        try:
            if app_id in self.monitored_apps and app_id in self.processes:
                app_info = self.monitored_apps[app_id]
                process = self.processes[app_id]
                
                app_info.status = AppStatus.RUNNING
                app_info.pid = process.processId()
                app_info.start_time = datetime.now()
                app_info.last_error = None
                
                self.logger.info(f"Process started for {app_id} with PID {app_info.pid}")
                
                self.process_status_changed.emit(app_id, AppStatus.RUNNING, {
                    'pid': app_info.pid,
                    'start_time': app_info.start_time
                })
        finally:
            self.mutex.unlock()
    
    def _on_process_finished(self, app_id: str, exit_code: int, exit_status: QProcess.ExitStatus):
        """Handle process finished signal."""
        self.mutex.lock()
        try:
            if app_id in self.monitored_apps:
                app_info = self.monitored_apps[app_id]
                
                # Determine status based on exit code and status
                if exit_status == QProcess.CrashExit or exit_code != 0:
                    app_info.status = AppStatus.ERROR
                    status_text = "crashed" if exit_status == QProcess.CrashExit else f"exited with code {exit_code}"
                    
                    # Get error output if available
                    error_output = ""
                    if app_id in self.processes:
                        process = self.processes[app_id]
                        error_data = process.readAllStandardError()
                        if error_data:
                            error_output = error_data.data().decode('utf-8', errors='replace').strip()
                    
                    app_info.last_error = error_output or f"Process {status_text}"
                    
                    self.logger.warning(f"Process {app_id} {status_text}")
                    if error_output:
                        self.logger.error(f"Error output from {app_id}: {error_output}")
                    
                    self.process_status_changed.emit(app_id, AppStatus.ERROR, {
                        "exit_code": exit_code,
                        "exit_status": exit_status,
                        "error": app_info.last_error
                    })
                else:
                    app_info.status = AppStatus.STOPPED
                    app_info.last_error = None
                    self.logger.info(f"Process {app_id} exited normally")
                    self.process_status_changed.emit(app_id, AppStatus.STOPPED, {
                        "exit_code": exit_code
                    })
                
                # Reset process info
                app_info.pid = None
                app_info.start_time = None
                
                # Clean up process reference
                if app_id in self.processes:
                    try:
                        self.processes[app_id].deleteLater()
                    except Exception:
                        pass
                    del self.processes[app_id]
                
        except Exception as e:
            self.logger.error(f"Error in process finished handler for {app_id}: {e}")
        finally:
            self.mutex.unlock()
    
    def _handle_stdout(self, app_id: str, process: QProcess):
        """Handle process standard output."""
        try:
            data = process.readAllStandardOutput()
            if data:
                output = data.data().decode('utf-8', errors='replace').strip()
                if output:
                    self.logger.debug(f"[{app_id}][stdout] {output}")
        except Exception as e:
            self.logger.warning(f"Error reading stdout from {app_id}: {e}")
    
    def _handle_stderr(self, app_id: str, process: QProcess):
        """Handle process standard error."""
        try:
            data = process.readAllStandardError()
            if data:
                output = data.data().decode('utf-8', errors='replace').strip()
                if output:
                    self.logger.warning(f"[{app_id}][stderr] {output}")
        except Exception as e:
            self.logger.warning(f"Error reading stderr from {app_id}: {e}")
    
    def _on_process_error(self, app_id: str, error):
        """Handle process error signal."""
        self.mutex.lock()
        try:
            if app_id in self.monitored_apps:
                app_info = self.monitored_apps[app_id]
                app_info.status = AppStatus.ERROR
                
                # Get error message
                error_messages = {
                    QProcess.FailedToStart: "Failed to start",
                    QProcess.Crashed: "Process crashed",
                    QProcess.Timedout: "Process timed out",
                    QProcess.WriteError: "Write error",
                    QProcess.ReadError: "Read error",
                    QProcess.UnknownError: "Unknown error"
                }
                
                error_msg = error_messages.get(error, f"Process error: {error}")
                app_info.last_error = error_msg
                
                self.logger.error(f"Process error for {app_id}: {error_msg}")
                self.process_status_changed.emit(app_id, AppStatus.ERROR, {"error": error_msg})
        except Exception as e:
            self.logger.error(f"Error in error handler for {app_id}: {e}")
        finally:
            self.mutex.unlock()
    
    def run(self):
        """Main monitoring thread loop."""
        while self._running:
            try:
                self._update_resource_stats()
                self.msleep(2000)  # Update every 2 seconds
            except Exception as e:
                self.logger.error(f"Error in process monitor: {e}")
                self.msleep(5000)
    
    def _update_resource_stats(self):
        """Update resource statistics for all monitored applications."""
        self.mutex.lock()
        try:
            for app_id, app_info in self.monitored_apps.items():
                if app_info.status == AppStatus.RUNNING and app_info.pid:
                    try:
                        process = psutil.Process(app_info.pid)
                        
                        # Get resource usage
                        memory_info = process.memory_info()
                        memory_mb = memory_info.rss / (1024 * 1024)
                        cpu_percent = process.cpu_percent()
                        
                        # Update app info
                        app_info.memory_usage = memory_mb
                        app_info.cpu_usage = cpu_percent
                        
                        # Emit stats
                        stats = {
                            'memory_mb': memory_mb,
                            'cpu_percent': cpu_percent,
                            'threads': process.num_threads(),
                            'status': process.status(),
                            'create_time': process.create_time()
                        }
                        
                        self.resource_stats_updated.emit(app_id, stats)
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process no longer exists
                        app_info.status = AppStatus.STOPPED
                        app_info.pid = None
                        app_info.start_time = None
                        self.process_status_changed.emit(app_id, AppStatus.STOPPED, {})
                    except Exception as e:
                        self.logger.warning(f"Error getting stats for {app_id}: {e}")
        finally:
            self.mutex.unlock()
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self._running = False
        
        # Stop all running processes
        self.mutex.lock()
        try:
            for app_id in list(self.processes.keys()):
                self.stop_application(app_id, force=True)
        finally:
            self.mutex.unlock()
        
        self.quit()
        self.wait()


class ModernAppCard(QFrame):
    """Modern application card with advanced controls and status display."""
    
    start_requested = Signal(str)
    stop_requested = Signal(str)
    restart_requested = Signal(str)
    configure_requested = Signal(str)
    view_logs_requested = Signal(str)
    
    def __init__(self, app_info: ApplicationInfo, parent=None):
        super().__init__(parent)
        
        self.app_info = app_info
        self.status_animation = None
        
        self._setup_ui()
        self._setup_style()
        self._setup_animations()
        self._update_display()
    
    def _setup_ui(self):
        """Setup the card UI components."""
        self.setFixedHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header with app name and status
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # App icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #00A8FF;
                border-radius: 16px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setText(self.app_info.name[0].upper() if self.app_info.name else "?")
        header_layout.addWidget(self.icon_label)
        
        # App details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)
        
        self.name_label = QLabel(self.app_info.name)
        self.name_label.setObjectName("appName")
        details_layout.addWidget(self.name_label)
        
        self.description_label = QLabel(self.app_info.description)
        self.description_label.setObjectName("appDescription")
        self.description_label.setWordWrap(True)
        details_layout.addWidget(self.description_label)
        
        header_layout.addLayout(details_layout)
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFixedSize(80, 24)
        self.status_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Error message (if any)
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setMaximumHeight(30)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Metrics row (when running)
        self.metrics_widget = QWidget()
        metrics_layout = QHBoxLayout(self.metrics_widget)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(16)
        
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setObjectName("metricLabel")
        metrics_layout.addWidget(self.cpu_label)
        
        self.memory_label = QLabel("RAM: 0 MB")
        self.memory_label.setObjectName("metricLabel")
        metrics_layout.addWidget(self.memory_label)
        
        self.uptime_label = QLabel("Uptime: --")
        self.uptime_label.setObjectName("metricLabel")
        metrics_layout.addWidget(self.uptime_label)
        
        metrics_layout.addStretch()
        layout.addWidget(self.metrics_widget)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        
        self.start_stop_btn = QPushButton()
        self.start_stop_btn.setFixedSize(80, 28)
        self.start_stop_btn.clicked.connect(self._on_start_stop_clicked)
        actions_layout.addWidget(self.start_stop_btn)
        
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.setFixedSize(70, 28)
        self.restart_btn.clicked.connect(lambda: self.restart_requested.emit(self.app_info.id))
        actions_layout.addWidget(self.restart_btn)
        
        self.logs_btn = QPushButton("Logs")
        self.logs_btn.setFixedSize(60, 28)
        self.logs_btn.clicked.connect(lambda: self.view_logs_requested.emit(self.app_info.id))
        actions_layout.addWidget(self.logs_btn)
        
        # Menu button
        self.menu_btn = QPushButton("⋯")
        self.menu_btn.setFixedSize(28, 28)
        self.menu_btn.clicked.connect(self._show_context_menu)
        actions_layout.addWidget(self.menu_btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
    
    def _setup_style(self):
        """Setup card styling."""
        self.setObjectName("appCard")
        self.setStyleSheet("""
            QFrame#appCard {
                background-color: #2A2F42;
                border: 1px solid #37414F;
                border-radius: 12px;
                margin: 2px;
            }
            
            QFrame#appCard:hover {
                border-color: #00A8FF;
                background-color: #2F3447;
            }
            
            QLabel#appName {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
            }
            
            QLabel#appDescription {
                color: #B0BEC5;
                font-size: 11px;
                line-height: 1.2;
            }
            
            QLabel#statusLabel {
                border-radius: 12px;
                font-size: 10px;
                font-weight: 500;
                padding: 0 8px;
            }
            
            QLabel#errorLabel {
                color: #F44336;
                font-size: 10px;
                font-style: italic;
            }
            
            QLabel#metricLabel {
                color: #78909C;
                font-size: 10px;
            }
            
            QPushButton {
                background-color: #353A4F;
                color: #FFFFFF;
                border: 1px solid #37414F;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #3E4358;
                border-color: #00A8FF;
            }
            
            QPushButton:pressed {
                background-color: #2C3441;
            }
        """)
    
    def _setup_animations(self):
        """Setup status change animations."""
        self.status_animation = QPropertyAnimation(self.status_label, b"geometry")
        self.status_animation.setDuration(300)
        self.status_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _update_display(self):
        """Update the card display based on current app info."""
        # Update status label
        status_colors = {
            AppStatus.RUNNING: ("#4CAF50", "#FFFFFF"),
            AppStatus.STOPPED: ("#78909C", "#FFFFFF"),
            AppStatus.STARTING: ("#FF9800", "#FFFFFF"),
            AppStatus.STOPPING: ("#FF9800", "#FFFFFF"),
            AppStatus.ERROR: ("#F44336", "#FFFFFF"),
            AppStatus.NOT_INSTALLED: ("#9E9E9E", "#FFFFFF"),
            AppStatus.UNKNOWN: ("#9E9E9E", "#FFFFFF"),
        }
        
        bg_color, text_color = status_colors.get(self.app_info.status, ("#9E9E9E", "#FFFFFF"))
        
        self.status_label.setText(self.app_info.status.value.replace('_', ' ').title())
        self.status_label.setStyleSheet(f"""
            QLabel#statusLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 12px;
                font-size: 10px;
                font-weight: 500;
                padding: 0 8px;
            }}
        """)
        
        # Show/hide error message
        if self.app_info.last_error:
            self.error_label.setText(f"Error: {self.app_info.last_error}")
            self.error_label.show()
        else:
            self.error_label.hide()
        
        # Update metrics visibility
        if self.app_info.status == AppStatus.RUNNING:
            self.metrics_widget.show()
            self.cpu_label.setText(f"CPU: {self.app_info.cpu_usage:.1f}%")
            self.memory_label.setText(f"RAM: {self.app_info.memory_usage:.0f} MB")
            
            if self.app_info.start_time:
                uptime = datetime.now() - self.app_info.start_time
                hours, remainder = divmod(uptime.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                self.uptime_label.setText(f"Up: {int(hours)}h {int(minutes)}m")
            else:
                self.uptime_label.setText("Up: --")
        else:
            self.metrics_widget.hide()
        
        # Update buttons
        if self.app_info.status in [AppStatus.STOPPED, AppStatus.ERROR, AppStatus.NOT_INSTALLED]:
            self.start_stop_btn.setText("Start")
            self.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 10px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #45A049;
                }
                QPushButton:disabled {
                    background-color: #2E7D32;
                    opacity: 0.6;
                }
            """)
            self.restart_btn.setEnabled(False)
            
            # Disable start button for invalid applications
            if self.app_info.status == AppStatus.NOT_INSTALLED:
                self.start_stop_btn.setEnabled(False)
            else:
                self.start_stop_btn.setEnabled(True)
                
        elif self.app_info.status == AppStatus.RUNNING:
            self.start_stop_btn.setText("Stop")
            self.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 10px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #E53935;
                }
            """)
            self.restart_btn.setEnabled(True)
            self.start_stop_btn.setEnabled(True)
        else:
            self.start_stop_btn.setText("...")
            self.start_stop_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)
    
    def _on_start_stop_clicked(self):
        """Handle start/stop button click."""
        if self.app_info.status in [AppStatus.STOPPED, AppStatus.ERROR]:
            self.start_requested.emit(self.app_info.id)
        elif self.app_info.status == AppStatus.RUNNING:
            self.stop_requested.emit(self.app_info.id)
    
    def _show_context_menu(self):
        """Show context menu with additional options."""
        menu = QMenu(self)
        
        # Configure action
        configure_action = QAction("Configure", self)
        configure_action.triggered.connect(lambda: self.configure_requested.emit(self.app_info.id))
        menu.addAction(configure_action)
        
        menu.addSeparator()
        
        # Auto-restart toggle
        auto_restart_action = QAction("Auto-restart", self)
        auto_restart_action.setCheckable(True)
        auto_restart_action.setChecked(self.app_info.auto_restart)
        auto_restart_action.triggered.connect(self._toggle_auto_restart)
        menu.addAction(auto_restart_action)
        
        # Show executable path
        path_action = QAction("Show executable path", self)
        path_action.triggered.connect(self._show_executable_path)
        menu.addAction(path_action)
        
        menu.addSeparator()
        
        # Force stop (if running)
        if self.app_info.status == AppStatus.RUNNING:
            force_stop_action = QAction("Force Stop", self)
            force_stop_action.triggered.connect(
                lambda: self.stop_requested.emit(self.app_info.id + "|force")
            )
            menu.addAction(force_stop_action)
        
        # Show menu
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
    
    def _toggle_auto_restart(self):
        """Toggle auto-restart for the application."""
        self.app_info.auto_restart = not self.app_info.auto_restart
    
    def _show_executable_path(self):
        """Show the executable path in a message box."""
        QMessageBox.information(
            self, 
            f"{self.app_info.name} - Executable Path",
            f"Executable: {self.app_info.executable_path}\n"
            f"Working Directory: {self.app_info.working_directory}\n"
            f"Validated: {'Yes' if self.app_info.validated else 'No'}"
        )
    
    def update_app_info(self, app_info: ApplicationInfo):
        """Update the app info and refresh display."""
        self.app_info = app_info
        self._update_display()
    
    def update_resource_stats(self, stats: Dict[str, Any]):
        """Update resource statistics."""
        if 'memory_mb' in stats:
            self.app_info.memory_usage = stats['memory_mb']
        if 'cpu_percent' in stats:
            self.app_info.cpu_usage = stats['cpu_percent']
        
        self._update_display()


class ApplicationManagerTab(QWidget):
    """
    Modern Application Manager Tab with comprehensive app management features.
    
    Features:
    - Visual app cards with real-time status
    - Advanced process monitoring
    - Bulk operations
    - Resource usage tracking
    - Log viewing
    - Auto-restart capabilities
    - Application validation
    """
    
    # Signals
    app_status_changed = Signal(str, str)
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.applications: Dict[str, ApplicationInfo] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Process monitoring
        self.process_monitor = ProcessMonitor()
        self.process_monitor.process_status_changed.connect(self._on_process_status_changed)
        self.process_monitor.resource_stats_updated.connect(self._on_resource_stats_updated)
        
        # UI components
        self.app_cards: Dict[str, ModernAppCard] = {}
        self.filter_combo: Optional[QComboBox] = None
        self.search_edit: Optional[QLineEdit] = None
        
        self._setup_ui()
        self._load_applications()
        self._setup_connections()
        
        # Start monitoring
        self.process_monitor.start()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Header section
        header_section = self._create_header_section()
        main_layout.addWidget(header_section)
        
        # Filter and search section
        filter_section = self._create_filter_section()
        main_layout.addWidget(filter_section)
        
        # Applications grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.apps_container = QWidget()
        self.apps_layout = QGridLayout(self.apps_container)
        self.apps_layout.setSpacing(16)
        self.apps_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.apps_container)
        main_layout.addWidget(self.scroll_area)
    
    def _create_header_section(self) -> QWidget:
        """Create the header section with title and stats."""
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
        
        # Title and description
        title_layout = QHBoxLayout()
        
        title = QLabel("Application Manager")
        title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 24px;
            font-weight: bold;
        """)
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        # Bulk action buttons
        self.start_all_btn = QPushButton("Start All")
        self.start_all_btn.setFixedHeight(36)
        self.start_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        self.start_all_btn.clicked.connect(self._start_all_applications)
        title_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QPushButton("Stop All")
        self.stop_all_btn.setFixedHeight(36)
        self.stop_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        self.stop_all_btn.clicked.connect(self._stop_all_applications)
        title_layout.addWidget(self.stop_all_btn)
        
        layout.addLayout(title_layout)
        
        # Description
        description = QLabel("Manage and monitor CommandCore applications")
        description.setStyleSheet("""
            color: #B0BEC5;
            font-size: 14px;
        """)
        layout.addWidget(description)
        
        # Stats row
        stats_layout = QHBoxLayout()
        
        self.total_apps_label = QLabel("Total: 0")
        self.total_apps_label.setStyleSheet("color: #78909C; font-size: 12px;")
        stats_layout.addWidget(self.total_apps_label)
        
        self.running_apps_label = QLabel("Running: 0")
        self.running_apps_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        stats_layout.addWidget(self.running_apps_label)
        
        self.stopped_apps_label = QLabel("Stopped: 0")
        self.stopped_apps_label.setStyleSheet("color: #F44336; font-size: 12px;")
        stats_layout.addWidget(self.stopped_apps_label)
        
        self.error_apps_label = QLabel("Errors: 0")
        self.error_apps_label.setStyleSheet("color: #FF9800; font-size: 12px;")
        stats_layout.addWidget(self.error_apps_label)
        
        stats_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(28)
        refresh_btn.clicked.connect(self._refresh_applications)
        stats_layout.addWidget(refresh_btn)
        
        layout.addLayout(stats_layout)
        
        return header
    
    def _create_filter_section(self) -> QWidget:
        """Create the filter and search section."""
        filter_section = QWidget()
        layout = QHBoxLayout(filter_section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Category filter
        filter_label = QLabel("Category:")
        filter_label.setStyleSheet("color: #B0BEC5; font-weight: 500;")
        layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "System", "Development", "Network", "Security", "Utilities"])
        self.filter_combo.currentTextChanged.connect(self._filter_applications)
        layout.addWidget(self.filter_combo)
        
        layout.addStretch()
        
        # Search
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #B0BEC5; font-weight: 500;")
        layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search applications...")
        self.search_edit.setFixedWidth(200)
        self.search_edit.textChanged.connect(self._filter_applications)
        layout.addWidget(self.search_edit)
        
        return filter_section
    
    def _load_applications(self):
        """Load application configurations with improved path detection."""
        # Try to find CommandCore base directory
        base_dirs = [
            Path.home() / "Outback CommandCore",
            Path("/home/outbackelectronics/Outback CommandCore"),
            Path(__file__).parent.parent,
            Path.cwd() / "CommandCore",
        ]
        
        base_dir = None
        for dir_path in base_dirs:
            if dir_path.exists() and dir_path.is_dir():
                base_dir = dir_path
                break
        
        if not base_dir:
            self.logger.warning("CommandCore base directory not found, using current directory")
            base_dir = Path.cwd()
        
        self.logger.info(f"Using CommandCore base directory: {base_dir}")
        
        # Define application configurations with relative paths
        app_configs = [
            {
                "id": "ares_i",
                "name": "ARES-I",
                "description": "AI-powered research and analysis tool for advanced data processing.",
                "path": "ARES-i/main.py", 
                "category": "Development",
            },
            {
                "id": "blackstorm_launcher",
                "name": "Blackstorm Launcher",
                "description": "Comprehensive launcher for the Blackstorm application suite.",
                "path": "BLACKSTORM/blackstorm_launcher.py",
                "category": "System",
            },
            {
                "id": "codex",
                "name": "Codex",
                "description": "AI-powered code generation and analysis platform.",
                "path": "Codex/codex.py", 
                "category": "Development",
            },
            {
                "id": "droidcom",
                "name": "DROIDCOM",
                "description": "Advanced Android device management and debugging toolkit.",
                "path": "DROIDCOM/main.py", 
                "category": "Development",
            },
            {
                "id": "hackattack",
                "name": "HackAttack",
                "description": "Comprehensive penetration testing and security assessment framework.",
                "path": "HackAttack/launch.py", 
                "category": "Security",
            },
            {
                "id": "nightfire",
                "name": "Nightfire",
                "description": "Real-time system monitoring and performance optimization tool.",
                "path": "NIGHTFIRE/nightfire.py", 
                "category": "System",
            },
            {
                "id": "omniscribe",
                "name": "Omniscribe",
                "description": "Advanced transcription and natural language processing engine.",
                "path": "OMNISCRIBE/omniscribe.py", 
                "category": "Utilities",
            },
            {
                "id": "pc_tools_linux",
                "name": "PC Tools Linux",
                "description": "Comprehensive Linux system management and optimization utilities.",
                "path": "PC-X/pc_tools_linux.py",
                "category": "System",
            },
            {
                "id": "vantage",
                "name": "VANTAGE",
                "description": "Advanced system monitoring with real-time analytics and reporting.",
                "path": "VANTAGE/launch_vantage.py",
                "category": "System",
            }
        ]
        
        # Create ApplicationInfo objects
        for config in app_configs:
            try:
                exec_path = base_dir / config["path"]
                working_dir = exec_path.parent
                
                app_info = ApplicationInfo(
                    id=config["id"],
                    name=config["name"],
                    description=config["description"],
                    executable_path=str(exec_path),
                    working_directory=str(working_dir),
                    category=config.get("category", "General"),
                    status=AppStatus.STOPPED,
                    environment_vars={
                        "PYTHONPATH": str(base_dir)
                    }
                )
                
                self.applications[app_info.id] = app_info
                self.process_monitor.add_application(app_info)
                
                self.logger.debug(f"Added application: {app_info.name} at {exec_path}")
                
            except Exception as e:
                self.logger.error(f"Error adding application {config['name']}: {e}")
        
        self._update_app_display()
        self._update_stats()
    
    def _setup_connections(self):
        """Setup signal connections."""
        pass  # Connections are set up in _create_app_card
    
    def _update_app_display(self):
        """Update the application cards display."""
        # Clear existing cards
        for card in self.app_cards.values():
            card.setParent(None)
        self.app_cards.clear()
        
        # Filter applications
        filtered_apps = self._get_filtered_applications()
        
        # Create cards
        row = 0
        col = 0
        cols_per_row = 2
        
        for app_info in filtered_apps:
            card = self._create_app_card(app_info)
            self.app_cards[app_info.id] = card
            
            self.apps_layout.addWidget(card, row, col)
            
            col += 1
            if col >= cols_per_row:
                col = 0
                row += 1
        
        # Add stretch to fill remaining space
        self.apps_layout.setRowStretch(row + 1, 1)
    
    def _create_app_card(self, app_info: ApplicationInfo) -> ModernAppCard:
        """Create a modern app card for the application."""
        card = ModernAppCard(app_info)
        
        # Connect signals
        card.start_requested.connect(self._start_application)
        card.stop_requested.connect(self._stop_application)
        card.restart_requested.connect(self._restart_application)
        card.configure_requested.connect(self._configure_application)
        card.view_logs_requested.connect(self._view_application_logs)
        
        return card
    
    def _get_filtered_applications(self) -> List[ApplicationInfo]:
        """Get applications filtered by current filter and search criteria."""
        filtered = list(self.applications.values())
        
        # Filter by category
        if self.filter_combo and self.filter_combo.currentText() != "All":
            category = self.filter_combo.currentText()
            filtered = [app for app in filtered if app.category == category]
        
        # Filter by search text
        if self.search_edit and self.search_edit.text():
            search_text = self.search_edit.text().lower()
            filtered = [
                app for app in filtered 
                if search_text in app.name.lower() or search_text in app.description.lower()
            ]
        
        # Sort by name
        filtered.sort(key=lambda app: app.name)
        
        return filtered
    
    def _filter_applications(self):
        """Apply current filters and update display."""
        self._update_app_display()
    
    def _update_stats(self):
        """Update the statistics labels."""
        total = len(self.applications)
        running = len([app for app in self.applications.values() if app.status == AppStatus.RUNNING])
        stopped = len([app for app in self.applications.values() if app.status == AppStatus.STOPPED])
        errors = len([app for app in self.applications.values() if app.status == AppStatus.ERROR])
        
        self.total_apps_label.setText(f"Total: {total}")
        self.running_apps_label.setText(f"Running: {running}")
        self.stopped_apps_label.setText(f"Stopped: {stopped}")
        self.error_apps_label.setText(f"Errors: {errors}")
    
    def _start_application(self, app_id: str):
        """Start an application."""
        if app_id in self.applications:
            success = self.process_monitor.start_application(app_id)
            if not success:
                app_info = self.applications[app_id]
                error_msg = app_info.last_error or "Unknown error"
                QMessageBox.warning(
                    self, 
                    "Start Failed", 
                    f"Failed to start {app_info.name}:\n{error_msg}"
                )
    
    def _stop_application(self, app_id_with_flags: str):
        """Stop an application."""
        # Handle force stop flag
        force = False
        if "|force" in app_id_with_flags:
            app_id = app_id_with_flags.replace("|force", "")
            force = True
        else:
            app_id = app_id_with_flags
        
        if app_id in self.applications:
            success = self.process_monitor.stop_application(app_id, force=force)
            if not success:
                QMessageBox.warning(
                    self, 
                    "Stop Failed", 
                    f"Failed to stop {self.applications[app_id].name}"
                )
    
    def _restart_application(self, app_id: str):
        """Restart an application."""
        if app_id in self.applications:
            # First stop, then start after a delay
            if self.process_monitor.stop_application(app_id):
                QTimer.singleShot(2000, lambda: self.process_monitor.start_application(app_id))
            else:
                QMessageBox.warning(
                    self, 
                    "Restart Failed", 
                    f"Failed to stop {self.applications[app_id].name} for restart"
                )
    
    def _configure_application(self, app_id: str):
        """Open application configuration dialog."""
        if app_id in self.applications:
            app_info = self.applications[app_id]
            QMessageBox.information(
                self, 
                f"Configuration - {app_info.name}", 
                f"Configuration for {app_info.name} is not yet implemented.\n\n"
                f"Executable: {app_info.executable_path}\n"
                f"Working Directory: {app_info.working_directory}\n"
                f"Status: {app_info.status.value}\n"
                f"Validated: {'Yes' if app_info.validated else 'No'}"
            )
    
    def _view_application_logs(self, app_id: str):
        """View application logs."""
        if app_id in self.applications:
            app_info = self.applications[app_id]
            QMessageBox.information(
                self, 
                f"Logs - {app_info.name}", 
                f"Log viewer for {app_info.name} is not yet implemented.\n\n"
                f"You can check the console output or system logs for debugging information."
            )
    
    def _start_all_applications(self):
        """Start all valid applications."""
        started_count = 0
        for app_id, app_info in self.applications.items():
            if app_info.status in [AppStatus.STOPPED, AppStatus.ERROR] and app_info.validated:
                if self.process_monitor.start_application(app_id):
                    started_count += 1
        
        if started_count > 0:
            QMessageBox.information(
                self,
                "Start All",
                f"Started {started_count} applications successfully."
            )
    
    def _stop_all_applications(self):
        """Stop all running applications."""
        stopped_count = 0
        for app_id, app_info in self.applications.items():
            if app_info.status == AppStatus.RUNNING:
                if self.process_monitor.stop_application(app_id):
                    stopped_count += 1
        
        if stopped_count > 0:
            QMessageBox.information(
                self,
                "Stop All",
                f"Stopped {stopped_count} applications successfully."
            )
    
    def _refresh_applications(self):
        """Refresh application status and reload configurations."""
        self._load_applications()
    
    def _on_process_status_changed(self, app_id: str, status: AppStatus, details: Dict):
        """Handle process status change signals."""
        if app_id in self.applications:
            self.applications[app_id].status = status
            
            # Update additional details
            if 'pid' in details:
                self.applications[app_id].pid = details['pid']
            if 'start_time' in details:
                self.applications[app_id].start_time = details['start_time']
            if 'error' in details:
                self.applications[app_id].last_error = details['error']
            
            # Update card display
            if app_id in self.app_cards:
                self.app_cards[app_id].update_app_info(self.applications[app_id])
            
            # Update stats
            self._update_stats()
            
            # Emit status change signal
            self.app_status_changed.emit(app_id, status.value)
    
    def _on_resource_stats_updated(self, app_id: str, stats: Dict):
        """Handle resource statistics updates."""
        if app_id in self.app_cards:
            self.app_cards[app_id].update_resource_stats(stats)
    
    def get_installed_apps(self) -> List[Dict[str, Any]]:
        """Get list of installed applications for external use."""
        return [
            {
                'id': app.id,
                'name': app.name,
                'status': app.status.value,
                'description': app.description,
                'validated': app.validated
            }
            for app in self.applications.values()
        ]
    
    def launch_application(self, app_id: str):
        """Launch an application by ID (external interface)."""
        self._start_application(app_id)
    
    def cleanup(self):
        """Cleanup resources when tab is destroyed."""
        if self.process_monitor.isRunning():
            self.process_monitor.stop_monitoring()
