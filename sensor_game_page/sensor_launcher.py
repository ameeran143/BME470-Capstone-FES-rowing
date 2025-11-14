#!/usr/bin/env python3
"""
Sensor Game Page Launcher
This script launches the application with live hardware sensor data from NI-DAQ
Includes start page, calibration page, and game page
"""

import wx
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from game_page import GamePage, SharedStats
from sensor_reader import SensorReader
from start_page import StartPage
from calib_page import CalibPage
from instructions import InstructionsPage


class SensorGameFrame(wx.Frame):
    def __init__(self):
        super(SensorGameFrame, self).__init__(None, title="FES Rowing - Live Sensor Data", size=(1200, 900))
        
        # Center the window
        self.Centre()
        
        print("=" * 60)
        print("🧪 LIVE SENSOR DATA MODE")
        print("=" * 60)
        
        # Initialize sensor reader
        try:
            self.sensor_reader = SensorReader()
            
            # Attempt to start/connect
            if not self.sensor_reader.start():
                # Show error dialog
                error_msg = (
                    "Failed to connect to NI-DAQ hardware.\n\n"
                    "Troubleshooting:\n"
                    "• Check NI-DAQ device is connected via USB/Ethernet\n"
                    "• Verify device name is 'Dev1' in NI MAX\n"
                    "• Install/update NI-DAQmx drivers\n"
                    "• Try running as administrator\n"
                    "• Ensure you're on Windows or Linux (macOS not supported)\n\n"
                )
                if self.sensor_reader.last_error:
                    error_msg += f"Error: {self.sensor_reader.last_error}"
                
                wx.MessageBox(error_msg, "Hardware Connection Error", wx.OK | wx.ICON_ERROR)
                print("❌ Hardware connection failed - exiting")
                sys.exit(1)
            
            print("✅ Sensor reader initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize sensor reader: {e}")
            import traceback
            traceback.print_exc()
            wx.MessageBox(
                f"Failed to initialize sensor reader:\n{e}\n\n"
                "Please check:\n"
                "• NI-DAQmx drivers are installed\n"
                "• Hardware is connected\n"
                "• You're running on Windows or Linux",
                "Initialization Error", 
                wx.OK | wx.ICON_ERROR
            )
            sys.exit(1)
        
        # Create shared state with sensor mode
        try:
            self.shared_state = SharedStats(
                playback_mode=False, 
                playback_source=None,
                sensor_mode=True, 
                sensor_source=self.sensor_reader
            )
            print("✅ Shared stats initialized")
        except Exception as e:
            print(f"❌ Failed to initialize shared stats: {e}")
            import traceback
            traceback.print_exc()
            wx.MessageBox(
                f"Failed to initialize game state:\n{e}",
                "Initialization Error",
                wx.OK | wx.ICON_ERROR
            )
            sys.exit(1)
        
        # Create all pages
        try:
            self.start_page = StartPage(self)
            self.calib_page = CalibPage(self, self.shared_state, self.sensor_reader)
            self.game_page = GamePage(self, self.shared_state)
            self.instructions_page = InstructionsPage(self)
            print("✅ All pages created")
        except Exception as e:
            print(f"❌ Failed to create pages: {e}")
            import traceback
            traceback.print_exc()
            wx.MessageBox(
                f"Failed to create pages:\n{e}",
                "Initialization Error",
                wx.OK | wx.ICON_ERROR
            )
            sys.exit(1)
        
        # Layout - use sizer to hold all pages
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.start_page, 1, wx.EXPAND)
        self.sizer.Add(self.calib_page, 1, wx.EXPAND)
        self.sizer.Add(self.game_page, 1, wx.EXPAND)
        self.sizer.Add(self.instructions_page, 1, wx.EXPAND)
        
        # Hide all pages except start page
        self.calib_page.Hide()
        self.game_page.Hide()
        self.instructions_page.Hide()
        
        self.SetSizer(self.sizer)
        self.current_panel = self.start_page
        
        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        print("\n" + "=" * 60)
        print("▶️  Application launched with live sensor data")
        print("=" * 60)
        print("\nStatus:")
        if self.sensor_reader.is_connected:
            print("  ✅ Hardware connected")
        else:
            print("  ⚠️  Hardware not connected - check console for errors")
        print("\nNavigation:")
        print("  • Start Page: Select mode")
        print("  • Calibration: Configure seat position range")
        print("  • Game Page: Main rowing interface")
        print("\n")
    
    def switch_to_start_page(self):
        """Switch to start/selection page"""
        self.current_panel.Hide()
        self.start_page.Show()
        self.current_panel = self.start_page
        self.Refresh()
        self.Layout()
    
    def switch_to_calib_page(self):
        """Switch to calibration page"""
        self.current_panel.Hide()
        self.calib_page.Show()
        self.current_panel = self.calib_page
        self.Refresh()
        self.Layout()
    
    def switch_to_game_page(self):
        """Switch to game page"""
        self.current_panel.Hide()
        self.game_page.Show()
        self.current_panel = self.game_page
        self.Refresh()
        self.Layout()
    
    def switch_to_instructions_page(self):
        """Switch to instructions/tutorial page"""
        self.current_panel.Hide()
        self.instructions_page.Show()
        self.current_panel = self.instructions_page
        self.Refresh()
        self.Layout()
    
    def on_close(self, event):
        """Handle window close event"""
        print("\n👋 Closing sensor game application...")
        if hasattr(self, 'sensor_reader'):
            print("   Cleaning up sensor reader...")
        self.Destroy()


def main():
    """Main entry point"""
    app = wx.App(False)
    
    try:
        frame = SensorGameFrame()
        
        # Check if hardware is connected before showing
        if frame.sensor_reader.is_connected:
            frame.Show()
            app.MainLoop()
        else:
            print("❌ Cannot start application - hardware not connected")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


