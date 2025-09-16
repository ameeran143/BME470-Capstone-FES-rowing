# game page
import os
import wx
import time
import wx.grid as gridlib
from button import CustomButton
import nidaqmx
# import pygame
import csv

#Correct_Sound = pygame.mixer.Sound("Correct_Sound.wav")
#Wrong_Sound = pygame.mixer.Sound("Wrong_Sound.wav")

class SharedStats:
    def __init__(self):
        # stats table
        self.time_elapsed = 0
        self.time_start = time.time()
        self.temp_power = []
        self.avg_power = []
        self.stroke_rate = []
        self.score = 0
        self.misses = 0

        # sensor data
        self.handle_force = []
        self.handle_position = []
        self.raw_seat_pos = []  # raw collected seat position at each time point
        self.converted_seat_position = []  # converted seat position at each time point
        self.L_foot_force = []
        self.R_foot_force = []
        self.switch_press = []  # off = 5V, on = 0V
        self.stroke_time = []  # start time of each stroke
        self.stroke_duration = []

        # FES button
        self.is_pressed = False
        self.loading_phase = 0  # 0 for orange, 1 for green
        self.button_press_seat_pos = []  # store seat position at button-press
        self.msg = False

        # for calibration
        self.front_max_pos = 520  # fake data equal 100
        self.back_max_pos = 43  # fake data equal 0
        self.fes_active_pos = self.front_max_pos - 96.5 # constant (different for each user)
        self.seat_direction = 0  # fake data
        self.converted_fes_pos = 100 - (self.fes_active_pos - self.front_max_pos) / (self.back_max_pos - self.front_max_pos) * 100
        self.userID = None
        self.age = 0
        self.height = 0
        self.weight = 0
        self.same_stroke = False

        # File to store stats
        self.stats_file_path = None
    
    def convert_raw_to_scale(self, raw_pos):
        if raw_pos:
            converted = 100 - (raw_pos - self.front_max_pos) / (self.back_max_pos - self.front_max_pos) * 100
            return converted
        return None
    
    def convert_scale_to_raw(self, converted):
        if converted is not None:
            raw_pos = self.front_max_pos + (100 - converted) / 100 * (self.back_max_pos - self.front_max_pos)
            return raw_pos
        return None
        
    def create_stats_file(self):
        filename = f"{self.userID}_rowing_stats_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        self.stats_file_path = os.path.join(os.path.expanduser("~\OneDrive\Documents\FES Rowing\Coaching App\Training_Data"), filename)
        # ~/Desktop/Game/new_game/Training_Data
        
        with open(self.stats_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time Elapsed (min)", "Stroke Rate", "Average Power", "Score", "Misses", "Handle Force", "Handle Position", "Raw Seat Position", "Converted Seat Position", "Left Foot Force", "Right Foot Force"])

    def update_stats(self):
        # update time
        self.time_elapsed = int(time.time() - self.time_start) / 60

        '''
        with nidaqmx.Task() as task:
                task.ai_channels.add_ai_voltage_chan("Dev4/ai0:7")  
                data = task.read(number_of_samples_per_channel=1)
                self.pos = data[7][-1]*100
                
                self.raw_seat_pos.append(self.pos)
                self.handle_position.append(data[6][-1])
                self.handle_force.append(data[5][-1])
                self.L_foot_force.append(data[2][-1])
                self.R_foot_force.append(data[4][-1])
                self.switch_press.append(data[0][-1])
                self.temp_time.append(time.time())

        # update power (need to verify)
        if len(self.raw_seat_pos) > 1:
            self.temp_power.append(((self.handle_force[-1]+self.handle_force[-2])/2)*abs(self.handle_position[-1]-self.handle_position[-2])/(self.temp_time[-1]-self.temp_time[-2]))
            self.avg_power.append(sum(self.temp_power[-1])/len(self.temp_power))
        '''

        # update stroke rate
        if self.raw_seat_pos:
            if self.raw_seat_pos[-1] >= self.front_max_pos:
                self.stroke_time.append(time.time())
            if len(self.stroke_time) > 1:
                self.stroke_duration.append(self.stroke_time[-1] - self.stroke_time[-2])
                self.stroke_rate.append(60/round(self.stroke_duration[-1]))

        # convert raw seat position to 0-100 scale
        if self.raw_seat_pos:
            if self.raw_seat_pos[-1] <= self.back_max_pos:
                self.raw_seat_pos[-1] = self.back_max_pos
            elif self.raw_seat_pos[-1] >= self.front_max_pos:
                self.raw_seat_pos[-1] = self.front_max_pos
            self.converted_seat_position.append(self.convert_raw_to_scale(self.raw_seat_pos[-1]))
        
        # update score and misses
        if self.converted_seat_position:
            if self.converted_seat_position[-1] <= 0:
                self.same_stroke = False
        
        if len(self.switch_press) > 1:
            if self.switch_press[-1] == 5 and self.switch_press[-2] == 0:  # button needs to be held pressed -> 5V
                self.button_press_seat_pos.append(self.raw_seat_pos[-1])
                print("button press seat pos", self.button_press_seat_pos[-1])
                if self.fes_active_pos - 93.3 <= self.button_press_seat_pos[-1] <= self.fes_active_pos + 93.3 and self.is_pressed:
                    self.score += 1
                    #Correct_Sound.play()
                else:
                    self.misses += 1
                    #Wrong_Sound.play()
            self.same_stroke = True
        
        self.write_stats_to_file()
    
    def write_stats_to_file(self):
        if self.stats_file_path:
            with open(self.stats_file_path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    f"{self.time_elapsed:.2f}",
                    self.stroke_rate[-1] if self.stroke_rate else 0,
                    self.avg_power[-1] if self.avg_power else 0,
                    self.score,
                    self.misses,
                    self.handle_force[-1] if self.handle_force else 0,
                    self.handle_position[-1] if self.handle_position else 0,
                    self.raw_seat_pos[-1] if self.raw_seat_pos else 0,
                    self.converted_seat_position[-1] if self.converted_seat_position else 0,
                    self.L_foot_force[-1] if self.L_foot_force else 0,
                    self.R_foot_force[-1] if self.R_foot_force else 0
                    # add in names for everything after misses
                ])
    
    def stop_writing_stats(self):
        self.stats_file_path = None

