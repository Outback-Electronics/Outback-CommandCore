"""
Modern Splash Screen for CommandCore Launcher - FIXED VERSION

Features a beautiful, animated splash screen with working animations,
loading progress, and modern visual effects without black squares.
"""

import math
import random
from typing import List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QParallelAnimationGroup, QSequentialAnimationGroup,
    Property, QRectF, QPointF, QRect, QObject
)
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient,
    QPainterPath, QFont, QFontMetrics, QPen, QBrush,
    QPixmap, QIcon, QConicalGradient
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar,
    QGraphicsEffect, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QFrame, QApplication
)


@dataclass
class Particle:
    """Represents a single animated particle in the background."""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    color: QColor
    rotation: float
    rotation_speed: float
    opacity: float
    life: float
    max_life: float


class ParticleSystem:
    """Manages animated particles for the background effect with proper cleanup."""
    
    def __init__(self, particle_count: int = 60):
        self.particles: List[Particle] = []
        self.particle_count = particle_count
        self.time = 0.0
        self._active = True
        
        # CommandCore color palette
        self.colors = [
            QColor(0, 168, 255, 80),    # Primary blue
            QColor(0, 210, 211, 60),    # Accent cyan
            QColor(76, 175, 80, 40),    # Success green
            QColor(156, 39, 176, 50),   # Purple accent
        ]
        
        self._init_particles()
    
    def _init_particles(self):
        """Initialize all particles with random properties."""
        self.particles.clear()
        
        if not self._active:
            return
        
        for _ in range(self.particle_count):
            particle = Particle(
                x=random.uniform(-0.1, 1.1),
                y=random.uniform(-0.1, 1.1),
                vx=random.uniform(-0.0005, 0.0005),
                vy=random.uniform(-0.0005, 0.0005),
                size=random.uniform(0.002, 0.008),
                color=random.choice(self.colors),
                rotation=random.uniform(0, 2 * math.pi),
                rotation_speed=random.uniform(-0.02, 0.02),
                opacity=random.uniform(0.3, 0.8),
                life=random.uniform(0, 1),
                max_life=random.uniform(2.0, 8.0)
            )
            self.particles.append(particle)
    
    def update(self, delta_time: float, width: int, height: int):
        """Update all particles for one frame."""
        if not self._active:
            return
            
        self.time += delta_time
        
        for particle in self.particles:
            # Update position
            particle.x += particle.vx
            particle.y += particle.vy
            
            # Update rotation
            particle.rotation += particle.rotation_speed
            
            # Update life
            particle.life += delta_time
            if particle.life > particle.max_life:
                self._respawn_particle(particle)
            
            # Bounce off edges
            if particle.x < -0.05 or particle.x > 1.05:
                particle.vx *= -0.8
                particle.x = max(-0.05, min(1.05, particle.x))
            
            if particle.y < -0.05 or particle.y > 1.05:
                particle.vy *= -0.8
                particle.y = max(-0.05, min(1.05, particle.y))
            
            # Subtle pulsing effect
            try:
                pulse = math.sin(self.time * 2 + particle.rotation) * 0.1 + 0.9
                particle.opacity = min(0.8, particle.opacity * pulse)
            except (ValueError, OverflowError):
                # Handle potential math errors
                particle.opacity = 0.5
    
    def _respawn_particle(self, particle: Particle):
        """Respawn a particle at a random edge."""
        if not self._active:
            return
            
        edge = random.randint(0, 3)
        
        if edge == 0:  # Top
            particle.x = random.uniform(0, 1)
            particle.y = -0.05
            particle.vy = random.uniform(0.0002, 0.0008)
        elif edge == 1:  # Right
            particle.x = 1.05
            particle.y = random.uniform(0, 1)
            particle.vx = random.uniform(-0.0008, -0.0002)
        elif edge == 2:  # Bottom
            particle.x = random.uniform(0, 1)
            particle.y = 1.05
            particle.vy = random.uniform(-0.0008, -0.0002)
        else:  # Left
            particle.x = -0.05
            particle.y = random.uniform(0, 1)
            particle.vx = random.uniform(0.0002, 0.0008)
        
        particle.life = 0
        particle.color = random.choice(self.colors)
        particle.size = random.uniform(0.002, 0.008)
    
    def draw(self, painter: QPainter, width: int, height: int):
        """Draw all particles."""
        if not self._active or not painter:
            return
            
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            
            for particle in self.particles:
                # Calculate screen position
                x = particle.x * width
                y = particle.y * height
                size = particle.size * min(width, height)
                
                # Set color with current opacity
                color = QColor(particle.color)
                color.setAlphaF(particle.opacity)
                
                # Draw particle
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                
                # Create a subtle glow effect
                glow_size = size * 2
                glow_color = QColor(color)
                glow_color.setAlphaF(color.alphaF() * 0.3)
                
                painter.setBrush(QBrush(glow_color))
                painter.drawEllipse(
                    QRectF(x - glow_size/2, y - glow_size/2, glow_size, glow_size)
                )
                
                # Draw main particle
                painter.setBrush(QBrush(color))
                painter.drawEllipse(
                    QRectF(x - size/2, y - size/2, size, size)
                )
        except Exception as e:
            # Log drawing errors but don't crash
            logging.warning(f"Error drawing particles: {e}")
    
    def cleanup(self):
        """Clean up particle system resources."""
        self._active = False
        self.particles.clear()


