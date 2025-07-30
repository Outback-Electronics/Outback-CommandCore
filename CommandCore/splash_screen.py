"""
Modern Splash Screen for CommandCore Launcher - ENHANCED VERSION

Features animated particles, waves, and proper timing controls.
Ensures 6+ second display time with full 0-100% loading simulation.
"""

import logging
import math
import random
from typing import List, Tuple, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QApplication, QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QPointF, QRectF, Property, Signal
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QLinearGradient, 
    QRadialGradient, QFont, QPainterPath
)


class Particle:
    """Individual particle for the animated background."""
    
    def __init__(self, x: float, y: float, size: float, speed: float, color: QColor):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.color = color
        self.opacity = random.uniform(0.3, 0.8)
        self.direction = random.uniform(0, 2 * math.pi)
        self.pulse_phase = random.uniform(0, 2 * math.pi)
        
    def update(self, dt: float, width: int, height: int):
        """Update particle position and properties."""
        # Move particle
        self.x += math.cos(self.direction) * self.speed * dt
        self.y += math.sin(self.direction) * self.speed * dt
        
        # Wrap around screen edges
        if self.x < -self.size:
            self.x = width + self.size
        elif self.x > width + self.size:
            self.x = -self.size
            
        if self.y < -self.size:
            self.y = height + self.size
        elif self.y > height + self.size:
            self.y = -self.size
        
        # Update pulse phase for breathing effect
        self.pulse_phase += dt * 2
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase -= 2 * math.pi


class ParticleSystem(QWidget):
    """Animated particle system for the splash screen background."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        self.particles: List[Particle] = []
        self.wave_offset = 0.0
        self._active = True
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(16)  # ~60 FPS
        
    def _create_particles(self, count: int = 50):
        """Create initial particles."""
        self.particles.clear()
        
        colors = [
            QColor(0, 168, 255, 80),   # Primary blue
            QColor(0, 210, 211, 60),   # Secondary cyan
            QColor(255, 255, 255, 40), # White
        ]
        
        for _ in range(count):
            x = random.uniform(0, self.width())
            y = random.uniform(0, self.height())
            size = random.uniform(2, 8)
            speed = random.uniform(10, 30)
            color = random.choice(colors)
            
            self.particles.append(Particle(x, y, size, speed, color))
    
    def _update_animation(self):
        """Update all animations."""
        if not self._active:
            return
            
        dt = 0.016  # 16ms frame time
        
        # Update wave offset
        self.wave_offset += dt * 50
        if self.wave_offset > 360:
            self.wave_offset -= 360
        
        # Update particles
        for particle in self.particles:
            particle.update(dt, self.width(), self.height())
        
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Paint the animated background."""
        if not self._active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        try:
            # Create gradient background
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0.0, QColor(26, 31, 46, 240))
            gradient.setColorAt(0.5, QColor(42, 47, 66, 220))
            gradient.setColorAt(1.0, QColor(15, 20, 25, 240))
            
            painter.fillRect(self.rect(), QBrush(gradient))
            
            # Draw animated waves
            self._draw_waves(painter)
            
            # Draw particles
            self._draw_particles(painter)
            
        except Exception as e:
            logging.warning(f"Error painting particle system: {e}")
        finally:
            painter.end()
    
    def _draw_waves(self, painter: QPainter):
        """Draw animated wave patterns."""
        try:
            painter.setBrush(Qt.NoBrush)
            
            # Multiple wave layers
            wave_configs = [
                {'amplitude': 30, 'frequency': 0.01, 'phase': 0, 'color': QColor(0, 168, 255, 30)},
                {'amplitude': 20, 'frequency': 0.015, 'phase': 120, 'color': QColor(0, 210, 211, 25)},
                {'amplitude': 25, 'frequency': 0.008, 'phase': 240, 'color': QColor(255, 255, 255, 15)},
            ]
            
            for config in wave_configs:
                path = QPainterPath()
                
                # Calculate wave points
                points = []
                for x in range(0, self.width() + 10, 5):
                    phase = (config['phase'] + self.wave_offset) * math.pi / 180
                    y = self.height() * 0.6 + config['amplitude'] * math.sin(
                        config['frequency'] * x + phase
                    )
                    points.append(QPointF(x, y))
                
                if points:
                    # Create wave path
                    path.moveTo(points[0])
                    for point in points[1:]:
                        path.lineTo(point)
                    
                    # Close path to bottom for fill effect
                    path.lineTo(self.width(), self.height())
                    path.lineTo(0, self.height())
                    path.closeSubpath()
                    
                    # Draw wave
                    painter.setPen(QPen(config['color'], 2))
                    painter.setBrush(QBrush(config['color']))
                    painter.drawPath(path)
                    
        except Exception as e:
            logging.warning(f"Error drawing waves: {e}")
    
    def _draw_particles(self, painter: QPainter):
        """Draw animated particles."""
        try:
            for particle in self.particles:
                # Calculate pulsing size
                pulse = math.sin(particle.pulse_phase)
                current_size = particle.size + pulse * 2
                
                # Calculate pulsing opacity
                current_opacity = particle.opacity + pulse * 0.2
                current_opacity = max(0.1, min(1.0, current_opacity))
                
                # Set color with current opacity
                color = QColor(particle.color)
                color.setAlphaF(current_opacity)
                
                # Draw particle with glow effect
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                
                # Main particle
                painter.drawEllipse(
                    QPointF(particle.x, particle.y),
                    current_size, current_size
                )
                
                # Glow effect
                glow_color = QColor(color)
                glow_color.setAlphaF(current_opacity * 0.3)
                painter.setBrush(QBrush(glow_color))
                painter.drawEllipse(
                    QPointF(particle.x, particle.y),
                    current_size * 2, current_size * 2
                )
                
        except Exception as e:
            logging.warning(f"Error drawing particles: {e}")
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        if self.width() > 0 and self.height() > 0:
            self._create_particles()
    
    def stop_animation(self):
        """Stop all animations."""
        self._active = False
        if self.animation_timer:
            self.animation_timer.stop()
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_animation()
        self.particles.clear()


