# game page
"""
SENSOR CHANNEL MAPPING (NI-DAQ Dev4):
======================================
ai0: Switch Sensor (0V = pressed, 5V = released, threshold at 2.5V)
ai1: [UNUSED]
ai2: Left Foot Force Sensor
ai3: [UNUSED]  
ai4: Right Foot Force Sensor
ai5: Handle Force Sensor
ai6: Front Potentiometer → Handle Position
ai7: Back Potentiometer → Seat Position (converted: voltage * 100)
"""
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
        self.total_distance = 0.0  # Total distance in meters
        self.last_update_time = time.time()  # For distance calculations

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
        
        # Hardware testing - Auto-detect OS
        import platform
        self.is_mac = platform.system() == 'Darwin'
        self.hardware_mode = not self.is_mac  # Disable hardware mode on Mac
        self.hardware_connected = False
        self.last_hardware_check = 0
        
        if self.is_mac:
            print("⚠️  macOS detected: Running in simulation mode only")
            print("   NI-DAQmx is not supported on macOS")
            print("   Use Windows/Linux for hardware testing")
    
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
        # Use relative path to Training_Data folder in the same directory as the script
        training_data_dir = os.path.join(os.path.dirname(__file__), "Training_Data")
        # Ensure the Training_Data directory exists
        os.makedirs(training_data_dir, exist_ok=True)
        self.stats_file_path = os.path.join(training_data_dir, filename)
        
        with open(self.stats_file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time Elapsed (min)", "Stroke Rate", "Average Power", "Score", "Misses", "Handle Force", "Handle Position", "Raw Seat Position", "Converted Seat Position", "Left Foot Force", "Right Foot Force"])

    def update_stats(self):
        # update time
        self.time_elapsed = int(time.time() - self.time_start) / 60

        # Hardware sensor data collection (Windows/Linux only)
        if not self.is_mac and self.hardware_mode:
            try:
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
                if len(self.raw_seat_pos) > 1 and hasattr(self, 'temp_time'):
                    self.temp_power.append(((self.handle_force[-1]+self.handle_force[-2])/2)*abs(self.handle_position[-1]-self.handle_position[-2])/(self.temp_time[-1]-self.temp_time[-2]))
                    self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                    
                return  # Exit early if hardware read was successful
            except Exception as e:
                print(f"Hardware error: {e}")
                # Fall through to simulation mode
        
        # Simulation mode (always used on macOS, fallback for Windows/Linux)
        if not hasattr(self, 'temp_time'):
            self.temp_time = []
        self.temp_time.append(time.time())

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
    
    def calculate_distance(self):
        """Calculate realistic rowing distance based on power and time"""
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        self.last_update_time = current_time
        
        if self.avg_power and time_delta > 0:
            current_power = self.avg_power[-1]
            
            # Realistic rowing physics:
            # Distance = (Power / Drag Factor) * Time
            # Drag factor for realistic rowing is typically around 100-150
            # We'll use 120 as a moderate resistance setting
            drag_factor = 120
            
            # Only calculate distance if there's meaningful power (reduce noise)
            if current_power > 10:  # Minimum 10W to register movement
                # Distance per time interval based on power
                # Formula: distance = (power / drag_factor) * time
                distance_increment = (current_power / drag_factor) * time_delta
                self.total_distance += distance_increment

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
        self.SetBackgroundColour(wx.Colour(248, 249, 250))  # Light gray background
        self.shared_state = shared_state

        # initialize sizer for the page
        outer_sizer = wx.BoxSizer(wx.VERTICAL)

        # initialize modern stats panel - top section
        self.stats_panel = ModernStatsDisplay(self, self.shared_state)
        outer_sizer.Add(self.stats_panel, 2, wx.EXPAND | wx.ALL, 20)

        # initialize gamified rowing scene - middle section
        self.rowing_scene_panel = RowingScenePanel(self, self.shared_state)
        outer_sizer.Add(self.rowing_scene_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)

        # initialize FES timing indicator - bottom section
        self.fes_indicator_panel = ModernFESIndicator(self, self.shared_state)
        outer_sizer.Add(self.fes_indicator_panel, 2, wx.EXPAND | wx.ALL, 20)

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
        # Simulate seat position for FES indicator (no visual seat anymore)
        if not self.shared_state.raw_seat_pos:
            self.shared_state.raw_seat_pos.append(self.shared_state.back_max_pos)
        else:
            self.shared_state.converted_seat_position.append(self.shared_state.convert_raw_to_scale(self.shared_state.raw_seat_pos[-1]))
            next_pos = self.shared_state.converted_seat_position[-1] + self.shared_state.seat_direction 
            self.shared_state.raw_seat_pos.append(self.shared_state.convert_scale_to_raw(next_pos)) 
            
            # Simulation logic
            if next_pos >= 100:
                self.shared_state.seat_direction = -3
            elif next_pos <= 0:
                self.shared_state.seat_direction = 3
            if self.shared_state.is_pressed:
                self.shared_state.switch_press.append(5)
            else:
                self.shared_state.switch_press.append(0)
            
            self.shared_state.converted_seat_position.append(next_pos)
        
        # Generate realistic fake power data
        import random
        if not hasattr(self.shared_state, 'temp_time'):
            self.shared_state.temp_time = []
        self.shared_state.temp_time.append(time.time())
        
        # Add some initial fake data if lists are empty
        if not self.shared_state.avg_power:
            # Start with some baseline values
            initial_power = random.uniform(85, 125)
            self.shared_state.temp_power.append(initial_power)
            self.shared_state.avg_power.append(initial_power)
            self.shared_state.stroke_rate.append(random.uniform(24, 26))
        
        # Simulate realistic power output (varies between 50-200W with rowing motion)
        if self.shared_state.converted_seat_position:
            current_pos = self.shared_state.converted_seat_position[-1]
            
            # Power varies with rowing phase - higher during drive phase (moving toward front)
            if len(self.shared_state.converted_seat_position) >= 2:
                prev_pos = self.shared_state.converted_seat_position[-2]
                is_driving = current_pos > prev_pos  # Moving toward front (drive phase)
                
                if is_driving and current_pos > 50:  # High power during drive phase
                    base_power = random.uniform(120, 200)
                elif is_driving:  # Moderate power during early drive
                    base_power = random.uniform(80, 150)
                else:  # Lower power during recovery phase
                    base_power = random.uniform(30, 80)
                
                # Add some random variation
                power_variation = random.uniform(-20, 20)
                simulated_power = max(0, base_power + power_variation)
                
                self.shared_state.temp_power.append(simulated_power)
                self.shared_state.avg_power.append(sum(self.shared_state.temp_power) / len(self.shared_state.temp_power))
                
                # Simulate stroke rate (strokes per minute) - typical rowing is 20-35 SPM
                if not self.shared_state.stroke_rate:
                    simulated_stroke_rate = random.uniform(22, 28)  # Start with moderate pace
                else:
                    # Vary stroke rate slightly around current rate
                    current_rate = self.shared_state.stroke_rate[-1]
                    rate_change = random.uniform(-2, 2)
                    simulated_stroke_rate = max(18, min(35, current_rate + rate_change))
                
                self.shared_state.stroke_rate.append(simulated_stroke_rate)
        
        # Calculate realistic distance
        self.shared_state.calculate_distance()
        
        # Generate fake accuracy data (simulate some successful and missed FES activations)
        if len(self.shared_state.converted_seat_position) > 10:  # Wait a bit before starting accuracy simulation
            # Randomly simulate button presses at appropriate times
            if random.random() < 0.05:  # 5% chance per update to simulate a button press
                current_pos = self.shared_state.raw_seat_pos[-1] if self.shared_state.raw_seat_pos else 0
                
                # Simulate success/failure based on timing accuracy (80% success rate)
                if random.random() < 0.8:  # 80% success rate
                    self.shared_state.score += 1
                else:
                    self.shared_state.misses += 1
        
        self.stats_panel.update_stats()
        self.rowing_scene_panel.update_scene()
        self.fes_indicator_panel.update_indicator()
    
    def reset_game(self):
        self.stats_panel.reset()
        self.rowing_scene_panel.reset()
        self.fes_indicator_panel.reset()

    def on_back_button(self, event):
        self.shared_state.stop_writing_stats()
        parent = self.GetParent()
        parent.switch_to_start_page()

# ------------------------------------------------------------------------------------------------------------

class ModernStatsDisplay(wx.Panel):
    def __init__(self, parent, shared_state):
        super(ModernStatsDisplay, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.shared_state = shared_state

        # Create main horizontal sizer for the four metric cards
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Time Card
        self.time_card = self.create_metric_card("Time", "00:05:32", wx.Colour(255, 255, 255))
        main_sizer.Add(self.time_card, 1, wx.EXPAND | wx.RIGHT, 15)

        # Power Card
        self.power_card = self.create_metric_card("Power", "185 W", wx.Colour(255, 255, 255))
        main_sizer.Add(self.power_card, 1, wx.EXPAND | wx.RIGHT, 15)

        # Distance Card
        self.distance_card = self.create_metric_card("Distance", "0.5 km", wx.Colour(255, 255, 255))
        main_sizer.Add(self.distance_card, 1, wx.EXPAND | wx.RIGHT, 15)

        # Accuracy Card
        self.accuracy_card = self.create_metric_card("Accuracy", "92%", wx.Colour(255, 255, 255))
        main_sizer.Add(self.accuracy_card, 1, wx.EXPAND)

        self.SetSizer(main_sizer)

    def create_metric_card(self, title, value, bg_color):
        # Create panel for the card
        card_panel = wx.Panel(self)
        card_panel.SetBackgroundColour(bg_color)
        
        # Create sizer for card content
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        card_sizer.AddStretchSpacer()  # Top flexible space

        # Title label - much larger
        title_label = wx.StaticText(card_panel, label=title)
        title_label.SetForegroundColour(wx.Colour(128, 128, 128))
        title_label.SetFont(wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        card_sizer.Add(title_label, 0, wx.ALIGN_CENTER)
        card_sizer.AddSpacer(20)

        # Value label - much larger
        value_label = wx.StaticText(card_panel, label=value)
        value_label.SetForegroundColour(wx.Colour(64, 64, 64))
        value_label.SetFont(wx.Font(72, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        card_sizer.Add(value_label, 0, wx.ALIGN_CENTER)
        card_sizer.AddStretchSpacer()  # Bottom flexible space

        card_panel.SetSizer(card_sizer)
        
        # Store references to update later
        if title == "Time":
            self.time_value_label = value_label
        elif title == "Power":
            self.power_value_label = value_label
        elif title == "Distance":
            self.distance_value_label = value_label
        elif title == "Accuracy":
            self.accuracy_value_label = value_label

        return card_panel

    def update_stats(self):
        # Update time
        minutes = int(self.shared_state.time_elapsed)
        seconds = int((self.shared_state.time_elapsed - minutes) * 60)
        time_str = f"{minutes:02d}:{seconds:02d}:00"
        self.time_value_label.SetLabel(time_str)

        # Update power
        current_power = self.shared_state.avg_power[-1] if self.shared_state.avg_power else 0
        power_str = f"{int(current_power)} W"
        self.power_value_label.SetLabel(power_str)

        # Update distance (based on realistic rowing physics)
        distance_meters = self.shared_state.total_distance
        if distance_meters >= 1000:
            distance_str = f"{distance_meters/1000:.1f} km"
        else:
            distance_str = f"{int(distance_meters)} m"
        self.distance_value_label.SetLabel(distance_str)

        # Update accuracy (calculate as score / (score + misses) * 100)
        total_attempts = self.shared_state.score + self.shared_state.misses
        if total_attempts > 0:
            accuracy = (self.shared_state.score / total_attempts) * 100
            accuracy_str = f"{int(accuracy)}%"
        else:
            accuracy_str = "0%"
        self.accuracy_value_label.SetLabel(accuracy_str)

        # Update the color of accuracy label based on percentage
        if total_attempts > 0:
            if accuracy >= 90:
                self.accuracy_value_label.SetForegroundColour(wx.Colour(76, 175, 80))  # Green
            elif accuracy >= 70:
                self.accuracy_value_label.SetForegroundColour(wx.Colour(255, 193, 7))  # Amber
            else:
                self.accuracy_value_label.SetForegroundColour(wx.Colour(244, 67, 54))  # Red
        else:
            self.accuracy_value_label.SetForegroundColour(wx.Colour(64, 64, 64))  # Default gray

        self.Layout()

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
        self.shared_state.total_distance = 0.0
        self.shared_state.last_update_time = time.time()

        self.shared_state.handle_force = []
        self.shared_state.handle_position = []
        self.shared_state.L_foot_force = []
        self.shared_state.R_foot_force = []
        self.shared_state.switch_press = []

        # Reset display
        self.time_value_label.SetLabel("00:00:00")
        self.power_value_label.SetLabel("0 W")
        self.distance_value_label.SetLabel("0 m")
        self.accuracy_value_label.SetLabel("0%")
        self.accuracy_value_label.SetForegroundColour(wx.Colour(64, 64, 64))

# ------------------------------------------------------------------------------------------------------------

class RowingScenePanel(wx.Panel):
    def __init__(self, parent, shared_state):
        super(RowingScenePanel, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(135, 206, 250))  # Sky blue background
        self.shared_state = shared_state
        self.SetMinSize((-1, 200))
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # Background scrolling based on cumulative power/distance
        self.background_offset = 0.0  # How far the background has scrolled
        self.cumulative_distance = 0.0  # Total distance traveled
        self.distance_per_power_unit = 0.05  # How much distance per watt of power (slowed down further)
        
        # Boat animation
        self.boat_x_position = 0.3  # Fixed boat position (30% from left)
        self.boat_bob_offset = 0.0  # Vertical bobbing offset
        self.bob_speed = 0.1  # Speed of bobbing animation
        
        # Current location theme
        self.current_location = "North Pole"
        
        # Predefined iceberg shapes to cycle through (no randomness)
        self.iceberg_templates = [
            # Iceberg 1 - Sharp peak
            [(0, 1), (0.15, 0.7), (0.3, 0.4), (0.5, 0), (0.7, 0.3), (0.85, 0.6), (1, 1)],
            # Iceberg 2 - Double peak
            [(0, 1), (0.2, 0.6), (0.35, 0.2), (0.5, 0.4), (0.65, 0.1), (0.8, 0.5), (1, 1)],
            # Iceberg 3 - Rolling hills
            [(0, 1), (0.25, 0.5), (0.5, 0.3), (0.75, 0.4), (1, 1)],
            # Iceberg 4 - Steep cliff
            [(0, 1), (0.1, 0.8), (0.2, 0.2), (0.4, 0.1), (0.8, 0.6), (1, 1)],
            # Iceberg 5 - Gentle slope
            [(0, 1), (0.3, 0.4), (0.6, 0.2), (0.9, 0.7), (1, 1)]
        ]
        self.locations = {
            "North Pole": {
                "landscape_color": wx.Colour(240, 248, 255),  # Alice blue for ice
                "accent_color": wx.Colour(176, 196, 222),     # Light steel blue
                "water_color": wx.Colour(70, 130, 180),       # Steel blue
                "features": "icebergs"
            },
            "Amazon": {
                "landscape_color": wx.Colour(34, 139, 34),    # Forest green
                "accent_color": wx.Colour(107, 142, 35),      # Olive drab
                "water_color": wx.Colour(139, 69, 19),        # Saddle brown (muddy water)
                "features": "trees"
            },
            "Mediterranean": {
                "landscape_color": wx.Colour(255, 218, 185),  # Peach puff
                "accent_color": wx.Colour(210, 180, 140),     # Tan
                "water_color": wx.Colour(0, 191, 255),        # Deep sky blue
                "features": "cliffs"
            }
        }
        
        # Create location label
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSpacer(15)
        
        self.location_label = wx.StaticText(self, label=f"Location: {self.current_location}")
        self.location_label.SetForegroundColour(wx.Colour(255, 255, 255))
        self.location_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        main_sizer.Add(self.location_label, 0, wx.ALIGN_CENTER)
        
        main_sizer.AddStretchSpacer()
        self.SetSizer(main_sizer)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        size = self.GetSize()
        width, height = size.width, size.height
        
        # Get current location theme
        theme = self.locations[self.current_location]
        
        # Draw sky background
        dc.SetBrush(wx.Brush(wx.Colour(135, 206, 250)))
        dc.Clear()
        
        # Draw landscape/mountains in background
        self.draw_landscape(dc, width, height, theme)
        
        # Draw enhanced water
        water_height = height // 3
        water_y = height - water_height
        self.draw_water(dc, width, water_y, water_height, theme)
        
        # Draw boat at fixed position with bobbing motion
        boat_x = int(width * self.boat_x_position)
        boat_y = water_y - 20 + int(self.boat_bob_offset)
        self.draw_boat(dc, boat_x, boat_y)
        
        # Draw location-specific features
        self.draw_location_features(dc, width, height, theme)

    def draw_landscape(self, dc, width, height, theme):
        """Draw scrolling background landscape"""
        landscape_height = height // 2
        
        if theme["features"] == "icebergs":
            # Draw icy mountains/icebergs that scroll with randomness
            dc.SetBrush(wx.Brush(theme["landscape_color"]))
            dc.SetPen(wx.TRANSPARENT_PEN)
            
            # Calculate scroll offset (wrap around for continuous scrolling)
            scroll_offset = int(self.background_offset) % (width * 2)
            
            # Draw multiple ice formations with procedural generation
            self.draw_random_icebergs(dc, width, height, scroll_offset)
            
        elif theme["features"] == "trees":
            # Draw forest silhouette
            dc.SetBrush(wx.Brush(theme["landscape_color"]))
            # Create jagged tree line
            for i in range(0, width, 20):
                tree_height = height//4 + (i % 40)
                dc.DrawRectangle(i, height//2 - tree_height, 15, tree_height)
                
        elif theme["features"] == "cliffs":
            # Draw Mediterranean cliffs
            dc.SetBrush(wx.Brush(theme["landscape_color"]))
            cliff_points = [
                (0, height//2), (width//4, height//3), (width//2, height//2),
                (3*width//4, height//4), (width, height//2)
            ]
            dc.DrawPolygon(cliff_points)

    def draw_random_icebergs(self, dc, width, height, scroll_offset):
        """Draw predefined icebergs that cycle smoothly"""
        
        # Fixed iceberg positions and characteristics
        iceberg_spacing = width // 3  # Space between icebergs
        base_y = height // 2
        
        # Calculate which icebergs to draw based on scroll position
        for repeat in range(-2, 4):  # Draw enough sections to cover screen plus margins
            section_x = repeat * iceberg_spacing * 5 - scroll_offset
            
            # Draw 5 icebergs per section using predefined templates
            for i in range(5):
                iceberg_x = section_x + i * iceberg_spacing
                
                # Fixed characteristics (no randomness)
                iceberg_width = width // 4 if i % 2 == 0 else width // 5  # Alternate sizes
                iceberg_height = height // 4 if i % 3 == 0 else height // 5  # Vary heights
                
                # Select template based on position (cycles through templates)
                template_index = (repeat * 5 + i) % len(self.iceberg_templates)
                template = self.iceberg_templates[template_index]
                
                # Convert template to actual coordinates
                points = []
                for template_x, template_y in template:
                    actual_x = iceberg_x - iceberg_width//2 + template_x * iceberg_width
                    actual_y = base_y - template_y * iceberg_height
                    points.append((int(actual_x), int(actual_y)))
                
                # Only draw if any part is visible on screen
                if (iceberg_x - iceberg_width//2 < width + 100 and 
                    iceberg_x + iceberg_width//2 > -100):
                    dc.DrawPolygon(points)

    def draw_random_floating_icebergs(self, dc, width, water_y, scroll_offset):
        """Draw predefined floating icebergs in the water"""
        
        # Predefined floating iceberg shapes (small triangular chunks)
        floating_templates = [
            [(0.5, 0), (0, 1), (1, 1)],  # Simple triangle
            [(0.3, 0), (0, 0.8), (0.7, 1), (1, 0.6)],  # Irregular chunk
            [(0.2, 0.2), (0.6, 0), (1, 0.7), (0.3, 1), (0, 0.8)],  # Jagged piece
        ]
        
        # Fixed spacing for floating icebergs
        float_spacing = width // 2
        
        # Generate floating icebergs across sections
        for repeat in range(-1, 4):
            base_x = repeat * float_spacing * 3
            
            # 3 floating icebergs per section
            for i in range(3):
                iceberg_x = base_x + i * float_spacing - int(scroll_offset * 0.3)
                
                # Fixed size variations
                iceberg_size = 15 if i % 2 == 0 else 20
                iceberg_height = 25 if i % 3 == 0 else 30
                
                # Select template
                template_index = (repeat * 3 + i) % len(floating_templates)
                template = floating_templates[template_index]
                
                # Convert template to actual coordinates
                points = []
                for template_x, template_y in template:
                    actual_x = iceberg_x - iceberg_size//2 + template_x * iceberg_size
                    actual_y = water_y + template_y * iceberg_height
                    points.append((int(actual_x), int(actual_y)))
                
                # Only draw if on screen
                if -50 <= iceberg_x <= width + 50:
                    dc.DrawPolygon(points)

    def draw_water(self, dc, width, water_y, water_height, theme):
        """Draw enhanced water with gradient and animated waves"""
        import math
        
        # Draw water base with gradient effect
        base_color = theme["water_color"]
        
        # Create gradient from darker at top to lighter at bottom
        for y_step in range(water_height):
            progress = y_step / water_height
            # Darker at top, lighter at bottom
            r = int(base_color.Red() * (0.7 + 0.3 * progress))
            g = int(base_color.Green() * (0.7 + 0.3 * progress))
            b = int(base_color.Blue() * (0.7 + 0.3 * progress))
            
            dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
            dc.DrawLine(0, water_y + y_step, width, water_y + y_step)
        
        # Draw animated wave patterns
        self.draw_water_waves(dc, width, water_y, water_height)
        
        # Draw surface reflections
        self.draw_water_reflections(dc, width, water_y, water_height)

    def draw_water_waves(self, dc, width, water_y, water_height):
        """Draw animated wave patterns on water surface"""
        import math
        
        # Calculate wave scroll offset
        wave_offset = self.background_offset * 0.8
        
        # Draw multiple wave layers for depth
        wave_colors = [
            wx.Colour(255, 255, 255, 80),   # Light waves
            wx.Colour(200, 220, 255, 60),   # Medium waves
            wx.Colour(150, 180, 255, 40)    # Deep waves
        ]
        
        for layer, color in enumerate(wave_colors):
            dc.SetPen(wx.Pen(color, 2))
            
            # Different wave frequencies for each layer
            frequency = 0.05 + layer * 0.02
            amplitude = 3 + layer
            phase_offset = wave_offset * (1 + layer * 0.3)
            
            # Draw sinusoidal waves
            prev_x, prev_y = 0, water_y + int(amplitude * math.sin(phase_offset * frequency))
            
            for x in range(5, width, 5):
                wave_y = water_y + int(amplitude * math.sin((x + phase_offset) * frequency))
                dc.DrawLine(prev_x, prev_y, x, wave_y)
                prev_x, prev_y = x, wave_y

    def draw_water_reflections(self, dc, width, water_y, water_height):
        """Draw subtle reflections and surface details"""
        # Draw horizontal reflection lines that move
        dc.SetPen(wx.Pen(wx.Colour(255, 255, 255, 30), 1))
        
        reflection_offset = int(self.background_offset * 0.5) % 40
        
        for i in range(2, 6):  # Multiple reflection layers
            reflect_y = water_y + i * water_height // 6
            for x in range(-40, width + 40, 40):
                reflect_x = x - reflection_offset + (i * 8)  # Offset each layer
                dc.DrawLine(reflect_x, reflect_y, reflect_x + 20, reflect_y)

    def draw_boat(self, dc, x, y):
        """Draw the rowing boat"""
        # Add wake behind boat if moving (based on power)
        current_power = self.shared_state.avg_power[-1] if self.shared_state.avg_power else 0
        if current_power > 10:  # Show wake when there's good power
            dc.SetPen(wx.Pen(wx.Colour(255, 255, 255, 150), 2))
            # Draw wake lines behind boat
            for i in range(3):
                wake_x = x - 40 - (i * 15)
                dc.DrawLine(wake_x, y + 5 + i*3, wake_x + 20, y + 5 + i*3)
        
        # Boat hull
        dc.SetBrush(wx.Brush(wx.Colour(139, 69, 19)))  # Saddle brown
        dc.SetPen(wx.Pen(wx.Colour(101, 67, 33), 2))
        
        boat_width = 60
        boat_height = 20
        boat_points = [
            (x - boat_width//2, y),
            (x - boat_width//3, y + boat_height),
            (x + boat_width//3, y + boat_height),
            (x + boat_width//2, y)
        ]
        dc.DrawPolygon(boat_points)
        
        # Rower (simple stick figure)
        dc.SetBrush(wx.Brush(wx.Colour(255, 220, 177)))  # Skin color
        dc.DrawCircle(x, y - 15, 8)  # Head
        
        # Body
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 3))
        dc.DrawLine(x, y - 7, x, y + 5)  # Body
        
        # Arms with oar - animate based on power
        oar_extend = 25
        if current_power > 15:  # More extended oars when rowing hard
            oar_extend = 30
        dc.DrawLine(x - oar_extend, y - 5, x + oar_extend, y)  # Oar
        dc.DrawLine(x - 10, y - 5, x + 10, y)  # Arms

    def draw_location_features(self, dc, width, height, theme):
        """Draw scrolling location-specific decorative features"""
        if theme["features"] == "icebergs":
            # Draw floating icebergs in water that scroll with randomness
            dc.SetBrush(wx.Brush(wx.Colour(240, 248, 255)))
            water_y = height - height//3
            
            # Calculate scroll offset
            scroll_offset = int(self.background_offset * 0.3) % (width * 2)  # Much slower scroll for parallax effect
            
            # Generate random floating icebergs
            self.draw_random_floating_icebergs(dc, width, water_y, scroll_offset)
                
        elif theme["features"] == "trees":
            # Draw some individual palm trees
            dc.SetBrush(wx.Brush(wx.Colour(139, 69, 19)))  # Brown trunk
            tree_positions = [width//5, 4*width//5]
            for pos in tree_positions:
                dc.DrawRectangle(pos-3, height//2-40, 6, 40)  # Trunk
                # Palm fronds
                dc.SetBrush(wx.Brush(wx.Colour(34, 139, 34)))
                dc.DrawCircle(pos, height//2-40, 12)

    def update_scene(self):
        """Update the scene based on rowing power"""
        import math
        
        # Update background scrolling based on cumulative power
        if self.shared_state.avg_power:
            current_power = self.shared_state.avg_power[-1]
            
            # Only scroll if there's significant power (reduce jitter)
            if current_power > 5:  # Only count power above 5W
                # Add to cumulative distance based on power
                self.cumulative_distance += current_power * self.distance_per_power_unit
                
                # Background scrolls based on cumulative distance
                self.background_offset = self.cumulative_distance
        
        # Animate boat bobbing (always bob, even without power)
        self.boat_bob_offset = math.sin(self.cumulative_distance * 0.1) * 5  # 5 pixel amplitude
        
        # Add extra bobbing when rowing hard
        if self.shared_state.avg_power and self.shared_state.avg_power[-1] > 15:
            self.boat_bob_offset += math.sin(self.cumulative_distance * 0.3) * 2  # Extra motion when rowing hard
        
        self.Refresh()

    def reset(self):
        """Reset the scene"""
        self.background_offset = 0.0  # Reset background scroll
        self.cumulative_distance = 0.0  # Reset distance
        self.boat_bob_offset = 0.0  # Reset boat bobbing
        self.Refresh()

# ------------------------------------------------------------------------------------------------------------

class ModernFESIndicator(wx.Panel):
    def __init__(self, parent, shared_state):
        super(ModernFESIndicator, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.shared_state = shared_state
        self.SetMinSize((-1, 200))  # Larger minimum height
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.previous_position = 0  # Track previous position for direction
        
        # Create sizer with labels
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddStretchSpacer()  # Top flexible space
        
        # Title
        title_label = wx.StaticText(self, label="FES Timing Indicator")
        title_label.SetForegroundColour(wx.Colour(64, 64, 64))
        title_label.SetFont(wx.Font(36, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        main_sizer.Add(title_label, 0, wx.ALIGN_CENTER)
        main_sizer.AddSpacer(60)
        
        # Labels sizer
        labels_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        release_label = wx.StaticText(self, label="")
        release_label.SetForegroundColour(wx.Colour(128, 128, 128))
        release_label.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        labels_sizer.Add(release_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        labels_sizer.AddStretchSpacer()
        
        push_label = wx.StaticText(self, label="")
        push_label.SetForegroundColour(wx.Colour(128, 128, 128))
        push_label.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        labels_sizer.Add(push_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        main_sizer.Add(labels_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 60)
        main_sizer.AddSpacer(100)
        main_sizer.AddStretchSpacer()  # Bottom flexible space
        
        self.SetSizer(main_sizer)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        size = self.GetSize()
        width, height = size.width, size.height
        
        # Draw background
        dc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()
        
        # Progress bar dimensions - much larger and centered
        bar_y = height // 2 - 25  # Center the bar vertically
        bar_height = 50  # Even thicker bar
        bar_padding = 60
        end_bar_width = 80  # Much wider end bars
        bar_width = width - (2 * bar_padding) - (2 * end_bar_width)  # Account for end bars
        main_bar_x = bar_padding + end_bar_width  # Start after the left end bar
        
        # Draw Release bar (left end)
        dc.SetBrush(wx.Brush(wx.Colour(255, 152, 0)))  # Orange for release
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRoundedRectangle(bar_padding, bar_y, end_bar_width, bar_height, 25)
        
        # Draw Press bar (right end)
        dc.SetBrush(wx.Brush(wx.Colour(76, 175, 80)))  # Green for press
        dc.DrawRoundedRectangle(bar_padding + end_bar_width + bar_width, bar_y, end_bar_width, bar_height, 25)
        
        # Draw background track (middle section)
        dc.SetBrush(wx.Brush(wx.Colour(240, 240, 240)))
        dc.DrawRoundedRectangle(main_bar_x, bar_y, bar_width, bar_height, 25)
        
        # Calculate progress based on seat position
        if self.shared_state.converted_seat_position:
            current_progress = self.shared_state.converted_seat_position[-1] / 100.0
        else:
            current_progress = 0.0
        
        # Determine direction and color
        if len(self.shared_state.converted_seat_position) >= 2:
            current_pos = self.shared_state.converted_seat_position[-1]
            prev_pos = self.shared_state.converted_seat_position[-2]
            moving_right = current_pos > prev_pos  # Moving towards push (right)
            moving_left = current_pos < prev_pos   # Moving towards release (left)
        else:
            moving_right = False
            moving_left = False
        
        # Color logic: Green when moving left, Orange when moving right
        if moving_left:
            progress_color = wx.Colour(76, 175, 80)  # Green
        elif moving_right:
            progress_color = wx.Colour(255, 152, 0)  # Orange
        else:
            progress_color = wx.Colour(158, 158, 158)  # Gray when stationary
        
        # Draw progress fill (in the middle section)
        progress_width = int(bar_width * current_progress)
        if progress_width > 0:
            dc.SetBrush(wx.Brush(progress_color))
            dc.DrawRoundedRectangle(main_bar_x, bar_y, progress_width, bar_height, 25)
        
        # Add labels for the end bars
        dc.SetTextForeground(wx.Colour(255, 255, 255))  # White text
        dc.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Release label (horizontal, centered in left bar)
        release_text_width, release_text_height = dc.GetTextExtent("RELEASE")
        release_x = bar_padding + (end_bar_width - release_text_width) // 2
        release_y = bar_y + (bar_height - release_text_height) // 2
        dc.DrawText("RELEASE", release_x, release_y)
        
        # Press label (horizontal, centered in right bar)
        press_text_width, press_text_height = dc.GetTextExtent("PRESS")
        press_x = bar_padding + end_bar_width + bar_width + (end_bar_width - press_text_width) // 2
        press_y = bar_y + (bar_height - press_text_height) // 2
        dc.DrawText("PRESS", press_x, press_y)

    def update_indicator(self):
        self.Refresh()

    def reset(self):
        self.shared_state.is_pressed = False
        self.shared_state.loading_phase = 0
        self.Refresh()

# ------------------------------------------------------------------------------------------------------------




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