class AnimatedBackground(QWidget):
    """Widget that displays the animated background with particles and effects."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup widget properties - NO BLACK BACKGROUND
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # Animation state
        self.particle_system = ParticleSystem()
        self.wave_phase = 0.0
        self.time = 0.0
        self._should_animate = True
        
        # Animation timer with proper cleanup
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.setSingleShot(False)
        self.animation_timer.start(16)  # ~60 FPS
    
    def stop_animation(self):
        """Stop the background animation to save resources."""
        self._should_animate = False
        if self.animation_timer and self.animation_timer.isActive():
            self.animation_timer.stop()
    
    def _update_animation(self):
        """Update animation state and trigger repaint."""
        if not self._should_animate:
            return
        
        try:
            delta_time = 0.016  # 16ms for 60fps
            self.time += delta_time
            self.wave_phase += 0.02
            
            if self.particle_system:
                self.particle_system.update(delta_time, self.width(), self.height())
            
            self.update()
        except Exception as e:
            logging.warning(f"Error updating background animation: {e}")
    
    def paintEvent(self, event):
        """Paint the animated background."""
        if not self._should_animate:
            return
            
        painter = QPainter(self)
        try:
            painter.setRenderHints(
                QPainter.Antialiasing | 
                QPainter.SmoothPixmapTransform | 
                QPainter.TextAntialiasing
            )
            
            # Create clipping path with rounded corners
            path = QPainterPath()
            path.addRoundedRect(self.rect(), 20, 20)
            painter.setClipPath(path)
            
            # Draw gradient background
            self._draw_background(painter)
            
            # Draw animated particles
            if self.particle_system:
                self.particle_system.draw(painter, self.width(), self.height())
            
            # Draw subtle wave patterns
            self._draw_wave_patterns(painter)
            
        except Exception as e:
            logging.warning(f"Error in background paint event: {e}")
        finally:
            painter.end()
    
    def _draw_background(self, painter: QPainter):
        """Draw the gradient background."""
        try:
            # Main gradient
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0.0, QColor(25, 32, 48))    # Dark blue-gray
            gradient.setColorAt(0.3, QColor(30, 39, 58))    # Slightly lighter
            gradient.setColorAt(0.7, QColor(35, 45, 68))    # Medium
            gradient.setColorAt(1.0, QColor(40, 52, 78))    # Lighter at bottom
            
            painter.fillRect(self.rect(), QBrush(gradient))
            
            # Subtle radial overlay for depth
            center = QPointF(self.width() * 0.3, self.height() * 0.2)
            radial = QRadialGradient(center, min(self.width(), self.height()) * 0.6)
            radial.setColorAt(0.0, QColor(0, 168, 255, 15))  # Subtle blue glow
            radial.setColorAt(0.5, QColor(0, 168, 255, 8))
            radial.setColorAt(1.0, QColor(0, 0, 0, 0))
            
            painter.fillRect(self.rect(), QBrush(radial))
        except Exception as e:
            logging.warning(f"Error drawing background: {e}")
    
    def _draw_wave_patterns(self, painter: QPainter):
        """Draw subtle animated wave patterns."""
        if not self._should_animate:
            return
        
        try:
            painter.setPen(Qt.NoPen)
            
            # Draw multiple wave layers
            for i in range(3):
                alpha = 8 - i * 2
                wavelength = 200 + i * 100
                amplitude = 30 + i * 10
                phase_offset = i * math.pi / 3
                
                color = QColor(0, 168, 255, alpha)
                painter.setBrush(QBrush(color))
                
                # Create wave path
                path = QPainterPath()
                points = []
                
                for x in range(0, self.width() + 20, 10):
                    try:
                        y = self.height() * 0.5 + amplitude * math.sin(
                            (x / wavelength) * 2 * math.pi + self.wave_phase + phase_offset
                        )
                        points.append(QPointF(x, y))
                    except (ValueError, OverflowError):
                        # Handle potential math errors
                        points.append(QPointF(x, self.height() * 0.5))
                
                if points:
                    path.moveTo(points[0])
                    for point in points[1:]:
                        path.lineTo(point)
                    
                    # Close the path to create a filled shape
                    path.lineTo(self.width(), self.height())
                    path.lineTo(0, self.height())
                    path.closeSubpath()
                    
                    painter.drawPath(path)
        except Exception as e:
            logging.warning(f"Error drawing wave patterns: {e}")
    
    def cleanup(self):
        """Clean up background resources."""
        self.stop_animation()
        if self.particle_system:
            self.particle_system.cleanup()
            self.particle_system = None


class LoadingIndicator(QWidget):
    """Modern loading indicator with smooth animations - FIXED VERSION."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(80, 80)
        
        # NO BLACK BACKGROUND
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # Animation properties
        self._rotation = 0.0
        self._progress = 0.0
        self._active = True
        self._pulse = 0.0
        
        # Setup rotation animation with proper cleanup
        self.rotation_animation = QPropertyAnimation(self, b"rotation")
        self.rotation_animation.setDuration(2000)
        self.rotation_animation.setStartValue(0)
        self.rotation_animation.setEndValue(360)
        self.rotation_animation.setLoopCount(-1)  # Infinite
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
        """Paint the loading indicator with working animation."""
        if not self._active:
            return
            
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            
            # Fill with transparent background
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
            
            center = QPointF(self.width() / 2, self.height() / 2)
            outer_radius = min(self.width(), self.height()) / 2 - 8
            inner_radius = outer_radius - 12
            
            # Rotate the painter
            painter.translate(center)
            painter.rotate(self._rotation)
            
            # Create animated gradient
            gradient = QConicalGradient(0, 0, 0)
            
            # Pulsing effect
            pulse_intensity = (math.sin(self._pulse) * 0.3 + 0.7)
            
            # Primary gradient colors with pulse
            primary_color = QColor(0, 168, 255)
            secondary_color = QColor(0, 210, 211)
            
            primary_color.setAlphaF(pulse_intensity)
            secondary_color.setAlphaF(pulse_intensity * 0.8)
            
            gradient.setColorAt(0.0, primary_color)
            gradient.setColorAt(0.3, secondary_color)
            gradient.setColorAt(0.7, QColor(156, 39, 176, int(180 * pulse_intensity)))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
            
            # Draw outer ring (spinning gradient)
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            
            # Create ring path
            outer_path = QPainterPath()
            outer_path.addEllipse(QRectF(-outer_radius, -outer_radius, outer_radius * 2, outer_radius * 2))
            inner_path = QPainterPath()
            inner_path.addEllipse(QRectF(-inner_radius, -inner_radius, inner_radius * 2, inner_radius * 2))
            ring_path = outer_path - inner_path
            
            painter.drawPath(ring_path)
            
            # Draw progress arc if there's progress
            if self._progress > 0:
                painter.setBrush(Qt.NoBrush)
                
                # Progress gradient
                progress_gradient = QLinearGradient(-outer_radius, -outer_radius, outer_radius, outer_radius)
                progress_gradient.setColorAt(0, QColor(76, 175, 80, 255))
                progress_gradient.setColorAt(1, QColor(139, 195, 74, 200))
                
                pen = QPen(QBrush(progress_gradient), 6, Qt.SolidLine, Qt.RoundCap)
                painter.setPen(pen)
                
                span_angle = int((self._progress / 100) * 360 * 16)  # Qt uses 16ths of degrees
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
    Modern splash screen with beautiful animations and loading indicators - FIXED VERSION.
    
    Features:
    - Animated particle background
    - Working loading spinner with rotation and pulse effects
    - Smooth loading progress
    - Modern typography and layout
    - Responsive design
    - NO BLACK SQUARES - all backgrounds are transparent
    """
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Window setup - TRANSPARENT BACKGROUND
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
        
        # Components
        self.background = None
        self.loading_indicator = None
        
        # Timers
        self.progress_timer = None
        self.text_fade_animation = None
        self.fade_out_animation = None
        
        # Setup UI
        try:
            self._setup_ui()
            self._center_on_screen()
            self._setup_animations()
            self._setup_progress_simulation()
        except Exception as e:
            self.logger.error(f"Error initializing splash screen: {e}")
    
    def _setup_ui(self):
        """Setup the user interface components."""
        try:
            # Background fills the entire widget
            self.background = AnimatedBackground(self)
            self.background.setGeometry(self.rect())
            
            # Loading indicator
            self.loading_indicator = LoadingIndicator()
            
            # Main layout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(80, 100, 80, 80)
            layout.setSpacing(40)
            
            # Logo/Title area
            title_widget = QWidget()
            title_widget.setAttribute(Qt.WA_TranslucentBackground, True)
            title_widget.setStyleSheet("background: transparent;")
            
            title_layout = QVBoxLayout(title_widget)
            title_layout.setAlignment(Qt.AlignCenter)
            title_layout.setSpacing(20)
            
            # Main title
            self.title_label = QLabel("CommandCore")
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setAttribute(Qt.WA_TranslucentBackground, True)
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #00A8FF;
                    font-size: 56px;
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    letter-spacing: 2px;
                    background: transparent;
                }
            """)
            
            # Add drop shadow effect for title
            title_shadow = QGraphicsDropShadowEffect()
            title_shadow.setBlurRadius(30)
            title_shadow.setColor(QColor(0, 168, 255, 100))
            title_shadow.setOffset(0, 0)
            self.title_label.setGraphicsEffect(title_shadow)
            
            # Subtitle
            self.subtitle_label = QLabel("Device Management Suite")
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
            
            layout.addStretch(1)
            layout.addWidget(title_widget)
            layout.addStretch(1)
            
            # Loading area
            loading_widget = QWidget()
            loading_widget.setAttribute(Qt.WA_TranslucentBackground, True)
            loading_widget.setStyleSheet("background: transparent;")
            
            loading_layout = QVBoxLayout(loading_widget)
            loading_layout.setAlignment(Qt.AlignCenter)
            loading_layout.setSpacing(25)
            
            # Loading indicator
            indicator_container = QWidget()
            indicator_container.setFixedHeight(100)
            indicator_container.setAttribute(Qt.WA_TranslucentBackground, True)
            indicator_container.setStyleSheet("background: transparent;")
            
            indicator_layout = QVBoxLayout(indicator_container)
            indicator_layout.setAlignment(Qt.AlignCenter)
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
            
            layout.addWidget(loading_widget)
            layout.addStretch(1)
            
            # Add drop shadow effect to the whole window
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(40)
            shadow.setColor(QColor(0, 0, 0, 120))
            shadow.setOffset(0, 15)
            self.setGraphicsEffect(shadow)
            
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
            
            # Start text animation immediately
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
        """Setup automatic progress simulation."""
        try:
            self.progress_timer = QTimer()
            self.progress_timer.timeout.connect(self._update_progress)
            self.progress_timer.setSingleShot(False)
            self.progress_timer.start(75)  # Update every 75ms for smoother progress
            
            # Progress stages with realistic timing
            self.progress_stages = [
                (0, "Initializing components..."),
                (10, "Loading configuration..."),
                (25, "Setting up theme system..."),
                (40, "Preparing user interface..."),
                (55, "Loading applications..."),
                (70, "Starting system monitoring..."),
                (85, "Finalizing setup..."),
                (95, "Almost ready..."),
                (100, "Ready!")
            ]
            self.current_stage = 0
            self.progress_speed = 0.7
            self.stage_delay = 0
        except Exception as e:
            self.logger.error(f"Error setting up progress simulation: {e}")
    
    def _update_progress(self):
        """Update the loading progress simulation."""
        try:
            if self._closing or self.current_stage >= len(self.progress_stages):
                return
            
            target_progress, stage_text = self.progress_stages[self.current_stage]
            
            # Add some delay between stages for realism
            if self._progress >= target_progress:
                self.stage_delay += 1
                if self.stage_delay >= 30:  # Wait about 2 seconds between major stages
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
                # Slow down as we progress
                self.progress_speed *= 0.95
            
            # Update loading indicator and progress label
            if self.loading_indicator:
                self.loading_indicator.progress = self._progress
            
            self.progress_label.setText(f"{int(self._progress)}%")
            
            # Stop timer when complete
            if self._progress >= 100:
                if self.progress_timer:
                    self.progress_timer.stop()
        except Exception as e:
            self.logger.error(f"Error updating progress: {e}")
    
    def get_text_opacity(self):
        return self._text_opacity
    
    def set_text_opacity(self, value):
        if not self._closing:
            self._text_opacity = value
            # Apply opacity to text elements
            for widget in [self.title_label, self.subtitle_label, self.version_label, self.loading_label, self.progress_label]:
                if widget:
                    effect = QGraphicsOpacityEffect()
                    effect.setOpacity(value)
                    widget.setGraphicsEffect(effect)
    
    text_opacity = Property(float, get_text_opacity, set_text_opacity)
    
    def finish(self, main_window):
        """Finish the splash screen with a smooth fade-out."""
        if self._closing:
            return
            
        try:
            self._closing = True
            
            # Stop all timers and animations
            self._stop_all_animations()
            
            # Create fade-out animation
            self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_out_animation.setDuration(800)
            self.fade_out_animation.setStartValue(1.0)
            self.fade_out_animation.setEndValue(0.0)
            self.fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
            self.fade_out_animation.finished.connect(lambda: self._complete_finish(main_window))
            self.fade_out_animation.start()
            
        except Exception as e:
            self.logger.error(f"Error finishing splash screen: {e}")
            self._complete_finish(main_window)
    
    def _stop_all_animations(self):
        """Stop all animations and timers."""
        try:
            # Stop background animations
            if self.background:
                self.background.stop_animation()
            
            # Stop timers
            if self.progress_timer:
                self.progress_timer.stop()
                self.progress_timer = None
            
            # Stop animations
            if self.text_fade_animation:
                self.text_fade_animation.stop()
                self.text_fade_animation = None
                
        except Exception as e:
            self.logger.error(f"Error stopping animations: {e}")
    
    def _complete_finish(self, main_window):
        """Complete the splash screen closure."""
        try:
            if main_window and not self._closing:
                main_window.show()
                main_window.raise_()
                main_window.activateWindow()
            
            self.close()
        except Exception as e:
            self.logger.error(f"Error completing splash finish: {e}")
    
    def resizeEvent(self, event):
        """Handle resize events to update background size."""
        try:
            super().resizeEvent(event)
            if self.background:
                self.background.setGeometry(self.rect())
        except Exception as e:
            self.logger.error(f"Error handling resize event: {e}")
    
    def closeEvent(self, event):
        """Handle close event with proper cleanup."""
        try:
            self._closing = True
            
            # Stop all animations and timers
            self._stop_all_animations()
            
            # Clean up components
            if self.background:
                self.background.cleanup()
                self.background = None
            
            if self.loading_indicator:
                self.loading_indicator.cleanup()
                self.loading_indicator = None
            
            # Stop fade out animation if active
            if self.fade_out_animation:
                self.fade_out_animation.stop()
                self.fade_out_animation = None
            
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