# ------------------------------------------------------------------------------------------------------------

class GamePage(wx.Panel):
    def __init__(self, parent, shared_state):
        super(GamePage, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(45, 97, 181))
        self.shared_state = shared_state

        # initialize sizer for the page
        outer_sizer = wx.BoxSizer(wx.VERTICAL)

        # initialize stats panel
        self.stats_panel = StatsDisplay(self, self.shared_state)
        outer_sizer.Add(self.stats_panel, 1, wx.EXPAND | wx.BOTTOM, 15)

        # initialize button panel
        FEStext = wx.StaticText(self, label="FES Activation:")
        FEStext.SetForegroundColour(wx.WHITE)
        FEStext.SetFont(wx.Font(17, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        outer_sizer.Add(FEStext, 0, wx.LEFT, 150)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_panel = FESButton(self, self.shared_state)
        self.button_panel.SetMinSize((350, 200))
        self.button_panel.SetMaxSize((350, 200))
        button_sizer.Add(self.button_panel, 0, wx.EXPAND | wx.RIGHT, 30)
        self.loading_bar_panel = LoadingBar(self, self.shared_state)
        self.loading_bar_panel.SetMinSize((50, 200))
        self.loading_bar_panel.SetMaxSize((50, 200))
        button_sizer.Add(self.loading_bar_panel, 0, wx.EXPAND)
        outer_sizer.Add(button_sizer, 0, wx.CENTER | wx.BOTTOM, 10)

        # initialize moving seat
        Seattext = wx.StaticText(self, label="Seat Position:")
        Seattext.SetForegroundColour(wx.WHITE)
        Seattext.SetFont(wx.Font(17, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        outer_sizer.Add(Seattext, 0, wx.LEFT, 150)
        self.seat_panel = SeatPos(self, self.shared_state)
        self.seat_panel.SetMinSize((500, 200))
        self.seat_panel.SetMaxSize((500, 200))
        outer_sizer.Add(self.seat_panel, 0, wx.ALL | wx.CENTER)

        # initialize back button
        self.back_button = CustomButton(self, label="\nBack\n", size=(120, 60), font=30, handler=self.on_back_button)
        outer_sizer.Add(self.back_button, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(outer_sizer)

        # initialize the main timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(100)

    def on_timer(self, event):
        self.shared_state.update_stats()
        if self.shared_state.raw_seat_pos:
            print('raw seat pos: ', self.shared_state.raw_seat_pos[-1])
            print('Current seat position: ', self.shared_state.converted_seat_position[-1])
            print('front max pos', self.shared_state.front_max_pos)
            print('back max pos', self.shared_state.back_max_pos)
            print('is pressed', self.shared_state.is_pressed)
            if self.shared_state.switch_press:
                print('switch press', self.shared_state.switch_press[-1])
        self.seat_panel.simulate_seat_position()
        self.stats_panel.display_stats()
        self.seat_panel.Refresh()
        self.button_panel.update_button_state()
        self.loading_bar_panel.update_loading_bar()
        self.loading_bar_panel.edge_case()
    
    def reset_game(self):
        self.stats_panel.reset()
        self.button_panel.reset()
        self.loading_bar_panel.reset()
        self.seat_panel.reset()

    def on_back_button(self, event):
        self.shared_state.stop_writing_stats()
        parent = self.GetParent()
        parent.switch_to_start_page()

# ------------------------------------------------------------------------------------------------------------

class StatsDisplay(wx.Panel):
    def __init__(self, parent, shared_state):
        super(StatsDisplay, self).__init__(parent)
        self.shared_state = shared_state

        # table for stats
        attr1 = gridlib.GridCellAttr()
        attr1.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        font1 = wx.Font(22, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        attr1.SetFont(font1)

        self.grid1 = gridlib.Grid(self)
        self.grid1.CreateGrid(1, 2)
        self.grid1.HideRowLabels()
        self.grid1.SetColLabelValue(0, "Stroke Rate (cycles/min)")
        self.grid1.SetColLabelValue(1, "Average Power (W/stroke)")
        self.grid1.SetColSize(0, 525)
        self.grid1.SetColSize(1, 525)
        self.grid1.SetRowSize(0, 30)

        for row in range(1):
            for col in range(2):
                self.grid1.SetAttr(row, col, attr1)
                self.grid1.SetCellValue(row, col, "0")

        attr2 = gridlib.GridCellAttr()
        attr2.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        font2 = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        attr2.SetFont(font2)

        self.grid2 = gridlib.Grid(self)
        self.grid2.CreateGrid(1, 3)
        self.grid2.HideRowLabels()
        self.grid2.SetColLabelValue(0, "Time Elapsed (min)")
        self.grid2.SetColLabelValue(1, "Score")
        self.grid2.SetColLabelValue(2, "Misses")
        self.grid2.SetColSize(0, 350)
        self.grid2.SetColSize(1, 350)
        self.grid2.SetColSize(2, 350)
        self.grid2.SetRowSize(0, 30)

        for row in range(1):
            for col in range(3):
                self.grid2.SetAttr(row, col, attr2)
                self.grid2.SetCellValue(row, col, "0")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid1, 0, wx.ALIGN_CENTER | wx.TOP, 30)
        sizer.Add(self.grid2, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        self.Layout()

    def display_stats(self):
        self.grid1.SetCellValue(0, 0, str(self.shared_state.stroke_rate[-1] if self.shared_state.stroke_rate else 0))
        self.grid1.SetCellValue(0, 1, str(self.shared_state.avg_power[-1] if self.shared_state.avg_power else 0))
        self.grid2.SetCellValue(0, 0, f"{self.shared_state.time_elapsed:.2f}")
        self.grid2.SetCellValue(0, 1, str(self.shared_state.score))
        self.grid2.SetCellValue(0, 2, str(self.shared_state.misses))

    def reset(self):
        self.shared_state.time_start = time.time()
        self.shared_state.time_elapsed = 0
        self.shared_state.avg_power = []
        self.shared_state.temp_power = []
        self.shared_state.stroke_rate = []
        self.shared_state.stroke_time = []
        self.shared_state.stroke_duration = []
        self.shared_state.score = 0
        self.shared_state.misses = 0
        self.shared_state.same_stroke = False

        self.shared_state.handle_force = []
        self.shared_state.handle_position = []
        self.shared_state.L_foot_force = []
        self.shared_state.R_foot_force = []
        self.shared_state.switch_press = []

        for row in range(1):
            for col in range(2):
                self.grid1.SetCellValue(row, col, "0")
        for row in range(1):
            for col in range(3):
                self.grid2.SetCellValue(row, col, "0")

# ------------------------------------------------------------------------------------------------------------

class FESButton(wx.Panel):
    def __init__(self, parent, shared_state, id=wx.ID_ANY, size=(300, 200)):
        super(FESButton, self).__init__(parent, id, size=size)
        self.shared_state = shared_state
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.top_color = wx.Colour(255, 140, 0)
        self.bottom_color = wx.BLACK
        self.filler_color = wx.Colour(45, 97, 181)
        self.border_color = wx.Colour(0, 0, 0)
        self.message_text = None

    def update_button_state(self):
        if not self.shared_state.converted_seat_position:
            return

        if self.shared_state.converted_seat_position[-1] <= 0:
            self.shared_state.converted_seat_position[-1] = 0
        elif self.shared_state.converted_seat_position[-1] >= 100:
            self.shared_state.converted_seat_position[-1] = 100

        current_pos = self.shared_state.converted_seat_position[-1]
        
        if self.shared_state.is_pressed:
            if current_pos <= 0:  # near the back (0 is back, 100 is front)
                self.shared_state.is_pressed = False
                self.shared_state.loading_phase = 0  # orange state
                self.top_color = wx.Colour(255, 140, 0)
        else:
            if current_pos >= self.shared_state.converted_fes_pos:  # near the front
                self.shared_state.is_pressed = True
                self.shared_state.loading_phase = 1  # green state
                self.top_color = wx.Colour(126, 197, 53)
        
        if self.shared_state.msg:
            self.show_message("Please finish the stroke!", (60, 140))
        else:
            self.show_message("", (60, 140))
        
        self.Refresh()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        width, height = self.GetSize()

        # Dimensions for the rectangles
        bottom_rect_width = width
        bottom_rect_height = height // 2

        if self.shared_state.loading_phase == 1:
            top_rect_height = height // 4
        else:
            top_rect_height = height // 2

        top_rect_width = int((width - 100) * (bottom_rect_width - 25 / 100))

        filler_rec_width = 50
        filler_rec_height = height // 2

        # Calculate the top rectangle's position to start from the left edge
        top_rect_x = 50
        top_rect_y = (height // 2) - top_rect_height

        # Draw bottom rectangle
        dc.SetBrush(wx.Brush(self.bottom_color))
        dc.DrawRectangle(0, height // 2, bottom_rect_width, bottom_rect_height)

        dc.SetPen(wx.TRANSPARENT_PEN)

        # Draw top rectangle
        dc.SetBrush(wx.Brush(self.top_color))
        dc.DrawRectangle(top_rect_x, top_rect_y, top_rect_width, top_rect_height)

        # Draw filler rectangle
        dc.SetBrush(wx.Brush(self.filler_color))
        dc.DrawRectangle(0, 0, filler_rec_width, filler_rec_height)
        dc.DrawRectangle(width - filler_rec_width, 0, filler_rec_width, filler_rec_height)
    
    def show_message(self, message, pos):
        if self.message_text:
            self.message_text.Destroy()
        self.message_text = wx.StaticText(self, label=message, pos=pos)
        self.message_text.SetForegroundColour(wx.RED)
        self.message_text.SetBackgroundColour(wx.BLACK)
        self.message_text.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.Refresh()

    def reset(self):
        self.shared_state.is_pressed = False
        self.top_color = wx.Colour(255, 140, 0)
        if self.message_text:
            self.message_text.Destroy()
            self.message_text = None
        self.Refresh()

# ------------------------------------------------------------------------------------------------------------

class LoadingBar(wx.Panel):
    def __init__(self, parent, shared_state, id=wx.ID_ANY, size=(50, 240)):
        super(LoadingBar, self).__init__(parent, id, size=size)
        self.shared_state = shared_state
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.bar_color = wx.Colour(255, 140, 0)
        self.loading_progress = 100
        self.stroke = False
        self.pass_fes = False
        self.remaining_progress = 100

    def update_loading_bar(self):
        if not self.shared_state.converted_seat_position:
            return

        current_pos = self.shared_state.converted_seat_position[-1]
        converted_first_dist = (self.shared_state.fes_active_pos - self.shared_state.front_max_pos) / (self.shared_state.back_max_pos - self.shared_state.front_max_pos) * 100

        if not self.shared_state.is_pressed:  # orange state
            if current_pos >= self.shared_state.converted_fes_pos:  # at FES activation point
                self.shared_state.is_pressed = True  # switch to green state
                self.shared_state.loading_phase = 1
                self.bar_color = wx.Colour(126, 197, 53)
            else:
                # decrease from max to 0 as moving from back to converted_fes_pos
                distance_traveled = self.shared_state.converted_fes_pos - current_pos
                self.loading_progress = (distance_traveled / self.shared_state.converted_fes_pos) * 100
        else:  # green state
            if current_pos == 0:  # at backmost position
                self.shared_state.is_pressed = False  # switch to orange state
                self.shared_state.loading_phase = 0
                self.bar_color = wx.Colour(255, 140, 0)
            else:
                if 100 >= current_pos >= self.shared_state.converted_fes_pos and self.shared_state.converted_seat_position[-2] < self.shared_state.converted_seat_position[-1]:
                    # Unloading from FES position to the front
                    distance_traveled = current_pos - self.shared_state.converted_fes_pos
                    front_range = 100 - self.shared_state.converted_fes_pos
                    self.loading_progress = 100 - ((distance_traveled / front_range) * converted_first_dist)
                    self.remaining_progress = self.loading_progress
                elif current_pos <= 100 and self.shared_state.converted_seat_position[-2] > self.shared_state.converted_seat_position[-1]:
                    # Unloading from front to back
                    distance_traveled = 100 - current_pos
                    self.loading_progress = self.remaining_progress - ((distance_traveled / 100) * 100)

        self.Refresh()
    
    def edge_case(self):
        if self.shared_state.converted_seat_position:
            if self.shared_state.converted_seat_position[-1] <= 0:
                self.stroke = True
                self.pass_fes = False
                self.shared_state.msg = False
            elif self.shared_state.converted_seat_position[-1] >= 100:
                self.stroke = False
                self.pass_fes = False
                self.shared_state.msg = False
            
            # check if passed FES position
            if self.shared_state.converted_seat_position[-1] >= self.shared_state.converted_fes_pos:
                self.pass_fes = True
            
            # update loading bar
            if self.pass_fes and self.stroke and self.shared_state.converted_seat_position[-1] <= self.shared_state.converted_fes_pos:
                self.loading_progress = 100
                self.shared_state.msg = True

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        width, height = self.GetSize()

        bar_height = int(height * (self.loading_progress / 100))

        if self.shared_state.loading_phase == 1:
            self.bar_color = wx.Colour(126, 197, 53)
        else:
            self.bar_color = wx.Colour(255, 140, 0)

        dc.SetBrush(wx.Brush(self.bar_color))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, height - bar_height, width, bar_height)

        # Draw border
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 4))
        dc.DrawLine(0, 0, 0, height)
        dc.DrawLine(width, 0, width, height)
        dc.DrawLine(0, 0, width, 0)
        dc.DrawLine(0, height, width, height)

    def reset(self):
        self.loading_progress = 100
        self.shared_state.is_pressed = False
        self.shared_state.loading_phase = 0
        self.bar_color = wx.Colour(255, 140, 0)
        self.Refresh()

# ------------------------------------------------------------------------------------------------------------

class SeatPos(wx.Panel):
    def __init__(self, parent, shared_state):
        super(SeatPos, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(45, 97, 181))
        self.shared_state = shared_state
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.turn_back = True
    
    # fake data
    def simulate_seat_position(self):
        if not self.shared_state.raw_seat_pos:
            self.shared_state.raw_seat_pos.append(self.shared_state.back_max_pos)
        else:
            self.shared_state.converted_seat_position.append(self.shared_state.convert_raw_to_scale(self.shared_state.raw_seat_pos[-1]))
            next_pos = self.shared_state.converted_seat_position[-1] + self.shared_state.seat_direction 
            self.shared_state.raw_seat_pos.append(self.shared_state.convert_scale_to_raw(next_pos)) 
            # test cases 
            state = "normal"
            match state:
                case "normal":
                    if next_pos >= 100:
                        self.shared_state.seat_direction = -3
                    elif next_pos <= 0:
                        self.shared_state.seat_direction = 3
                    if self.shared_state.is_pressed:
                        self.shared_state.switch_press.append(5)
                    else:
                        self.shared_state.switch_press.append(0)
                case "beyond fes but below 100":
                    if next_pos >= 95 and self.turn_back:
                        self.shared_state.seat_direction = -3
                    elif next_pos <= 92 and self.turn_back and self.shared_state.seat_direction < 0:
                        self.shared_state.seat_direction = 3
                        self.turn_back = False
                    elif next_pos >= 100:
                        self.shared_state.seat_direction = -3
                    elif next_pos <= 0:
                        self.shared_state.seat_direction = 3
                        self.turn_back = True
                case "reach fes then drop":
                    if next_pos >= 95 and self.turn_back:
                        self.shared_state.seat_direction = -3
                    elif next_pos <= 20 and self.turn_back and self.shared_state.seat_direction < 0:
                        self.shared_state.seat_direction = 3
                        self.turn_back = False
                    elif next_pos >= 100:
                        self.shared_state.seat_direction = -3
                    elif next_pos <= 0:
                        self.shared_state.seat_direction = 3
                        self.turn_back = True
                case "didnt reach fes":
                    if next_pos >= 70 and self.turn_back:
                        self.shared_state.seat_direction = -3
                    elif next_pos <= 50 and self.turn_back and self.shared_state.seat_direction < 0:
                        self.shared_state.seat_direction = 3
                        self.turn_back = False
                    elif next_pos >= 100:
                        self.shared_state.seat_direction = -3
                    elif next_pos <= 0:
                        self.shared_state.seat_direction = 3
                        self.turn_back = True

            self.shared_state.converted_seat_position.append(next_pos)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.Clear()

        width, height = self.GetSize()
        padding = 67
        machine_height = height // 2
        machine_width = width - 2 * padding
        seat_width = 30
        seat_height = 20
        backrest_height = 30

        # Draw the rowing machine
        # Base line
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 4))
        dc.DrawLine(padding, machine_height, padding + machine_width, machine_height)

        # Left stand
        dc.DrawLine(padding, machine_height, padding, machine_height + 40)
        dc.DrawLine(padding - 10, machine_height + 40, padding + 10, machine_height + 40)

        # Right stand
        dc.DrawLine(padding + machine_width, machine_height, padding + machine_width + 40, machine_height - 50)  # upper slant
        dc.DrawLine(padding + machine_width, machine_height, padding + machine_width + 20, machine_height + 40)  # bottom slant 
        dc.DrawLine(padding + machine_width + 10, machine_height + 40, padding + machine_width + 30, machine_height + 40)  # horizontal bar
        dc.DrawLine(padding + machine_width + 20, machine_height + 40, padding + machine_width + 40, machine_height - 50)

        # Wheel
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
        dc.DrawCircle(padding + machine_width + 40, machine_height - 60, 25)

        # Draw the L-shaped seat
        if self.shared_state.converted_seat_position:
            seat_x = padding + int(machine_width * (self.shared_state.converted_seat_position[-1] / 100)) - (seat_width // 2)
        else:
            seat_x = padding - (seat_width // 2)
        seat_y = machine_height - seat_height

        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
        dc.DrawRectangle(seat_x, seat_y, seat_width, seat_height)
        dc.DrawRectangle(seat_x, seat_y - backrest_height, seat_width // 2, backrest_height)
    
    def reset(self):
        self.shared_state.converted_seat_position = []
        self.shared_state.raw_seat_pos = []
        self.Refresh()




# new version
'''
stats displayed:
- Time elapsed
- Average power (total power of pulling force and leg force)
- Stroke rate (inverse of time per cycle)
- Score
- Misses

FES timing:
button-press when seat is 96.5 ± 93.3 mm from the front_max_pos of each user
'''