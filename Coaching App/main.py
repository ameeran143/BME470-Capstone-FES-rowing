# main
import wx
from start_page import StartPage
from calib_page_new import CalibPage
from game_page import GamePage
from game_page import SharedStats
from instructions import InstructionsPage
from session_summary import SessionSummaryPage

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

        display = wx.Display()
        screen_geometry = display.GetGeometry()
        screen_width, screen_height = screen_geometry.width, screen_geometry.height
        frame_width = int(screen_width * 0.95)
        frame_height = int(screen_height * 0.95)
        self.SetSize(frame_width, frame_height)
        self.Centre()
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.start_page = StartPage(self)
        self.calib_page = CalibPage(self, self.shared_state)
        self.game_page = GamePage(self, self.shared_state)
        self.instructions_page = InstructionsPage(self)
        self.summary_page = None  # Will be created when needed
        
        self.sizer.Add(self.start_page, 1, wx.EXPAND)
        self.sizer.Add(self.calib_page, 1, wx.EXPAND)
        self.sizer.Add(self.game_page, 1, wx.EXPAND)
        self.sizer.Add(self.instructions_page, 1, wx.EXPAND)
        
        self.calib_page.Hide()
        self.game_page.Hide()
        self.instructions_page.Hide()
        
        self.SetSizer(self.sizer)
        
        self.current_panel = self.start_page

    def switch_to_calib_page(self):
        self.current_panel.Hide()
        self.calib_page.Show()
        self.current_panel = self.calib_page
        self.Refresh()
        self.Layout()

    def switch_to_start_page(self):
        self.current_panel.Hide()
        self.start_page.Show()
        self.current_panel = self.start_page
        self.start_page.manual_button.Enable()
        #self.start_page.auto_button.Enable()
        self.Refresh()
        self.Layout()
    
    def switch_to_game_page(self):
        self.current_panel.Hide()
        self.game_page.Show()
        self.current_panel = self.game_page
        self.Refresh()
        self.Layout()

    def switch_to_instructions_page(self):
        self.current_panel.Hide()
        self.instructions_page.Show()
        self.current_panel = self.instructions_page
        self.Refresh()
        self.Layout()
    
    def switch_to_summary_page(self, summary_data):
        """Switch to session summary page with summary data"""
        # Create summary page if it doesn't exist or recreate it
        if self.summary_page is not None:
            self.sizer.Remove(self.summary_page)
            self.summary_page.Destroy()
        
        self.summary_page = SessionSummaryPage(self, summary_data)
        self.sizer.Add(self.summary_page, 1, wx.EXPAND)
        
        self.current_panel.Hide()
        self.summary_page.Show()
        self.current_panel = self.summary_page
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
