# main
import wx
from start_page import StartPage
from calib_page import CalibPage
from game_page import GamePage
from game_page import SharedStats

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
        
        self.sizer.Add(self.start_page, 1, wx.EXPAND)
        self.sizer.Add(self.calib_page, 1, wx.EXPAND)
        self.sizer.Add(self.game_page, 1, wx.EXPAND)
        
        self.calib_page.Hide()
        self.game_page.Hide()
        
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


if __name__ == "__main__":
    app = RowingApp(False)
    app.MainLoop()
