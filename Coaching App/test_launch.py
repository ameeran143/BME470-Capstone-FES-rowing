#!/usr/bin/env python3
"""
Test Launcher for FES-Rowing Application
Launches the main app with additional hardware diagnostics
"""

import sys
import os
import nidaqmx

def check_prerequisites():
    """Check all prerequisites before launching"""
    print("🔍 Checking prerequisites...")
    
    # Check NI-DAQmx
    try:
        import nidaqmx
        print("✅ NI-DAQmx library available")
    except ImportError:
        print("❌ NI-DAQmx not installed")
        return False
    
    # Check hardware connection
    try:
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev4/ai0:7")
            print("✅ Hardware connection verified")
    except Exception as e:
        print(f"❌ Hardware not connected: {e}")
        response = input("Continue in simulation mode? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Check wxPython
    try:
        import wx
        print("✅ wxPython available")
    except ImportError:
        print("❌ wxPython not installed")
        return False
    
    return True

def main():
    print("🚀 FES-Rowing Application Test Launcher")
    print("=" * 45)
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix issues above.")
        sys.exit(1)
    
    print("\n✅ All checks passed! Launching application...")
    print("📊 Monitor the console for hardware diagnostics")
    print("-" * 45)
    
    # Launch the main application
    try:
        import main
        app = main.RowingApp(False)
        app.MainLoop()
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 