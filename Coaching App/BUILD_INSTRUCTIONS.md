# Building Standalone Executable

This guide explains how to create a standalone .exe file that anyone can run without installing Python.

## Prerequisites

1. **Python 3.8+** installed on your system
2. **All dependencies installed**:
   ```bash
   pip install wxpython matplotlib numpy scipy pillow pyinstaller
   ```

## Building the Executable

**Important**: To create a Windows `.exe` file, you must build on a Windows machine. Building on macOS/Linux will create platform-specific executables.

### Option 1: Using the build script (Recommended)

**On Windows:**
```bash
cd "Coaching App"
python build_exe.py
```

**On macOS/Linux:**
```bash
cd "Coaching App"
python build_exe.py
# This will create a macOS/Linux executable, not a .exe file
```

### Option 2: Using PyInstaller directly

```bash
cd "Coaching App"
pyinstaller build_exe.spec
```

### Option 3: Manual PyInstaller command

```bash
cd "Coaching App"
pyinstaller --name=FES_Rowing_App --onefile --windowed --add-data "assets;assets" --add-data "compress.jpg;." --add-data "extend.jpg;." main.py
```

## Output Location

After building, the executable will be in:
- **Windows**: `dist/FES_Rowing_App.exe`
- **macOS**: `dist/FES_Rowing_App`
- **Linux**: `dist/FES_Rowing_App`

## Distribution

The executable is standalone - you can copy it to any computer and run it directly. No Python installation required!

**Note**: The executable includes all dependencies, so it may be large (50-200MB). This is normal for standalone Python applications.

## Troubleshooting

1. **If build fails**: Make sure all dependencies are installed
2. **If executable doesn't run**: Check that all assets are included (images, sounds)
3. **For Windows**: You may need to run as administrator if antivirus blocks it initially

## Features Disabled in Standalone Version

- **Calibration data saving**: Calibration data is not saved to disk
- **Session data saving**: Session summaries are not saved to CSV files
- Data is still displayed in the UI, but not persisted to disk

