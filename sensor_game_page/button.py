# button class
import wx

class CustomButton(wx.Button):
    def __init__(self, parent, label, size, font, handler):
        super(CustomButton, self).__init__(parent, label=label, size=size)
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.SetForegroundColour(wx.Colour(0, 0, 0))
        self.SetFont(wx.Font(font, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.Bind(wx.EVT_BUTTON, handler)
        self.default_background_colour = self.GetBackgroundColour()
        self.disabled_background_colour = wx.Colour(128, 128, 128)
    
    def Disable(self):
        super(CustomButton, self).Disable()
        self.SetBackgroundColour(self.disabled_background_colour)
        self.Refresh()
    
    def Enable(self, enable=True):
        super(CustomButton, self).Enable(enable)
        if enable:
            self.SetBackgroundColour(self.default_background_colour)
        self.Refresh()