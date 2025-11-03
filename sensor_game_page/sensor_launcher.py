#!/usr/bin/env python3
"""
Sensor Game Page Launcher
This script launches the game page with live hardware sensor data from NI-DAQ
"""

import wx
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from game_page import GamePage, SharedStats
from sensor_reader import SensorReader


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
                    "• Verify device name is 'Dev2' in NI MAX\n"
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
        
        # Create game page
        try:
            self.game_page = GamePage(self, self.shared_state)
            print("✅ Game page created")
        except Exception as e:
            print(f"❌ Failed to create game page: {e}")
            import traceback
            traceback.print_exc()
            wx.MessageBox(
                f"Failed to create game page:\n{e}",
                "Initialization Error",
                wx.OK | wx.ICON_ERROR
            )
            sys.exit(1)
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.game_page, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        print("\n" + "=" * 60)
        print("▶️  Game launched with live sensor data")
        print("=" * 60)
        print("\nStatus:")
        if self.sensor_reader.is_connected:
            print("  ✅ Hardware connected")
        else:
            print("  ⚠️  Hardware not connected - check console for errors")
        print("\nControls:")
        print("  • Close: Click window close button or Back button")
        print("  • Data updates every 100ms (10 Hz)")
        print("\n")
    
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
            print("❌ Cannot start game - hardware not connected")
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

