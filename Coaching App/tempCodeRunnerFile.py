
        self.frame = MainFrame(None, title="FES-Rowing App")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# ------------------------------------------------------------------------------------------------------------

class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MainFrame, self).__init__(*args, **kw)
        