class LoadingIndicator(QWidget):
    """Modern loading indicator with smooth animations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(80, 80)
        
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # Animation properties
        self._rotation = 0.0
        self._progress = 0.0
        self._active = True
        self._pulse = 0.0
        
        # Setup rotation animation
        self.rotation_animation = QPropertyAnimation(self, b"rotation")
        self.rotation_animation.setDuration(2000)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)
        self.rotation_animation.setEasingCurve(QEasingCurve.Linear)
        
        # Setup pulse animation
        self.pulse_animation = QPropertyAnimation(self, b"pulse")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setStartValue(0.0)
        self.pulse_animation.setEndValue(2 * math.pi)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
        
        # Start animations
        self.rotation_animation.start()
        self.pulse_animation.start()
    
    def get_rotation(self):
        return self._rotation
    
    def set_rotation(self, value):
        if self._active:
            self._rotation = value % 360
            self.update()
    
    def get_progress(self):
        return self._progress
    
    def set_progress(self, value):
        if self._active:
            self._progress = max(0, min(100, value))
            self.update()
    
    def get_pulse(self):
        return self._pulse
    
    def set_pulse(self, value):
        if self._active:
            self._pulse = value
            self.update()
    
    rotation = Property(float, get_rotation, set_rotation)
    progress = Property(float, get_progress, set_progress)
    pulse = Property(float, get_pulse, set_pulse)
    
    def paintEvent(self, event):
        """Paint the loading indicator."""
        if not self._active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        try:
            center = self.rect().center()
            painter.translate(center)
            painter.rotate(self._rotation)
            
            # Calculate dimensions
            outer_radius = 35
            inner_radius = 25
            
            # Calculate pulse intensity
            pulse_intensity = (math.sin(self._pulse) + 1) / 2  # 0 to 1
            
            # Draw outer ring segments
            painter.setBrush(Qt.NoBrush)
            
            # Static segments
            segment_colors = [
                QColor(0, 168, 255, 100),
                QColor(0, 180, 255, 80),
                QColor(0, 190, 255, 60),
                QColor(0, 200, 255, 40),
            ]
            
            for i, color in enumerate(segment_colors):
                painter.setPen(QPen(color, 3))
                start_angle = i * 90 * 16  # Qt uses 16ths of degrees
                span_angle = 60 * 16
                painter.drawArc(
                    QRectF(-outer_radius, -outer_radius, outer_radius * 2, outer_radius * 2),
                    start_angle, span_angle
                )
            
            # Draw progress arc
            if self._progress > 0:
                progress_color = QColor(0, 255, 128, int(150 * pulse_intensity))
                painter.setPen(QPen(progress_color, 4))
                
                span_angle = int((self._progress / 100) * 360 * 16)
                painter.drawArc(
                    QRectF(-outer_radius + 3, -outer_radius + 3, (outer_radius - 3) * 2, (outer_radius - 3) * 2),
                    90 * 16,  # Start at top
                    -span_angle  # Draw clockwise
                )
            
            # Draw inner glow
            painter.setBrush(Qt.NoBrush)
            glow_color = QColor(0, 168, 255, int(100 * pulse_intensity))
            painter.setPen(QPen(glow_color, 2))
            painter.drawEllipse(QRectF(-inner_radius + 2, -inner_radius + 2, (inner_radius - 2) * 2, (inner_radius - 2) * 2))
            
            # Draw center dot
            center_size = 8
            center_color = QColor(255, 255, 255, int(200 * pulse_intensity))
            painter.setBrush(QBrush(center_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(-center_size/2, -center_size/2, center_size, center_size))
            
        except Exception as e:
            logging.warning(f"Error painting loading indicator: {e}")
        finally:
            painter.end()
    
    def cleanup(self):
        """Clean up loading indicator resources."""
        self._active = False
        if self.rotation_animation:
            self.rotation_animation.stop()
            self.rotation_animation = None
        if self.pulse_animation:
            self.pulse_animation.stop()
            self.pulse_animation = None


class ModernSplashScreen(QWidget):
    """
    Modern splash screen with animated background and proper timing controls.
    
    Features:
    - Animated particle background with waves
    - Working loading spinner with rotation and pulse effects
    - Guaranteed 6+ second display time
    - Proper 0-100% loading progress
    - Background loading of main application
    - Smooth fade-out animation
    """
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Window setup
        self.setFixedSize(1000, 650)
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # Animation properties
        self._progress = 0.0
        self._text_opacity = 0.0
        self._closing = False
        
        # Timing controls - ENHANCED
        self.start_time = None
        self.min_display_time = 6000  # 6 seconds minimum
        self.loading_complete = False
        self.can_close = False
        self.main_window_ref = None
        
        # Components
        self.particle_system = None
        self.loading_indicator = None
        
        # Timers and animations
        self.progress_timer = None
        self.text_fade_animation = None
        self.fade_out_animation = None
        self.min_time_timer = None
        
        # Setup UI
        try:
            self._setup_ui()
            self._center_on_screen()
            self._setup_animations()
            self._setup_progress_simulation()
            
            # Start minimum time timer
            self.min_time_timer = QTimer()
            self.min_time_timer.timeout.connect(self._check_can_close)
            self.min_time_timer.setSingleShot(True)
            self.min_time_timer.start(self.min_display_time)
            
        except Exception as e:
            self.logger.error(f"Error initializing splash screen: {e}")
    
    def _setup_ui(self):
        """Setup the user interface components."""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Animated background
            self.particle_system = ParticleSystem(self)
            self.particle_system.setGeometry(self.rect())
            
            # Content layout over background
            content_widget = QWidget()
            content_widget.setAttribute(Qt.WA_TranslucentBackground, True)
            content_widget.setStyleSheet("background: transparent;")
            
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(60, 80, 60, 80)
            content_layout.setSpacing(40)
            
            # Title section
            title_widget = QWidget()
            title_widget.setAttribute(Qt.WA_TranslucentBackground, True)
            title_widget.setStyleSheet("background: transparent;")
            
            title_layout = QVBoxLayout(title_widget)
            title_layout.setAlignment(Qt.AlignCenter)
            title_layout.setSpacing(15)
            
            # Main title
            self.title_label = QLabel("CommandCore Launcher")
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setAttribute(Qt.WA_TranslucentBackground, True)
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    font-size: 42px;
                    font-weight: 300;
                    font-family: 'Segoe UI Light', 'Helvetica Neue', Arial, sans-serif;
                    letter-spacing: 2px;
                    background: transparent;
                }
            """)
            
            # Subtitle
            self.subtitle_label = QLabel("Modern Application Management Suite")
            self.subtitle_label.setAlignment(Qt.AlignCenter)
            self.subtitle_label.setAttribute(Qt.WA_TranslucentBackground, True)
            self.subtitle_label.setStyleSheet("""
                QLabel {
                    color: #B0BEC5;
                    font-size: 18px;
                    font-weight: 300;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    letter-spacing: 1px;
                    background: transparent;
                }
            """)
            
            # Version
            self.version_label = QLabel("v2.0.0")
            self.version_label.setAlignment(Qt.AlignCenter)
            self.version_label.setAttribute(Qt.WA_TranslucentBackground, True)
            self.version_label.setStyleSheet("""
                QLabel {
                    color: #78909C;
                    font-size: 14px;
                    font-weight: 500;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: transparent;
                }
            """)
            
            title_layout.addWidget(self.title_label)
            title_layout.addWidget(self.subtitle_label)
            title_layout.addWidget(self.version_label)
            
            content_layout.addStretch(1)
            content_layout.addWidget(title_widget)
            content_layout.addStretch(1)
            
            # Loading section
            loading_widget = QWidget()
            loading_widget.setAttribute(Qt.WA_TranslucentBackground, True)
            loading_widget.setStyleSheet("background: transparent;")
            
            loading_layout = QVBoxLayout(loading_widget)
            loading_layout.setAlignment(Qt.AlignCenter)
            loading_layout.setSpacing(25)
            
            # Loading indicator container
            indicator_container = QWidget()
            indicator_container.setFixedHeight(100)
            indicator_container.setAttribute(Qt.WA_TranslucentBackground, True)
            indicator_container.setStyleSheet("background: transparent;")
            
            indicator_layout = QVBoxLayout(indicator_container)
            indicator_layout.setAlignment(Qt.AlignCenter)
            
            # Create loading indicator
            self.loading_indicator = LoadingIndicator()
            indicator_layout.addWidget(self.loading_indicator)
            
            # Loading text
            self.loading_label = QLabel("Initializing...")
            self.loading_label.setAlignment(Qt.AlignCenter)
            self.loading_label.setAttribute(Qt.WA_TranslucentBackground, True)
            self.loading_label.setStyleSheet("""
                QLabel {
                    color: #B0BEC5;
                    font-size: 16px;
                    font-weight: 400;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: transparent;
                }
            """)
            
            # Progress percentage
            self.progress_label = QLabel("0%")
            self.progress_label.setAlignment(Qt.AlignCenter)
            self.progress_label.setAttribute(Qt.WA_TranslucentBackground, True)
            self.progress_label.setStyleSheet("""
                QLabel {
                    color: #00A8FF;
                    font-size: 14px;
                    font-weight: 600;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: transparent;
                }
            """)
            
            loading_layout.addWidget(indicator_container)
            loading_layout.addWidget(self.loading_label)
            loading_layout.addWidget(self.progress_label)
            
            content_layout.addWidget(loading_widget)
            content_layout.addStretch(1)
            
            # Add content widget to main layout
            layout.addWidget(content_widget)
            
            # Add drop shadow effect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(40)
            shadow.setColor(QColor(0, 0, 0, 120))
            shadow.setOffset(0, 15)
            content_widget.setGraphicsEffect(shadow)
            
        except Exception as e:
            self.logger.error(f"Error setting up splash screen UI: {e}")
    
    def _center_on_screen(self):
        """Center the splash screen on the primary display."""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                x = (screen_geometry.width() - self.width()) // 2
                y = (screen_geometry.height() - self.height()) // 2
                self.move(max(0, x), max(0, y))
        except Exception as e:
            self.logger.error(f"Error centering splash screen: {e}")
    
    def _setup_animations(self):
        """Setup smooth animations for the splash screen."""
        try:
            # Text fade-in animation
            self.text_fade_animation = QPropertyAnimation(self, b"text_opacity")
            self.text_fade_animation.setDuration(1200)
            self.text_fade_animation.setStartValue(0.0)
            self.text_fade_animation.setEndValue(1.0)
            self.text_fade_animation.setEasingCurve(QEasingCurve.OutCubic)
            
            # Start text animation after a brief delay
            QTimer.singleShot(300, self._start_text_animation)
        except Exception as e:
            self.logger.error(f"Error setting up animations: {e}")
    
    def _start_text_animation(self):
        """Start the text fade animation safely."""
        try:
            if self.text_fade_animation and not self._closing:
                self.text_fade_animation.start()
        except Exception as e:
            self.logger.error(f"Error starting text animation: {e}")
    
    def _setup_progress_simulation(self):
        """Setup automatic progress simulation with proper timing."""
        try:
            self.progress_timer = QTimer()
            self.progress_timer.timeout.connect(self._update_progress)
            self.progress_timer.setSingleShot(False)
            self.progress_timer.start(50)  # Update every 50ms for smooth progress
            
            # Progress stages with realistic timing
            self.progress_stages = [
                (0, "Initializing components..."),
                (8, "Loading configuration..."),
                (18, "Setting up theme system..."),
                (28, "Preparing user interface..."),
                (38, "Loading applications..."),
                (48, "Starting system monitoring..."),
                (58, "Initializing update checker..."),
                (68, "Setting up system tray..."),
                (78, "Loading notification system..."),
                (88, "Finalizing setup..."),
                (96, "Almost ready..."),
                (100, "Ready!")
            ]
            self.current_stage = 0
            self.progress_speed = 0.3  # Slower for more realistic loading
            self.stage_delay = 0
            
        except Exception as e:
            self.logger.error(f"Error setting up progress simulation: {e}")
    
    def _update_progress(self):
        """Update the loading progress simulation."""
        try:
            if self._closing or self.current_stage >= len(self.progress_stages):
                if self._progress >= 100:
                    self.loading_complete = True
                    self._check_can_finish()
                return
            
            target_progress, stage_text = self.progress_stages[self.current_stage]
            
            # Add realistic delay between stages
            if self._progress >= target_progress:
                self.stage_delay += 1
                # Vary delay times for different stages
                if target_progress < 30:
                    delay_needed = 20  # Slower at start
                elif target_progress < 80:
                    delay_needed = 15  # Medium speed
                else:
                    delay_needed = 25  # Slower at end for dramatic effect
                    
                if self.stage_delay >= delay_needed:
                    self.current_stage += 1
                    self.stage_delay = 0
                    if self.current_stage < len(self.progress_stages):
                        _, new_stage_text = self.progress_stages[self.current_stage]
                        self.loading_label.setText(new_stage_text)
                return
            
            # Smoothly animate to target progress
            self._progress += self.progress_speed
            if self._progress >= target_progress:
                self._progress = target_progress
                self.loading_label.setText(stage_text)
                # Slow down as we progress for realism
                self.progress_speed *= 0.98
            
            # Update loading indicator and progress label
            if self.loading_indicator:
                self.loading_indicator.progress = self._progress
            
            self.progress_label.setText(f"{int(self._progress)}%")
            
            # Check if loading is complete
            if self._progress >= 100:
                self.loading_complete = True
                if self.progress_timer:
                    self.progress_timer.stop()
                self._check_can_finish()
                    
        except Exception as e:
            self.logger.error(f"Error updating progress: {e}")
    
    def _check_can_close(self):
        """Called when minimum display time has passed."""
        self.can_close = True
        self.logger.info("Minimum display time reached")
        self._check_can_finish()
    
    def _check_can_finish(self):
        """Check if we can finish the splash screen."""
        if self.loading_complete and self.can_close and self.main_window_ref:
            self.logger.info("All conditions met, finishing splash screen")
            self._do_finish()
    
    def finish(self, main_window):
        """Called to finish the splash screen."""
        if self._closing:
            return
            
        self.main_window_ref = main_window
        self.logger.info("Finish requested, checking conditions...")
        self._check_can_finish()
    
    def _do_finish(self):
        """Actually perform the finish sequence."""
        if self._closing:
            return
            
        try:
            self._closing = True
            self.logger.info("Starting splash screen fade-out")
            
            # Stop all timers and animations
            self._stop_all_animations()
            
            # Create fade-out animation
            self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_out_animation.setDuration(800)
            self.fade_out_animation.setStartValue(1.0)
            self.fade_out_animation.setEndValue(0.0)
            self.fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
            self.fade_out_animation.finished.connect(self._complete_finish)
            self.fade_out_animation.start()
            
        except Exception as e:
            self.logger.error(f"Error finishing splash screen: {e}")
            self._complete_finish()
    
    def _complete_finish(self):
        """Complete the splash screen closure and show main window."""
        try:
            if self.main_window_ref:
                # Show the window maximized
                self.main_window_ref.showMaximized()
                self.main_window_ref.raise_()
                self.main_window_ref.activateWindow()
                self.logger.info("Main window shown maximized")
            
            self.close()
        except Exception as e:
            self.logger.error(f"Error completing splash finish: {e}")
    
    def _stop_all_animations(self):
        """Stop all animations and timers."""
        try:
            timers_to_stop = [
                self.progress_timer,
                self.min_time_timer
            ]
            
            for timer in timers_to_stop:
                if timer and timer.isActive():
                    timer.stop()
            
            animations_to_stop = [
                self.text_fade_animation
            ]
            
            for animation in animations_to_stop:
                if animation and animation.state() == QPropertyAnimation.Running:
                    animation.stop()
            
            # Stop particle system
            if self.particle_system:
                self.particle_system.stop_animation()
                
        except Exception as e:
            self.logger.error(f"Error stopping animations: {e}")
    
    def get_text_opacity(self):
        return self._text_opacity
    
    def set_text_opacity(self, value):
        if not self._closing:
            self._text_opacity = value
            # Apply opacity to text elements
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            for widget in [self.title_label, self.subtitle_label, self.version_label, self.loading_label, self.progress_label]:
                if widget:
                    effect = QGraphicsOpacityEffect()
                    effect.setOpacity(value)
                    widget.setGraphicsEffect(effect)
    
    text_opacity = Property(float, get_text_opacity, set_text_opacity)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        try:
            super().resizeEvent(event)
            if self.particle_system:
                self.particle_system.setGeometry(self.rect())
        except Exception as e:
            self.logger.error(f"Error handling resize event: {e}")
    
    def closeEvent(self, event):
        """Handle close event with proper cleanup."""
        try:
            self._closing = True
            
            # Stop all animations and timers
            self._stop_all_animations()
            
            # Clean up components
            if self.particle_system:
                self.particle_system.cleanup()
                self.particle_system = None
            
            if self.loading_indicator:
                self.loading_indicator.cleanup()
                self.loading_indicator = None
            
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Error during splash screen cleanup: {e}")
            event.accept()


# Convenience function for showing splash screen
def show_splash_screen() -> Optional[ModernSplashScreen]:
    """Show the modern splash screen and return the instance."""
    try:
        splash = ModernSplashScreen()
        splash.show()
        return splash
    except Exception as e:
        logging.error(f"Error showing splash screen: {e}")
        return None