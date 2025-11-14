"""
Build script for creating a standalone .exe file using PyInstaller
Run this script to create a distributable executable.

Requirements:
    pip install pyinstaller

Usage:
    python build_exe.py
"""

import PyInstaller.__main__
import os
import sys

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# PyInstaller arguments
args = [
    'main.py',  # Main entry point
    '--name=FES_Rowing_App',  # Name of the executable
    '--onefile',  # Create a single executable file
    '--windowed',  # No console window (GUI app)
    '--clean',  # Clean PyInstaller cache before building
    '--noconfirm',  # Overwrite output directory without asking
    
    # Include all necessary files
    # Note: Path separator is ; for Windows, : for macOS/Linux
    '--add-data=assets' + (os.pathsep + 'assets' if sys.platform == 'win32' else ':assets'),
    '--add-data=compress.jpg' + (os.pathsep + '.' if sys.platform == 'win32' else ':.'),
    '--add-data=extend.jpg' + (os.pathsep + '.' if sys.platform == 'win32' else ':.'),
    
    # Hidden imports (modules that PyInstaller might miss)
    '--hidden-import=wx',
    '--hidden-import=wx.grid',
    '--hidden-import=matplotlib',
    '--hidden-import=matplotlib.backends.backend_wxagg',
    '--hidden-import=matplotlib.figure',
    '--hidden-import=matplotlib.dates',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=scipy',
    '--hidden-import=scipy.signal',
    '--hidden-import=numpy',
    
    # Exclude unnecessary modules to reduce size
    '--exclude-module=tkinter',
    '--exclude-module=unittest',
    '--exclude-module=test',
    '--exclude-module=tests',
    
    # Icon (optional - add if you have an icon file)
    # '--icon=icon.ico',
]

print("Building standalone executable...")
print("This may take a few minutes...")
print()
print(f"Platform: {sys.platform}")
if sys.platform != 'win32':
    print("Note: To create a Windows .exe file, you need to build on Windows.")
    print("This will create a macOS/Linux executable instead.")
print()

try:
    PyInstaller.__main__.run(args)
    print()
    print("Build complete! The executable should be in the 'dist' folder.")
    print("On Windows: dist/FES_Rowing_App.exe")
    print("On macOS: dist/FES_Rowing_App")
    print("On Linux: dist/FES_Rowing_App")
except Exception as e:
    print(f"Build failed: {e}")
    print("\nMake sure PyInstaller is installed:")
    print("  pip install pyinstaller")
    sys.exit(1)

