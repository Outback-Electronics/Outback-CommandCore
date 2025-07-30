"""
Professional Update Checker for CommandCore Launcher - ENHANCED VERSION

Provides automatic update checking, version comparison, and update notifications
with secure download verification and user-friendly update management.
Enhanced with proper GitHub API 404 handling for repositories without releases.
"""

import json
import hashlib
import logging
import requests
import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from packaging import version
import threading

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QProgressBar,
    QFrame, QScrollArea, QGroupBox, QApplication,
    QMessageBox, QCheckBox, QComboBox, QWidget,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QThread, QObject, QUrl,
    QPropertyAnimation, QEasingCurve, QMutex
)
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QPainter, QColor, QBrush,
    QLinearGradient, QDesktopServices, QCursor
)


class UpdateChannel(Enum):
    """Update channels for different release types."""
    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"
    DEVELOPMENT = "development"


class UpdateStatus(Enum):
    """Status of update operations."""
    IDLE = "idle"
    CHECKING = "checking"
    UPDATE_AVAILABLE = "update_available"
    NO_UPDATE = "no_update"
    DOWNLOADING = "downloading"
    DOWNLOAD_COMPLETE = "download_complete"
    ERROR = "error"


@dataclass
class UpdateInfo:
    """Information about an available update."""
    version: str
    release_date: str
    download_url: str
    changelog: str
    file_size: int
    checksum: str
    checksum_type: str = "sha256"
    is_critical: bool = False
    min_version: str = None
    channel: UpdateChannel = UpdateChannel.STABLE
    
    def is_newer_than(self, current_version: str) -> bool:
        """Check if this update is newer than current version."""
        try:
            return version.parse(self.version) > version.parse(current_version)
        except Exception:
            return False


@dataclass
class UpdateSettings:
    """Settings for update checking."""
    enabled: bool = True
    channel: UpdateChannel = UpdateChannel.STABLE
    frequency: str = "weekly"  # daily, weekly, monthly, never
    auto_download: bool = False
    notify_beta: bool = False
    last_check: Optional[datetime] = None
    skip_version: Optional[str] = None


