import wx
from button import CustomButton
from PIL import Image
import os


class CalibPage(wx.Panel):
    """Calibration UI with non-blocking 10s front/back timers and visual progress.

    - Shows user fields and Begin button.
    - When Begin pressed: runs FRONT 10s then BACK 10s using wx.Timer.
    - Highlights exact instruction+image area with a green rectangle (based on control positions).
    - Shows a horizontal progress bar for the active phase.
    """

    PHASE_IDLE = 0
    PHASE_FRONT = 1
    PHASE_BACK = 2

    def __init__(self, parent, shared_state):
        super().__init__(parent)
        self.shared_state = shared_state
        self.phase = self.PHASE_IDLE
        self.buffer_duration = 5.0   # seconds of transition/buffer per phase
        self.collect_duration = 5.0  # seconds of data collection per phase
        self.phase_duration = self.buffer_duration + self.collect_duration
        self.phase_elapsed = 0.0
        self.subphase = None  # 'buffer' or 'collect'

        # Visual style
        self.bg_color = wx.Colour(248, 249, 250)
        self.label_color = wx.Colour(64, 64, 64)
        self.SetBackgroundColour(self.bg_color)

        # Layout
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)

        label_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_MEDIUM)
        input_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        # User inputs
        uid_lbl = wx.StaticText(self, label="User ID:")
        uid_lbl.SetFont(label_font)
        uid_lbl.SetForegroundColour(self.label_color)
        input_sizer.Add(uid_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        self.user_id_input = wx.TextCtrl(self, size=(220, -1))
        self.user_id_input.SetFont(input_font)
        self.user_id_input.SetBackgroundColour(wx.WHITE)
        self.user_id_input.SetForegroundColour(self.label_color)
        input_sizer.Add(self.user_id_input, 0, wx.ALIGN_CENTER | wx.ALL, 7)

        age_lbl = wx.StaticText(self, label="Age:")
        age_lbl.SetFont(label_font)
        age_lbl.SetForegroundColour(self.label_color)
        input_sizer.Add(age_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        self.age_input = wx.TextCtrl(self, size=(100, -1))
        self.age_input.SetFont(input_font)
        self.age_input.SetBackgroundColour(wx.WHITE)
        self.age_input.SetForegroundColour(self.label_color)
        input_sizer.Add(self.age_input, 0, wx.ALIGN_CENTER | wx.ALL, 7)

        h_lbl = wx.StaticText(self, label="Height (cm):")
        h_lbl.SetFont(label_font)
        h_lbl.SetForegroundColour(self.label_color)
        input_sizer.Add(h_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        self.height_input = wx.TextCtrl(self, size=(120, -1))
        self.height_input.SetFont(input_font)
        self.height_input.SetBackgroundColour(wx.WHITE)
        self.height_input.SetForegroundColour(self.label_color)
        input_sizer.Add(self.height_input, 0, wx.ALIGN_CENTER | wx.ALL, 7)

        w_lbl = wx.StaticText(self, label="Weight (kg):")
        w_lbl.SetFont(label_font)
        w_lbl.SetForegroundColour(self.label_color)
        input_sizer.Add(w_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 7)
        self.weight_input = wx.TextCtrl(self, size=(120, -1))
        self.weight_input.SetFont(input_font)
        self.weight_input.SetBackgroundColour(wx.WHITE)
        self.weight_input.SetForegroundColour(self.label_color)
        input_sizer.Add(self.weight_input, 0, wx.ALIGN_CENTER | wx.ALL, 7)

        # Submit
        self.submit_button = CustomButton(self, label="\nSubmit\n", size=(140, 50), font=25, handler=self.on_submit)
        input_sizer.Add(self.submit_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.main_sizer.Add(input_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # Begin calibration
        self.begin_button = CustomButton(self, label="\nBegin Calibration\n", size=(360, 60), font=30, handler=self.on_begin)
        self.main_sizer.Add(self.begin_button, 0, wx.ALIGN_CENTER)

        # Instructions and images in a vertical sizer so we can compute their bounding boxes
        self.instr_sizer = wx.BoxSizer(wx.VERTICAL)

        self.instr1_label = wx.StaticText(self, label="Compress your legs to the best of your abilities, with your feet remaining flat")
        self.instr1_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.instr1_label.SetForegroundColour(self.label_color)
        self.instr_sizer.Add(self.instr1_label, 0, wx.ALIGN_CENTER | wx.ALL, 12)

        # compress image
        self.img1_ctrl = None
        img_path = os.path.join(os.path.dirname(__file__), "assets", "images", "compress.jpg")
        if os.path.exists(img_path):
            img = Image.open(img_path).resize((360, 200))
            wximg = wx.Image(img.size[0], img.size[1])
            wximg.SetData(img.convert('RGB').tobytes())
            self.img1_ctrl = wx.StaticBitmap(self, -1, wx.Bitmap(wximg))
            self.instr_sizer.Add(self.img1_ctrl, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        else:
            # spacer if missing
            self.instr_sizer.AddSpacer(220)

        # progress bar for the front phase (placed under image 1)
        self.phase_gauge_front = wx.Gauge(self, range=100, size=(420, 24))
        self.phase_gauge_front.SetValue(0)
        # make gauge background and bar color more visible
        try:
            self.phase_gauge_front.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.phase_gauge_front.SetForegroundColour(wx.Colour(60, 180, 75))
        except Exception:
            pass
        self.instr_sizer.Add(self.phase_gauge_front, 0, wx.ALIGN_CENTER | wx.ALL, 8)
        self.phase_label_front = wx.StaticText(self, label="Front: 5s transitioning + 5s collect")
        self.phase_label_front.SetForegroundColour(self.label_color)
        self.phase_label_front.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.instr_sizer.Add(self.phase_label_front, 0, wx.ALIGN_CENTER | wx.BOTTOM, 6)

        # second instruction
        self.instr2_label = wx.StaticText(self, label="Extend your legs to the best of your abilities, with your feet remaining flat")
        self.instr2_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.instr2_label.SetForegroundColour(self.label_color)
        self.instr_sizer.Add(self.instr2_label, 0, wx.ALIGN_CENTER | wx.ALL, 12)

        self.img2_ctrl = None
        img2_path = os.path.join(os.path.dirname(__file__), "assets", "images", "extend.jpg")
        if os.path.exists(img2_path):
            img2 = Image.open(img2_path).resize((360, 200))
            wximg2 = wx.Image(img2.size[0], img2.size[1])
            wximg2.SetData(img2.convert('RGB').tobytes())
            self.img2_ctrl = wx.StaticBitmap(self, -1, wx.Bitmap(wximg2))
            self.instr_sizer.Add(self.img2_ctrl, 0, wx.ALIGN_CENTER | wx.ALL, 10)

            # progress bar for the back phase (placed under image 2)
            self.phase_gauge_back = wx.Gauge(self, range=100, size=(420, 24))
            self.phase_gauge_back.SetValue(0)
            try:
                self.phase_gauge_back.SetBackgroundColour(wx.Colour(240, 240, 240))
                self.phase_gauge_back.SetForegroundColour(wx.Colour(60, 180, 75))
            except Exception:
                pass
            self.instr_sizer.Add(self.phase_gauge_back, 0, wx.ALIGN_CENTER | wx.ALL, 8)
            self.phase_label_back = wx.StaticText(self, label="Back: 5s transitioning + 5s collect")
            self.phase_label_back.SetForegroundColour(self.label_color)
            self.phase_label_back.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            self.instr_sizer.Add(self.phase_label_back, 0, wx.ALIGN_CENTER | wx.BOTTOM, 6)
        else:
            # spacer if missing
            self.instr_sizer.AddSpacer(220)

        self.main_sizer.Add(self.instr_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # back button
        self.back_button = CustomButton(self, label="\nBack\n", size=(120, 60), font=30, handler=self.on_back)
        self.main_sizer.Add(self.back_button, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(self.main_sizer)

        # Timer for phase updates (fires every 100ms)
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.update_timer)

        # Bind paint to draw highlights
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def on_submit(self, event):
        # validate minimal inputs
        if not self.user_id_input.GetValue():
            wx.MessageBox("Please enter a User ID", "Info", wx.OK | wx.ICON_INFORMATION)
            return
        # store into shared_state
        self.shared_state.userID = self.user_id_input.GetValue()
        try:
            self.shared_state.age = int(self.age_input.GetValue())
        except Exception:
            self.shared_state.age = 0
        try:
            self.shared_state.height = int(self.height_input.GetValue())
        except Exception:
            self.shared_state.height = 0
        try:
            self.shared_state.weight = int(self.weight_input.GetValue())
        except Exception:
            self.shared_state.weight = 0

        self.begin_button.Enable()
        self.submit_button.Disable()

    def on_begin(self, event):
        # start front phase
        if self.phase != self.PHASE_IDLE:
            return
        self.phase = self.PHASE_FRONT
        self.phase_elapsed = 0.0
        self.subphase = 'buffer'
        # ensure both gauges exist (create fallback if images missing)
        if not hasattr(self, 'phase_gauge_front'):
            self.phase_gauge_front = wx.Gauge(self, range=100, size=(420, 24))
            self.phase_gauge_front.SetValue(0)
            self.phase_label_front = wx.StaticText(self, label="Front: 5s transitioning + 5s collect")
            self.phase_label_front.SetForegroundColour(self.label_color)
            try:
                self.phase_gauge_front.SetBackgroundColour(wx.Colour(240, 240, 240))
                self.phase_gauge_front.SetForegroundColour(wx.Colour(60, 180, 75))
            except Exception:
                pass
        if not hasattr(self, 'phase_gauge_back'):
            self.phase_gauge_back = wx.Gauge(self, range=100, size=(420, 24))
            self.phase_gauge_back.SetValue(0)
            self.phase_label_back = wx.StaticText(self, label="Back: 5s transitioning + 5s collect")
            self.phase_label_back.SetForegroundColour(self.label_color)
            try:
                self.phase_gauge_back.SetBackgroundColour(wx.Colour(240, 240, 240))
                self.phase_gauge_back.SetForegroundColour(wx.Colour(60, 180, 75))
            except Exception:
                pass
        # disable begin button while running
        try:
            self.begin_button.Disable()
        except Exception:
            pass
        self.update_timer.Start(100)  # 100 ms updates

    def on_timer(self, event):
        self.phase_elapsed += 0.1

        # Determine current subphase duration and update UI accordingly
        if self.subphase == 'buffer':
            current_duration = self.buffer_duration
            frac = 0.0  # no progress bar during buffer
        else:
            current_duration = self.collect_duration
            frac = min(1.0, self.phase_elapsed / current_duration)

        remaining = max(0, int(current_duration - self.phase_elapsed))

        # Update UI elements depending on phase and subphase
        if self.phase == self.PHASE_FRONT:
            if self.subphase == 'buffer':
                # Buffer countdown label, no gauge progress
                if hasattr(self, 'phase_label_front'):
                    self.phase_label_front.SetLabel(f"Front (transitioning): {remaining}s")
                self.phase_gauge_front.SetValue(0)
            else:
                # Collection progress and label
                self.phase_gauge_front.SetValue(int(frac * 100))
                if hasattr(self, 'phase_label_front'):
                    self.phase_label_front.SetLabel(f"Front (collect): {remaining}s")
        elif self.phase == self.PHASE_BACK:
            if self.subphase == 'buffer':
                if hasattr(self, 'phase_label_back'):
                    self.phase_label_back.SetLabel(f"Back (transitioning): {remaining}s")
                self.phase_gauge_back.SetValue(0)
            else:
                self.phase_gauge_back.SetValue(int(frac * 100))
                if hasattr(self, 'phase_label_back'):
                    self.phase_label_back.SetLabel(f"Back (collect): {remaining}s")
        self.Refresh()  # triggers OnPaint to update highlight

        # Handle subphase and phase transitions
        if self.phase_elapsed >= current_duration:
            if self.subphase == 'buffer':
                # Move to collection subphase for the same phase
                self.subphase = 'collect'
                self.phase_elapsed = 0.0
            else:
                # Collection complete for current phase
                if self.phase == self.PHASE_FRONT:
                    # record front position at end of collection
                    if hasattr(self.shared_state, 'raw_seat_pos') and self.shared_state.raw_seat_pos:
                        self.shared_state.front_max_pos = self.shared_state.raw_seat_pos[-1]
                        self.shared_state.fes_active_pos = self.shared_state.front_max_pos - 96.5
                    # start back phase with buffer
                    self.phase = self.PHASE_BACK
                    self.subphase = 'buffer'
                    self.phase_elapsed = 0.0
                    # clear front gauge when moving to back
                    if hasattr(self, 'phase_gauge_front'):
                        self.phase_gauge_front.SetValue(0)
                    if hasattr(self, 'phase_label_back'):
                        self.phase_label_back.SetLabel("Back (transitioning): 5s")
                elif self.phase == self.PHASE_BACK:
                    # record back position at end of collection
                    if hasattr(self.shared_state, 'raw_seat_pos') and self.shared_state.raw_seat_pos:
                        self.shared_state.back_max_pos = self.shared_state.raw_seat_pos[-1]
                        if self.shared_state.back_max_pos != self.shared_state.front_max_pos:
                            self.shared_state.converted_fes_pos = 100 - (self.shared_state.fes_active_pos - self.shared_state.front_max_pos) / (self.shared_state.back_max_pos - self.shared_state.front_max_pos) * 100
                    # stop after back collection
                    self.phase = self.PHASE_IDLE
                    self.subphase = None
                    self.update_timer.Stop()
                    self.begin_button.Disable()
                    # clear both gauges and reset labels
                    self.phase_gauge_front.SetValue(0)
                    self.phase_gauge_back.SetValue(0)
                    if hasattr(self, 'phase_label_front'):
                        self.phase_label_front.SetLabel("Front: 5s transitioning + 5s collect")
                    if hasattr(self, 'phase_label_back'):
                        self.phase_label_back.SetLabel("Back: 5s transitioning + 5s collect")
                    wx.MessageBox("Calibration complete", "Info", wx.OK | wx.ICON_INFORMATION)

    def OnPaint(self, event):
        # default paint to preserve controls
        dc = wx.PaintDC(self)
        # draw highlight depending on phase around the active instruction+image
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(wx.Colour(210, 242, 121), 6))

        if self.phase == self.PHASE_FRONT:
            # compute bounding box for instr1_label + img1_ctrl
            rect = self._get_widget_area(self.instr1_label, self.img1_ctrl)
            if rect:
                dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)

        elif self.phase == self.PHASE_BACK:
            rect = self._get_widget_area(self.instr2_label, self.img2_ctrl)
            if rect:
                dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)

    def _get_widget_area(self, label_ctrl, img_ctrl):
        """Return a wx.Rect bounding the label and image, in panel coordinates."""
        try:
            # label pos and size
            lx, ly = label_ctrl.GetPosition()
            lw, lh = label_ctrl.GetSize()
            top = ly
            left = lx
            right = lx + lw
            bottom = ly + lh

            if img_ctrl is not None:
                ix, iy = img_ctrl.GetPosition()
                iw, ih = img_ctrl.GetSize()
                # include image area
                left = min(left, ix)
                right = max(right, ix + iw)
                bottom = max(bottom, iy + ih)

            width = right - left + 12
            height = bottom - top + 12
            return wx.Rect(left - 6, top - 6, width, height)
        except Exception:
            return None

    def on_back(self, event):
        parent = self.GetParent()
        parent.switch_to_start_page()
        self.reset()

    def reset(self):
        self.phase = self.PHASE_IDLE
        self.subphase = None
        if self.update_timer.IsRunning():
            self.update_timer.Stop()
        self.submit_button.Enable()
        self.begin_button.Enable()
        # reset both gauges
        if hasattr(self, 'phase_gauge_front'):
            self.phase_gauge_front.SetValue(0)
        if hasattr(self, 'phase_gauge_back'):
            self.phase_gauge_back.SetValue(0)
        if hasattr(self, 'phase_label_front'):
            self.phase_label_front.SetLabel("Front: 5s transitioning + 5s collect")
        if hasattr(self, 'phase_label_back'):
            self.phase_label_back.SetLabel("Back: 5s transitioning + 5s collect")
