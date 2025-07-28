#!/usr/bin/env python3
"""
Setup script for CommandCore Launcher - Modern Edition

Provides installation, distribution, and executable building capabilities
for the modernized CommandCore Launcher application.
"""

import sys
import os
from pathlib import Path
from setuptools import setup, find_packages

# Ensure minimum Python version
if sys.version_info < (3, 8):
    print("CommandCore Launcher requires Python 3.8 or higher.")
    print(f"You are running Python {sys.version}")
    sys.exit(1)

# Get the directory containing this script
here = Path(__file__).parent.absolute()

# Read the README file for long description
def read_readme():
    readme_path = here / "README.md"
    if readme_path.exists():
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "CommandCore Launcher - Modern application management suite"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = here / "requirements.txt"
    requirements = []
    
    if requirements_path.exists():
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Handle platform-specific requirements
                    if ';' in line:
                        requirements.append(line)
                    else:
                        requirements.append(line)
    
    return requirements

# Get version from main module
def get_version():
    version_file = here / "__init__.py"
    if version_file.exists():
        with open(version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return "2.0.0"

# Application metadata
METADATA = {
    'name': 'commandcore-launcher',
    'version': get_version(),
    'description': 'Modern application launcher and manager for the CommandCore suite',
    'long_description': read_readme(),
    'long_description_content_type': 'text/markdown',
    'author': 'Outback Electronics',
    'author_email': 'support@outbackelectronics.com',
    'url': 'https://github.com/outback-electronics/commandcore-launcher',
    'project_urls': {
        'Documentation': 'https://docs.commandcore.org',
        'Bug Reports': 'https://github.com/outback-electronics/commandcore-launcher/issues',
        'Source': 'https://github.com/outback-electronics/commandcore-launcher',
        'Funding': 'https://github.com/sponsors/outback-electronics',
    },
    'license': 'MIT',
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
        'Topic :: Desktop Environment',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Environment :: X11 Applications :: Qt',
        'Environment :: Win32 (MS Windows)',
        'Environment :: MacOS X',
    ],
    'keywords': 'launcher, application manager, system monitor, qt, pyside6, commandcore',
    'python_requires': '>=3.8',
}

# Package configuration
PACKAGES = {
    'packages': find_packages(exclude=['tests', 'tests.*', 'docs', 'docs.*']),
    'include_package_data': True,
    'package_data': {
        '': [
            '*.md', '*.txt', '*.yml', '*.yaml', '*.json',
            '*.png', '*.ico', '*.svg', '*.qss',
            'assets/*', 'themes/*', 'icons/*'
        ],
        'ui': ['*.qss', '*.css', 'themes/*'],
        'assets': ['*'],
    },
    'zip_safe': False,
}

# Dependencies
DEPENDENCIES = {
    'install_requires': read_requirements(),
    'extras_require': {
        'dev': [
            'pytest>=7.4.0',
            'pytest-qt>=4.2.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.1.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.7.0',
            'pre-commit>=3.6.0',
        ],
        'build': [
            'cx-Freeze>=6.15.0',
            'pyinstaller>=6.2.0',
            'setuptools>=69.0.0',
            'wheel>=0.42.0',
        ],
        'docs': [
            'sphinx>=7.0.0',
            'sphinx-rtd-theme>=1.3.0',
            'myst-parser>=2.0.0',
        ],
        'optional': [
            'matplotlib>=3.8.0',  # Advanced charting
            'plotly>=5.17.0',     # Interactive charts
            'qtawesome>=1.3.0',  # Icon fonts
        ],
    },
}

# Entry points
ENTRY_POINTS = {
    'entry_points': {
        'console_scripts': [
            'commandcore-launcher=main:main',
            'commandcore=main:main',
        ],
        'gui_scripts': [
            'commandcore-launcher-gui=main:main',
        ],
    },
}

# Platform-specific configuration
def get_platform_config():
    """Get platform-specific configuration."""
    config = {}
    
    if sys.platform == 'win32':
        # Windows-specific configuration
        config.update({
            'data_files': [
                ('', ['README.md', 'LICENSE']),
                ('assets', ['assets/CommandCore.png'] if Path('assets/CommandCore.png').exists() else []),
            ],
        })
    
    elif sys.platform == 'darwin':
        # macOS-specific configuration
        config.update({
            'data_files': [
                ('', ['README.md', 'LICENSE']),
                ('Resources', ['assets/CommandCore.png'] if Path('assets/CommandCore.png').exists() else []),
            ],
        })
    
    else:
        # Linux/Unix configuration
        config.update({
            'data_files': [
                ('share/doc/commandcore-launcher', ['README.md', 'LICENSE']),
                ('share/pixmaps', ['assets/CommandCore.png'] if Path('assets/CommandCore.png').exists() else []),
                ('share/applications', ['assets/commandcore-launcher.desktop'] if Path('assets/commandcore-launcher.desktop').exists() else []),
            ],
        })
    
    return config