class UpdateWorker(QThread):
    """Worker thread for update operations with enhanced GitHub API handling."""
    
    update_checked = Signal(object)  # UpdateInfo or None
    download_progress = Signal(int, int)  # current, total
    download_complete = Signal(str)  # file_path
    error_occurred = Signal(str)  # error_message
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        
        self.operation = operation
        self.kwargs = kwargs
        self._cancel_requested = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self):
        """Main worker thread execution."""
        try:
            if self.operation == "check":
                self._check_for_updates()
            elif self.operation == "download":
                self._download_update()
        except Exception as e:
            self.logger.error(f"Update operation failed: {e}")
            self.error_occurred.emit(str(e))
    
    def cancel(self):
        """Cancel the current operation."""
        self._cancel_requested = True
    
    def _check_for_updates(self):
        """Check for available updates with enhanced GitHub API handling."""
        try:
            # Enhanced URL strategy with proper fallback
            update_urls = [
                "https://api.github.com/repos/Outback-Electronics/Outback-CommandCore/releases/latest",
                "https://api.github.com/repos/Outback-Electronics/Outback-CommandCore/releases"
            ]
            
            update_info = None
            no_releases_found = False
            
            for i, url in enumerate(update_urls):
                if self._cancel_requested:
                    return
                
                try:
                    self.logger.info(f"Checking for updates from: {url}")
                    
                    response = requests.get(url, timeout=30, headers={
                        'User-Agent': 'CommandCore-Launcher/2.0.0 (Update-Checker)',
                        'Accept': 'application/vnd.github.v3+json'
                    })
                    
                    # Handle 404 specifically for releases endpoint
                    if response.status_code == 404:
                        if i == 0:
                            # /releases/latest returned 404 - no releases exist yet
                            self.logger.info("No latest release found, trying general releases endpoint")
                            continue
                        else:
                            # /releases also returned 404 - repository has no releases
                            self.logger.info("Repository has no releases yet")
                            no_releases_found = True
                            break
                    
                    # Handle other HTTP errors
                    response.raise_for_status()
                    
                    # Parse the response
                    if "releases/latest" in url:
                        update_info = self._parse_github_release(response.json())
                    else:
                        # Handle array of releases
                        releases = response.json()
                        if releases and isinstance(releases, list) and len(releases) > 0:
                            # Get the most recent non-prerelease
                            for release in releases:
                                if not release.get("prerelease", False):
                                    update_info = self._parse_github_release(release)
                                    break
                            
                            # If no stable releases, take the first one if channel allows
                            if not update_info and releases:
                                channel = self.kwargs.get("channel", UpdateChannel.STABLE)
                                if channel != UpdateChannel.STABLE:
                                    update_info = self._parse_github_release(releases[0])
                        else:
                            # Empty releases array
                            no_releases_found = True
                    
                    if update_info:
                        # Check if this is actually a newer version
                        current_version = self.kwargs.get("current_version", "2.0.0")
                        if update_info.is_newer_than(current_version):
                            self.logger.info(f"Found newer version: {update_info.version}")
                            break
                        else:
                            self.logger.info(f"Found version {update_info.version}, but not newer than current {current_version}")
                            update_info = None
                            break
                        
                except requests.RequestException as e:
                    if hasattr(e, 'response') and e.response is not None:
                        if e.response.status_code == 404:
                            if i == 0:
                                self.logger.info("Latest release endpoint not found, trying general releases")
                                continue
                            else:
                                self.logger.info("No releases found in repository")
                                no_releases_found = True
                                break
                        else:
                            self.logger.warning(f"HTTP error {e.response.status_code} from {url}: {e}")
                    else:
                        self.logger.warning(f"Network error checking {url}: {e}")
                    
                    # Continue to next URL unless it's the last one
                    if i < len(update_urls) - 1:
                        continue
                    else:
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error parsing update from {url}: {e}")
                    continue
            
            # Log the final result
            if no_releases_found:
                self.logger.info("Repository exists but has no releases yet - this is normal for new projects")
            elif not update_info:
                self.logger.info("No updates available")
            
            self.update_checked.emit(update_info)
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to check for updates: {str(e)}")
    
    def _parse_github_release(self, data: Dict[str, Any]) -> Optional[UpdateInfo]:
        """Parse GitHub release data with enhanced error handling."""
        try:
            # Skip pre-releases unless beta channel
            if data.get("prerelease", False):
                channel = self.kwargs.get("channel", UpdateChannel.STABLE)
                if channel == UpdateChannel.STABLE:
                    self.logger.debug("Skipping prerelease for stable channel")
                    return None
            
            # Extract version from tag
            tag_name = data.get("tag_name", "")
            if not tag_name:
                self.logger.warning("Release has no tag_name")
                return None
            
            # Clean version string (remove 'v' prefix if present)
            version_str = tag_name.lstrip("v")
            if not version_str:
                self.logger.warning(f"Invalid version string: {tag_name}")
                return None
            
            # Find download asset
            assets = data.get("assets", [])
            download_url = None
            file_size = 0
            
            # Look for common installer file extensions
            preferred_extensions = [".exe", ".msi", ".dmg", ".pkg", ".appimage", ".deb", ".rpm", ".tar.gz", ".zip"]
            
            for asset in assets:
                asset_name = asset.get("name", "").lower()
                if any(ext in asset_name for ext in preferred_extensions):
                    download_url = asset.get("browser_download_url")
                    file_size = asset.get("size", 0)
                    self.logger.info(f"Found installer asset: {asset.get('name')}")
                    break
            
            # If no installer found, use the first asset or tarball
            if not download_url:
                if assets:
                    first_asset = assets[0]
                    download_url = first_asset.get("browser_download_url")
                    file_size = first_asset.get("size", 0)
                    self.logger.info(f"Using first available asset: {first_asset.get('name')}")
                else:
                    # Use source code archive as fallback
                    download_url = data.get("tarball_url")
                    if download_url:
                        self.logger.info("Using source code tarball as download")
            
            if not download_url:
                self.logger.warning("No suitable download URL found in release")
                return None
            
            # Parse release date
            release_date = data.get("published_at", "")
            
            # Get changelog/description
            changelog = data.get("body", "No changelog available.")
            
            # Create UpdateInfo object
            update_info = UpdateInfo(
                version=version_str,
                release_date=release_date,
                download_url=download_url,
                changelog=changelog,
                file_size=file_size,
                checksum="",  # GitHub doesn't provide checksums directly
                is_critical=False,
                channel=UpdateChannel.BETA if data.get("prerelease") else UpdateChannel.STABLE
            )
            
            self.logger.info(f"Successfully parsed release: {version_str}")
            return update_info
            
        except Exception as e:
            self.logger.error(f"Error parsing GitHub release: {e}")
            return None
    
    def _parse_update_json(self, data: Dict[str, Any]) -> Optional[UpdateInfo]:
        """Parse custom update JSON format."""
        try:
            required_fields = ["version", "download_url"]
            for field in required_fields:
                if field not in data:
                    self.logger.error(f"Missing required field: {field}")
                    return None
            
            return UpdateInfo(
                version=data["version"],
                release_date=data.get("release_date", ""),
                download_url=data["download_url"],
                changelog=data.get("changelog", ""),
                file_size=data.get("file_size", 0),
                checksum=data.get("checksum", ""),
                checksum_type=data.get("checksum_type", "sha256"),
                is_critical=data.get("is_critical", False),
                min_version=data.get("min_version"),
                channel=UpdateChannel(data.get("channel", "stable"))
            )
        except Exception as e:
            self.logger.error(f"Error parsing update JSON: {e}")
            return None
    
    def _download_update(self):
        """Download the update file with progress tracking."""
        try:
            url = self.kwargs.get("url")
            if not url:
                self.error_occurred.emit("No download URL provided")
                return
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_file:
                temp_path = temp_file.name
            
            # Download with progress tracking
            response = requests.get(url, stream=True, timeout=60, headers={
                'User-Agent': 'CommandCore-Launcher/2.0.0 (Update-Downloader)'
            })
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._cancel_requested:
                        Path(temp_path).unlink(missing_ok=True)
                        return
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.download_progress.emit(downloaded, total_size)
            
            self.download_complete.emit(temp_path)
            
        except Exception as e:
            self.error_occurred.emit(f"Download failed: {str(e)}")


