# main
import wx
from start_page import StartPage
from calib_page import CalibPage
from game_page import GamePage
from game_page import SharedStats
from instructions import InstructionsPage
from session_summary import SessionSummaryPage
from dashboard import DashboardPage
from tutorial import GameTutorialPage

class RowingApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None, title="FES-Rowing App")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# ------------------------------------------------------------------------------------------------------------

class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MainFrame, self).__init__(*args, **kw)
        
        # Bind close event to cleanup hardware
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.shared_state = SharedStats()

        # Maximize the window to fullscreen automatically
        self.Maximize(True)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.dashboard_page = DashboardPage(self)
        self.start_page = StartPage(self)
        self.calib_page = CalibPage(self, self.shared_state)
        self.game_page = GamePage(self, self.shared_state)
        self.instructions_page = InstructionsPage(self)
        self.game_tutorial_page = GameTutorialPage(self)
        self.summary_page = None  # Will be created when needed
        
        self.sizer.Add(self.dashboard_page, 1, wx.EXPAND)
        self.sizer.Add(self.start_page, 1, wx.EXPAND)
        self.sizer.Add(self.calib_page, 1, wx.EXPAND)
        self.sizer.Add(self.game_page, 1, wx.EXPAND)
        self.sizer.Add(self.instructions_page, 1, wx.EXPAND)
        self.sizer.Add(self.game_tutorial_page, 1, wx.EXPAND)

        self.start_page.Hide()
        self.calib_page.Hide()
        self.game_page.Hide()
        self.instructions_page.Hide()
        self.game_tutorial_page.Hide()
        self.SetSizer(self.sizer)
        
        self.current_panel = self.dashboard_page

    def switch_to_calib_page(self):
        self.current_panel.Hide()
        self.calib_page.Show()
        self.current_panel = self.calib_page
        self.Refresh()
        self.Layout()

    def switch_to_dashboard(self):
        """Switch to dashboard page"""
        self.current_panel.Hide()
        # Hide summary page if it exists
        if self.summary_page is not None:
            self.summary_page.Hide()
        
        # Refresh dashboard data before showing (to update stats after sessions)
        self.dashboard_page.refresh_dashboard()
        
        self.dashboard_page.Show()
        self.current_panel = self.dashboard_page
        self.Refresh()
        self.Layout()
    
    def switch_to_start_page(self):
        self.current_panel.Hide()
        # Hide summary page if it exists
        if self.summary_page is not None:
            self.summary_page.Hide()
        
        # Force start page to get correct size before showing
        client_size = self.GetClientSize()
        self.start_page.SetSize(client_size)
        
        self.start_page.Show()
        self.current_panel = self.start_page
        
        # Force layout recalculation
        self.start_page.Layout()
        self.start_page.Refresh()
        
        # Send a size event to force proper layout
        size_event = wx.SizeEvent(self.start_page.GetSize())
        wx.PostEvent(self.start_page, size_event)
        
        self.Refresh()
        self.Layout()
    
    def switch_to_game_page(self):
        self.current_panel.Hide()
        # Hide summary page if it exists
        if self.summary_page is not None:
            self.summary_page.Hide()
        
        # Reset CSV playback to beginning when switching to game page
        if hasattr(self.game_page, 'shared_state') and self.game_page.shared_state.anc_playback_mode:
            self.game_page.shared_state.anc_index = 0
            self.game_page.shared_state.anc_playback_start_time = None
        
        self.game_page.Show()
        self.current_panel = self.game_page
        self.Refresh()
        self.Layout()
        # Ensure game page can receive keyboard events for button press detection
        # Make sure frame can accept focus and set it
        self.SetCanFocus(True)
        wx.CallAfter(self.SetFocus)  # Focus the frame itself

    def switch_to_instructions_page(self):
        self.current_panel.Hide()
        self.instructions_page.Show()
        self.current_panel = self.instructions_page
        self.Refresh()
        self.Layout()
    
    def switch_to_summary_page(self, summary_data):
        """Switch to session summary page with summary data"""
        # Hide current panel first
        self.current_panel.Hide()
        
        # Clean up old summary page if it exists
        if self.summary_page is not None:
            try:
                self.sizer.Remove(self.summary_page)
                self.summary_page.Destroy()
            except:
                pass  # If already destroyed, ignore
            self.summary_page = None
        
        # Create new summary page
        self.summary_page = SessionSummaryPage(self, summary_data)
        self.sizer.Add(self.summary_page, 1, wx.EXPAND)
        
        # Show summary page
        self.summary_page.Show()
        self.current_panel = self.summary_page
        self.Refresh()
        self.Layout()
    
    def switch_to_game_tutorial(self):
        self.current_panel.Hide()
        # <<< Reset tutorial state on entry
        self.game_tutorial_page.step = 0
        self.game_tutorial_page.show_step()
        
        self.game_tutorial_page.Show()
        self.current_panel = self.game_tutorial_page
        self.Refresh()
        self.Layout()

    def OnClose(self, event):
        """Handle application close event - cleanup hardware resources"""
        if hasattr(self, 'shared_state'):
            self.shared_state.cleanup_hardware()
        event.Skip()  # Allow normal close process to continue


if __name__ == "__main__":
    app = RowingApp(False)
    app.MainLoop()
