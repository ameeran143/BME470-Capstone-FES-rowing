# calibration page
import wx
from button import CustomButton
from PIL import Image
import time
import os

class CalibPage(wx.Panel):
    def __init__(self, parent, shared_state):
        super(CalibPage, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(45, 97, 181))
        self.shared_state = shared_state
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.state = "start"

        sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # User ID
        user_id_label = wx.StaticText(self, label="User ID:")
        user_id_label.SetForegroundColour(wx.Colour(0, 0, 0))
        input_sizer.Add(user_id_label, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        self.user_id_input = wx.TextCtrl(self, size=(150, -1))
        input_sizer.Add(self.user_id_input, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        
        # Age
        age_label = wx.StaticText(self, label="Age:")
        age_label.SetForegroundColour(wx.Colour(0, 0, 0))
        input_sizer.Add(age_label, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        self.age_input = wx.TextCtrl(self, size=(150, -1))
        input_sizer.Add(self.age_input, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        
        # Height
        height_label = wx.StaticText(self, label="Height (cm):")
        height_label.SetForegroundColour(wx.Colour(0, 0, 0))
        input_sizer.Add(height_label, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        self.height_input = wx.TextCtrl(self, size=(150, -1))
        input_sizer.Add(self.height_input, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        
        # Weight
        weight_label = wx.StaticText(self, label="Weight (kg):")
        weight_label.SetForegroundColour(wx.Colour(0, 0, 0))
        input_sizer.Add(weight_label, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        self.weight_input = wx.TextCtrl(self, size=(150, -1))
        input_sizer.Add(self.weight_input, 0, wx.ALIGN_CENTER | wx.ALL, 7)

        # Submit button
        self.submit_button = CustomButton(self, label="\nSubmit\n", size=(140, 50), font=25, handler=self.on_submit)
        input_sizer.Add(self.submit_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        sizer.Add(input_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # initialize begin button
        self.begin_button = CustomButton(self, label="\nBegin Calibration\n", size=(350, 60), font=30, handler=self.on_begin_button)
        sizer.Add(self.begin_button, 0, wx.ALIGN_CENTER)

        # instruction 1
        instruction1 = wx.StaticText(self, label="Compress your legs to the best of your abilities, with your feet remaining flat")
        ins_text = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        instruction1.SetFont(ins_text)
        instruction1.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(instruction1, 0, wx.ALIGN_CENTER | wx.ALL, 15)

        # image 1
        image_path = os.path.expanduser("~\OneDrive\Documents\FES Rowing\Coaching App\compress.jpg")
        # ~/Desktop/Game/new_game/compress.jpg
        img1 = Image.open(image_path)
        img1 = img1.resize((300, 160))
        img1_wx = wx.Image(img1.size[0], img1.size[1])
        img1_wx.SetData(img1.convert('RGB').tobytes())
        img1_bitmap = wx.StaticBitmap(self, -1, wx.Bitmap(img1_wx))
        sizer.Add(img1_bitmap, 0, wx.ALIGN_CENTER | wx.ALL, 15)

        # instruction 2
        instruction2 = wx.StaticText(self, label="Extend your legs to the best of your abilities, with your feet remaining flat")
        instruction2.SetFont(ins_text)
        instruction2.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(instruction2, 0, wx.ALIGN_CENTER | wx.ALL, 15)

        # image 2
        image_path = os.path.expanduser("~\OneDrive\Documents\FES Rowing\Coaching App\extend.jpg")
        # ~/Desktop/Game/new_game/extend.jpg
        img2 = Image.open(image_path)
        img2 = img2.resize((300, 160))
        img2_wx = wx.Image(img2.size[0], img2.size[1])
        img2_wx.SetData(img2.convert('RGB').tobytes())
        img2_bitmap = wx.StaticBitmap(self, -1, wx.Bitmap(img2_wx))
        sizer.Add(img2_bitmap, 0, wx.ALIGN_CENTER | wx.ALL, 15)

        # initialize back button
        self.back_button = CustomButton(self, label="\nBack\n", size=(120, 60), font=30, handler=self.on_back_button)
        sizer.Add(self.back_button, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        self.SetSizer(sizer)

        self.begin_button.Disable()
    
    def on_submit(self, event):
        if not self.user_id_input.GetValue() or not self.age_input.GetValue() or not self.height_input.GetValue() or not self.weight_input.GetValue():
            wx.MessageBox("Please ensure all fields are filled!", "Info", wx.OK | wx.ICON_INFORMATION)
            return
        
        self.shared_state.userID = self.user_id_input.GetValue()
        self.shared_state.age = int(self.age_input.GetValue())
        self.shared_state.height = int(self.height_input.GetValue())
        self.shared_state.weight = int(self.weight_input.GetValue())
        self.begin_button.Enable()

        self.Refresh()
        self.clear_fields()

        self.submit_button.Disable()
    
    def clear_fields(self):
        self.user_id_input.Clear()
        self.age_input.Clear()
        self.height_input.Clear()
        self.weight_input.Clear()
    
    def on_begin_button(self, event):
        # instruction 1
        self.state = "front"
        self.Refresh()
        wx.Yield()
        time.sleep(3)
        #self.shared_state.update_stats()
        self.shared_state.front_max_pos = self.shared_state.raw_seat_pos[-1]
        self.shared_state.fes_active_pos = self.shared_state.front_max_pos - 96.5

        # instruction 2
        self.state = "back"
        self.Refresh()
        wx.Yield()
        time.sleep(3)
        #self.shared_state.update_stats()
        self.shared_state.back_max_pos = self.shared_state.raw_seat_pos[-1]
        self.shared_state.converted_fes_pos = 100 - (self.shared_state.fes_active_pos - self.shared_state.front_max_pos) / (self.shared_state.back_max_pos - self.shared_state.front_max_pos) * 100
        self.Refresh()

        self.state = "start"
        self.Refresh()

        self.begin_button.Disable()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(wx.Colour(210, 242, 121), 7))
        if self.state == "front":
            dc.DrawRectangle(160, 160, 960, 50)
        if self.state == "back":
            dc.DrawRectangle(160, 410, 950, 50)

    def on_back_button(self, event):
        parent = self.GetParent()
        parent.switch_to_start_page()
        self.reset()
    
    def reset(self):
        self.state = "start"
        self.submit_button.Enable()
        self.clear_fields()
        self.Refresh()