# Combine all configuration
def get_setup_config():
    """Combine all setup configuration."""
    config = {}
    config.update(METADATA)
    config.update(PACKAGES)
    config.update(DEPENDENCIES)
    config.update(ENTRY_POINTS)
    config.update(get_platform_config())
    
    return config

# Custom commands for building executables
class BuildExecutable:
    """Base class for executable builders."""
    
    def __init__(self, name, icon_path=None):
        self.name = name
        self.icon_path = icon_path or self._find_icon()
    
    def _find_icon(self):
        """Find application icon."""
        icon_paths = [
            'assets/CommandCore.ico',
            'assets/CommandCore.png',
            'CommandCore.ico',
            'icon.ico'
        ]
        
        for path in icon_paths:
            if Path(path).exists():
                return str(Path(path).absolute())
        
        return None

class BuildWithCxFreeze(BuildExecutable):
    """Build executable using cx_Freeze."""
    
    def build(self):
        try:
            from cx_Freeze import setup, Executable
            
            # Build options
            build_exe_options = {
                'packages': [
                    'PySide6', 'psutil', 'git', 'json', 'pathlib',
                    'datetime', 'dataclasses', 'typing', 'enum'
                ],
                'excludes': [
                    'tkinter', 'unittest', 'pydoc', 'difflib',
                    'doctest', 'inspect', 'multiprocessing'
                ],
                'include_files': [
                    ('README.md', 'README.md'),
                    ('assets/', 'assets/') if Path('assets').exists() else None,
                ],
                'zip_include_packages': ['PySide6'],
                'optimize': 2,
            }
            
            # Remove None entries
            build_exe_options['include_files'] = [
                item for item in build_exe_options['include_files'] if item is not None
            ]
            
            # Executable configuration
            executables = [
                Executable(
                    'main.py',
                    base='Win32GUI' if sys.platform == 'win32' else None,
                    target_name=self.name,
                    icon=self.icon_path,
                    shortcut_name='CommandCore Launcher',
                    shortcut_dir='DesktopFolder',
                )
            ]
            
            # Setup configuration
            setup_config = get_setup_config()
            setup_config.update({
                'options': {'build_exe': build_exe_options},
                'executables': executables,
            })
            
            setup(**setup_config)
            
        except ImportError:
            print("cx_Freeze not available. Install with: pip install cx-freeze")
            sys.exit(1)

class BuildWithPyInstaller(BuildExecutable):
    """Build executable using PyInstaller."""
    
    def build(self):
        try:
            import PyInstaller.__main__
            
            args = [
                'main.py',
                '--name', self.name,
                '--windowed',
                '--onefile',
                '--clean',
                '--noconfirm',
            ]
            
            if self.icon_path:
                args.extend(['--icon', self.icon_path])
            
            # Add data files
            if Path('README.md').exists():
                args.extend(['--add-data', 'README.md;.'])
            
            if Path('assets').exists():
                args.extend(['--add-data', 'assets;assets'])
            
            PyInstaller.__main__.run(args)
            
        except ImportError:
            print("PyInstaller not available. Install with: pip install pyinstaller")
            sys.exit(1)

# Custom commands
def build_executable(builder='auto'):
    """Build executable using specified builder."""
    app_name = 'CommandCoreLauncher'
    
    if builder == 'auto':
        # Try PyInstaller first, then cx_Freeze
        try:
            import PyInstaller
            builder = 'pyinstaller'
        except ImportError:
            try:
                import cx_Freeze
                builder = 'cx_freeze'
            except ImportError:
                print("No executable builder available.")
                print("Install with: pip install pyinstaller or pip install cx-freeze")
                sys.exit(1)
    
    if builder == 'pyinstaller':
        BuildWithPyInstaller(app_name).build()
    elif builder == 'cx_freeze':
        BuildWithCxFreeze(app_name).build()
    else:
        print(f"Unknown builder: {builder}")
        sys.exit(1)

# Main setup
def main():
    """Main setup function."""
    # Check for custom commands
    if len(sys.argv) > 1 and sys.argv[1] == 'build_exe':
        builder = sys.argv[2] if len(sys.argv) > 2 else 'auto'
        build_executable(builder)
        return
    
    # Standard setup
    config = get_setup_config()
    setup(**config)

if __name__ == '__main__':
    main()