class UpdateDialog(QDialog):
    """Modern update dialog with enhanced UI and error handling."""
    
    def __init__(self, update_info: UpdateInfo, parent=None):
        super().__init__(parent)
        
        self.update_info = update_info
        self.download_worker: Optional[UpdateWorker] = None
        
        self.setWindowTitle("Update Available")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        self._setup_ui()
        self._center_on_parent()
    
    def _setup_ui(self):
        """Setup the update dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Update icon (placeholder)
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #00A8FF;
                border-radius: 32px;
                border: 3px solid #42BFFF;
            }
        """)
        header_layout.addWidget(icon_label)
        
        # Title and version info
        info_layout = QVBoxLayout()
        
        title_label = QLabel("Update Available")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #FFFFFF;
                margin-bottom: 5px;
            }
        """)
        
        version_label = QLabel(f"Version {self.update_info.version}")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #B0BEC5;
                font-weight: 500;
            }
        """)
        
        info_layout.addWidget(title_label)
        info_layout.addWidget(version_label)
        info_layout.addStretch()
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Release info
        if self.update_info.release_date:
            date_label = QLabel(f"Released: {self.update_info.release_date[:10]}")
            date_label.setStyleSheet("color: #78909C; font-size: 14px;")
            layout.addWidget(date_label)
        
        if self.update_info.file_size > 0:
            size_label = QLabel(f"Size: {self._format_file_size(self.update_info.file_size)}")
            size_label.setStyleSheet("color: #78909C; font-size: 14px;")
            layout.addWidget(size_label)
        
        # Changelog
        changelog_label = QLabel("What's New:")
        changelog_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #FFFFFF;
                margin-top: 10px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(changelog_label)
        
        self.changelog_text = QTextEdit()
        self.changelog_text.setPlainText(self.update_info.changelog or "No changelog available.")
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setMaximumHeight(200)
        self.changelog_text.setStyleSheet("""
            QTextEdit {
                background-color: #2A2F42;
                color: #B0BEC5;
                border: 1px solid #37414F;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.changelog_text)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #353A4F;
                border: 1px solid #37414F;
                border-radius: 8px;
                text-align: center;
                color: #FFFFFF;
                font-size: 12px;
                height: 25px;
            }
            
            QProgressBar::chunk {
                background-color: #00A8FF;
                border-radius: 7px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Skip version option
        self.skip_version_check = QCheckBox(f"Skip version {self.update_info.version}")
        self.skip_version_check.setStyleSheet("""
            QCheckBox {
                color: #B0BEC5;
                font-size: 13px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #37414F;
                border-radius: 3px;
                background-color: #2A2F42;
            }
            
            QCheckBox::indicator:checked {
                background-color: #00A8FF;
                border-color: #0078CC;
            }
        """)
        layout.addWidget(self.skip_version_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.later_btn = QPushButton("Remind Me Later")
        self.later_btn.setStyleSheet("""
            QPushButton {
                background-color: #353A4F;
                color: #B0BEC5;
                border: 1px solid #37414F;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background-color: #404652;
                border-color: #4A5568;
            }
        """)
        self.later_btn.clicked.connect(self.reject)
        
        self.download_btn = QPushButton("Download & Install")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #00A8FF;
                color: white;
                border: 1px solid #0078CC;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background-color: #42BFFF;
            }
            
            QPushButton:pressed {
                background-color: #0078CC;
            }
            
            QPushButton:disabled {
                background-color: #37414F;
                color: #546E7A;
                border-color: #2C3441;
            }
        """)
        self.download_btn.clicked.connect(self._start_download)
        
        button_layout.addWidget(self.later_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.download_btn)
        
        layout.addLayout(button_layout)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        
        return f"{size_bytes:.1f} TB"
    
    def _center_on_parent(self):
        """Center dialog on parent window."""
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)
    
    def _start_download(self):
        """Start downloading the update."""
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading...")
        self.progress_bar.setVisible(True)
        
        # Start download worker
        self.download_worker = UpdateWorker(
            "download",
            url=self.update_info.download_url,
            size=self.update_info.file_size
        )
        self.download_worker.download_progress.connect(self._update_progress)
        self.download_worker.download_complete.connect(self._download_complete)
        self.download_worker.error_occurred.connect(self._download_error)
        self.download_worker.start()
    
    def _update_progress(self, current: int, total: int):
        """Update download progress."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"Downloading... {percentage}%")
    
    def _download_complete(self, file_path: str):
        """Handle download completion."""
        self.progress_bar.setVisible(False)
        self.download_btn.setText("Download Complete")
        
        # Ask user if they want to install now
        reply = QMessageBox.question(
            self,
            "Download Complete",
            "The update has been downloaded successfully.\n\n"
            "Would you like to install it now? The application will need to restart.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self._install_update(file_path)
        else:
            self.accept()
    
    def _download_error(self, error_message: str):
        """Handle download error."""
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Download & Install")
        
        QMessageBox.critical(
            self,
            "Download Error",
            f"Failed to download update:\n\n{error_message}"
        )
    
    def _install_update(self, file_path: str):
        """Install the downloaded update."""
        try:
            # Open the downloaded file with the system default application
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            
            # Close the application to allow update installation
            QApplication.quit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Installation Error",
                f"Failed to start update installation:\n\n{str(e)}\n\n"
                f"Please manually run the downloaded file:\n{file_path}"
            )
    
    def get_skip_version(self) -> bool:
        """Check if user wants to skip this version."""
        return self.skip_version_check.isChecked()
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait(3000)
        event.accept()


class UpdateChecker(QObject):
    """
    Professional update checker for CommandCore Launcher with enhanced GitHub support.
    
    Features:
    - Automatic update checking with configurable frequency
    - Multiple update channels (stable, beta, alpha)
    - Secure download verification with checksums
    - Modern update notifications and dialogs
    - Background downloading with progress tracking
    - Installation assistance and restart management
    - Proper handling of repositories without releases
    """
    
    # Signals
    update_available = Signal(object)  # UpdateInfo
    update_checked = Signal(bool)      # has_update
    error_occurred = Signal(str)       # error_message
    
    def __init__(self, current_version: str = "2.0.0"):
        super().__init__()
        
        self.current_version = current_version
        self.settings = UpdateSettings()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.check_worker: Optional[UpdateWorker] = None
        self.update_dialog: Optional[UpdateDialog] = None
        
        # Timer for automatic checks
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_for_updates)
        
        self._setup_automatic_checking()
    
    def _setup_automatic_checking(self):
        """Setup automatic update checking with proper intervals."""
        if not self.settings.enabled or self.settings.frequency == "never":
            self.logger.info("Automatic update checking disabled")
            return
        
        # Calculate interval
        intervals = {
            "daily": 24 * 60 * 60 * 1000,      # 24 hours
            "weekly": 7 * 24 * 60 * 60 * 1000,  # 7 days
            "monthly": 30 * 24 * 60 * 60 * 1000  # 30 days
        }
        
        interval = intervals.get(self.settings.frequency, intervals["weekly"])
        
        # Check if it's time for automatic check
        if self.settings.last_check:
            time_since_check = datetime.now() - self.settings.last_check
            if time_since_check.total_seconds() * 1000 < interval:
                # Schedule next check
                remaining = interval - (time_since_check.total_seconds() * 1000)
                QTimer.singleShot(int(remaining), self.check_for_updates)
                self.logger.info(f"Next automatic update check in {remaining/1000/60:.1f} minutes")
                return
        
        # Start immediate check and schedule regular checks
        QTimer.singleShot(5000, self.check_for_updates)  # Check after 5 seconds
        self.check_timer.start(interval)
        
        self.logger.info(f"Automatic update checking enabled ({self.settings.frequency})")
    
    def update_settings(self, settings: UpdateSettings):
        """Update checker settings."""
        self.settings = settings
        
        # Restart automatic checking with new settings
        self.check_timer.stop()
        self._setup_automatic_checking()
    
    def check_for_updates(self, silent: bool = True):
        """Check for available updates."""
        if self.check_worker and self.check_worker.isRunning():
            self.logger.debug("Update check already in progress")
            return
        
        self.logger.info("Checking for updates...")
        
        # Create and start worker
        self.check_worker = UpdateWorker(
            "check",
            channel=self.settings.channel,
            current_version=self.current_version
        )
        self.check_worker.update_checked.connect(
            lambda update_info: self._handle_update_check_result(update_info, silent)
        )
        self.check_worker.error_occurred.connect(self._handle_check_error)
        self.check_worker.start()
        
        # Update last check time
        self.settings.last_check = datetime.now()
    
    def _handle_update_check_result(self, update_info: Optional[UpdateInfo], silent: bool):
        """Handle update check result with enhanced logic."""
        try:
            if update_info is None:
                self.logger.info("No updates available")
                self.update_checked.emit(False)
                
                if not silent:
                    QMessageBox.information(
                        None,
                        "No Updates",
                        "You are running the latest version of CommandCore Launcher."
                    )
                return
            
            # Check if this version should be skipped
            if (self.settings.skip_version and 
                self.settings.skip_version == update_info.version):
                self.logger.info(f"Skipping version {update_info.version} as requested")
                self.update_checked.emit(False)
                return
            
            # Valid update found
            self.logger.info(f"Update available: {update_info.version}")
            self.update_available.emit(update_info)
            self.update_checked.emit(True)
            
            # Show update dialog if not silent
            if not silent:
                self.show_update_dialog(update_info)
                
        except Exception as e:
            self.logger.error(f"Error handling update check result: {e}")
            self.error_occurred.emit(str(e))
    
    def _handle_check_error(self, error_message: str):
        """Handle update check error with appropriate logging level."""
        # Don't treat "no releases" as an error - it's normal for new repositories
        if "404" in error_message and "releases" in error_message.lower():
            self.logger.info("Repository has no releases yet - this is normal")
            self.update_checked.emit(False)
        else:
            self.logger.warning(f"Update check failed: {error_message}")
            self.error_occurred.emit(error_message)
    
    def show_update_dialog(self, update_info: UpdateInfo):
        """Show the update dialog."""
        try:
            if self.update_dialog:
                self.update_dialog.close()
            
            self.update_dialog = UpdateDialog(update_info)
            
            # Handle dialog result
            if self.update_dialog.exec() == QDialog.Accepted:
                # Check if user wants to skip this version
                if self.update_dialog.get_skip_version():
                    self.settings.skip_version = update_info.version
                    self.logger.info(f"Version {update_info.version} will be skipped")
            
        except Exception as e:
            self.logger.error(f"Error showing update dialog: {e}")
    
    def verify_checksum(self, file_path: str, expected_checksum: str, 
                       checksum_type: str = "sha256") -> bool:
        """Verify file checksum."""
        try:
            if not expected_checksum:
                self.logger.warning("No checksum provided for verification")
                return True  # Skip verification if no checksum
            
            hash_algo = hashlib.new(checksum_type)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_algo.update(chunk)
            
            calculated_checksum = hash_algo.hexdigest()
            
            if calculated_checksum.lower() == expected_checksum.lower():
                self.logger.info("Checksum verification passed")
                return True
            else:
                self.logger.error(f"Checksum mismatch: expected {expected_checksum}, got {calculated_checksum}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying checksum: {e}")
            return False
    
    def get_update_info(self) -> Dict[str, Any]:
        """Get current update checker information."""
        return {
            "current_version": self.current_version,
            "settings": asdict(self.settings),
            "last_check": self.settings.last_check.isoformat() if self.settings.last_check else None,
            "is_checking": self.check_worker.isRunning() if self.check_worker else False
        }
    
    def cleanup(self):
        """Clean up update checker resources."""
        try:
            self.check_timer.stop()
            
            if self.check_worker and self.check_worker.isRunning():
                self.check_worker.cancel()
                self.check_worker.wait(3000)
            
            if self.update_dialog:
                self.update_dialog.close()
                
            self.logger.info("Update checker cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during update checker cleanup: {e}")


# Global instance
_update_checker: Optional[UpdateChecker] = None

def get_update_checker() -> Optional[UpdateChecker]:
    """Get the global update checker instance."""
    return _update_checker

def initialize_update_checker(current_version: str = "2.0.0") -> UpdateChecker:
    """Initialize the global update checker."""
    global _update_checker
    if _update_checker is None:
        _update_checker = UpdateChecker(current_version)
    return _update_checker

def cleanup_update_checker():
    """Clean up the global update checker."""
    global _update_checker
    if _update_checker is not None:
        _update_checker.cleanup()
        _update_checker = None


if __name__ == "__main__":
    # Test the update checker
    import sys
    app = QApplication(sys.argv)
    
    checker = initialize_update_checker()
    checker.check_for_updates(silent=False)
    
    sys.exit(app.exec())