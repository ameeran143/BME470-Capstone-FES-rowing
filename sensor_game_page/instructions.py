# how-to-play page
import wx
from button import CustomButton

class InstructionsPage(wx.Panel):
    def __init__(self, parent):
        super(InstructionsPage, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(248, 249, 250))

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self, label="Tutorial")
        title.SetFont(wx.Font(60, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        main_sizer.Add(title, 0, wx.ALL, 30)

        # Content placeholder
        body = wx.StaticText(self, label=(
            "Learn how to use the app. This is a placeholder tutorial.\n\n"
            "- Automatic Mode: System assists your rowing.\n"
            "- Manual Mode: Practice timing with FES indicator.\n"
            "- Calibration: Configure your seat range and FES timing."
        ))
        body.SetFont(wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        body.SetForegroundColour(wx.Colour(73, 80, 87))
        main_sizer.Add(body, 0, wx.LEFT | wx.RIGHT, 30)

        main_sizer.AddStretchSpacer()

        # Back button
        back_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.back_btn = CustomButton(self, label="\u2190  Back", size=(180, 70), font=24, handler=self.on_back)
        back_bar.Add(self.back_btn, 0, wx.LEFT | wx.BOTTOM, 20)
        back_bar.AddStretchSpacer()
        main_sizer.Add(back_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        self.SetSizer(main_sizer)

    def on_back(self, event):
        parent = self.GetParent()
        parent.switch_to_start_page()

