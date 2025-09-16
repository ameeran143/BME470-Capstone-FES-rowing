# start page
import wx
from button import CustomButton

class StartPage(wx.Panel):
    def __init__(self, parent):
        super(StartPage, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(45, 97, 181))

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # title
        title = wx.StaticText(self, label="FES-ROWING")
        title_font = wx.Font(110, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(255, 255, 255))
        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        title_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)
        main_sizer.Add(title_sizer, 0, wx.ALIGN_CENTER | wx.TOP, 80)

        # buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.manual_button = CustomButton(self, label="\nManual Mode\n", size=(400, 120), font=40, handler=self.on_start_game)
        self.auto_button = CustomButton(self, label="\nAutodrive Mode\n", size=(400, 120), font=40, handler=self.on_start_game)
        button_sizer.Add(self.manual_button, 0, wx.ALIGN_CENTER | wx.ALL, 50)
        button_sizer.Add(self.auto_button, 0, wx.ALIGN_CENTER | wx.ALL, 50)
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 30)
        self.calib_button = CustomButton(self, label="\nCalibration\n", size=(400, 120), font=40, handler=self.on_calib)
        main_sizer.Add(self.calib_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 50)

        self.SetSizer(main_sizer)

        #self.manual_button.Disable()
        self.auto_button.Disable()

    def on_start_game(self, event):
        parent = self.GetParent()

        parent.game_page.shared_state.stop_writing_stats()
        parent.game_page.shared_state.create_stats_file()

        parent.game_page.reset_game()
        parent.switch_to_game_page()
    
    def on_calib(self, event):
        parent = self.GetParent()
        parent.game_page.shared_state.stop_writing_stats()
        parent.switch_to_calib_page()