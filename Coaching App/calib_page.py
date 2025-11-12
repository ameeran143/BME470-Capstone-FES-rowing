import wx
from button import CustomButton
from PIL import Image
import os
import json
import time
import platform
try:
    import nidaqmx
except ImportError:
    nidaqmx = None


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
        
        # Hardware configuration (same as game_page.py)
        self.is_mac = platform.system() == 'Darwin'
        self.volts_to_mm_factor = 2032.0 / 10.0  # Conversion factor for potentiometers (same as game_page.py)
        self.calib_seat_positions = []  # Store seat positions during calibration
        self.all_calib_positions = []  # Store all positions (front + back) for zero-shifting

        # Visual style
        self.bg_color = wx.Colour(248, 249, 250)
        self.label_color = wx.Colour(64, 64, 64)
        self.SetBackgroundColour(self.bg_color)

        # Layout
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Begin calibration button (enabled from the start)
        self.begin_button = CustomButton(self, label="\nBegin Calibration\n", size=(360, 60), font=30, handler=self.on_begin)
        self.main_sizer.Add(self.begin_button, 0, wx.ALIGN_CENTER | wx.ALL, 20)

        # Instructions and images in a vertical sizer so we can compute their bounding boxes
        self.instr_sizer = wx.BoxSizer(wx.VERTICAL)

        self.instr1_label = wx.StaticText(self, label="Compress your legs to the best of your abilities, with your feet remaining flat")
        self.instr1_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.instr1_label.SetForegroundColour(self.label_color)
        self.instr_sizer.Add(self.instr1_label, 0, wx.ALIGN_CENTER | wx.ALL, 12)

        # compress image
        self.img1_ctrl = None
        img_path = os.path.join(os.path.dirname(__file__), "compress.jpg")
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
        img2_path = os.path.join(os.path.dirname(__file__), "extend.jpg")
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

    def read_seat_position_hardware(self):
        """Read seat position from hardware using same channel and conversion as game_page.py.
        Returns seat position in mm, or None if hardware not available.
        """
        if self.is_mac or nidaqmx is None:
            return None
        
        try:
            with nidaqmx.Task() as task:
                # Use same channel configuration as game_page.py: Dev2/ai22 for seat position
                task.ai_channels.add_ai_voltage_chan("Dev2/ai22",
                                                     terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                     min_val=0.0, max_val=10.0)
                data = task.read(number_of_samples_per_channel=1)
                
                # Extract voltage value
                seat_voltage = data[0] if isinstance(data, list) else data
                
                # Convert voltage to mm using same conversion factor as game_page.py
                seat_position_mm = seat_voltage * self.volts_to_mm_factor
                
                return seat_position_mm
        except Exception as e:
            print(f"Hardware read error during calibration: {e}")
            return None
    
    def on_timer(self, event):
        self.phase_elapsed += 0.1

        # Read seat position from hardware during collection phase
        if self.subphase == 'collect':
            seat_pos_mm = self.read_seat_position_hardware()
            if seat_pos_mm is not None:
                # Store seat position for calibration
                self.calib_seat_positions.append(seat_pos_mm)
                self.all_calib_positions.append(seat_pos_mm)  # Keep all positions for zero-shifting
                # Also update shared_state for compatibility
                if not hasattr(self.shared_state, 'raw_seat_pos'):
                    self.shared_state.raw_seat_pos = []
                self.shared_state.raw_seat_pos.append(seat_pos_mm)

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
                    # record front position at end of collection (use average of collected positions)
                    if self.calib_seat_positions:
                        # Calculate average seat position during front collection (in mm)
                        avg_front_pos_mm = sum(self.calib_seat_positions) / len(self.calib_seat_positions)
                        self.shared_state.front_max_pos = avg_front_pos_mm
                        print(f"Front position recorded: {avg_front_pos_mm:.2f} mm")
                        # Clear positions for back phase
                        self.calib_seat_positions = []
                    elif hasattr(self.shared_state, 'raw_seat_pos') and self.shared_state.raw_seat_pos:
                        # Fallback to shared_state if hardware read failed
                        self.shared_state.front_max_pos = self.shared_state.raw_seat_pos[-1]
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
                    # record back position at end of collection (use average of collected positions)
                    if self.calib_seat_positions:
                        # Calculate average seat position during back collection (in mm)
                        avg_back_pos_mm = sum(self.calib_seat_positions) / len(self.calib_seat_positions)
                        self.shared_state.back_max_pos = avg_back_pos_mm
                        print(f"Back position recorded: {avg_back_pos_mm:.2f} mm")
                    elif hasattr(self.shared_state, 'raw_seat_pos') and self.shared_state.raw_seat_pos:
                        # Fallback to shared_state if hardware read failed
                        self.shared_state.back_max_pos = self.shared_state.raw_seat_pos[-1]
                    
                    # Zero-shift both front and back positions by subtracting the back_max_pos (mean of back positions)
                    # This ensures back_max_pos becomes 0 after zero-shifting
                    zero_shift_reference = self.shared_state.back_max_pos
                    self.shared_state.front_max_pos = self.shared_state.front_max_pos - zero_shift_reference
                    self.shared_state.back_max_pos = self.shared_state.back_max_pos - zero_shift_reference
                    print(f"Zero-shifted front position: {self.shared_state.front_max_pos:.2f} mm")
                    print(f"Zero-shifted back position: {self.shared_state.back_max_pos:.2f} mm")
                    print(f"Calibration range: {self.shared_state.front_max_pos - self.shared_state.back_max_pos:.2f} mm")
                    
                    # Save calibration data to file
                    self.save_calibration_data()
                    
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

    def save_calibration_data(self):
        """Save calibration data (front_max_pos, back_max_pos) to a JSON file."""
        try:
            # Create Calibration_Data directory if it doesn't exist
            calib_dir = os.path.join(os.path.dirname(__file__), "Calibration_Data")
            os.makedirs(calib_dir, exist_ok=True)
            
            # Create filename based on timestamp
            filename = f"calibration_{time.strftime('%Y%m%d_%H%M%S')}.json"
            
            calib_file = os.path.join(calib_dir, filename)
            
            # Prepare calibration data (only calibration values, zero-shifted positions)
            calib_data = {
                "front_max_pos": self.shared_state.front_max_pos,
                "back_max_pos": self.shared_state.back_max_pos,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save to JSON file
            with open(calib_file, 'w') as f:
                json.dump(calib_data, f, indent=2)
            
            # Also save/update a "latest" calibration file
            latest_file = os.path.join(calib_dir, "calibration_latest.json")
            with open(latest_file, 'w') as f:
                json.dump(calib_data, f, indent=2)
            
            print(f"Calibration data saved to: {calib_file}")
        except Exception as e:
            print(f"Failed to save calibration data: {e}")
    
    def reset(self):
        self.phase = self.PHASE_IDLE
        self.subphase = None
        if self.update_timer.IsRunning():
            self.update_timer.Stop()
        self.begin_button.Enable()
        # Clear calibration data
        self.calib_seat_positions = []
        self.all_calib_positions = []
        # reset both gauges
        if hasattr(self, 'phase_gauge_front'):
            self.phase_gauge_front.SetValue(0)
        if hasattr(self, 'phase_gauge_back'):
            self.phase_gauge_back.SetValue(0)
        if hasattr(self, 'phase_label_front'):
            self.phase_label_front.SetLabel("Front: 5s transitioning + 5s collect")
        if hasattr(self, 'phase_label_back'):
            self.phase_label_back.SetLabel("Back: 5s transitioning + 5s collect")
