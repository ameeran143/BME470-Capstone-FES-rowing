#!/usr/bin/env python3
"""
Standalone Test Launcher for Real Data Playback
This script launches the game page with recorded rowing data
"""

import wx
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from game_page import GamePage, SharedStats
from data_playback import DataPlayback


class TestFrame(wx.Frame):
    def __init__(self):
        super(TestFrame, self).__init__(None, title="FES Rowing - Real Data Test", size=(1200, 900))
        
        # Center the window
        self.Centre()
        
        # Initialize playback data source
        data_file_path = os.path.join(os.path.dirname(__file__), "../Data_Analysis/rowing_data/rowing01.ANC")
        
        print("=" * 60)
        print("🧪 REAL DATA TESTING MODE")
        print("=" * 60)
        
        try:
            self.playback = DataPlayback(data_file_path)
            self.playback.start()
            print("✅ Playback initialized and started")
        except Exception as e:
            print(f"❌ Failed to load playback data: {e}")
            wx.MessageBox(f"Failed to load data file:\n{e}", 
                         "Error", wx.OK | wx.ICON_ERROR)
            sys.exit(1)
        
        # Create shared state with playback mode
        self.shared_state = SharedStats(playback_mode=True, playback_source=self.playback)
        
        # Create game page
        self.game_page = GamePage(self, self.shared_state)
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.game_page, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        print("\n" + "=" * 60)
        print("▶️  Game launched with real data playback")
        print("=" * 60)
        print("\nControls:")
        print("  • Pause/Play: Click pause button in playback panel")
        print("  • Reset: Click reset button to restart from beginning")
        print("  • Close: Click window close button or Back button")
        print("\n")
    
    def on_close(self, event):
        """Handle window close event"""
        print("\n👋 Closing test application...")
        self.Destroy()


def main():
    """Main entry point"""
    app = wx.App(False)
    frame = TestFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()

