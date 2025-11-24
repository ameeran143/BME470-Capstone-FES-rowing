# game page
"""
SENSOR CHANNEL MAPPING (NI-DAQ Dev2):
======================================
ai0-ai15: [UNUSED]
ai16: Left Foot Force Sensor
ai17: [UNUSED]
ai18: Right Foot Force Sensor
ai19: [UNUSED]
ai20: Handle Force Sensor
ai21: Front Potentiometer → Handle Position
ai22: Back Potentiometer → Seat Position (converted: voltage * 100)


a16:23

"""
import os
import wx
import time
import wx.grid as gridlib
import nidaqmx
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not installed - controller support disabled. Install with: pip install pygame")
import csv
import math
from map_logic import MapLogic
from settings_manager import SettingsManager
import json
from PIL import Image, ImageDraw
from scipy import signal

#Correct_Sound = pygame.mixer.Sound("Correct_Sound.wav")
#Wrong_Sound = pygame.mixer.Sound("Wrong_Sound.wav")

class ModernCard(wx.Panel):
    """A modern card panel with shadow effect and hover interaction"""
    def __init__(self, parent, label, handler=None, enabled=True, font_size=38):
        super(ModernCard, self).__init__(parent)
        self.enabled = enabled
        self.handler = handler
        self.label_text = label
        self.is_hovered = False
        self.font_size = font_size
        
        # Set base colors
        if enabled:
            self.bg_color = wx.Colour(255, 255, 255)
            self.text_color = wx.Colour(33, 37, 41)
        else:
            self.bg_color = wx.Colour(230, 230, 230)
            self.text_color = wx.Colour(150, 150, 150)
        
        self.SetBackgroundColour(self.bg_color)
        self.SetMinSize((380, 200))
        
        # Bind paint and mouse events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        if enabled and handler:
            self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
            self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
            self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        
        # Ensure the panel is shown and visible
        self.Show()
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = self.GetSize()
        
        # Ensure we have valid dimensions
        if width <= 0 or height <= 0:
            return
        
        # Draw shadow effect (subtle)
        if self.enabled and not self.is_hovered:
            shadow_color = wx.Colour(0, 0, 0, 15)
            gc.SetBrush(wx.Brush(shadow_color))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRoundedRectangle(4, 4, width - 4, height - 4, 12)
        
        # Draw card background with rounded corners
        if self.is_hovered and self.enabled and self.handler:
            # Slight elevation on hover
            bg = wx.Colour(245, 247, 250)
            border = wx.Colour(76, 175, 80)  # Green accent on hover
            gc.SetPen(wx.Pen(border, 3))
        else:
            bg = self.bg_color
            border = wx.Colour(220, 220, 220)
            gc.SetPen(wx.Pen(border, 2))
        
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(0, 0, width - 4, height - 4, 12)
        
        # Draw text with custom font size
        dc.SetFont(wx.Font(self.font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        dc.SetTextForeground(self.text_color)
        
        text_width, text_height = dc.GetTextExtent(self.label_text)
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2
        dc.DrawText(self.label_text, text_x, text_y)
    
    def OnEnter(self, event):
        if self.handler:
            self.is_hovered = True
            self.Refresh()
    
    def OnLeave(self, event):
        if self.handler:
            self.is_hovered = False
            self.Refresh()
    
    def OnClick(self, event):
        if self.enabled and self.handler:
            self.handler(event)
    
    def Enable(self, enable=True):
        """Enable or disable the button"""
        self.enabled = enable
        if enable:
            self.bg_color = wx.Colour(255, 255, 255)
            self.text_color = wx.Colour(33, 37, 41)
            if self.handler:
                self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
                self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
                self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
                self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.bg_color = wx.Colour(230, 230, 230)
            self.text_color = wx.Colour(150, 150, 150)
            self.Unbind(wx.EVT_LEFT_DOWN)
            self.Unbind(wx.EVT_ENTER_WINDOW)
            self.Unbind(wx.EVT_LEAVE_WINDOW)
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        self.SetBackgroundColour(self.bg_color)
        self.Refresh()
    
    def Disable(self):
        """Disable the button"""
        self.Enable(False)

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
        self.game_started = False  # Flag to prevent distance calculation until game is properly reset

        # sensor data
        self.handle_force = []  # Handle force (ai20)
        self.handle_position = []  # Front potentiometer (ai21) - handle position sensor
        self.raw_seat_pos = []  # Back potentiometer (ai22) - raw collected seat position at each time point
        self.converted_seat_position = []  # converted seat position at each time point (0-100 scale)
        self.seat_position_mm = []  # Seat position in mm (for CSV playback and percentile-based progress)
        self.L_foot_force = []  # Left foot force (ai16)
        self.R_foot_force = []  # Right foot force (ai18)
        self.switch_press = []  # [REMOVED - no switch sensor in new mapping]
        self.stroke_time = []  # start time of each stroke
        self.stroke_duration = []
        
        # CSV playback mode min/max values (calculated from CSV data, not calibration)
        self.csv_seat_min = None  # Minimum seat position from CSV data (in mm)
        self.csv_seat_max = None  # Maximum seat position from CSV data (in mm)

        # Mode flag: True for automatic mode, False for manual mode
        self.is_automatic_mode = False

        # FES button
        self.is_pressed = False
        self.loading_phase = 0  # 0 for orange, 1 for green
        self.button_press_seat_pos = []  # store seat position at button-press
        self.msg = False
        
        # Button press-hold-release accuracy tracking (for manual mode)
        self.button_press_accuracies = []  # List of press accuracies when button pressed (0-100%)
        self.button_release_accuracies = []  # List of release accuracies when button released (0-100%)
        self.button_combined_accuracies = []  # List of combined (press+release)/2 accuracies
        # Button push window will be loaded from settings
        self.button_press_window_mm = 160.0  # Window size in mm (±160mm from optimal position) - will be updated from settings
        self.button_press_perfect_zone_mm = 70.0  # "Perfect" zone around optimal (±70mm = 100% accuracy) - will be updated from settings
        
        # Button state tracking for press-hold-release mechanism
        self.button_currently_held = False  # True when button is currently held down
        self.button_press_position_mm = None  # Position where button was pressed
        self.button_press_accuracy_temp = None  # Temporary storage for press accuracy until release

        # for calibration
        self.front_max_pos = 520  # fake data equal 100
        self.back_max_pos = 43  # fake data equal 0
        self.fes_active_pos = self.front_max_pos - 96.5 # constant (different for each user)
        self.seat_direction = 0  # fake data
        self.converted_fes_pos = 100 - (self.fes_active_pos - self.front_max_pos) / (self.back_max_pos - self.front_max_pos) * 100
        self.userID = None
        self.user_name = "demo"  # Default demo user name
        self.age = 0
        self.height = 0
        self.weight = 0
        self.same_stroke = False

        # File to store stats
        self.stats_file_path = None
        self.accounts_file = os.path.join(os.path.dirname(__file__), "user_accounts.json")
        self.total_distance = 0.0
        self.session_rowing_time = 0.0 # Time spent rowing (power > 0) in seconds
        self.cumulative_distance_live = 0.0
        self.cumulative_distance_saved = 0.0
        self.cumulative_time_live = 0.0 # Base cumulative rowing time from file
        self._cumulative_loaded = False
        self._last_cumulative_persist = 0
        self._cumulative_user = None
        self.ensure_cumulative_distance_loaded()
        
        self.settings_manager = SettingsManager()
        
        # Load button push window from settings (one side in mm)
        button_push_window_one_side = self.settings_manager.get_button_push_window()
        self.button_press_perfect_zone_mm = button_push_window_one_side  # One side value
        
        # Hardware testing - Auto-detect OS
        import platform
        self.is_mac = platform.system() == 'Darwin'
        self.hardware_mode = not self.is_mac  # Disable hardware mode on Mac
        self.hardware_connected = True
        self.last_hardware_check = 0
        
        # Mode control: "hardware", "csv_playback", or None
        self.current_mode = None  # Will be determined by detect_mode()
        self.mode_override = "csv_playback"  # Force CSV playback mode (uses hikaru data)
        
        # CSV playback mode (replay data from sensor CSV files)
        self.anc_playback_mode = False
        self.anc_data = []  # list of tuples: (L_foot, R_foot, handle_force, handle_pos, raw_seat_pos)
        self.anc_index = 0
        self.anc_extra = []  # list of tuples: (time, ...) or other auxiliary columns
        self.anc_playback_start_time = None  # Track playback start time
        self.anc_source_type = "csv_voltage"  # csv_voltage | other
        self.anc_sampling_rate = 10  # Hz (default, will be estimated from CSV)
        self.anc_index_step = 1  # Default downsampling factor for playback
        self.anc_power_series = []
        
        # Hardware mode raw voltage storage for processing
        self.hardware_raw_voltages = {
            'handle_force': [],
            'handle_position': [],
            'seat_position': [],
            'left_foot': [],
            'right_foot': []
        }
        self.hardware_processing_buffer_size = 100  # Buffer size for filtering
        self.hardware_min_values = {
            'handle_force': None,
            'handle_position': None,
            'seat_position': None
        }
        self.hardware_volts_to_mm_factor = 2032.0 / 10.0  # Conversion factor for potentiometers
        self.hardware_sampling_rate = 10.0  # Hz (will be estimated from timing)
        
        # Hardware task for persistent connection (B - from game_page.py)
        self.hardware_task = None  # Persistent task for sensor readings
        
        # Location override for manual control or automatic switching
        # None = automatic (switches to Japan after 30 minutes)
        # "Hawaii" = force Hawaii location
        # "Japan" = force Japan location
        self.location_override = None  # Set to "Japan", "Antarctica", "Amazon", "Australia" or "Hawaii" for manual control, None for auto
        self.current_location = "Hawaii"  # Current location name (updated by RowingScenePanel)
        
        # Don't auto-detect mode here - wait until game page is activated
        # Mode will be detected when reset_game() is called
        # Hardware task initialization will happen after mode detection in reset_game()
    
    def test_hardware_connection(self):
        """Test if NI-DAQ device is connected and responsive"""
        if self.is_mac:
            return False  # Hardware not supported on macOS
        
        try:
            # Get hardware settings
            hw_settings = self.settings_manager.get_hardware_settings()
            dev_number = hw_settings.get("dev_number", 1)
            left_foot_ch = hw_settings.get("left_foot_force_channel", 16)
            right_foot_ch = hw_settings.get("right_foot_force_channel", 18)
            handle_ch = hw_settings.get("handle_force_channel", 20)
            front_pot_ch = hw_settings.get("front_potentiometer_channel", 21)
            back_pot_ch = hw_settings.get("back_potentiometer_channel", 22)
            voltage = hw_settings.get("voltage_v", 5.0)
            
            with nidaqmx.Task() as task:
                # Test with channel mapping from settings
                task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{left_foot_ch}",
                                                     terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                     min_val=0.0, max_val=10.0)
                task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{right_foot_ch}",
                                                     terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                     min_val=0.0, max_val=10.0)
                task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{handle_ch}",
                                                     terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                     min_val=0.0, max_val=10.0)
                task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{front_pot_ch}",
                                                     terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                     min_val=0.0, max_val=10.0)
                task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{back_pot_ch}",
                                                     terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                     min_val=0.0, max_val=10.0)
                return True
        except Exception as e:
            print(f"Hardware connection test failed: {e}")
            return False
    
    def find_csv_recordings(self):
        """Find available CSV recording files in Test_Recordings directory"""
        csv_files = []
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))
            recordings_dir = os.path.join(project_root, "Test_Recordings")
            
            if not os.path.exists(recordings_dir):
                return csv_files
            
            # Search for sensor_data.csv files in subdirectories
            for root, dirs, files in os.walk(recordings_dir):
                for file in files:
                    if file == "sensor_data.csv":
                        csv_path = os.path.join(root, file)
                        csv_files.append(csv_path)
            
            # Sort by modification time (newest first)
            csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        except Exception as e:
            print(f"Error searching for CSV files: {e}")
        
        return csv_files
    
    def load_calibration_data(self, userID=None):
        """Load calibration data from JSON file.
        
        Args:
            userID: Deprecated parameter (kept for compatibility, but not used).
        
        Returns:
            bool: True if calibration data was loaded successfully, False otherwise
        """
        try:
            calib_dir = os.path.join(os.path.dirname(__file__), "Calibration_Data")
            
            if not os.path.exists(calib_dir):
                print("Calibration_Data directory not found")
                return False
            
            # Load the latest calibration file
            calib_file = os.path.join(calib_dir, "calibration_latest.json")
            
            if not os.path.exists(calib_file):
                print(f"Calibration file not found: {calib_file}")
                return False
            
            # Load calibration data
            with open(calib_file, 'r') as f:
                calib_data = json.load(f)
            
            # Update shared_state with calibration values only (zero-shifted positions)
            self.front_max_pos = calib_data.get("front_max_pos", self.front_max_pos)
            self.back_max_pos = calib_data.get("back_max_pos", self.back_max_pos)
            # Calculate fes_active_pos and converted_fes_pos from zero-shifted positions
            self.fes_active_pos = self.front_max_pos - 96.5
            if self.back_max_pos != self.front_max_pos:
                self.converted_fes_pos = 100 - (self.fes_active_pos - self.front_max_pos) / (self.back_max_pos - self.front_max_pos) * 100
            else:
                self.converted_fes_pos = 0
            
            return True
            
        except Exception as e:
            print(f"Failed to load calibration data: {e}")
            return False
    
    def detect_and_set_mode(self):
        """Detect and set the appropriate mode based on priority:
        1. Hardware (if connected)
        2. CSV playback (if CSV files found - uses hikaru data)
        """
        # Check for manual override
        if self.mode_override:
            mode = self.mode_override
            # If overriding to CSV playback, load the hikaru CSV file
            if mode == "csv_playback":
                project_root = os.path.dirname(os.path.dirname(__file__))
                default_csv_path = os.path.join(project_root, "Test_Recordings", "hikaru", "sensor_data.csv")
                if os.path.exists(default_csv_path):
                    try:
                        self.load_sensor_csv(default_csv_path)
                    except Exception as e:
                        print(f"⚠️  Failed to load hikaru CSV: {e}")
                        mode = None
                else:
                    print(f"⚠️  Hikaru CSV not found at: {default_csv_path}")
                    mode = None
        else:
            # Auto-detect mode based on priority
            # Priority 1: Hardware
            if not self.is_mac and self.test_hardware_connection():
                mode = "hardware"
            else:
                # Priority 2: CSV playback - check for default CSV first
                project_root = os.path.dirname(os.path.dirname(__file__))
                default_csv_path = os.path.join(project_root, "Test_Recordings", "hikaru", "sensor_data.csv")
                
                if os.path.exists(default_csv_path):
                    try:
                        self.load_sensor_csv(default_csv_path)
                        mode = "csv_playback"
                    except Exception as e:
                        print(f"⚠️  Failed to load CSV: {e}")
                        mode = None
                else:
                    # No CSV found - mode will remain None (silent fallback)
                    mode = None
        
        # Set the mode
        self.current_mode = mode
        
        # Load calibration data only for hardware mode
        if mode == "hardware":
            calib_loaded = self.load_calibration_data()
            if not calib_loaded:
                # Display error message if calibration data not found
                import wx
                error_msg = (
                    "⚠️  CALIBRATION DATA NOT FOUND\n\n"
                    "Hardware acquisition mode requires calibration data.\n"
                    "Please run calibration first before using hardware mode.\n\n"
                    "Cannot proceed without calibration."
                )
                # Show wx message box if wx is available
                try:
                    wx.MessageBox(error_msg, "Calibration Required", wx.OK | wx.ICON_WARNING)
                except:
                    pass
                # Cannot use hardware without calibration
                print("❌ Cannot use hardware mode without calibration data")
                mode = None
                self.current_mode = mode
                self.hardware_mode = False
                self.hardware_connected = False
        
        # Configure mode-specific settings
        if mode == "hardware":
            self.hardware_mode = True
            self.anc_playback_mode = False
            self.hardware_connected = True
        elif mode == "csv_playback":
            self.hardware_mode = False
            self.anc_playback_mode = True
            self.hardware_connected = False
        else:  # No valid mode
            self.hardware_mode = False
            self.anc_playback_mode = False
            self.hardware_connected = False
            # No data source configured (silent - will be detected later in reset_game)
    
    def set_mode(self, mode, csv_path=None):
        """Manually set the mode. Modes: 'hardware' or 'csv_playback'
        
        Args:
            mode: 'hardware' for sensor mode, 'csv_playback' for CSV playback, or None for auto-detect
            csv_path: Optional path to CSV file (required if mode is 'csv_playback')
        
        Returns:
            True if mode was set successfully, False otherwise
        """

        print(f"Setting mode: {mode}")
        if mode is None:
            self.mode_override = None
            self.detect_and_set_mode()
        elif mode == "hardware":
            if self.is_mac:
                return False
            if not self.test_hardware_connection():
                return False
            # Check for calibration data
            calib_loaded = self.load_calibration_data()
            if not calib_loaded:
                # Display error message if calibration data not found
                import wx
                error_msg = (
                    "⚠️  CALIBRATION DATA NOT FOUND\n\n"
                    "Hardware acquisition mode requires calibration data.\n"
                    "Please run calibration first before using hardware mode.\n\n"
                    "Cannot switch to hardware mode."
                )
                # Show wx message box if wx is available
                try:
                    wx.MessageBox(error_msg, "Calibration Required", wx.OK | wx.ICON_WARNING)
                except:
                    pass
                return False
            self.mode_override = "hardware"
            self.current_mode = "hardware"
            self.hardware_mode = True
            self.anc_playback_mode = False
            self.hardware_connected = True
            return True
        elif mode == "csv_playback":
            if csv_path:
                try:
                    self.load_sensor_csv(csv_path)
                except Exception as e:
                    print(f"⚠️  Failed to load CSV: {e}")
                    return False
            elif not self.anc_data:
                # Check for default CSV first
                project_root = os.path.dirname(os.path.dirname(__file__))
                default_csv_path = os.path.join(project_root, "Test_Recordings", "hikaru", "sensor_data.csv")
                
                if os.path.exists(default_csv_path):
                    try:
                        self.load_sensor_csv(default_csv_path)
                    except Exception as e:
                        print(f"⚠️  Failed to load CSV: {e}")
                        return False
                else:
                    print(f"⚠️  Default CSV not found at: {default_csv_path}")
                    print("   Cannot switch to CSV playback mode")
                    return False
            self.mode_override = "csv_playback"
            self.current_mode = "csv_playback"
            self.hardware_mode = False
            self.anc_playback_mode = True
            self.hardware_connected = False
            return True
        else:
            print(f"❌ Invalid mode: {mode}")
            return False
    
    def convert_raw_to_scale(self, raw_pos):
        """Convert raw seat position to 0-100 scale"""
        if raw_pos:
            # Use CSV min/max if in CSV playback mode, otherwise use calibration values
            if self.current_mode == "csv_playback" and self.csv_seat_min is not None and self.csv_seat_max is not None:
                # Use CSV-derived min/max values
                converted = 100 - (raw_pos - self.csv_seat_max) / (self.csv_seat_min - self.csv_seat_max) * 100
            else:
                # Use calibration values (for hardware mode)
                converted = 100 - (raw_pos - self.front_max_pos) / (self.back_max_pos - self.front_max_pos) * 100
            return converted
        return None
    
    def convert_scale_to_raw(self, converted):
        if converted is not None:
            raw_pos = self.front_max_pos + (100 - converted) / 100 * (self.back_max_pos - self.front_max_pos)
            return raw_pos
        return None
    
    def set_user_name(self, username):
        """Set the current user name and ensure their directory exists"""
        if not username:
            username = "demo"
        
        self.user_name = username
        
        # Ensure user directory exists
        self.get_user_data_dir()
        
        # Reset cumulative distance loading so it reloads for the new user
        self._cumulative_loaded = False
        self._cumulative_user = None
    
    def get_user_data_dir(self):
        """Get the user-specific data directory, creating it if needed"""
        # Use user_name for folder name, sanitize for filesystem
        if not self.user_name:
            self.user_name = "demo"
        
        # Sanitize user name for filesystem (remove invalid characters)
        safe_name = "".join(c for c in self.user_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            safe_name = "demo"
        
        # Create user-specific subfolder
        base_dir = os.path.join(os.path.dirname(__file__), "user_session_data")
        user_dir = os.path.join(base_dir, safe_name)
        os.makedirs(user_dir, exist_ok=True)
        
        # Ensure session_summary.csv file exists (create with headers if it doesn't exist)
        csv_file = os.path.join(user_dir, "session_summary.csv")
        if not os.path.exists(csv_file):
            try:
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Date', 'Name', 'Total Time (min:sec)', 'Average Power (W)', 'Total Distance (m)', 'Average Accuracy (%)', 'Rowing Time (s)'])
            except Exception as e:
                print(f"Error creating session_summary.csv for {safe_name}: {e}")
        
        return user_dir
    
    def ensure_cumulative_distance_loaded(self):
        """Load cumulative stats for the active user from user_accounts.json"""
        current_user = self.user_name or "demo"
        if self._cumulative_loaded and self._cumulative_user == current_user:
            return
        
        self._cumulative_user = current_user
        cumulative_dist = 0.0
        cumulative_time = 0.0
        try:
            accounts = self._load_accounts_data()
            user_entry = accounts.get(current_user, {})
            cumulative_dist = float(user_entry.get("cumulative_distance_m", 0.0))
            cumulative_time = float(user_entry.get("cumulative_rowing_time_seconds", 0.0))
        except Exception as e:
            print(f"Failed to load cumulative stats for {current_user}: {e}")
        
        self.cumulative_distance_live = cumulative_dist
        self.cumulative_time_live = cumulative_time
        self._cumulative_loaded = True
        self._last_cumulative_persist = time.time()
    
    def _load_accounts_data(self):
        """Read user_accounts.json and return dict"""
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Unable to read accounts file: {e}")
        return {}
    
    def _save_accounts_data(self, data):
        """Write updated accounts JSON to disk"""
        try:
            with open(self.accounts_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Unable to save accounts file: {e}")
    
    def _maybe_persist_cumulative_distance(self, force=False):
        """DISABLED: Cumulative distance is now calculated from session summaries by dashboard.
        Do not persist cumulative distance from game screen - it conflicts with dashboard calculation."""
        # Do nothing - cumulative distance is calculated from session summaries
        pass
    
    def force_persist_cumulative_distance(self):
        """DISABLED: Cumulative distance is now calculated from session summaries by dashboard."""
        # Do nothing - cumulative distance is calculated from session summaries
        pass
    
    def increment_cumulative_distance(self, distance_increment):
        """DISABLED: Do not increment cumulative_distance_live during game.
        Cumulative distance is calculated from session summaries by dashboard.
        For display during game, we use: base_cumulative (from sessions) + current session distance."""
        # Do nothing - cumulative distance is calculated from session summaries
        pass
    
    def get_cumulative_total_distance(self):
        """Return cumulative distance for display: base (from sessions) + current session distance."""
        self.ensure_cumulative_distance_loaded()
        return self.cumulative_distance_live + self.total_distance

    def get_cumulative_total_rowing_time(self):
        """Return cumulative rowing time (seconds) for display/logic."""
        self.ensure_cumulative_distance_loaded()
        return self.cumulative_time_live + self.session_rowing_time
        
    def create_stats_file(self):
        """Disabled - no longer creating rowing stats files, only session summaries"""
        # Do nothing - rowing stats files are no longer needed
        pass

    def load_sensor_csv(self, file_path):
        """Load sensor playback data from a CSV file with columns:
        Time (s), Left Foot, Right Foot, Handle Force, Handle Position, Seat Position.
        """
        self.anc_data = []
        self.anc_extra = []
        self.anc_index = 0
        self.anc_playback_start_time = None
        self.anc_source_type = "csv_voltage"
        self.anc_sampling_rate = 10  # Start with a safe default
        self.anc_index_step = 1
        intervals = []
        last_time = None
        try:
            with open(file_path, 'r', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                col_map = None
                if headers:
                    col_map = {name.strip().lower(): idx for idx, name in enumerate(headers)}
                for row in reader:
                    if not row or all(cell.strip() == "" for cell in row):
                        continue
                    try:
                        # Attempt to map columns by header name if available
                        if col_map and len(headers) >= 6:
                            time_idx = col_map.get("time (s)", 0)
                            left_idx = col_map.get("left foot (ai16)", 1)
                            right_idx = col_map.get("right foot (ai18)", 2)
                            handle_force_idx = col_map.get("handle force (ai20)", 3)
                            handle_pos_idx = col_map.get("handle position (ai21)", 4)
                            seat_idx = col_map.get("seat position (ai22)", 5)
                        else:
                            time_idx, left_idx, right_idx, handle_force_idx, handle_pos_idx, seat_idx = range(6)
                        time_val = float(row[time_idx])
                        l_foot = float(row[left_idx])
                        r_foot = float(row[right_idx])
                        handle_force = float(row[handle_force_idx])
                        handle_pos = float(row[handle_pos_idx])
                        seat_pos = float(row[seat_idx])
                    except (ValueError, IndexError):
                        continue

                    handle_force = self._convert_handle_force_voltage(handle_force)
                    self.anc_data.append((l_foot, r_foot, handle_force, handle_pos, seat_pos))
                    self.anc_extra.append((time_val,))
                    if last_time is not None:
                        dt = time_val - last_time
                        if dt > 0:
                            intervals.append(dt)
                    last_time = time_val

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                if avg_interval > 0:
                    self.anc_sampling_rate = 1.0 / avg_interval
            self.anc_index_step = max(1, int(round(self.anc_sampling_rate / 10.0))) if self.anc_sampling_rate > 0 else 1

            # Trim first and last 5 seconds of data
            if self.anc_data and self.anc_sampling_rate > 0:
                samples_to_trim = int(5.0 * self.anc_sampling_rate)
                if len(self.anc_data) > samples_to_trim * 2:
                    # Trim first 5 seconds
                    self.anc_data = self.anc_data[samples_to_trim:]
                    self.anc_extra = self.anc_extra[samples_to_trim:]
                    # Trim last 5 seconds
                    self.anc_data = self.anc_data[:-samples_to_trim]
                    self.anc_extra = self.anc_extra[:-samples_to_trim]

            if self.anc_data:
                self._process_data()
                # Plotting disabled for CSV playback mode
                # self.plot_anc_data(file_path)
        except Exception as e:
            print(f"Failed to load sensor CSV: {e}")

    def _process_data(self):
        """Apply Butterworth low-pass filter and remap seat position to millimeters."""
        if not self.anc_data or len(self.anc_data) == 0:
            return
        
        try:
            # Extract columns
            handle_force_data = [row[2] for row in self.anc_data]
            handle_data = [row[3] for row in self.anc_data]
            seat_data = [row[4] for row in self.anc_data]
            
            # Sampling frequency (default to 10 Hz if unknown)
            fs = self.anc_sampling_rate if self.anc_sampling_rate and self.anc_sampling_rate > 0 else 10
            cutoff = 10.0  # Hz
            nyquist = fs / 2

            def _filter_channel(series):
                if not series:
                    return series
                if nyquist <= 0:
                    return series
                local_cutoff = cutoff
                if local_cutoff >= nyquist:
                    local_cutoff = max(0.1, nyquist * 0.9)
                normal_cutoff = local_cutoff / nyquist
                if normal_cutoff >= 1.0 or normal_cutoff <= 0.0:
                    return series
                b, a = signal.butter(4, normal_cutoff, btype='low')
                return signal.filtfilt(b, a, series)

            filtered_force = _filter_channel(handle_force_data)
            filtered_handle = _filter_channel(handle_data)
            filtered_seat = _filter_channel(seat_data)

            # Ensure array-like results are plain lists
            if hasattr(filtered_force, "tolist"):
                filtered_force = filtered_force.tolist()
            if hasattr(filtered_handle, "tolist"):
                filtered_handle = filtered_handle.tolist()
            if hasattr(filtered_seat, "tolist"):
                filtered_seat = filtered_seat.tolist()

            min_force_raw = min(filtered_force)
            max_force_raw = max(filtered_force)
            min_handle_raw = min(filtered_handle)
            max_handle_raw = max(filtered_handle)
            min_seat_raw = min(filtered_seat)
            max_seat_raw = max(filtered_seat)

            if self.anc_source_type == "csv_voltage":
                # Inputs are 0-10 V → convert to mm and shift to start at 0
                volts_to_mm_factor = 2032.0 / 10.0 # this is the conversion factor for the seat position sensor
                #because the potentiometer range is 0-10V and maps to 0-2032, we need to use the conversion factor to convert the voltage to mm
                remapped_seat = [(x * volts_to_mm_factor) for x in filtered_seat]
                remapped_handle = [(x * volts_to_mm_factor) for x in filtered_handle]
                remapped_force = [x - min_force_raw for x in filtered_force]
                handle_min_shift = min(remapped_handle)
                seat_min_shift = min(remapped_seat)
                remapped_handle = [x - handle_min_shift for x in remapped_handle]
                remapped_seat = [x - seat_min_shift for x in remapped_seat]
            else:
                # For unknown sources, rescale to 0-2032 mm based on observed range
                seat_rng = max_seat_raw - min_seat_raw
                handle_rng = max_handle_raw - min_handle_raw
                force_rng = max_force_raw - min_force_raw
                if seat_rng <= 0:
                    remapped_seat = [0.0 for _ in filtered_seat]
                else:
                    remapped_seat = [((x - min_seat_raw) / seat_rng) * 2032.0 for x in filtered_seat]
                if handle_rng <= 0:
                    remapped_handle = [0.0 for _ in filtered_handle]
                else:
                    remapped_handle = [((x - min_handle_raw) / handle_rng) * 2032.0 for x in filtered_handle]
                if force_rng <= 0:
                    remapped_force = [0.0 for _ in filtered_force]
                else:
                    remapped_force = [x - min_force_raw for x in filtered_force]

            # Ensure force baseline is zero
            if remapped_force:
                force_min = min(remapped_force)
                remapped_force = [x - force_min for x in remapped_force]
            
            # Calculate release and press positions for FES timing indicator
            import numpy as np
            seat_array = np.array(remapped_seat)
            self.seat_position_release = max(seat_array)* 0.15  #the optimal timing for anterior position is not defined yet, so set to 15th percentile for now 
            self.seat_position_press = max(seat_array) - 140  #set it to 140 mm seat position from the front, max(seat_array) would be based on the calibrated values in practice
            
            # Store CSV min/max values for use in CSV playback mode (not calibration values)
            self.csv_seat_min = min(seat_array)
            self.csv_seat_max = max(seat_array)
            
            # Update the anc_data with filtered and remapped channels
            self.anc_data = [
                (row[0], row[1], new_force, new_handle, new_seat)
                for row, new_force, new_handle, new_seat in zip(self.anc_data, remapped_force, remapped_handle, remapped_seat)
            ]

            # Pre-compute instantaneous power using the same formula as runtime
            self.anc_power_series = []
            prev_force = None
            prev_handle = None
            dt = 1.0 / self.anc_sampling_rate if self.anc_sampling_rate and self.anc_sampling_rate > 0 else None
            for idx, (_l, _r, force_val, handle_val, _seat_val) in enumerate(self.anc_data):
                if dt is None or idx == 0 or prev_force is None or prev_handle is None or dt <= 0:
                    self.anc_power_series.append(0.0)
                else:
                    avg_force = (force_val + prev_force) / 2.0 #N
                    delta_handle = abs(handle_val - prev_handle) #mm 
                    power_val = avg_force * delta_handle / dt / 1000 if dt else 0.0 #W
                    self.anc_power_series.append(power_val)
                prev_force = force_val
                prev_handle = handle_val
            
            source_units_map = {
                "csv_voltage": "V",
            }
            source_units = source_units_map.get(self.anc_source_type, "raw units")
            force_units = "raw units"
            if self.anc_source_type == "csv_voltage":
                force_units = "N"
            
        except Exception as e:
            print(f"Failed to process seat position: {e}")

    def _process_hardware_data(self, handle_force_voltage, handle_position_voltage, seat_position_voltage):
        """Process hardware sensor data using the same method as CSV playback mode.
        Applies Butterworth filter, converts voltages to physical units, and zero-shifts.
        Returns: (processed_handle_force_N, processed_handle_position_mm, processed_seat_position_mm)
        """
        try:
            # Store raw voltages
            self.hardware_raw_voltages['handle_force'].append(handle_force_voltage)
            self.hardware_raw_voltages['handle_position'].append(handle_position_voltage)
            self.hardware_raw_voltages['seat_position'].append(seat_position_voltage)
            
            # Keep buffer size manageable
            if len(self.hardware_raw_voltages['handle_force']) > self.hardware_processing_buffer_size:
                self.hardware_raw_voltages['handle_force'] = self.hardware_raw_voltages['handle_force'][-self.hardware_processing_buffer_size:]
                self.hardware_raw_voltages['handle_position'] = self.hardware_raw_voltages['handle_position'][-self.hardware_processing_buffer_size:]
                self.hardware_raw_voltages['seat_position'] = self.hardware_raw_voltages['seat_position'][-self.hardware_processing_buffer_size:]
            
            # Need at least a few samples for filtering
            if len(self.hardware_raw_voltages['handle_force']) < 10:
                # Not enough data yet, use simple conversion without filtering
                handle_force_N = self._convert_handle_force_voltage(handle_force_voltage)
                handle_position_mm = handle_position_voltage * self.hardware_volts_to_mm_factor
                seat_position_mm = seat_position_voltage * self.hardware_volts_to_mm_factor
                
                # Track minimums for zero-shifting
                if self.hardware_min_values['handle_force'] is None:
                    self.hardware_min_values['handle_force'] = handle_force_N
                else:
                    self.hardware_min_values['handle_force'] = min(self.hardware_min_values['handle_force'], handle_force_N)
                
                if self.hardware_min_values['handle_position'] is None:
                    self.hardware_min_values['handle_position'] = handle_position_mm
                else:
                    self.hardware_min_values['handle_position'] = min(self.hardware_min_values['handle_position'], handle_position_mm)
                
                if self.hardware_min_values['seat_position'] is None:
                    self.hardware_min_values['seat_position'] = seat_position_mm
                else:
                    self.hardware_min_values['seat_position'] = min(self.hardware_min_values['seat_position'], seat_position_mm)
                
                # Apply zero-shifting
                handle_force_N = handle_force_N - self.hardware_min_values['handle_force']
                handle_position_mm = handle_position_mm - self.hardware_min_values['handle_position']
                seat_position_mm = seat_position_mm - self.hardware_min_values['seat_position']
                
                return handle_force_N, handle_position_mm, seat_position_mm
            
            # Apply Butterworth filter (same as CSV processing)
            fs = self.hardware_sampling_rate if self.hardware_sampling_rate > 0 else 10.0
            cutoff = 10.0  # Hz
            nyquist = fs / 2
            
            def _filter_channel(series):
                if not series or len(series) < 4:
                    return series
                if nyquist <= 0:
                    return series
                local_cutoff = cutoff
                if local_cutoff >= nyquist:
                    local_cutoff = max(0.1, nyquist * 0.9)
                normal_cutoff = local_cutoff / nyquist
                if normal_cutoff >= 1.0 or normal_cutoff <= 0.0:
                    return series
                b, a = signal.butter(4, normal_cutoff, btype='low')
                filtered = signal.filtfilt(b, a, series)
                return filtered.tolist() if hasattr(filtered, "tolist") else filtered
            
            # Filter the voltage series
            filtered_force_voltage = _filter_channel(self.hardware_raw_voltages['handle_force'])
            filtered_handle_voltage = _filter_channel(self.hardware_raw_voltages['handle_position'])
            filtered_seat_voltage = _filter_channel(self.hardware_raw_voltages['seat_position'])
            
            # Get the latest filtered value
            if filtered_force_voltage:
                latest_force_voltage = filtered_force_voltage[-1]
            else:
                latest_force_voltage = handle_force_voltage
            
            if filtered_handle_voltage:
                latest_handle_voltage = filtered_handle_voltage[-1]
            else:
                latest_handle_voltage = handle_position_voltage
            
            if filtered_seat_voltage:
                latest_seat_voltage = filtered_seat_voltage[-1]
            else:
                latest_seat_voltage = seat_position_voltage
            
            # Convert voltages to physical units (same as CSV processing)
            # Handle force: voltage to Newtons
            handle_force_N = self._convert_handle_force_voltage(latest_force_voltage)
            
            # Handle position and seat position: voltage to mm
            handle_position_mm = latest_handle_voltage * self.hardware_volts_to_mm_factor
            seat_position_mm = latest_seat_voltage * self.hardware_volts_to_mm_factor
            
            # Track minimums for zero-shifting
            if self.hardware_min_values['handle_force'] is None:
                self.hardware_min_values['handle_force'] = handle_force_N
            else:
                self.hardware_min_values['handle_force'] = min(self.hardware_min_values['handle_force'], handle_force_N)
            
            if self.hardware_min_values['handle_position'] is None:
                self.hardware_min_values['handle_position'] = handle_position_mm
            else:
                self.hardware_min_values['handle_position'] = min(self.hardware_min_values['handle_position'], handle_position_mm)
            
            if self.hardware_min_values['seat_position'] is None:
                self.hardware_min_values['seat_position'] = seat_position_mm
            else:
                self.hardware_min_values['seat_position'] = min(self.hardware_min_values['seat_position'], seat_position_mm)
            
            # Apply zero-shifting (same as CSV processing)
            handle_force_N = handle_force_N - self.hardware_min_values['handle_force']
            handle_position_mm = handle_position_mm - self.hardware_min_values['handle_position']
            seat_position_mm = seat_position_mm - self.hardware_min_values['seat_position']
            
            return handle_force_N, handle_position_mm, seat_position_mm
            
        except Exception as e:
            print(f"Hardware data processing error: {e}")
            # Fallback to simple conversion without filtering
            handle_force_N = self._convert_handle_force_voltage(handle_force_voltage)
            handle_position_mm = handle_position_voltage * self.hardware_volts_to_mm_factor
            seat_position_mm = seat_position_voltage * self.hardware_volts_to_mm_factor
            return handle_force_N, handle_position_mm, seat_position_mm

    def _convert_handle_force_voltage(self, voltage):
        """Convert handle force sensor voltage to force (N) using calibration."""

        #this conversoin is done by the following equation
        #recorded voltage / (sensitivity*excitation voltage ) * rated capacity mass (kg) * gravity (m/s^2)
        #note that sensitivity is 2.0 mv/V and excitation voltage is from settings, rated capacity mass is 250 kg and gravity is 9.81 m/s^2
        #assume amplification of 1000 times
        try:
            # Get voltage from hardware settings
            excitation_voltage = self.settings_manager.get_hardware_setting("voltage_v")
            return (voltage / (2.0 * excitation_voltage) * 250.0 * 9.81)
        except Exception as e:
            print(f"Error converting handle force voltage: {voltage}, error: {e}")
            print(f"Sensitivity: 2.0 mv/V")
            print(f"Rated capacity mass: 250 kg")
            print(f"Gravity: 9.81 m/s^2")
            # Fallback to default voltage if settings unavailable
            return (voltage / (2.0 * 5.0)) * 250.0 * 9.81
            return voltage

    def plot_anc_data(self, src_path):
        """Create a PNG plot with separate channel panels and open it (macOS)."""
        if not self.anc_data:
            return
        try:
            from PIL import Image, ImageDraw, ImageFont
            width, height = 1400, 900
            margin_left, margin_right, margin_top, margin_bottom = 110, 30, 70, 60
            panel_gap = 20
            num_channels = 5
            total_gap = panel_gap * (num_channels - 1)
            available_h = height - margin_top - margin_bottom - total_gap
            panel_h = max(80, available_h // num_channels)
            plot_w = width - margin_left - margin_right
            img = Image.new('RGB', (width, height), (255, 255, 255))
            draw = ImageDraw.Draw(img)

            # Prepare series and metadata
            series = []
            labels = []
            colors = []

            if self.anc_extra:
                series_extra = list(zip(*self.anc_extra))
                extra_colors = [(0, 0, 0), (128, 128, 128), (169, 169, 169)]
                for idx, extra in enumerate(series_extra):
                    if self.anc_source_type == "csv_voltage" and idx == 0:
                        label = "Time (s)"
                    else:
                        label = f"Extra {idx + 1}"
                    series.append(extra)
                    labels.append(label)
                    colors.append(extra_colors[idx % len(extra_colors)])

            series_main = list(zip(*self.anc_data))  # [(L),(R),(HF),(HP),(Seat)]
            main_labels = ["L Foot", "R Foot", "Handle Force (N)", "Handle Pos (mm)", "Seat Pos (mm)"]
            main_colors = [
                (220, 20, 60), (65, 105, 225), (34, 139, 34), (255, 140, 0), (128, 0, 128)
            ]
            for idx, data in enumerate(series_main):
                label = main_labels[idx] if idx < len(main_labels) else f"Channel {idx+1}"
                series.append(data)
                labels.append(label)
                colors.append(main_colors[idx % len(main_colors)])

            if self.anc_power_series:
                series.append(self.anc_power_series)
                labels.append("Power (W)")
                colors.append((0, 100, 0))
            n = len(self.anc_data)

            # Title
            title = f"CSV Plot: {os.path.basename(src_path)}"
            draw.text((margin_left, 20), title, fill=(0, 0, 0))

            # Draw each channel in its own panel
            num_channels = len(series)
            total_gap = panel_gap * (num_channels - 1)
            available_h = height - margin_top - margin_bottom - total_gap
            panel_h = max(80, available_h // max(1, num_channels))
            for ch in range(num_channels):
                data = series[ch]
                color = colors[ch]
                label = labels[ch]
                smin = min(data)
                smax = max(data)
                rng = (smax - smin) if (smax > smin) else 1.0
                origin_x = margin_left
                origin_y = margin_top + ch * (panel_h + panel_gap)
                # Panel border
                draw.rectangle([origin_x, origin_y, origin_x + plot_w, origin_y + panel_h], outline=(200, 200, 200), width=1)
                # Channel label and range annotations
                draw.text((origin_x - 100, origin_y + 5), label, fill=(0, 0, 0))
                draw.text((origin_x + plot_w + 6, origin_y), f"max {smax:.2f}", fill=(80, 80, 80))
                draw.text((origin_x + plot_w + 6, origin_y + panel_h - 16), f"min {smin:.2f}", fill=(80, 80, 80))
                # Y-axis ticks with numeric labels (5 ticks including min/max)
                tick_n = 5
                for t in range(tick_n):
                    frac = t / (tick_n - 1) if tick_n > 1 else 0
                    val = smax - frac * rng
                    y = origin_y + int(frac * (panel_h - 2))
                    # Grid line
                    draw.line([origin_x, y, origin_x + plot_w, y], fill=(235, 235, 235), width=1)
                    # Tick marker
                    draw.line([origin_x - 6, y, origin_x, y], fill=(120, 120, 120), width=1)
                    # Label - shifted further left to avoid overlap, positioned higher
                    draw.text((origin_x - 90, max(origin_y, min(origin_y + panel_h - 12, y ))), f"{val:.2f}", fill=(60, 60, 60))
                # Polyline
                prev = None
                for i, v in enumerate(data):
                    x = origin_x + int(i / max(1, n - 1) * plot_w)
                    y_norm = (v - smin) / rng
                    y = origin_y + panel_h - 1 - int(y_norm * (panel_h - 2))
                    if prev is not None:
                        draw.line([prev, (x, y)], fill=color, width=2)
                    prev = (x, y)
                # Zero/reference line if 0 in range
                if smin < 0 < smax:
                    zero_y = origin_y + panel_h - 1 - int((0 - smin) / rng * (panel_h - 2))
                    draw.line([origin_x, zero_y, origin_x + plot_w, zero_y], fill=(220, 220, 220), width=1)

            # Shared X-axis ticks (sample index)
            tick_count = 10
            for t in range(tick_count + 1):
                frac = t / tick_count
                x = margin_left + int(frac * plot_w)
                y0 = margin_top + num_channels * (panel_h + panel_gap) - panel_gap
                draw.line([x, y0 - 4, x, y0], fill=(160, 160, 160))
                idx = int(frac * (n - 1)) if n > 0 else 0
                draw.text((x - 10, y0 + 6), str(idx), fill=(0, 0, 0))

            # Save next to Training_Data
            out_dir = os.path.join(os.path.dirname(__file__), "Training_Data")
            os.makedirs(out_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(src_path))[0]
            out_path = os.path.join(out_dir, f"{base_name}_plot.png")
            img.save(out_path)
            # Open on macOS
            if self.is_mac:
                try:
                    os.system(f'open "{out_path}"')
                except Exception:
                    pass
        except Exception as e:
            print(f"Plotting CSV failed: {e}")

    def update_stats(self):
        # update time
        self.time_elapsed = (time.time() - self.time_start) / 60

        # CSV playback mode (replay from CSV file)
        if self.anc_playback_mode and self.anc_data:
            try:
                # Initialize playback start time
                if self.anc_playback_start_time is None:
                    self.anc_playback_start_time = time.time()
                
                # Downsample: skip samples to simulate real-time playback
                if self.anc_index >= len(self.anc_data):
                    # End of data, loop back to the beginning
                    self.anc_index = 0
                    self.anc_playback_start_time = time.time()  # Reset playback timer
                
                # Read next sample (already downsampled by index increment)
                current_idx = self.anc_index
                l_foot, r_foot, handle_force, handle_pos, raw_seat_mm = self.anc_data[current_idx]
                step = max(1, int(self.anc_index_step)) if hasattr(self, "anc_index_step") else 200
                self.anc_index = min(self.anc_index + step, len(self.anc_data))
                
                # Append sensor data
                self.L_foot_force.append(l_foot)
                self.R_foot_force.append(r_foot)
                self.handle_force.append(handle_force)
                self.handle_position.append(handle_pos)
                # For CSV playback, raw_seat is already in mm after filtering
                self.raw_seat_pos.append(raw_seat_mm)  # Store as raw_seat_pos for compatibility
                self.seat_position_mm.append(raw_seat_mm)  # Store explicitly in mm
                
                # Time base for power computation
                if not hasattr(self, 'temp_time'):
                    self.temp_time = []
                self.temp_time.append(time.time())
                
                # Convert to 0-100 scale for compatibility
                # Use CSV min/max values, not calibration values
                if self.raw_seat_pos:
                    if self.csv_seat_min is not None and self.csv_seat_max is not None:
                        # Clip using CSV-derived values
                        if self.raw_seat_pos[-1] <= self.csv_seat_min:
                            self.raw_seat_pos[-1] = self.csv_seat_min
                        elif self.raw_seat_pos[-1] >= self.csv_seat_max:
                            self.raw_seat_pos[-1] = self.csv_seat_max
                    self.converted_seat_position.append(self.convert_raw_to_scale(self.raw_seat_pos[-1]))
                
                if self.anc_power_series and current_idx < len(self.anc_power_series):
                    power_val = self.anc_power_series[current_idx]
                    self.temp_power.append(power_val)
                    self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                    # Print force and power values
                    current_force = handle_force
                elif len(self.handle_force) > 1 and len(self.handle_position) > 1 and len(self.temp_time) > 1:
                    avg_force = (self.handle_force[-1]+self.handle_force[-2])/2
                    delta_handle = abs(self.handle_position[-1]-self.handle_position[-2])
                    dt = self.temp_time[-1]-self.temp_time[-2]
                    power_val = avg_force * delta_handle / dt if dt > 0 else 0
                    self.temp_power.append(power_val)
                    self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                    # Print force and power values
                    print(f"CSV Playback (calc) - Force: {avg_force:.2f} N, Delta Handle: {delta_handle:.2f} mm, dt: {dt:.3f} s, Power: {power_val:.2f} W, Avg Power: {self.avg_power[-1]:.2f} W")
                self.hardware_connected = False
                return
            except Exception as e:
                print(f"⚠️  CSV playback error: {e}")
                import traceback
                traceback.print_exc()
                # Don't disable playback mode - try to continue with existing data
                # Calculate power from existing data if available
                if len(self.handle_force) > 1 and len(self.handle_position) > 1 and len(self.temp_time) > 1:
                    try:
                        self.temp_power.append(((self.handle_force[-1]+self.handle_force[-2])/2)*abs(self.handle_position[-1]-self.handle_position[-2])/(self.temp_time[-1]-self.temp_time[-2]))
                        self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                    except:
                        pass
                # Continue to allow other updates (score, misses, etc.)

        # Hardware sensor data collection (Windows/Linux only)
        if not self.is_mac and self.hardware_mode:
            # Check if hardware task was successfully initialized
            if self.hardware_task is None:
                print("❌ Hardware mode enabled but task initialization failed")
                print("   Sensor mode is not available")
                self.hardware_connected = False
                return  # Do not fall back to simulation
            
            try:
                # Use persistent task (created in __init__) - matches hardware_test_safe.py approach
                data = self.hardware_task.read(number_of_samples_per_channel=1)
                
                # Extract single values from nested list structure
                left_foot_voltage = data[0][0] if isinstance(data[0], list) else data[0]
                right_foot_voltage = data[1][0] if isinstance(data[1], list) else data[1]
                handle_force_voltage = data[2][0] if isinstance(data[2], list) else data[2]
                handle_position_voltage = data[3][0] if isinstance(data[3], list) else data[3]
                seat_position_voltage = data[4][0] if isinstance(data[4], list) else data[4]
                
                # Estimate sampling rate from timing
                current_time = time.time()
                if not hasattr(self, 'temp_time') or not self.temp_time:
                    self.temp_time = []
                self.temp_time.append(current_time)
                
                # Update sampling rate estimate (use last 10 samples)
                if len(self.temp_time) > 1:
                    recent_intervals = []
                    for i in range(max(1, len(self.temp_time) - 10), len(self.temp_time)):
                        if i > 0:
                            dt = self.temp_time[i] - self.temp_time[i-1]
                            if dt > 0:
                                recent_intervals.append(dt)
                    if recent_intervals:
                        avg_interval = sum(recent_intervals) / len(recent_intervals)
                        if avg_interval > 0:
                            self.hardware_sampling_rate = 1.0 / avg_interval
                
                # Process hardware data using the same method as CSV playback
                # This applies Butterworth filter, converts to physical units, and zero-shifts
                handle_force_N, handle_position_mm, seat_position_mm = self._process_hardware_data(
                    handle_force_voltage, handle_position_voltage, seat_position_voltage
                )
                
                # Store processed values (same format as CSV playback)
                self.L_foot_force.append(left_foot_voltage)  # Store raw voltage for foot sensors
                self.R_foot_force.append(right_foot_voltage)  # Store raw voltage for foot sensors
                self.handle_force.append(handle_force_N)  # Processed force in Newtons
                self.handle_position.append(handle_position_mm)  # Processed position in mm
                self.raw_seat_pos.append(seat_position_mm)  # Processed seat position in mm (for compatibility)
                self.seat_position_mm.append(seat_position_mm)  # Store explicitly in mm (already zero-shifted)
                
                # Calculate release and press positions for hardware mode
                # Use calibration values (front_max_pos, back_max_pos) to determine max seat position
                # Since seat_position_mm is zero-shifted, max = calibrated range = front_max_pos - back_max_pos
                # Calibration data is required for hardware mode (checked in detect_and_set_mode)
                if self.front_max_pos > self.back_max_pos:
                    # Use calibrated range as max seat position (after zero-shifting)
                    max_seat_calibrated = self.front_max_pos - self.back_max_pos
                    self.seat_position_release = max_seat_calibrated * 0.15
                    self.seat_position_press = max_seat_calibrated - 140
                else:
                    # This should not happen if calibration check worked, but handle gracefully
                    # Use a default calculation based on current data
                    if len(self.seat_position_mm) >= 10:
                        import numpy as np
                        seat_array = np.array(self.seat_position_mm)
                        max_seat = np.max(seat_array)
                        self.seat_position_release = max_seat * 0.15
                        self.seat_position_press = max_seat - 140
                    else:
                        # Not enough data yet, use defaults
                        self.seat_position_release = 0.0
                        self.seat_position_press = 100.0
                
                # Convert to 0-100 scale for compatibility (using processed mm values)
                if self.raw_seat_pos:
                    # Note: The 0-100 scale conversion may need calibration adjustment
                    # For now, use the same conversion as before but with mm values
                    if self.raw_seat_pos[-1] <= self.back_max_pos:
                        self.raw_seat_pos[-1] = self.back_max_pos
                    elif self.raw_seat_pos[-1] >= self.front_max_pos:
                        self.raw_seat_pos[-1] = self.front_max_pos
                    self.converted_seat_position.append(self.convert_raw_to_scale(self.raw_seat_pos[-1]))
                
                self.hardware_connected = True

                # Update power using processed values (same formula as CSV playback)
                if len(self.handle_force) > 1 and len(self.handle_position) > 1 and len(self.temp_time) > 1:
                    # Power calculation: avg_force * delta_handle / dt / 1000
                    # handle_force is in N, handle_position is in mm, need to convert mm to m
                    avg_force = (self.handle_force[-1] + self.handle_force[-2]) / 2.0  # N
                    delta_handle = abs(self.handle_position[-1] - self.handle_position[-2])  # mm
                    dt = self.temp_time[-1] - self.temp_time[-2]  # seconds
                    if dt > 0:
                        power_val = avg_force * delta_handle / dt / 1000.0  # W (divide by 1000 to convert mm->m)
                        self.temp_power.append(power_val)
                        self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                        # Print force and power values
                        print(f"Hardware - Force: {avg_force:.2f} N, Delta Handle: {delta_handle:.2f} mm, dt: {dt:.3f} s, Power: {power_val:.2f} W, Avg Power: {self.avg_power[-1]:.2f} W")
                    
                return  # Exit early if hardware read was successful
            except Exception as e:
                print(f"❌ Error reading from sensors: {e}")
                import traceback
                traceback.print_exc()
                self.hardware_connected = False
                # Don't return early - allow fallback power calculation from existing data
                # Continue to allow power calculation from existing sensor data
        
        # No simulation mode - only hardware or CSV playback
        # If we reach here, no valid data source is available
        # (This is normal during initialization - mode detection happens in reset_game)
        
        # Try to calculate power from existing data if we have sensor readings but no mode is active
        # This ensures power updates even if mode detection failed or data source is unavailable
        if len(self.handle_force) > 1 and len(self.handle_position) > 1:
            if not hasattr(self, 'temp_time') or not self.temp_time or len(self.temp_time) < 2:
                # Initialize temp_time if missing
                if not hasattr(self, 'temp_time'):
                    self.temp_time = []
                current_time = time.time()
                if len(self.temp_time) == 0:
                    self.temp_time.append(current_time)
                if len(self.temp_time) == 1:
                    self.temp_time.append(current_time)
            
            if len(self.temp_time) > 1 and len(self.handle_force) > 1 and len(self.handle_position) > 1:
                try:
                    dt = self.temp_time[-1] - self.temp_time[-2] if len(self.temp_time) > 1 else 0.1
                    if dt > 0:
                        avg_force = (self.handle_force[-1] + self.handle_force[-2]) / 2.0  # N
                        delta_handle = abs(self.handle_position[-1] - self.handle_position[-2])  # mm
                        power_val = avg_force * delta_handle / dt / 1000.0  # W (divide by 1000 to convert mm->m)
                        if not self.temp_power or len(self.temp_power) == 0:
                            self.temp_power = []
                        self.temp_power.append(power_val)
                        # Keep only last 100 power values to prevent memory growth
                        if len(self.temp_power) > 100:
                            self.temp_power = self.temp_power[-100:]
                        if not self.avg_power or len(self.avg_power) == 0:
                            self.avg_power = []
                        self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                        # Keep only last 100 avg power values
                        if len(self.avg_power) > 100:
                            self.avg_power = self.avg_power[-100:]
                        # Print force and power values
                        print(f"Fallback - Force: {avg_force:.2f} N, Delta Handle: {delta_handle:.2f} mm, dt: {dt:.3f} s, Power: {power_val:.2f} W, Avg Power: {self.avg_power[-1]:.2f} W")
                except Exception as e:
                    print(f"Power calculation fallback error: {e}")
        
        # update score and misses
        if self.converted_seat_position:
            if self.converted_seat_position[-1] <= 0:
                self.same_stroke = False
        
        if len(self.switch_press) > 1:
            if self.switch_press[-1] == 5 and self.switch_press[-2] == 0:  # button needs to be held pressed -> 5V
                self.button_press_seat_pos.append(self.raw_seat_pos[-1])
                if self.fes_active_pos - 93.3 <= self.button_press_seat_pos[-1] <= self.fes_active_pos + 93.3 and self.is_pressed:
                    self.score += 1
                    #Correct_Sound.play()
                else:
                    self.misses += 1
                    #Wrong_Sound.play()
            self.same_stroke = True
    
    def calculate_distance(self):
        """Calculate realistic rowing distance based on power and time"""
        # CRITICAL: Don't calculate distance until game is properly started/reset
        # This prevents distance jumps when CSV playback processes data before reset_game() is called
        if not self.game_started:
            return
        
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        
        # Fix bug: If time_delta is suspiciously large (> 1 second), it means this is the first
        # call after initialization or a long pause. Reset last_update_time to prevent
        # incorrectly calculating a huge distance jump.
        if time_delta > 1.0:
            # Reset to current time to start fresh - this prevents distance jumps on game start
            self.last_update_time = current_time
            time_delta = 0.0
        
        # Only proceed if we have a valid time delta
        if time_delta <= 0:
            return
        
        self.last_update_time = current_time
        
        if self.avg_power and time_delta > 0:
            current_power = self.avg_power[-1]
            
            # Realistic rowing physics:
            # Distance = (Power / Drag Factor) * Time
            # Drag factor for realistic rowing is typically around 100-150
            # We'll use 120 as a moderate resistance setting
            drag_factor = 120
            
            # Only calculate distance if there's meaningful power (reduce noise)
            if current_power > 5:  # Minimum 5W to register movement
                # Distance per time interval based on power
                # Formula: distance = (power / drag_factor) * time
                distance_increment = (current_power / drag_factor) * time_delta
                self.total_distance += distance_increment
                self.increment_cumulative_distance(distance_increment)
                
                # Increment rowing time if power > 0
                if current_power > 0:
                    self.session_rowing_time += time_delta

    def write_stats_to_file(self):
        """Disabled - no longer writing rowing stats files, only session summaries"""
        # Do nothing - rowing stats files are no longer needed
        pass
    
    def stop_writing_stats(self):
        self.stats_file_path = None
    
    def cleanup_hardware(self):
        """Clean up hardware task on app exit"""
        if self.hardware_task is not None:
            try:
                self.hardware_task.close()
                print("✅ Hardware task closed successfully")
            except Exception as e:
                print(f"⚠️  Error closing hardware task: {e}")
            finally:
                self.hardware_task = None
    
    def save_session_summary(self):
        """Save session summary to CSV file (one file per user, append rows)"""
        # Calculate final metrics
        total_time_minutes = self.time_elapsed
        
        # Convert time to MM:SS format
        minutes = int(total_time_minutes)
        seconds = int((total_time_minutes - minutes) * 60)
        time_str = f"{minutes}:{seconds:02d}"  # Format as MM:SS (e.g., 0:04, 1:23)
        
        # Average power: average of all avg_power values
        if self.avg_power:
            avg_power = sum(self.avg_power) / len(self.avg_power)
        else:
            avg_power = 0.0
        
        # Total distance (already calculated)
        total_distance = self.total_distance
        
        # Average accuracy - only calculate in manual mode, set to 0 in automatic mode
        if self.is_automatic_mode:
            # Automatic mode: don't record accuracy (set to 0)
            avg_accuracy = 0.0
        elif self.button_combined_accuracies:
            # Manual mode: use combined (press+release) accuracies
            avg_accuracy = sum(self.button_combined_accuracies) / len(self.button_combined_accuracies)
        else:
            # Manual mode: no completed press-release cycles yet
            avg_accuracy = 0.0
        
        # Use user-specific data directory
        data_dir = self.get_user_data_dir()
        filename = "session_summary.csv"
        file_path = os.path.join(data_dir, filename)
        
        # Check if file exists and validate header for "Rowing Time (s)" column
        file_exists = os.path.exists(file_path)
        header_needs_update = False
        existing_rows = []
        existing_header = []
        
        if file_exists:
            try:
                with open(file_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    try:
                        existing_header = next(reader)
                        if "Rowing Time (s)" not in existing_header:
                            header_needs_update = True
                            existing_rows = list(reader)
                    except StopIteration:
                        # Empty file
                        file_exists = False
            except Exception as e:
                print(f"Error reading CSV for header check: {e}")
                
        if header_needs_update:
            print(f"Updating CSV header for {file_path} to include Rowing Time")
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Create new header
                    new_header = ["Date", "Name", "Total Time (min:sec)", "Average Power (W)", "Total Distance (m)", "Average Accuracy (%)", "Rowing Time (s)"]
                    writer.writerow(new_header)
                    
                    # Map old columns to new header if possible, otherwise just append 0.0
                    # Assuming standard order for old files: Date, Name, Time, Power, Distance, Accuracy
                    for row in existing_rows:
                        # Check if row already has data for the new column (e.g. from a previous append without header update)
                        if len(row) >= 7:
                            # Keep the existing data (assuming 7th col is rowing time)
                            new_row = row[:7]
                        else:
                            # Pad row to ensure it has enough columns for old format
                            while len(row) < 6:
                                row.append("")
                            
                            # Take first 6 columns and add 0.0 for rowing time
                            new_row = row[:6] + ["0.0"]
                        
                        writer.writerow(new_row)
            except Exception as e:
                print(f"Error updating CSV header: {e}")

        # Get current date (date only, no time)
        date_str = time.strftime('%Y-%m-%d')
        
        # Write to CSV (append mode)
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            
            # Write header if file is new or was just reset/empty
            if not file_exists and not header_needs_update:
                 writer.writerow(["Date", "Name", "Total Time (min:sec)", "Average Power (W)", "Total Distance (m)", "Average Accuracy (%)", "Rowing Time (s)"])
            
            # Write session data in the correct order
            writer.writerow([
                date_str,  # Date (date only)
                self.user_name,  # Name
                time_str,  # Total Time in MM:SS format
                f"{avg_power:.2f}",  # Average Power
                f"{total_distance:.2f}",  # Total Distance
                f"{avg_accuracy:.2f}",  # Average Accuracy
                f"{self.session_rowing_time:.2f}" # Rowing Time (s)
            ])
        
        self.force_persist_cumulative_distance()
        print(f"✅ Session summary saved to: {file_path}")
        
        # Return summary data for display
        return {
            "user_name": self.user_name,
            "total_time": total_time_minutes,
            "avg_power": avg_power,
            "total_distance": total_distance,
            "avg_accuracy": avg_accuracy,
            "is_automatic_mode": self.is_automatic_mode  # Include mode for summary display
        }
    
    def export_session_stats(self):
        """Export session statistics to CSV file when back button is pressed."""
        try:
            # Calculate statistics
            # Total duration (in minutes)
            total_duration_min = self.time_elapsed if hasattr(self, 'time_elapsed') else (time.time() - self.time_start) / 60.0
            
            # Mean power (from avg_power list)
            if self.avg_power:
                mean_power = sum(self.avg_power) / len(self.avg_power)
            else:
                mean_power = 0.0
            
            # Total distance (already stored)
            total_distance_m = self.total_distance
            
            # Accuracy - only calculate in manual mode, set to 0 in automatic mode
            if self.is_automatic_mode:
                # Automatic mode: don't record accuracy (set to 0)
                accuracy = 0.0
            else:
                # Manual mode: calculate from score/misses (for backward compatibility)
                total_attempts = self.score + self.misses
                if total_attempts > 0:
                    accuracy = (self.score / total_attempts) * 100.0
                else:
                    accuracy = 0.0
            
            # Create Session_Data directory if it doesn't exist
            session_dir = os.path.join(os.path.dirname(__file__), "Session_Data")
            os.makedirs(session_dir, exist_ok=True)
            
            # Create filename with timestamp and userID if available
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            if self.userID:
                filename = f"{self.userID}_session_stats_{timestamp}.csv"
            else:
                filename = f"session_stats_{timestamp}.csv"
            
            session_file = os.path.join(session_dir, filename)
            
            # Write CSV file
            with open(session_file, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['Metric', 'Value', 'Unit'])
                # Write data
                writer.writerow(['Total Duration', f'{total_duration_min:.2f}', 'minutes'])
                writer.writerow(['Mean Power', f'{mean_power:.2f}', 'W'])
                writer.writerow(['Total Distance', f'{total_distance_m:.2f}', 'meters'])
                writer.writerow(['Accuracy', f'{accuracy:.2f}', '%'])
                writer.writerow(['Score', self.score, 'count'])
                writer.writerow(['Misses', self.misses, 'count'])
                writer.writerow(['Total Attempts', total_attempts, 'count'])
                # Add user info if available
                if self.userID:
                    writer.writerow(['User ID', self.userID, ''])
                if self.age:
                    writer.writerow(['Age', self.age, 'years'])
                if self.height:
                    writer.writerow(['Height', self.height, 'cm'])
                if self.weight:
                    writer.writerow(['Weight', self.weight, 'kg'])
                writer.writerow(['Timestamp', time.strftime('%Y-%m-%d %H:%M:%S'), ''])
            
            self.force_persist_cumulative_distance()
            
        except Exception as e:
            print(f"Failed to export session stats: {e}")

# ------------------------------------------------------------------------------------------------------------

class SpriteManager:
    """Manages sprite generation and caching for better graphics"""
    
    def __init__(self):
        self.sprites = {}
        self.generate_sprites()
    
    def generate_sprites(self):
        """Generate beautiful sprites programmatically"""
        # Load palm tree sprite from PNG file
        self.sprites['palm_tree'] = self.load_palm_tree_sprite()
        self.sprites['palm_tree_small'] = self.load_palm_tree_sprite(scale=0.7)
        # Load cherry blossom sprite from PNG file
        self.sprites['cherry_blossom'] = self.load_cherry_blossom_sprite()
        self.sprites['cherry_blossom_small'] = self.load_cherry_blossom_sprite(scale=0.7)
        # Load penguin sprite from PNG file (scaled to 1/2 size - 2x the 1/4 size)
        self.sprites['penguin'] = self.load_penguin_sprite(scale=0.5)
        self.sprites['penguin_small'] = self.load_penguin_sprite(scale=0.35)  # 0.175 * 2 = 0.35
        # Load jungle sprite from PNG file
        self.sprites['jungle'] = self.load_jungle_sprite()
        self.sprites['jungle_small'] = self.load_jungle_sprite(scale=0.7)
        # Load kangaroo sprite from PNG file (scaled to 1/2 size)
        self.sprites['kangaroo'] = self.load_kangaroo_sprite(scale=0.5)
        self.sprites['kangaroo_small'] = self.load_kangaroo_sprite(scale=0.35)  # 0.7 * 0.5 = 0.35
        # Load cloud sprite from PNG file
        self.sprites['cloud'] = self.load_cloud_sprite()
        self.sprites['boat'] = self.create_boat_sprite()
    
    def load_palm_tree_sprite(self, scale=1.0):
        """Load palm tree sprite from PNG file"""
        try:
            # Get the path to the palm-tree.png file (in parent directory)
            script_dir = os.path.dirname(os.path.dirname(__file__))
            palm_tree_path = os.path.join(script_dir, "palm-tree.png")
            
            # Load the PNG image
            img = Image.open(palm_tree_path)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Scale down the image to match the programmatic palm tree size
            # The programmatic version was 80x140, so we scale the PNG to approximately that size
            target_height = int(140 * scale)
            # Calculate width to maintain aspect ratio
            aspect_ratio = img.width / img.height
            target_width = int(target_height * aspect_ratio)
            
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            return self.pil_to_wx_bitmap(img)
        except Exception as e:
            print(f"Error loading palm tree PNG: {e}")
            # Fallback to programmatically generated palm tree
            return self.create_palm_tree_sprite(scale)
    
    def load_cherry_blossom_sprite(self, scale=1.0):
        """Load cherry blossom sprite from PNG file"""
        try:
            # Get the path to the cherryblossom.png file (in assets/images directory)
            script_dir = os.path.dirname(__file__)
            cherry_blossom_path = os.path.join(script_dir, "assets", "images", "cherryblossom.png")
            
            # Load the PNG image
            img = Image.open(cherry_blossom_path)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Scale down the image to match the programmatic palm tree size
            # The programmatic version was 80x140, so we scale the PNG to approximately that size
            target_height = int(140 * scale)
            # Calculate width to maintain aspect ratio
            aspect_ratio = img.width / img.height
            target_width = int(target_height * aspect_ratio)
            
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            return self.pil_to_wx_bitmap(img)
        except Exception as e:
            print(f"Error loading cherry blossom PNG: {e}")
            # Fallback to programmatically generated palm tree (as placeholder)
            return self.create_palm_tree_sprite(scale)
    
    def load_penguin_sprite(self, scale=1.0):
        """Load penguin sprite from PNG file"""
        try:
            # Get the path to the penguin.png file (in assets/images directory)
            script_dir = os.path.dirname(__file__)
            penguin_path = os.path.join(script_dir, "assets", "images", "penguin.png")
            
            # Load the PNG image
            img = Image.open(penguin_path)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Scale down the image to match the programmatic palm tree size
            # The programmatic version was 80x140, so we scale the PNG to approximately that size
            target_height = int(140 * scale)
            # Calculate width to maintain aspect ratio
            aspect_ratio = img.width / img.height
            target_width = int(target_height * aspect_ratio)
            
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            return self.pil_to_wx_bitmap(img)
        except Exception as e:
            print(f"Error loading penguin PNG: {e}")
            # Fallback to programmatically generated palm tree (as placeholder)
            return self.create_palm_tree_sprite(scale)
    
    def load_jungle_sprite(self, scale=1.0):
        """Load jungle sprite from PNG file"""
        try:
            # Get the path to the jungle.png file (in assets/images directory)
            script_dir = os.path.dirname(__file__)
            jungle_path = os.path.join(script_dir, "assets", "images", "jungle.png")
            
            # Load the PNG image
            img = Image.open(jungle_path)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Scale down the image to match the programmatic palm tree size
            # The programmatic version was 80x140, so we scale the PNG to approximately that size
            target_height = int(140 * scale)
            # Calculate width to maintain aspect ratio
            aspect_ratio = img.width / img.height
            target_width = int(target_height * aspect_ratio)
            
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            return self.pil_to_wx_bitmap(img)
        except Exception as e:
            print(f"Error loading jungle PNG: {e}")
            # Fallback to programmatically generated palm tree (as placeholder)
            return self.create_palm_tree_sprite(scale)
    
    def load_kangaroo_sprite(self, scale=1.0):
        """Load kangaroo sprite from PNG file"""
        try:
            # Get the path to the kangaroo.png file (in assets/images directory)
            script_dir = os.path.dirname(__file__)
            kangaroo_path = os.path.join(script_dir, "assets", "images", "kangaroo.png")
            
            # Load the PNG image
            img = Image.open(kangaroo_path)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Scale down the image to match the programmatic palm tree size
            # The programmatic version was 80x140, so we scale the PNG to approximately that size
            target_height = int(140 * scale)
            # Calculate width to maintain aspect ratio
            aspect_ratio = img.width / img.height
            target_width = int(target_height * aspect_ratio)
            
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            return self.pil_to_wx_bitmap(img)
        except Exception as e:
            print(f"Error loading kangaroo PNG: {e}")
            # Fallback to programmatically generated palm tree (as placeholder)
            return self.create_palm_tree_sprite(scale)
    
    def load_cloud_sprite(self):
        """Load cloud sprite from PNG file"""
        try:
            # Get the path to the cloud.png file (in assets/images directory)
            script_dir = os.path.dirname(__file__)
            cloud_path = os.path.join(script_dir, "assets", "images", "cloud.png")
            
            # Load the PNG image
            img = Image.open(cloud_path)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Scale down the image to a smaller size for better proportions
            # Make it smaller than the original programmatic cloud
            target_width = 70
            # Calculate height to maintain aspect ratio
            aspect_ratio = img.height / img.width
            target_height = int(target_width * aspect_ratio)
            
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            return self.pil_to_wx_bitmap(img)
        except Exception as e:
            print(f"Error loading cloud PNG: {e}")
            # Fallback to programmatically generated cloud
            return self.create_cloud_sprite()
    
    def create_palm_tree_sprite(self, scale=1.0):
        """Create a beautiful palm tree sprite with transparency"""
        width = int(80 * scale)
        height = int(140 * scale)
        
        # Create RGBA image with transparency
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        trunk_x = width // 2
        trunk_base_y = height
        trunk_top_y = int(height * 0.35)
        trunk_height = trunk_base_y - trunk_top_y
        
        # Draw trunk with segments (coconut palm style)
        trunk_width = int(10 * scale)
        num_segments = 6
        
        for i in range(num_segments):
            seg_y_start = trunk_base_y - int(i * trunk_height / num_segments)
            seg_y_end = trunk_base_y - int((i + 1) * trunk_height / num_segments)
            
            # Vary width slightly
            seg_width = trunk_width - i
            
            # Brown color with variation
            brown_shade = 90 - i * 5
            trunk_color = (brown_shade, brown_shade - 25, 20)
            
            # Draw trunk segment
            draw.rectangle(
                [trunk_x - seg_width//2, seg_y_end,
                 trunk_x + seg_width//2, seg_y_start],
                fill=trunk_color
            )
            
            # Add horizontal rings for texture
            if i < num_segments - 1:
                ring_y = seg_y_end
                draw.ellipse(
                    [trunk_x - seg_width//2 - 2, ring_y - 2,
                     trunk_x + seg_width//2 + 2, ring_y + 2],
                    fill=(brown_shade - 10, brown_shade - 30, 15)
                )
        
        # Draw palm fronds (6 main fronds)
        frond_center_x = trunk_x
        frond_center_y = trunk_top_y
        
        # Main frond angles (spread out nicely)
        frond_angles = [-60, -30, 0, 30, 60, 90]
        
        for angle in frond_angles:
            rad = math.radians(angle)
            
            # Draw each frond as a curved shape
            frond_length = int(50 * scale)
            frond_segments = 5
            
            for seg in range(frond_segments):
                t = seg / frond_segments
                
                # Calculate position along frond
                dist = frond_length * t
                x_offset = int(dist * math.cos(rad))
                y_offset = int(dist * math.sin(rad))
                
                # Leaf width decreases along frond
                leaf_width = int((25 - seg * 4) * scale)
                leaf_height = int((12 - seg * 1.5) * scale)
                
                # Green with slight darkening toward tips
                green_intensity = 140 - seg * 15
                leaf_color = (34, green_intensity, 34, 200 - seg * 20)
                
                # Draw leaflet
                leaf_x = frond_center_x + x_offset
                leaf_y = frond_center_y + y_offset
                
                # Rotate leaflet slightly
                draw.ellipse(
                    [leaf_x - leaf_width//2, leaf_y - leaf_height//2,
                     leaf_x + leaf_width//2, leaf_y + leaf_height//2],
                    fill=leaf_color
                )
        
        # Center crown
        draw.ellipse(
            [frond_center_x - int(18*scale), frond_center_y - int(18*scale),
             frond_center_x + int(18*scale), frond_center_y + int(18*scale)],
            fill=(34, 139, 34, 240)
        )
        
        return self.pil_to_wx_bitmap(img)
    
    def create_cloud_sprite(self):
        """Create a puffy cloud sprite"""
        width, height = 120, 60
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Multiple overlapping circles for cloud effect
        cloud_positions = [
            (20, 30, 25),   # (x, y, radius)
            (40, 35, 30),
            (65, 35, 28),
            (85, 30, 25),
            (50, 20, 22)
        ]
        
        for x, y, r in cloud_positions:
            draw.ellipse(
                [x - r, y - r, x + r, y + r],
                fill=(255, 255, 255, 200)
            )
        
        return self.pil_to_wx_bitmap(img)
    
    def create_boat_sprite(self):
        """Create a detailed rowing boat sprite"""
        width, height = 100, 60
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        boat_y = 30
        
        # Boat hull (polygon for realistic shape)
        hull_points = [
            (15, boat_y),                    # Front point
            (20, boat_y + 15),               # Front bottom
            (80, boat_y + 15),               # Back bottom
            (85, boat_y),                    # Back point
            (82, boat_y - 3),                # Back top
            (18, boat_y - 3),                # Front top
        ]
        draw.polygon(hull_points, fill=(101, 67, 33), outline=(80, 50, 20))
        
        # Rower head
        head_x, head_y = 50, boat_y - 10
        draw.ellipse(
            [head_x - 6, head_y - 6, head_x + 6, head_y + 6],
            fill=(255, 220, 177)
        )
        
        # Body
        draw.line(
            [head_x, head_y + 6, head_x, boat_y + 5],
            fill=(50, 50, 50),
            width=3
        )
        
        # Oar
        draw.line(
            [head_x - 30, boat_y - 2, head_x + 30, boat_y + 2],
            fill=(139, 90, 43),
            width=4
        )
        
        # Oar blades
        draw.ellipse(
            [head_x - 38, boat_y - 6, head_x - 28, boat_y + 2],
            fill=(200, 200, 200)
        )
        draw.ellipse(
            [head_x + 28, boat_y - 2, head_x + 38, boat_y + 6],
            fill=(200, 200, 200)
        )
        
        return self.pil_to_wx_bitmap(img)
    
    def pil_to_wx_bitmap(self, pil_image):
        """Convert PIL Image to wx.Bitmap with transparency support"""
        width, height = pil_image.size
        
        # Convert to wx.Image first
        wx_image = wx.Image(width, height)
        
        # Convert RGBA to RGB + Alpha
        rgb_image = pil_image.convert('RGB')
        wx_image.SetData(rgb_image.tobytes())
        
        # Set alpha channel if present
        if pil_image.mode == 'RGBA':
            alpha_data = pil_image.split()[3].tobytes()
            wx_image.SetAlpha(alpha_data)
        
        return wx.Bitmap(wx_image)
    
    def get_sprite(self, name):
        """Get a sprite by name"""
        return self.sprites.get(name)

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
        outer_sizer.Add(self.stats_panel, 1, wx.EXPAND | wx.ALL, 20)  # Reduced proportion from 2 to 1 (approximately 20% reduction in allocated space)

        # initialize location and progress display panel - new section
        self.location_progress_panel = LocationProgressPanel(self, self.shared_state)
        outer_sizer.Add(self.location_progress_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        # initialize gamified rowing scene - middle section
        self.rowing_scene_panel = RowingScenePanel(self, self.shared_state)
        outer_sizer.Add(self.rowing_scene_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        
        # Add small spacer between rowing scene and FES indicator
        spacer_panel = wx.Panel(self)
        spacer_panel.SetBackgroundColour(wx.Colour(248, 249, 250))
        spacer_panel.SetMinSize((-1, 10))  # Small fixed spacer
        outer_sizer.Add(spacer_panel, 0, wx.EXPAND)
        self.fes_spacer_panel = spacer_panel

        # initialize FES timing indicator - bottom section
        self.fes_indicator_panel = ModernFESIndicator(self, self.shared_state)
        outer_sizer.Add(self.fes_indicator_panel, 1, wx.EXPAND | wx.ALL, 20)

        # Button container for bottom-right buttons
        button_container = wx.BoxSizer(wx.HORIZONTAL)
        button_container.AddStretchSpacer()
        
        # initialize finish session button (bottom-right) - matching User Dashboard button style
        self.finish_button = ModernCard(self, "Finish Session →", self.on_finish_session, enabled=True, font_size=24)
        self.finish_button.SetMinSize((308, 70))
        button_container.Add(self.finish_button, 0, wx.ALL, 10)
        
        outer_sizer.Add(button_container, 0, wx.EXPAND | wx.ALL, 0)

        self.SetSizer(outer_sizer)
        
        # Button press counter for terminal output
        self.button_press_count = 0
        
        # CSV file for button press logging
        self.button_press_csv_file = None
        self.button_press_csv_writer = None
        self.button_press_csv_path = None
        self.game_start_time = None  # Track when game session starts
        
        # Track optimal position crossings for expected time calculation
        self.last_seat_position = None
        self.last_optimal_press_crossing_time = None
        self.last_optimal_release_crossing_time = None

        # initialize the main timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(100)
        
        # Setup button press/release detection (spacebar + game controller)
        # Keyboard detection - use EVT_KEY_DOWN and EVT_KEY_UP for press and release
        parent_frame = self.GetTopLevelParent()
        if parent_frame:
            parent_frame.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
            parent_frame.Bind(wx.EVT_KEY_UP, self.on_key_up)
        
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_KEY_UP, self.on_key_up)
        
        self.last_button_press_time = 0  # Debounce tracking
        self.spacebar_currently_pressed = False  # Track spacebar state
        
        # Game controller detection and setup
        self.controller = None
        self.controller_last_button_state = {}
        self.setup_game_controller()
        
        # Controller polling timer (check every 50ms)
        self.controller_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.poll_controller, self.controller_timer)
        if self.controller:
            self.controller_timer.Start(50)  # Poll every 50ms

    def on_timer(self, event):
        """Main timer callback - updates UI with current state (no simulation)"""
        try:
            # Update stats (reads from hardware or CSV playback)
            self.shared_state.update_stats()
            
            # Calculate distance based on current data
            self.shared_state.calculate_distance()
            
            # Track optimal position crossings for expected time calculation
            self._track_optimal_position_crossings()
            
            # Update all UI panels
            self.stats_panel.update_stats()
            self.location_progress_panel.update_display()
            self.rowing_scene_panel.update_scene()
            self.fes_indicator_panel.update_indicator()
        except Exception as e:
            print(f"Error in timer callback: {e}")
            import traceback
            traceback.print_exc()
    
    def _track_optimal_position_crossings(self):
        """Track when seat position crosses optimal press/release positions"""
        # Only track in manual mode
        if self.shared_state.is_automatic_mode:
            return
        
        # Get current seat position
        if self.shared_state.seat_position_mm and len(self.shared_state.seat_position_mm) > 0:
            current_pos = self.shared_state.seat_position_mm[-1]
        elif self.shared_state.raw_seat_pos and len(self.shared_state.raw_seat_pos) > 0:
            current_pos = self.shared_state.raw_seat_pos[-1]
        else:
            return
        
        current_time = time.time()
        
        # Track press optimal position crossing
        if hasattr(self.shared_state, 'seat_position_press') and self.shared_state.seat_position_press is not None:
            optimal_press = self.shared_state.seat_position_press
            if self.last_seat_position is not None:
                # Check if we crossed the optimal press position
                # Crossing from left to right (increasing position) or right to left (decreasing)
                if (self.last_seat_position < optimal_press and current_pos >= optimal_press) or \
                   (self.last_seat_position > optimal_press and current_pos <= optimal_press):
                    self.last_optimal_press_crossing_time = current_time
        
        # Track release optimal position crossing
        if hasattr(self.shared_state, 'seat_position_release') and self.shared_state.seat_position_release is not None:
            optimal_release = self.shared_state.seat_position_release
            if self.last_seat_position is not None:
                # Check if we crossed the optimal release position
                if (self.last_seat_position < optimal_release and current_pos >= optimal_release) or \
                   (self.last_seat_position > optimal_release and current_pos <= optimal_release):
                    self.last_optimal_release_crossing_time = current_time
        
        self.last_seat_position = current_pos
    
    def _write_button_event_to_csv(self, event_type, event_time, time_expected, accuracy, early_late):
        """Write button event to CSV file"""
        if not self.button_press_csv_writer:
            return
        
        try:
            # Calculate relative times from game start
            if self.game_start_time:
                time_relative = event_time - self.game_start_time
                time_expected_relative = time_expected - self.game_start_time
            else:
                time_relative = event_time
                time_expected_relative = time_expected
            
            # Write row: event, time, time expected, accuracy, early/late
            self.button_press_csv_writer.writerow([
                event_type,
                f"{time_relative:.3f}",
                f"{time_expected_relative:.3f}",
                f"{accuracy:.2f}",
                early_late
            ])
            
            # Flush to ensure data is written immediately
            if self.button_press_csv_file:
                self.button_press_csv_file.flush()
        except Exception as e:
            print(f"Error writing button event to CSV: {e}")
            import traceback
            traceback.print_exc()

    def reset_game(self):
        # Re-setup button press/release detection
        parent_frame = self.GetTopLevelParent()
        if parent_frame:
            parent_frame.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
            parent_frame.Bind(wx.EVT_KEY_UP, self.on_key_up)
        
        # Detect and set mode when game page is activated (only if not already set)
        if self.shared_state.current_mode is None:
            self.shared_state.detect_and_set_mode()
            # Initialize hardware task if in hardware mode (after mode detection)
            if self.shared_state.hardware_mode and self.shared_state.hardware_task is None:
                try:
                    # Get hardware settings
                    hw_settings = self.shared_state.settings_manager.get_hardware_settings()
                    dev_number = hw_settings.get("dev_number", 1)
                    left_foot_ch = hw_settings.get("left_foot_force_channel", 16)
                    right_foot_ch = hw_settings.get("right_foot_force_channel", 18)
                    handle_ch = hw_settings.get("handle_force_channel", 20)
                    front_pot_ch = hw_settings.get("front_potentiometer_channel", 21)
                    back_pot_ch = hw_settings.get("back_potentiometer_channel", 22)
                    voltage = hw_settings.get("voltage_v", 5.0)
                    
                    self.shared_state.hardware_task = nidaqmx.Task()
                    # Configure channels with RSE terminal configuration and 0-10V range
                    self.shared_state.hardware_task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{left_foot_ch}",
                                                                                   terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                                                   min_val=0.0, max_val=10.0)   # Left Foot Force
                    self.shared_state.hardware_task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{right_foot_ch}",
                                                                                   terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                                                   min_val=0.0, max_val=10.0)   # Right Foot Force
                    self.shared_state.hardware_task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{handle_ch}",
                                                                                   terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                                                   min_val=0.0, max_val=10.0)   # Handle Force
                    self.shared_state.hardware_task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{front_pot_ch}",
                                                                                   terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                                                   min_val=0.0, max_val=10.0)   # Front Potentiometer (Handle Position)
                    self.shared_state.hardware_task.ai_channels.add_ai_voltage_chan(f"Dev{dev_number}/ai{back_pot_ch}",
                                                                                   terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                                                   min_val=0.0, max_val=10.0)   # Back Potentiometer (Seat Position)
                    # Don't use CONTINUOUS mode - read on-demand to avoid blocking UI timer
                    # This matches hardware_test_safe.py approach
                    print(f"Hardware task initialized successfully with Dev{dev_number}, voltage={voltage}V")
                except Exception as e:
                    print(f"Failed to initialize hardware task: {e}")
                    self.shared_state.hardware_mode = False
        
        self.stats_panel.reset()
        self.rowing_scene_panel.reset()
        self.fes_indicator_panel.reset()
        
        # Initialize CSV file for button press logging
        self._initialize_button_press_csv()
        # Reset button press counter
        self.button_press_count = 0
        
        # Reset CSV playback to beginning (for new session)
        if self.shared_state.anc_playback_mode:
            self.shared_state.anc_index = 0
            self.shared_state.anc_playback_start_time = None
        
        # CRITICAL: Ensure user directory exists (creates it if needed)
        self.shared_state.get_user_data_dir()
        
        # CRITICAL: Reload cumulative distance from user_accounts.json (updated by dashboard)
        # This ensures we use the value calculated from session summaries, not stale data
        self.shared_state._cumulative_loaded = False
        self.shared_state.ensure_cumulative_distance_loaded()
        
        self.shared_state.session_rowing_time = 0.0 # Reset session rowing time
        
        # CRITICAL: Mark game as started and reset last_update_time to prevent distance jumps
        # This must happen AFTER resetting stats but BEFORE timer starts processing data
        self.shared_state.game_started = True
        self.shared_state.last_update_time = time.time()
        
        # Restart timer if it was stopped
        if not self.timer.IsRunning():
            self.timer.Start(100)
    
    def _initialize_button_press_csv(self):
        """Initialize CSV file for logging button press events"""
        try:
            # Close existing CSV file if open
            if self.button_press_csv_file:
                self.button_press_csv_file.close()
            
            # Get patient name (default to "demo" if not set)
            patient_name = getattr(self.shared_state, 'user_name', 'demo')
            if not patient_name or patient_name == "":
                patient_name = "demo"
            
            # Create filename with format: {patient_name}-{date}-{time}.csv
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{patient_name}-{timestamp}.csv"
            
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(__file__), "data")
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Full path to CSV file
            self.button_press_csv_path = os.path.join(data_dir, filename)
            
            # Open CSV file for writing
            self.button_press_csv_file = open(self.button_press_csv_path, 'w', newline='')
            self.button_press_csv_writer = csv.writer(self.button_press_csv_file)
            
            # Write header
            self.button_press_csv_writer.writerow(['event', 'time', 'time expected', 'accuracy', 'early/late'])
            
            # Track game start time
            self.game_start_time = time.time()
            
            # Reset optimal position crossing tracking
            self.last_seat_position = None
            self.last_optimal_press_crossing_time = None
            self.last_optimal_release_crossing_time = None
            
            print(f"Button press CSV initialized: {self.button_press_csv_path}")
        except Exception as e:
            print(f"Error initializing button press CSV: {e}")
            import traceback
            traceback.print_exc()
            self.button_press_csv_file = None
            self.button_press_csv_writer = None

    def setup_game_controller(self):
        """Initialize pygame and detect game controller"""
        if not PYGAME_AVAILABLE:
            print("Game controller support not available (pygame not installed)")
            return
        
        try:
            # Initialize pygame joystick module only
            pygame.init()
            pygame.joystick.init()
            
            # Check for connected controllers
            joystick_count = pygame.joystick.get_count()
            
            if joystick_count > 0:
                # Use the first controller found
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
                
                controller_name = self.controller.get_name()
                num_buttons = self.controller.get_numbuttons()
                
                print(f"✓ Controller connected: {controller_name}")
                print(f"  Buttons: {num_buttons}")
                print(f"  Press any button on the controller to register button press")
                
                # Initialize button state tracking
                for i in range(num_buttons):
                    self.controller_last_button_state[i] = False
            else:
                print("No game controller detected")
                print("Connect your 8bitdo controller via Bluetooth and restart the app")
                
        except Exception as e:
            print(f"Error initializing game controller: {e}")
            self.controller = None
    
    def poll_controller(self, event):
        """Poll game controller for button presses and releases"""
        if not self.controller:
            return
        
        try:
            # Process pygame events (required for joystick state updates)
            pygame.event.pump()
            
            # Check all buttons
            num_buttons = self.controller.get_numbuttons()
            for button_id in range(num_buttons):
                button_pressed = self.controller.get_button(button_id)
                was_pressed = self.controller_last_button_state.get(button_id, False)
                
                # Detect button press (transition from not pressed to pressed)
                if button_pressed and not was_pressed:
                    print(f"Controller button {button_id} pressed")
                    self.process_button_press()
                # Detect button release (transition from pressed to not pressed)
                elif not button_pressed and was_pressed:
                    print(f"Controller button {button_id} released")
                    self.process_button_release()
                
                # Update state
                self.controller_last_button_state[button_id] = button_pressed
                
        except Exception as e:
            print(f"Error polling controller: {e}")
    
    def on_key_down(self, event):
        """Handle key down events - detect button press"""
        keycode = event.GetKeyCode()
        
        if keycode == wx.WXK_SPACE:
            # Spacebar pressed down
            if not self.spacebar_currently_pressed:
                self.spacebar_currently_pressed = True
                self.process_button_press()
            return  # Don't propagate
        event.Skip()  # Let other keys through
    
    def on_key_up(self, event):
        """Handle key up events - detect button release"""
        keycode = event.GetKeyCode()
        
        if keycode == wx.WXK_SPACE:
            # Spacebar released
            if self.spacebar_currently_pressed:
                self.spacebar_currently_pressed = False
                self.process_button_release()
            return  # Don't propagate
        event.Skip()  # Let other keys through
    
    
    def process_button_press(self):
        """Process button press (when button is initially pressed down) for press accuracy tracking"""
        # Only process in manual mode
        if self.shared_state.is_automatic_mode:
            return
        
        # Ignore if button is already held (prevent repeat triggers)
        if self.shared_state.button_currently_held:
            return
        
        # Debounce: ignore if pressed within last 200ms
        current_time = time.time()
        if current_time - self.last_button_press_time < 0.2:
            return
        self.last_button_press_time = current_time
        
        # Mark button as held
        self.shared_state.button_currently_held = True
        self.button_press_count += 1
        
        # Get current seat position (prefer mm if available)
        if self.shared_state.seat_position_mm and len(self.shared_state.seat_position_mm) > 0:
            current_pos_mm = self.shared_state.seat_position_mm[-1]
        elif self.shared_state.raw_seat_pos and len(self.shared_state.raw_seat_pos) > 0:
            current_pos_mm = self.shared_state.raw_seat_pos[-1]
        else:
            return
        
        # Store the position where button was pressed
        self.shared_state.button_press_position_mm = current_pos_mm
        
        # Optimal position is seat_position_press (rightmost - where PRESS/green zone is)
        if hasattr(self.shared_state, 'seat_position_press') and self.shared_state.seat_position_press is not None:
            optimal_pos = self.shared_state.seat_position_press
        else:
            return
        
        # Calculate PRESS accuracy: Lenient with sweet spot zone, 0% beyond 200mm
        distance = abs(current_pos_mm - optimal_pos)
        perfect_zone = self.shared_state.button_press_perfect_zone_mm
        window = self.shared_state.button_press_window_mm
        
        if distance <= perfect_zone:
            # Within perfect zone - always 100%
            press_accuracy = 100.0
        elif distance <= window:
            # Outside perfect zone but within window - gentle cubic root decay
            excess_distance = distance - perfect_zone
            remaining_window = window - perfect_zone
            normalized_distance = excess_distance / remaining_window  # 0 to 1
            # Cubic root for very gentle curve from 100% down to 0%
            decay_factor = 1.0 - (normalized_distance ** 0.33)  # Cubic root
            press_accuracy = 100.0 * decay_factor
            press_accuracy = max(0.0, min(100.0, press_accuracy))
        else:
            # Outside window - no credit
            press_accuracy = 0.0
        
        # Store press accuracy temporarily (will be combined with release accuracy later)
        self.shared_state.button_press_accuracy_temp = press_accuracy
        self.shared_state.button_press_accuracies.append(press_accuracy)
        
        # Calculate expected time and early/late status
        time_expected = self.last_optimal_press_crossing_time if self.last_optimal_press_crossing_time else current_time
        if current_pos_mm < optimal_pos:
            early_late = "early"
        elif current_pos_mm > optimal_pos:
            early_late = "late"
        else:
            early_late = "on time"
        
        # Write to CSV
        self._write_button_event_to_csv("press", current_time, time_expected, press_accuracy, early_late)
        
        # Output
        print(f"Button PRESS #{self.button_press_count}: press_accuracy={press_accuracy:.1f}% (pos={current_pos_mm:.1f}mm, target={optimal_pos:.1f}mm) [HOLDING...]")
    
    def process_button_release(self):
        """Process button release (when button is let go) for release accuracy tracking"""
        # Only process in manual mode
        if self.shared_state.is_automatic_mode:
            return
        
        # Only process if button was actually held
        if not self.shared_state.button_currently_held:
            return
        
        # Mark button as no longer held
        self.shared_state.button_currently_held = False
        
        # Get current seat position (prefer mm if available)
        if self.shared_state.seat_position_mm and len(self.shared_state.seat_position_mm) > 0:
            current_pos_mm = self.shared_state.seat_position_mm[-1]
        elif self.shared_state.raw_seat_pos and len(self.shared_state.raw_seat_pos) > 0:
            current_pos_mm = self.shared_state.raw_seat_pos[-1]
        else:
            return
        
        # Optimal position is seat_position_release (leftmost - where RELEASE/orange zone is)
        if hasattr(self.shared_state, 'seat_position_release') and self.shared_state.seat_position_release is not None:
            optimal_pos = self.shared_state.seat_position_release
        else:
            return
        
        # Calculate RELEASE accuracy: Same gradient approach as press
        distance = abs(current_pos_mm - optimal_pos)
        perfect_zone = self.shared_state.button_press_perfect_zone_mm
        window = self.shared_state.button_press_window_mm
        
        if distance <= perfect_zone:
            # Within perfect zone - always 100%
            release_accuracy = 100.0
        elif distance <= window:
            # Outside perfect zone but within window - gentle cubic root decay
            excess_distance = distance - perfect_zone
            remaining_window = window - perfect_zone
            normalized_distance = excess_distance / remaining_window  # 0 to 1
            # Cubic root for very gentle curve from 100% down to 0%
            decay_factor = 1.0 - (normalized_distance ** 0.33)  # Cubic root
            release_accuracy = 100.0 * decay_factor
            release_accuracy = max(0.0, min(100.0, release_accuracy))
        else:
            # Outside window - no credit
            release_accuracy = 0.0
        
        # Store release accuracy
        self.shared_state.button_release_accuracies.append(release_accuracy)
        
        # Calculate combined accuracy (average of press and release)
        if self.shared_state.button_press_accuracy_temp is not None:
            combined_accuracy = (self.shared_state.button_press_accuracy_temp + release_accuracy) / 2.0
        else:
            # Fallback if press accuracy wasn't stored (shouldn't happen)
            combined_accuracy = release_accuracy
        
        # Store combined accuracy
        self.shared_state.button_combined_accuracies.append(combined_accuracy)
        self.shared_state.button_press_seat_pos.append(current_pos_mm)
        
        # Get press position for output
        press_pos = self.shared_state.button_press_position_mm if self.shared_state.button_press_position_mm is not None else "N/A"
        
        # Calculate expected time and early/late status
        current_time = time.time()
        time_expected = self.last_optimal_release_crossing_time if self.last_optimal_release_crossing_time else current_time
        if current_pos_mm < optimal_pos:
            early_late = "early"
        elif current_pos_mm > optimal_pos:
            early_late = "late"
        else:
            early_late = "on time"
        
        # Write to CSV
        self._write_button_event_to_csv("release", current_time, time_expected, release_accuracy, early_late)
        
        # Output
        print(f"Button RELEASE #{self.button_press_count}: release_accuracy={release_accuracy:.1f}% (pos={current_pos_mm:.1f}mm, target={optimal_pos:.1f}mm)")
        print(f"  → COMBINED accuracy={combined_accuracy:.1f}% (press={self.shared_state.button_press_accuracy_temp:.1f}%, release={release_accuracy:.1f}%)")
        
        # Reset temporary storage
        self.shared_state.button_press_accuracy_temp = None
        self.shared_state.button_press_position_mm = None
    
    def on_finish_session(self, event):
        """Handle finish session button click - save summary and show summary screen"""
        # Stop the timer
        self.timer.Stop()
        
        # Stop writing stats
        self.shared_state.stop_writing_stats()
        
        # Stop distance calculation when finishing session
        self.shared_state.game_started = False
        
        # Close button press CSV file
        if self.button_press_csv_file:
            try:
                self.button_press_csv_file.close()
                print(f"Button press CSV file closed: {self.button_press_csv_path}")
            except Exception as e:
                print(f"Error closing button press CSV file: {e}")
            self.button_press_csv_file = None
            self.button_press_csv_writer = None
        
        # Save session summary to CSV
        summary_data = self.shared_state.save_session_summary()
        
        # Switch to summary page
        parent = self.GetParent()
        parent.switch_to_summary_page(summary_data)

# ------------------------------------------------------------------------------------------------------------

class ModernStatsDisplay(wx.Panel):
    def __init__(self, parent, shared_state):
        super(ModernStatsDisplay, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.shared_state = shared_state

        # Create main horizontal sizer for the metric cards
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Time Card
        self.time_card = self.create_metric_card("Time", "00:05:32", wx.Colour(255, 255, 255))

        # Power Card
        self.power_card = self.create_metric_card("Power", "185 W", wx.Colour(255, 255, 255))

        # Distance Card
        self.distance_card = self.create_metric_card("Distance", "0.5 km", wx.Colour(255, 255, 255))

        # Accuracy Card
        self.accuracy_card = self.create_metric_card("Accuracy", "92%", wx.Colour(255, 255, 255))

        # Initialize layout based on current mode
        is_automatic = hasattr(shared_state, 'is_automatic_mode') and shared_state.is_automatic_mode
        if is_automatic:
            # AUTOMATIC MODE: Hide accuracy card and center the 3 remaining cards
            self.accuracy_card.Hide()
            self.main_sizer.AddStretchSpacer()
            self.main_sizer.Add(self.time_card, 1, wx.EXPAND | wx.RIGHT, 15)
            self.main_sizer.Add(self.power_card, 1, wx.EXPAND | wx.RIGHT, 15)
            self.main_sizer.Add(self.distance_card, 1, wx.EXPAND)
            self.main_sizer.AddStretchSpacer()
        else:
            # MANUAL MODE: Show all 4 cards
            self.main_sizer.Add(self.time_card, 1, wx.EXPAND | wx.RIGHT, 15)
            self.main_sizer.Add(self.power_card, 1, wx.EXPAND | wx.RIGHT, 15)
            self.main_sizer.Add(self.distance_card, 1, wx.EXPAND | wx.RIGHT, 15)
            self.main_sizer.Add(self.accuracy_card, 1, wx.EXPAND)

        self.SetSizer(self.main_sizer)
        
        # Track current mode to detect changes
        self.current_mode_is_automatic = is_automatic

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
        # Check if mode has changed and update layout accordingly
        is_automatic = hasattr(self.shared_state, 'is_automatic_mode') and self.shared_state.is_automatic_mode
        
        if self.current_mode_is_automatic != is_automatic:
            # Mode changed - rebuild layout
            self.current_mode_is_automatic = is_automatic
            
            # Clear and rebuild sizer based on mode
            self.main_sizer.Clear(delete_windows=False)  # Don't delete the card windows
            
            if is_automatic:
                # AUTOMATIC MODE: Hide accuracy card and center the 3 remaining cards
                self.accuracy_card.Hide()
                
                # Add stretch spacer, then the 3 cards, then another stretch spacer
                self.main_sizer.AddStretchSpacer()
                self.main_sizer.Add(self.time_card, 1, wx.EXPAND | wx.RIGHT, 15)
                self.main_sizer.Add(self.power_card, 1, wx.EXPAND | wx.RIGHT, 15)
                self.main_sizer.Add(self.distance_card, 1, wx.EXPAND)
                self.main_sizer.AddStretchSpacer()
            else:
                # MANUAL MODE: Show accuracy card, no centering spacers
                self.accuracy_card.Show()
                
                # Add the 4 cards without spacers
                self.main_sizer.Add(self.time_card, 1, wx.EXPAND | wx.RIGHT, 15)
                self.main_sizer.Add(self.power_card, 1, wx.EXPAND | wx.RIGHT, 15)
                self.main_sizer.Add(self.distance_card, 1, wx.EXPAND | wx.RIGHT, 15)
                self.main_sizer.Add(self.accuracy_card, 1, wx.EXPAND)
            
            self.Layout()
        
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

        # Update accuracy only in manual mode (card is hidden in automatic mode)
        if not is_automatic:
            # MANUAL MODE: accuracy from button press-hold-release timing (combined accuracy)
            if self.shared_state.button_combined_accuracies:
                # Average all combined (press + release) accuracies
                accuracy = sum(self.shared_state.button_combined_accuracies) / len(self.shared_state.button_combined_accuracies)
            else:
                # No completed press-release cycles yet - start at 0%
                accuracy = 0.0
            accuracy_str = f"{int(accuracy)}%"
            self.accuracy_value_label.SetLabel(accuracy_str)

            # Update accuracy label color based on percentage (only if we have completed cycles)
            has_completed_cycles = len(self.shared_state.button_combined_accuracies) > 0
            if has_completed_cycles:
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
        self.session_rowing_time = 0.0 # Reset rowing time
        self.shared_state.last_update_time = time.time()

        self.shared_state.handle_force = []
        self.shared_state.handle_position = []
        self.shared_state.L_foot_force = []
        self.shared_state.R_foot_force = []
        self.shared_state.switch_press = []
        
        # Reset button press-hold-release accuracy tracking
        self.shared_state.button_press_accuracies = []
        self.shared_state.button_release_accuracies = []
        self.shared_state.button_combined_accuracies = []
        self.shared_state.button_press_seat_pos = []
        self.shared_state.button_currently_held = False
        self.shared_state.button_press_position_mm = None
        self.shared_state.button_press_accuracy_temp = None

        # Reset display
        self.time_value_label.SetLabel("00:00:00")
        self.power_value_label.SetLabel("0 W")
        self.distance_value_label.SetLabel("0 m")
        self.accuracy_value_label.SetLabel("0%")
        self.accuracy_value_label.SetForegroundColour(wx.Colour(64, 64, 64))

# ------------------------------------------------------------------------------------------------------------

class LocationProgressPanel(wx.Panel):
    """Panel to display current location and progress to next milestone"""
    def __init__(self, parent, shared_state):
        super(LocationProgressPanel, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.shared_state = shared_state
        self.SetMinSize((-1, 130))
        
        # Use shared map logic for consistency with dashboard
        self.location_milestones = MapLogic.LOCATION_MILESTONES
        self.location_interval = MapLogic.LOCATION_INTERVAL
        self.cycle_distance = MapLogic.CYCLE_DISTANCE
        
        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSpacer(10)
        
        # Location header
        location_header = wx.StaticText(self, label="CURRENT LOCATION")
        location_header.SetForegroundColour(wx.Colour(128, 128, 128))
        location_header.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        main_sizer.Add(location_header, 0, wx.ALIGN_CENTER)
        main_sizer.AddSpacer(5)
        
        # Location name (large and prominent)
        self.location_label = wx.StaticText(self, label="Hawaii")
        self.location_label.SetForegroundColour(wx.Colour(33, 150, 243))  # Blue
        self.location_label.SetFont(wx.Font(36, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        main_sizer.Add(self.location_label, 0, wx.ALIGN_CENTER)
        #main_sizer.AddSpacer(5)
        
        # Progress section - horizontal layout
        progress_container = wx.BoxSizer(wx.HORIZONTAL)
        progress_container.AddSpacer(100)  # Left padding
        
        # Wrap progress bar container in a panel to maintain fixed width
        self.progress_bar_wrapper = wx.Panel(self)
        self.progress_bar_wrapper.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.progress_bar_wrapper.Bind(wx.EVT_SIZE, self.OnProgressBarWrapperSize)
        
        # Progress bar with distance label (showing meters in current segment)
        progress_bar_container = wx.BoxSizer(wx.VERTICAL)
        
        # Distance indicator (small, above progress bar) - shows meters in current 0-20m segment
        self.distance_label = wx.StaticText(self.progress_bar_wrapper, label="0.0m / 20m")
        self.distance_label.SetForegroundColour(wx.Colour(150, 150, 150))
        self.distance_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        progress_bar_container.Add(self.distance_label, 0, wx.ALIGN_LEFT)
        progress_bar_container.AddSpacer(3)
        
        # Progress bar (custom drawn)
        self.progress_bar_panel = wx.Panel(self.progress_bar_wrapper, size=(-1, 20))
        self.progress_bar_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.progress_bar_panel.Bind(wx.EVT_PAINT, self.OnPaintProgressBar)
        self.progress_bar_panel.Bind(wx.EVT_SIZE, self.OnProgressBarSize)
        progress_bar_container.Add(self.progress_bar_panel, 1, wx.EXPAND)
        
        self.progress_bar_wrapper.SetSizer(progress_bar_container)
        progress_container.Add(self.progress_bar_wrapper, 1, wx.EXPAND)
        progress_container.AddSpacer(20)  # Space between bar and destination
        
        # Destination marker at the end
        destination_container = wx.BoxSizer(wx.VERTICAL)
        destination_container.AddSpacer(3)  # Align with percentage
        
        # Arrow/indicator pointing to destination
        arrow_label = wx.StaticText(self, label="→")
        arrow_label.SetForegroundColour(wx.Colour(76, 175, 80))
        arrow_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        destination_container.Add(arrow_label, 0, wx.ALIGN_CENTER)
        
        progress_container.Add(destination_container, 0, wx.ALIGN_CENTER_VERTICAL)
        progress_container.AddSpacer(10)
        
        # Next location name (at the end of progress bar)
        next_location_container = wx.BoxSizer(wx.VERTICAL)
        next_location_header = wx.StaticText(self, label="NEXT")
        next_location_header.SetForegroundColour(wx.Colour(150, 150, 150))
        next_location_header.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        next_location_container.Add(next_location_header, 0, wx.ALIGN_LEFT)
        
        self.next_location_label = wx.StaticText(self, label="Fiji")
        self.next_location_label.SetForegroundColour(wx.Colour(76, 175, 80))
        self.next_location_label.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        next_location_container.Add(self.next_location_label, 0, wx.ALIGN_LEFT)
        
        # Calculate maximum width needed for location names to prevent layout shifts
        # Create a temporary DC to measure text width
        temp_dc = wx.ClientDC(self)
        temp_dc.SetFont(self.next_location_label.GetFont())
        max_location_width = 0
        for location_name, _ in self.location_milestones:
            text_width, _ = temp_dc.GetTextExtent(location_name)
            max_location_width = max(max_location_width, text_width)
        # Add some padding for safety
        max_location_width += 20
        
        # Set fixed minimum width for next_location_container to prevent layout shifts
        next_location_container.SetMinSize((max_location_width, -1))
        
        progress_container.Add(next_location_container, 0, wx.ALIGN_CENTER_VERTICAL)
        progress_container.AddSpacer(100)  # Right padding
        
        main_sizer.Add(progress_container, 0, wx.EXPAND)
        main_sizer.AddSpacer(20)
        
        self.SetSizer(main_sizer)
        
        # Store current progress for drawing
        self.current_progress = 0.0
        # Store fixed width for progress bar to prevent shrinking
        self.progress_bar_width = None
        self.progress_bar_wrapper_width = None
    
    def OnProgressBarWrapperSize(self, event):
        """Store the progress bar wrapper width when it's first properly sized and set minimum size"""
        size = self.progress_bar_wrapper.GetSize()
        if size.width > 0:
            # Store the maximum width we've seen to prevent shrinking
            if self.progress_bar_wrapper_width is None or size.width > self.progress_bar_wrapper_width:
                self.progress_bar_wrapper_width = size.width
                # Set minimum size to prevent the wrapper (and thus the bar) from shrinking
                self.progress_bar_wrapper.SetMinSize((self.progress_bar_wrapper_width, -1))
        event.Skip()
    
    def OnProgressBarSize(self, event):
        """Store the progress bar width when it's first properly sized and set minimum size"""
        size = self.progress_bar_panel.GetSize()
        if size.width > 0:
            # Store the maximum width we've seen to prevent shrinking
            if self.progress_bar_width is None or size.width > self.progress_bar_width:
                self.progress_bar_width = size.width
                # Set minimum size to prevent the bar from shrinking
                self.progress_bar_panel.SetMinSize((self.progress_bar_width, -1))
        event.Skip()
    
    def OnPaintProgressBar(self, event):
        """Draw the progress bar"""
        dc = wx.PaintDC(self.progress_bar_panel)
        size = self.progress_bar_panel.GetSize()
        width, height = size.width, size.height
        
        # Background
        dc.SetBrush(wx.Brush(wx.Colour(230, 230, 230)))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRoundedRectangle(0, 0, width, height, 10)
        
        # Progress fill
        if self.current_progress > 0:
            progress_width = int(width * self.current_progress)
            # Gradient effect
            dc.SetBrush(wx.Brush(wx.Colour(76, 175, 80)))  # Green
            dc.DrawRoundedRectangle(0, 0, progress_width, height, 10)
    
    def update_display(self):
        """Update location and progress display using shared MapLogic with time-based logic"""
        # Use time instead of distance
        cumulative_total_time = self.shared_state.get_cumulative_total_rowing_time()
        interval = self.shared_state.settings_manager.get_map_interval()
        
        # Use shared map logic with time
        location_info = MapLogic.get_current_location_info_by_time(cumulative_total_time, interval)
        
        # Update location and progress labels
        self.shared_state.current_location = location_info['current_location']
        self.location_label.SetLabel(location_info['current_location'])
        self.current_progress = location_info['progress_to_next']
        
        # Get time passed in current segment (in seconds)
        time_in_segment = location_info['distance_into_segment'] # Mapped to time_into_segment
        segment_duration = location_info['segment_length'] # Mapped to interval_seconds
        
        # Convert seconds to minutes for display, or keep as mm:ss
        # Display: "X min / Y min"
        time_min = time_in_segment / 60.0
        segment_min = segment_duration / 60.0
        
        # Update distance label to show time in current segment
        self.distance_label.SetLabel(f"{time_min:.1f} min / {segment_min:.0f} min")
        self.next_location_label.SetLabel(location_info['next_location'])
        
        # Refresh progress bar and scene panel (to update map image)
        self.progress_bar_panel.Refresh()
        if hasattr(self, 'rowing_scene_panel'):
            self.rowing_scene_panel.Refresh()  # This will update the map image/theme
        self.Layout()

# ------------------------------------------------------------------------------------------------------------

class RowingScenePanel(wx.Panel):
    def __init__(self, parent, shared_state):
        super(RowingScenePanel, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(135, 206, 250))  # Sky blue background
        self.shared_state = shared_state
        self.SetMinSize((-1, 200))
        
        # Enable double buffering for smoother rendering
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # Initialize sprite manager for beautiful graphics
        self.sprite_manager = SpriteManager()
        
        # Background scrolling based on cumulative power/distance
        self.background_offset = 0.0  # How far the background has scrolled
        self.cumulative_distance = 0.0  # Total distance traveled
        self.distance_per_power_unit = 0.05  # How much distance per watt of power (slowed down further)
        
        # Boat animation
        self.boat_x_position = 0.3  # Fixed boat position (30% from left)
        self.boat_bob_offset = 0.0  # Vertical bobbing offset
        self.bob_speed = 0.1  # Speed of bobbing animation
        
        # Current location theme
        self.current_location = "Hawaii"
        
        # Use shared map logic for consistency
        self.location_milestones = MapLogic.LOCATION_MILESTONES
        self.location_interval = MapLogic.LOCATION_INTERVAL
        self.cycle_distance = MapLogic.CYCLE_DISTANCE
        
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
            "Hawaii": {
                "landscape_color": wx.Colour(194, 178, 128),  # Sandy beach
                "accent_color": wx.Colour(34, 139, 34),       # Palm green
                "water_color": wx.Colour(0, 191, 255),        # Turquoise
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue
                "features": "palms"
            },
            "Fiji": {
                "landscape_color": wx.Colour(194, 178, 128),  # Sandy beach
                "accent_color": wx.Colour(34, 139, 34),       # Palm green
                "water_color": wx.Colour(64, 224, 208),       # Turquoise
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue
                "features": "palms"
            },
            "Tahiti": {
                "landscape_color": wx.Colour(139, 69, 19),    # Volcanic rock
                "accent_color": wx.Colour(34, 139, 34),       # Palm green
                "water_color": wx.Colour(0, 206, 209),        # Dark turquoise
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue
                "features": "palms"
            },
            "Bora Bora": {
                "landscape_color": wx.Colour(255, 239, 213),  # White sand
                "accent_color": wx.Colour(34, 139, 34),       # Palm green
                "water_color": wx.Colour(127, 255, 212),      # Aquamarine
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue
                "features": "palms"
            },
            "Maldives": {
                "landscape_color": wx.Colour(255, 250, 240),  # Pristine sand
                "accent_color": wx.Colour(34, 139, 34),       # Palm green
                "water_color": wx.Colour(64, 224, 208),       # Crystal turquoise
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue
                "features": "palms"
            },
            "North Pole": {
                "landscape_color": wx.Colour(240, 248, 255),  # Alice blue for ice
                "accent_color": wx.Colour(176, 196, 222),     # Light steel blue
                "water_color": wx.Colour(70, 130, 180),       # Steel blue
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue
                "features": "icebergs"
            },
            "Amazon": {
                "landscape_color": wx.Colour(34, 139, 34),    # Forest green
                "accent_color": wx.Colour(107, 142, 35),      # Olive drab
                "water_color": wx.Colour(139, 69, 19),        # Saddle brown (muddy water)
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue
                "features": "trees"
            },
            "Mediterranean": {
                "landscape_color": wx.Colour(255, 218, 185),  # Peach puff
                "accent_color": wx.Colour(210, 180, 140),     # Tan
                "water_color": wx.Colour(0, 191, 255),        # Deep sky blue
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue
                "features": "cliffs"
            },
            "Japan": {
                "landscape_color": wx.Colour(34, 139, 34),    # Green grass
                "accent_color": wx.Colour(34, 139, 34),       # Green
                "water_color": wx.Colour(0, 191, 255),        # Turquoise (same as Hawaii for now)
                "sky_color": wx.Colour(135, 206, 250),        # Sky blue (same as Hawaii for now)
                "features": "cherry_blossom"
            },
            "Antarctica": {
                "landscape_color": wx.Colour(176, 224, 230),  # Light blue ice
                "accent_color": wx.Colour(135, 206, 250),     # Light sky blue
                "water_color": wx.Colour(70, 130, 180),       # Steel blue (colder water)
                "sky_color": wx.Colour(135, 206, 250),       # Sky blue
                "features": "penguins"
            },
            "Amazon": {
                "landscape_color": wx.Colour(0, 100, 0),      # Dark green (darker than yellow sand)
                "accent_color": wx.Colour(34, 139, 34),       # Forest green
                "water_color": wx.Colour(0, 191, 255),        # Turquoise
                "sky_color": wx.Colour(135, 206, 250),       # Sky blue
                "features": "jungle"
            },
            "Australia": {
                "landscape_color": wx.Colour(194, 178, 128),  # Sandy beach (same as Hawaii)
                "accent_color": wx.Colour(34, 139, 34),       # Green
                "water_color": wx.Colour(0, 191, 255),        # Turquoise
                "sky_color": wx.Colour(135, 206, 250),       # Sky blue
                "features": "kangaroos"
            }
        }

    def OnPaint(self, event):
        #dc = wx.PaintDC(self)
        dc = wx.BufferedPaintDC(self)
        size = self.GetSize()
        width, height = size.width, size.height
        
        # Create GraphicsContext for smoother rendering
        try:
            gc = wx.GraphicsContext.Create(dc)
        except:
            # Fallback if GraphicsContext not available
            gc = None
        
        # Get current location theme
        theme = self.locations[self.current_location]
        
        # Draw sky background with gradient
        self.draw_gradient_sky(dc, gc, width, height, theme)
        
        # Draw clouds in the background (behind everything)
        self.draw_clouds(dc, width, height, theme)
        
        # Draw landscape/mountains in background
        self.draw_landscape(dc, gc, width, height, theme)
        
        # Draw enhanced water with reflections (reduced height for better sky visibility)
        water_height = height // 5  # Reduced from // 3 to // 5
        water_y = height - water_height
        self.draw_water(dc, gc, width, water_y, water_height, theme)
        
        # Draw boat sprite at fixed position (no bobbing)
        boat_x = int(width * self.boat_x_position)
        boat_y = water_y + 10  # Position boat on the water surface
        self.draw_boat_sprite(dc, boat_x, boat_y)
        
        # Draw location-specific features (clouds, etc.)
        self.draw_location_features(dc, gc, width, height, theme)

    def draw_clouds(self, dc, width, height, theme):
        """Draw clouds in the sky (for palm tree, cherry blossom, penguin, jungle, and kangaroo locations)"""
        if theme["features"] == "palms" or theme["features"] == "cherry_blossom" or theme["features"] == "penguins" or theme["features"] == "jungle" or theme["features"] == "kangaroos":
            cloud_sprite = self.sprite_manager.get_sprite('cloud')
            
            if cloud_sprite:
                # Calculate scroll offset for parallax effect (slower than other elements)
                cloud_offset = int(self.background_offset * 0.15) % (width * 2)
                
                # Draw puffy clouds
                cloud_spacing = width // 2
                for repeat in range(-1, 4):
                    for i in range(2):
                        cloud_x = repeat * cloud_spacing * 2 + i * cloud_spacing - cloud_offset
                        cloud_y = 40 + (i % 2) * 30
                        
                        if -150 <= cloud_x <= width + 150:
                            # Draw cloud sprite
                            sprite_width = cloud_sprite.GetWidth()
                            sprite_height = cloud_sprite.GetHeight()
                            dc.DrawBitmap(cloud_sprite, 
                                        cloud_x - sprite_width // 2, 
                                        cloud_y - sprite_height // 2, 
                                        True)
    
    def draw_gradient_sky(self, dc, gc, width, height, theme):
        """Draw gradient sky background"""
        if gc:
            # Create gradient from top to bottom
            sky_color = theme["sky_color"]
            
            # Lighter at horizon, darker at top
            color_top = wx.Colour(
                max(0, sky_color.Red() - 30),
                max(0, sky_color.Green() - 30),
                max(0, sky_color.Blue() - 30)
            )
            color_bottom = wx.Colour(
                min(255, sky_color.Red() + 40),
                min(255, sky_color.Green() + 40),
                min(255, sky_color.Blue() + 40)
            )
            
            # Create linear gradient brush
            gradient = gc.CreateLinearGradientBrush(
                0, 0, 0, height,
                color_top, color_bottom
            )
            gc.SetBrush(gradient)
            gc.DrawRectangle(0, 0, width, height)
        else:
            # Fallback to solid color
            dc.SetBrush(wx.Brush(theme["sky_color"]))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(0, 0, width, height)

    def draw_landscape(self, dc, gc, width, height, theme):
        """Draw scrolling background landscape"""
        landscape_height = height // 2
        
        if theme["features"] == "palms":
            # Draw sandy beach/island in background
            # Position beach to align with water line
            beach_y = height - (height // 5) - (height // 6)  # Above water line
            beach_height = height // 4
            
            # Calculate scroll offset to move with palm trees
            scroll_offset = int(self.background_offset * 0.5) % width
            
            # Draw beautiful textured sand that scrolls
            if gc:
                # Create gradient sand base - lighter colors
                sand_color = theme["landscape_color"]
                # Lighter sand - brighten instead of darken
                sand_light = wx.Colour(
                    min(255, sand_color.Red() + 30),
                    min(255, sand_color.Green() + 30),
                    min(255, sand_color.Blue() + 30)
                )
                # Slight gradient from base to lighter
                gradient = gc.CreateLinearGradientBrush(
                    0, beach_y, 0, beach_y + beach_height,
                    sand_color, sand_light
                )
                gc.SetBrush(gradient)
                gc.DrawRectangle(0, beach_y, width, beach_height)
                
                # Add sand texture details (dots/specks) that scroll
                dc.SetPen(wx.TRANSPARENT_PEN)
                for repeat in range(-1, 3):  # Multiple sections for scrolling
                    section_x = repeat * width - scroll_offset
                    
                    # Draw sand grain details
                    for i in range(0, width, 15):
                        x = section_x + i
                        if -20 <= x <= width + 20:
                            # Vary the y position and size for natural look
                            for j in range(3):
                                grain_x = x + (i * 7 % 10) - 5
                                grain_y = beach_y + beach_height // 3 + (i * 11 % (beach_height // 2))
                                grain_size = 2 + (i % 3)
                                
                                # Lighter sand grains for subtle texture
                                grain_color = wx.Colour(
                                    min(255, sand_color.Red() + 40),
                                    min(255, sand_color.Green() + 35),
                                    min(255, sand_color.Blue() + 25),
                                    120
                                )
                                dc.SetBrush(wx.Brush(grain_color))
                                dc.DrawCircle(grain_x, grain_y, grain_size)
            else:
                # Fallback without graphics context
                dc.SetBrush(wx.Brush(theme["landscape_color"]))
                dc.SetPen(wx.TRANSPARENT_PEN)
                dc.DrawRectangle(0, beach_y, width, beach_height)
            
            # Draw palm tree sprites in background
            self.draw_background_palm_sprites(dc, width, height, theme)
            
        elif theme["features"] == "cherry_blossom":
            # Draw green grass/landscape in background
            # Position grass to align with water line
            grass_y = height - (height // 5) - (height // 6)  # Above water line
            grass_height = height // 4
            
            # Calculate scroll offset to move with cherry blossom trees
            scroll_offset = int(self.background_offset * 0.5) % width
            
            # Draw beautiful textured grass that scrolls
            if gc:
                # Create gradient grass base - lighter green at top, darker at bottom
                grass_color = theme["landscape_color"]
                # Lighter grass - brighter green
                grass_light = wx.Colour(
                    min(255, grass_color.Red() + 20),
                    min(255, grass_color.Green() + 30),
                    min(255, grass_color.Blue() + 10)
                )
                # Slight gradient from lighter at top to darker at bottom
                gradient = gc.CreateLinearGradientBrush(
                    0, grass_y, 0, grass_y + grass_height,
                    grass_light, grass_color
                )
                gc.SetBrush(gradient)
                gc.DrawRectangle(0, grass_y, width, grass_height)
                
                # Add grass texture details (small dots/specks) that scroll
                dc.SetPen(wx.TRANSPARENT_PEN)
                for repeat in range(-1, 3):  # Multiple sections for scrolling
                    section_x = repeat * width - scroll_offset
                    
                    # Draw grass texture details
                    for i in range(0, width, 12):
                        x = section_x + i
                        if -20 <= x <= width + 20:
                            # Vary the y position and size for natural look
                            for j in range(2):
                                texture_x = x + (i * 7 % 10) - 5
                                texture_y = grass_y + grass_height // 3 + (i * 11 % (grass_height // 2))
                                texture_size = 1 + (i % 2)
                                
                                # Lighter/darker grass variations for subtle texture
                                texture_color = wx.Colour(
                                    min(255, max(0, grass_color.Red() + (i % 3) * 5 - 5)),
                                    min(255, max(0, grass_color.Green() + (i % 3) * 8 - 4)),
                                    min(255, max(0, grass_color.Blue() + (i % 3) * 3 - 2)),
                                    150
                                )
                                dc.SetBrush(wx.Brush(texture_color))
                                dc.DrawCircle(texture_x, texture_y, texture_size)
            else:
                # Fallback without graphics context
                dc.SetBrush(wx.Brush(theme["landscape_color"]))
                dc.SetPen(wx.TRANSPARENT_PEN)
                dc.DrawRectangle(0, grass_y, width, grass_height)
            
            # Draw cherry blossom tree sprites in background
            self.draw_background_cherry_blossom_sprites(dc, width, height, theme)
            
        elif theme["features"] == "penguins":
            # Draw ice/landscape in background
            # Position ice to align with water line
            ice_y = height - (height // 5) - (height // 6)  # Above water line
            ice_height = height // 4
            
            # Calculate scroll offset to move with penguins
            scroll_offset = int(self.background_offset * 0.5) % width
            
            # Draw beautiful textured ice that scrolls
            if gc:
                # Create gradient ice base - lighter blue at top, slightly darker at bottom
                ice_color = theme["landscape_color"]
                # Lighter ice - brighter light blue
                ice_light = wx.Colour(
                    min(255, ice_color.Red() + 30),
                    min(255, ice_color.Green() + 30),
                    min(255, ice_color.Blue() + 30)
                )
                # Slight gradient from lighter at top to darker at bottom
                gradient = gc.CreateLinearGradientBrush(
                    0, ice_y, 0, ice_y + ice_height,
                    ice_light, ice_color
                )
                gc.SetBrush(gradient)
                gc.DrawRectangle(0, ice_y, width, ice_height)
                
                # Add ice texture details (small dots/specks) that scroll
                dc.SetPen(wx.TRANSPARENT_PEN)
                for repeat in range(-1, 3):  # Multiple sections for scrolling
                    section_x = repeat * width - scroll_offset
                    
                    # Draw ice texture details
                    for i in range(0, width, 15):
                        x = section_x + i
                        if -20 <= x <= width + 20:
                            # Vary the y position and size for natural look
                            for j in range(3):
                                texture_x = x + (i * 7 % 10) - 5
                                texture_y = ice_y + ice_height // 3 + (i * 11 % (ice_height // 2))
                                texture_size = 2 + (i % 3)
                                
                                # Lighter/darker ice variations for subtle texture
                                texture_color = wx.Colour(
                                    min(255, max(0, ice_color.Red() + (i % 3) * 8 - 4)),
                                    min(255, max(0, ice_color.Green() + (i % 3) * 8 - 4)),
                                    min(255, max(0, ice_color.Blue() + (i % 3) * 8 - 4)),
                                    120
                                )
                                dc.SetBrush(wx.Brush(texture_color))
                                dc.DrawCircle(texture_x, texture_y, texture_size)
            else:
                # Fallback without graphics context
                dc.SetBrush(wx.Brush(theme["landscape_color"]))
                dc.SetPen(wx.TRANSPARENT_PEN)
                dc.DrawRectangle(0, ice_y, width, ice_height)
            
            # Draw penguin sprites in background
            self.draw_background_penguin_sprites(dc, width, height, theme)
            
        elif theme["features"] == "jungle":
            # Draw dark green ground/landscape in background
            # Position ground to align with water line
            ground_y = height - (height // 5) - (height // 6)  # Above water line
            ground_height = height // 4
            
            # Calculate scroll offset to move with jungle trees
            scroll_offset = int(self.background_offset * 0.5) % width
            
            # Draw beautiful textured dark green ground that scrolls
            if gc:
                # Create gradient ground base - lighter dark green at top, darker at bottom
                ground_color = theme["landscape_color"]
                # Lighter dark green - slightly brighter
                ground_light = wx.Colour(
                    min(255, ground_color.Red() + 20),
                    min(255, ground_color.Green() + 25),
                    min(255, ground_color.Blue() + 10)
                )
                # Slight gradient from lighter at top to darker at bottom
                gradient = gc.CreateLinearGradientBrush(
                    0, ground_y, 0, ground_y + ground_height,
                    ground_light, ground_color
                )
                gc.SetBrush(gradient)
                gc.DrawRectangle(0, ground_y, width, ground_height)
                
                # Add ground texture details (small dots/specks) that scroll
                dc.SetPen(wx.TRANSPARENT_PEN)
                for repeat in range(-1, 3):  # Multiple sections for scrolling
                    section_x = repeat * width - scroll_offset
                    
                    # Draw ground texture details
                    for i in range(0, width, 15):
                        x = section_x + i
                        if -20 <= x <= width + 20:
                            # Vary the y position and size for natural look
                            for j in range(3):
                                texture_x = x + (i * 7 % 10) - 5
                                texture_y = ground_y + ground_height // 3 + (i * 11 % (ground_height // 2))
                                texture_size = 2 + (i % 3)
                                
                                # Lighter/darker green variations for subtle texture
                                texture_color = wx.Colour(
                                    min(255, max(0, ground_color.Red() + (i % 3) * 5 - 5)),
                                    min(255, max(0, ground_color.Green() + (i % 3) * 8 - 4)),
                                    min(255, max(0, ground_color.Blue() + (i % 3) * 3 - 2)),
                                    120
                                )
                                dc.SetBrush(wx.Brush(texture_color))
                                dc.DrawCircle(texture_x, texture_y, texture_size)
            else:
                # Fallback without graphics context
                dc.SetBrush(wx.Brush(theme["landscape_color"]))
                dc.SetPen(wx.TRANSPARENT_PEN)
                dc.DrawRectangle(0, ground_y, width, ground_height)
            
            # Draw jungle tree sprites in background
            self.draw_background_jungle_sprites(dc, width, height, theme)
            
        elif theme["features"] == "kangaroos":
            # Draw sandy beach/island in background (same as palms)
            # Position beach to align with water line
            beach_y = height - (height // 5) - (height // 6)  # Above water line
            beach_height = height // 4
            
            # Calculate scroll offset to move with kangaroos
            scroll_offset = int(self.background_offset * 0.5) % width
            
            # Draw beautiful textured sand that scrolls
            if gc:
                # Create gradient sand base - lighter colors
                sand_color = theme["landscape_color"]
                # Lighter sand - brighten instead of darken
                sand_light = wx.Colour(
                    min(255, sand_color.Red() + 30),
                    min(255, sand_color.Green() + 30),
                    min(255, sand_color.Blue() + 30)
                )
                # Slight gradient from base to lighter
                gradient = gc.CreateLinearGradientBrush(
                    0, beach_y, 0, beach_y + beach_height,
                    sand_color, sand_light
                )
                gc.SetBrush(gradient)
                gc.DrawRectangle(0, beach_y, width, beach_height)
                
                # Add sand texture details (dots/specks) that scroll
                dc.SetPen(wx.TRANSPARENT_PEN)
                for repeat in range(-1, 3):  # Multiple sections for scrolling
                    section_x = repeat * width - scroll_offset
                    
                    # Draw sand grain details
                    for i in range(0, width, 15):
                        x = section_x + i
                        if -20 <= x <= width + 20:
                            # Vary the y position and size for natural look
                            for j in range(3):
                                grain_x = x + (i * 7 % 10) - 5
                                grain_y = beach_y + beach_height // 3 + (i * 11 % (beach_height // 2))
                                grain_size = 2 + (i % 3)
                                
                                # Lighter sand grains for subtle texture
                                grain_color = wx.Colour(
                                    min(255, sand_color.Red() + 40),
                                    min(255, sand_color.Green() + 35),
                                    min(255, sand_color.Blue() + 25),
                                    120
                                )
                                dc.SetBrush(wx.Brush(grain_color))
                                dc.DrawCircle(grain_x, grain_y, grain_size)
            else:
                # Fallback without graphics context
                dc.SetBrush(wx.Brush(theme["landscape_color"]))
                dc.SetPen(wx.TRANSPARENT_PEN)
                dc.DrawRectangle(0, beach_y, width, beach_height)
            
            # Draw kangaroo sprites in background
            self.draw_background_kangaroo_sprites(dc, width, height, theme)
            
        elif theme["features"] == "icebergs":
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

    def draw_background_palm_sprites(self, dc, width, height, theme):
        """Draw palm tree sprites in the background with scrolling"""
        palm_spacing = width // 3
        
        # Calculate beach position to match where it's actually drawn
        # This should match the beach_y calculation in draw_landscape
        beach_y = height - (height // 5) - (height // 6)  # Above water line
        
        # Calculate scroll offset for parallax effect
        scroll_offset = int(self.background_offset * 0.5) % (width * 2)
        
        # Get palm tree sprites
        palm_tree = self.sprite_manager.get_sprite('palm_tree')
        palm_tree_small = self.sprite_manager.get_sprite('palm_tree_small')
        
        if not palm_tree or not palm_tree_small:
            return
        
        # Draw multiple palm trees across sections
        for repeat in range(-1, 4):
            section_x = repeat * palm_spacing * 4 - scroll_offset
            
            # 4 palm trees per section at fixed positions
            for i in range(4):
                palm_x = section_x + i * palm_spacing
                
                # Alternate between sizes for variety
                sprite = palm_tree if i % 2 == 0 else palm_tree_small
                sprite_width = sprite.GetWidth()
                sprite_height = sprite.GetHeight()
                
                # Position palm tree on beach (bottom of tree should be at beach level)
                palm_draw_x = palm_x - sprite_width // 2
                palm_draw_y = beach_y - sprite_height + 20  # Adjust slightly to sit on beach
                
                # Only draw if on screen
                if -150 <= palm_x <= width + 150:
                    dc.DrawBitmap(sprite, palm_draw_x, palm_draw_y, True)

    def draw_background_cherry_blossom_sprites(self, dc, width, height, theme):
        """Draw cherry blossom tree sprites in the background with scrolling"""
        cherry_spacing = width // 3
        
        # Calculate grass position to match where it's actually drawn
        # This should match the grass_y calculation in draw_landscape
        grass_y = height - (height // 5) - (height // 6)  # Above water line
        
        # Calculate scroll offset for parallax effect
        scroll_offset = int(self.background_offset * 0.5) % (width * 2)
        
        # Get cherry blossom sprites
        cherry_blossom = self.sprite_manager.get_sprite('cherry_blossom')
        cherry_blossom_small = self.sprite_manager.get_sprite('cherry_blossom_small')
        
        if not cherry_blossom or not cherry_blossom_small:
            return
        
        # Draw multiple cherry blossom trees across sections
        for repeat in range(-1, 4):
            section_x = repeat * cherry_spacing * 4 - scroll_offset
            
            # 4 cherry blossom trees per section at fixed positions
            for i in range(4):
                cherry_x = section_x + i * cherry_spacing
                
                # Alternate between sizes for variety
                sprite = cherry_blossom if i % 2 == 0 else cherry_blossom_small
                sprite_width = sprite.GetWidth()
                sprite_height = sprite.GetHeight()
                
                # Position cherry blossom tree on grass (bottom of tree should be at grass level)
                cherry_draw_x = cherry_x - sprite_width // 2
                cherry_draw_y = grass_y - sprite_height + 20  # Adjust slightly to sit on grass
                
                # Only draw if on screen
                if -150 <= cherry_x <= width + 150:
                    dc.DrawBitmap(sprite, cherry_draw_x, cherry_draw_y, True)

    def draw_background_penguin_sprites(self, dc, width, height, theme):
        """Draw penguin sprites in the background with scrolling"""
        penguin_spacing = width // 3
        
        # Calculate ice position to match where it's actually drawn
        # This should match the ice_y calculation in draw_landscape
        ice_y = height - (height // 5) - (height // 6)  # Above water line
        
        # Calculate scroll offset for parallax effect
        scroll_offset = int(self.background_offset * 0.5) % (width * 2)
        
        # Get penguin sprites
        penguin = self.sprite_manager.get_sprite('penguin')
        penguin_small = self.sprite_manager.get_sprite('penguin_small')
        
        if not penguin or not penguin_small:
            return
        
        # Draw multiple penguins across sections
        for repeat in range(-1, 4):
            section_x = repeat * penguin_spacing * 4 - scroll_offset
            
            # 4 penguins per section at fixed positions
            for i in range(4):
                penguin_x = section_x + i * penguin_spacing
                
                # Alternate between sizes for variety
                sprite = penguin if i % 2 == 0 else penguin_small
                sprite_width = sprite.GetWidth()
                sprite_height = sprite.GetHeight()
                
                # Position penguin on ice (bottom of penguin should be at ice level)
                penguin_draw_x = penguin_x - sprite_width // 2
                penguin_draw_y = ice_y - sprite_height + 20  # Adjust slightly to sit on ice
                
                # Only draw if on screen
                if -150 <= penguin_x <= width + 150:
                    dc.DrawBitmap(sprite, penguin_draw_x, penguin_draw_y, True)

    def draw_background_jungle_sprites(self, dc, width, height, theme):
        """Draw jungle tree sprites in the background with scrolling"""
        jungle_spacing = width // 3
        
        # Calculate ground position to match where it's actually drawn
        # This should match the ground_y calculation in draw_landscape
        ground_y = height - (height // 5) - (height // 6)  # Above water line
        
        # Calculate scroll offset for parallax effect
        scroll_offset = int(self.background_offset * 0.5) % (width * 2)
        
        # Get jungle sprites
        jungle = self.sprite_manager.get_sprite('jungle')
        jungle_small = self.sprite_manager.get_sprite('jungle_small')
        
        if not jungle or not jungle_small:
            return
        
        # Draw multiple jungle trees across sections
        for repeat in range(-1, 4):
            section_x = repeat * jungle_spacing * 4 - scroll_offset
            
            # 4 jungle trees per section at fixed positions
            for i in range(4):
                jungle_x = section_x + i * jungle_spacing
                
                # Alternate between sizes for variety
                sprite = jungle if i % 2 == 0 else jungle_small
                sprite_width = sprite.GetWidth()
                sprite_height = sprite.GetHeight()
                
                # Position jungle tree on ground (bottom of tree should be at ground level)
                jungle_draw_x = jungle_x - sprite_width // 2
                jungle_draw_y = ground_y - sprite_height + 20  # Adjust slightly to sit on ground
                
                # Only draw if on screen
                if -150 <= jungle_x <= width + 150:
                    dc.DrawBitmap(sprite, jungle_draw_x, jungle_draw_y, True)

    def draw_background_kangaroo_sprites(self, dc, width, height, theme):
        """Draw kangaroo sprites in the background with scrolling"""
        kangaroo_spacing = width // 3
        
        # Calculate beach position to match where it's actually drawn
        # This should match the beach_y calculation in draw_landscape
        beach_y = height - (height // 5) - (height // 6)  # Above water line
        
        # Calculate scroll offset for parallax effect
        scroll_offset = int(self.background_offset * 0.5) % (width * 2)
        
        # Get kangaroo sprites
        kangaroo = self.sprite_manager.get_sprite('kangaroo')
        kangaroo_small = self.sprite_manager.get_sprite('kangaroo_small')
        
        if not kangaroo or not kangaroo_small:
            return
        
        # Draw multiple kangaroos across sections
        for repeat in range(-1, 4):
            section_x = repeat * kangaroo_spacing * 4 - scroll_offset
            
            # 4 kangaroos per section at fixed positions
            for i in range(4):
                kangaroo_x = section_x + i * kangaroo_spacing
                
                # Alternate between sizes for variety
                sprite = kangaroo if i % 2 == 0 else kangaroo_small
                sprite_width = sprite.GetWidth()
                sprite_height = sprite.GetHeight()
                
                # Position kangaroo on beach (bottom of kangaroo should be at beach level)
                kangaroo_draw_x = kangaroo_x - sprite_width // 2
                kangaroo_draw_y = beach_y - sprite_height + 20  # Adjust slightly to sit on beach
                
                # Only draw if on screen
                if -150 <= kangaroo_x <= width + 150:
                    dc.DrawBitmap(sprite, kangaroo_draw_x, kangaroo_draw_y, True)

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

    def draw_water(self, dc, gc, width, water_y, water_height, theme):
        """Draw enhanced water with gradient and animated waves"""
        
        # Draw water base with gradient effect
        base_color = theme["water_color"]
        
        if gc:
            # Use GraphicsContext for smoother gradient
            water_dark = wx.Colour(
                int(base_color.Red() * 0.7),
                int(base_color.Green() * 0.7),
                int(base_color.Blue() * 0.7)
            )
            water_light = wx.Colour(
                min(255, int(base_color.Red() * 1.1)),
                min(255, int(base_color.Green() * 1.1)),
                min(255, int(base_color.Blue() * 1.1))
            )
            
            gradient = gc.CreateLinearGradientBrush(
                0, water_y, 0, water_y + water_height,
                water_dark, water_light
            )
            gc.SetBrush(gradient)
            gc.DrawRectangle(0, water_y, width, water_height)
        else:
            # Fallback gradient
            for y_step in range(water_height):
                progress = y_step / water_height
                # Darker at top, lighter at bottom
                r = int(base_color.Red() * (0.7 + 0.3 * progress))
                g = int(base_color.Green() * (0.7 + 0.3 * progress))
                b = int(base_color.Blue() * (0.7 + 0.3 * progress))
                
                dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                dc.DrawLine(0, water_y + y_step, width, water_y + y_step)
        
        # Draw animated wave patterns
        self.draw_water_waves(dc, gc, width, water_y, water_height)
        
        # Draw surface reflections
        self.draw_water_reflections(dc, width, water_y, water_height)

    def draw_water_waves(self, dc, gc, width, water_y, water_height):
        """Draw animated wave patterns on water surface"""
        
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

    def draw_boat_sprite(self, dc, x, y):
        """Draw the rowing boat using sprite"""
        # Add wake behind boat if moving (based on power)
        current_power = self.shared_state.avg_power[-1] if self.shared_state.avg_power else 0
        if current_power > 10:  # Show wake when there's good power
            dc.SetPen(wx.Pen(wx.Colour(255, 255, 255, 180), 2))
            # Draw wake lines behind boat
            for i in range(4):
                wake_x = x - 50 - (i * 12)
                wake_y_offset = int(math.sin(self.background_offset * 0.1 + i) * 3)
                dc.DrawLine(wake_x, y + 10 + i*2 + wake_y_offset, wake_x + 15, y + 10 + i*2 + wake_y_offset)
        
        # Draw boat sprite
        boat_sprite = self.sprite_manager.get_sprite('boat')
        if boat_sprite:
            sprite_width = boat_sprite.GetWidth()
            sprite_height = boat_sprite.GetHeight()
            
            # Center the sprite at x, y
            draw_x = x - sprite_width // 2
            draw_y = y - sprite_height // 2
            
            # Draw the boat sprite with transparency
            dc.DrawBitmap(boat_sprite, draw_x, draw_y, True)
        else:
            # Fallback if sprite not available
            dc.SetBrush(wx.Brush(wx.Colour(139, 69, 19)))
            dc.DrawRectangle(x - 30, y - 10, 60, 20)

    def draw_location_features(self, dc, gc, width, height, theme):
        """Draw scrolling location-specific decorative features"""
        if theme["features"] == "palms":
            # Clouds are now drawn in a separate method before landscape
            pass
        elif theme["features"] == "cherry_blossom":
            # Clouds are now drawn in a separate method before landscape
            pass
        elif theme["features"] == "penguins":
            # Clouds are now drawn in a separate method before landscape
            pass
        elif theme["features"] == "jungle":
            # Clouds are now drawn in a separate method before landscape
            pass
        elif theme["features"] == "kangaroos":
            # Clouds are now drawn in a separate method before landscape
            pass
            
        elif theme["features"] == "icebergs":
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
        
        # Update background scrolling based on cumulative power
        if self.shared_state.avg_power:
            current_power = self.shared_state.avg_power[-1]
            
            # Only scroll if there's significant power (reduce jitter)
            if current_power > 5:  # Only count power above 5W
                # Add to cumulative distance based on power
                self.cumulative_distance += current_power * self.distance_per_power_unit
                
                # Background scrolls based on cumulative distance
                self.background_offset = self.cumulative_distance
        
        # Update location based on manual override or automatic switching
        if self.shared_state.location_override is not None:
            # Manual override: use the specified location
            self.current_location = self.shared_state.location_override
        else:
            # Automatic mode: switch based on live cumulative TIME
            cumulative_total_time = self.shared_state.get_cumulative_total_rowing_time()
            interval = self.shared_state.settings_manager.get_map_interval()
            location_info = MapLogic.get_current_location_info_by_time(cumulative_total_time, interval)
            self.current_location = location_info['current_location']
        
        # Update shared_state so LocationProgressPanel can access it
        self.shared_state.current_location = self.current_location
        
        # Trigger update of location label and map image
        # Find the parent GamePage to update the location label
        parent = self.GetParent()
        while parent and not hasattr(parent, 'location_label'):
            parent = parent.GetParent()
        if parent and hasattr(parent, 'location_label'):
            parent.update_display()
        
        self.Refresh()

    def reset(self):
        """Reset the scene"""
        self.background_offset = 0.0  # Reset background scroll
        self.cumulative_distance = 0.0  # Reset distance
        # Reset location based on override or cumulative time
        if self.shared_state.location_override is not None:
            self.current_location = self.shared_state.location_override
        else:
            cumulative_total_time = self.shared_state.get_cumulative_total_rowing_time()
            interval = self.shared_state.settings_manager.get_map_interval()
            location_info = MapLogic.get_current_location_info_by_time(cumulative_total_time, interval)
            self.current_location = location_info['current_location']
        # Update shared_state
        self.shared_state.current_location = self.current_location
        
        # Trigger update of location label and map image
        # Find the parent GamePage to update the location label
        parent = self.GetParent()
        while parent and not hasattr(parent, 'location_label'):
            parent = parent.GetParent()
        if parent and hasattr(parent, 'location_label'):
            parent.update_display()
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
        self.last_progress_color = wx.Colour(158, 158, 158)  # Track last color (default to grey)
        
        # Create sizer with labels
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddStretchSpacer()  # Top flexible space
        
        # Title - set based on initial mode, centered horizontally
        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        title_sizer.AddStretchSpacer()
        title_sizer.AddSpacer(60)  # Shift text 60 pixels to the right
        initial_title = "FES Stimulation" if (hasattr(shared_state, 'is_automatic_mode') and shared_state.is_automatic_mode) else "Button Press Indicator"
        self.title_label = wx.StaticText(self, label=initial_title)
        self.title_label.SetForegroundColour(wx.Colour(64, 64, 64))
        self.title_label.SetFont(wx.Font(36, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title_sizer.Add(self.title_label, 0, wx.ALIGN_CENTER)
        title_sizer.AddStretchSpacer()
        main_sizer.Add(title_sizer, 0, wx.EXPAND)
        main_sizer.AddSpacer(120)
        
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
        
        #bar_spacer = wx.Panel(self)
        #bar_spacer.SetMinSize((-1, 80))  # Reserve height for the bar
        #main_sizer.Add(bar_spacer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 60)

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
        bar_y = height // 2 - 5  # Center the bar vertically
        bar_height = 50  # Even thicker bar
        bar_padding = 60
        
        # Determine if in automatic mode
        is_automatic = hasattr(self.shared_state, 'is_automatic_mode') and self.shared_state.is_automatic_mode
        
        # Base widths
        base_press_width = int(80 * 1.1)  # Width of PRESS bar (right end) - 10% wider (88 pixels)
        base_release_width = int(80 * 1.2 * 1.1 * 1.1)  # RELEASE bar - 10% wider than before (116 pixels)
        
        # In automatic mode: make orange bar 8% narrower, then make green bar match orange width
        if is_automatic:
            # Start with 20% wider bars (from previous change)
            wider_release_width = int(base_release_width * 1.2)
            wider_press_width = int(base_press_width * 1.2)
            
            # Make orange bar 8% narrower
            release_bar_width = int(wider_release_width * 0.92)  # 8% narrower
            
            # Make green bar match orange bar width exactly
            press_bar_width = release_bar_width  # Same width as orange bar
        else:
            press_bar_width = base_press_width  # Keep original width in manual mode
            release_bar_width = base_release_width  # Keep original width in manual mode
        
        bar_width = width - (2 * bar_padding) - release_bar_width - press_bar_width  # Account for end bars
        main_bar_x = bar_padding + release_bar_width  # Start after the left end bar
        
        # Draw Release bar (left end) - extends to the left
        release_bar_x = bar_padding - (release_bar_width - press_bar_width)  # Extend left by the difference
        # In automatic mode, move orange button 10 pixels to the left
        if is_automatic:
            release_bar_x -= 10
        dc.SetBrush(wx.Brush(wx.Colour(255, 152, 0)))  # Orange for release
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRoundedRectangle(release_bar_x, bar_y, release_bar_width, bar_height, 25)
        
        # Draw Press bar (right end)
        press_bar_offset = 33  # Offset to move PRESS bar to the right
        press_bar_x = bar_padding + release_bar_width + bar_width + press_bar_offset
        # In automatic mode, move green button 20 pixels to the left
        if is_automatic:
            press_bar_x -= 20
        dc.SetBrush(wx.Brush(wx.Colour(76, 175, 80)))  # Green for press
        dc.DrawRoundedRectangle(press_bar_x, bar_y, press_bar_width, bar_height, 25)
        
        # Calculate the maximum right position the moving bar will reach
        # The progress calculation uses: progress_width = int(bar_width * current_progress)
        # When current_progress = 1.0 (maximum), progress_width = int(bar_width * 1.0) = bar_width
        # So the moving bar's maximum right edge is: main_bar_x + bar_width
        # Add rounding buffer to account for int() conversion potentially rounding up
        rounding_buffer = 2
        # Calculate grey_bar_width to extend exactly to where the moving bar's maximum reaches
        max_moving_bar_right = main_bar_x + bar_width + rounding_buffer
        grey_bar_width = max_moving_bar_right - main_bar_x
        dc.SetBrush(wx.Brush(wx.Colour(240, 240, 240)))
        dc.DrawRoundedRectangle(main_bar_x, bar_y, grey_bar_width, bar_height, 25)
        
        # Calculate progress based on seat position
        # Map seat position so that release_pos corresponds to left edge and press_pos to right edge
        if hasattr(self.shared_state, 'seat_position_release') and hasattr(self.shared_state, 'seat_position_press'):
            # Use release/press positions with mm position
            if self.shared_state.seat_position_mm:
                current_pos_mm = self.shared_state.seat_position_mm[-1]  # position in mm
                release_pos = self.shared_state.seat_position_release  # Left edge (RELEASE bar)
                press_pos = self.shared_state.seat_position_press  # Right edge (PRESS bar)
                
                # Map position to 0-1 scale: [release_pos, press_pos] -> [0, 1]
                # Left edge (release_pos) = 0.0, Right edge (press_pos) = 1.0
                if press_pos > release_pos:
                    # Calculate raw progress
                    raw_progress = (current_pos_mm - release_pos) / (press_pos - release_pos)
                    
                    # Clip progress at boundaries: stay at 0 when below release_pos, stay at 1 when above press_pos
                    # This keeps the bar visually clipped at the edges until seat returns to range
                    if current_pos_mm < release_pos:
                        # Seat is to the left of release position - clip at left boundary (0.0)
                        current_progress = 0.0
                    elif current_pos_mm > press_pos:
                        # Seat is to the right of press position - clip at right boundary (1.0)
                        # When seat goes beyond press_pos, clip to 1.0 and keep it there until seat returns below press_pos
                        current_progress = 1.0
                    else:
                        # Seat is within range [release_pos, press_pos] - use calculated progress
                        # Clip raw_progress to ensure it never exceeds 1.0 (safety check)
                        current_progress = min(raw_progress, 1.0)
                else:
                    current_progress = 0.0
            else:
                current_progress = 0.0
        else:
            # Fallback to 0-100 scale
            # Map [back_max_pos, front_max_pos] to [0, 1]
            # Where 0 = back (release) and 100 = front (press)
            if self.shared_state.converted_seat_position:
                raw_progress = self.shared_state.converted_seat_position[-1] / 100.0
                # Clip to [0, 1] range - if value exceeds 1.0, clip to 1.0
                current_progress = min(max(raw_progress, 0.0), 1.0)
            else:
                current_progress = 0.0
        
        # Final safety check: ensure current_progress never exceeds 1.0
        # This ensures the moving bar never extends beyond the grey bar
        if current_progress > 1.0:
            current_progress = 1.0
        
        # Determine direction and color based on position relative to release/press
        # When outside range, use appropriate color to indicate target direction
        if hasattr(self.shared_state, 'seat_position_release') and hasattr(self.shared_state, 'seat_position_press'):
            if self.shared_state.seat_position_mm:
                current_pos_mm = self.shared_state.seat_position_mm[-1]
                release_pos = self.shared_state.seat_position_release
                press_pos = self.shared_state.seat_position_press
                
                if current_pos_mm < release_pos:
                    # Before release position: moving towards press, use release color (orange)
                    progress_color = wx.Colour(255, 152, 0)  # Orange (release)
                    self.last_progress_color = progress_color
                elif current_pos_mm > press_pos:
                    # After press position: moving towards release, use press color (green)
                    progress_color = wx.Colour(76, 175, 80)  # Green (press)
                    self.last_progress_color = progress_color
                else:
                    # Within range: determine direction from movement
                    if len(self.shared_state.converted_seat_position) >= 2:
                        current_pos = self.shared_state.converted_seat_position[-1]
                        prev_pos = self.shared_state.converted_seat_position[-2]
                        moving_right = current_pos > prev_pos  # Moving towards push (right)
                        moving_left = current_pos < prev_pos   # Moving towards release (left)
                    else:
                        moving_right = False
                        moving_left = False
                    
                    # Color logic: Green when moving left, Orange when moving right
                    # Keep previous color when stationary
                    if moving_left:
                        progress_color = wx.Colour(76, 175, 80)  # Green
                        self.last_progress_color = progress_color
                    elif moving_right:
                        progress_color = wx.Colour(255, 152, 0)  # Orange
                        self.last_progress_color = progress_color
                    else:
                        # Use last color when stationary
                        progress_color = self.last_progress_color
            else:
                # No position data, use last color or default grey
                progress_color = self.last_progress_color
        else:
            # Fallback: determine direction from converted position
            if len(self.shared_state.converted_seat_position) >= 2:
                current_pos = self.shared_state.converted_seat_position[-1]
                prev_pos = self.shared_state.converted_seat_position[-2]
                moving_right = current_pos > prev_pos
                moving_left = current_pos < prev_pos
            else:
                moving_right = False
                moving_left = False
            
            if moving_left:
                progress_color = wx.Colour(76, 175, 80)  # Green
                self.last_progress_color = progress_color
            elif moving_right:
                progress_color = wx.Colour(255, 152, 0)  # Orange
                self.last_progress_color = progress_color
            else:
                progress_color = self.last_progress_color
        
        # Draw progress fill only in the middle section (not covering RELEASE/PRESS labels)
        # Map progress [0, 1] to bar_width (base width), so grey bar can extend beyond
        progress_width = int(bar_width * current_progress)
        if progress_width > 0:
            dc.SetBrush(wx.Brush(progress_color))
            # Start from the left edge of middle section (after RELEASE bar)
            progress_start_x = main_bar_x
            dc.DrawRoundedRectangle(progress_start_x, bar_y, progress_width, bar_height, 25)
        
        # Add labels for the end bars
        dc.SetTextForeground(wx.Colour(255, 255, 255))  # White text
        dc.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # Determine label text based on mode
        if hasattr(self.shared_state, 'is_automatic_mode') and self.shared_state.is_automatic_mode:
            left_label = "Hamstrings"
            right_label = "Quads"
        else:
            left_label = "RELEASE"
            right_label = "PRESS"
        
        # Release/Activate label (horizontal, centered in left bar)
        release_text_width, release_text_height = dc.GetTextExtent(left_label)
        release_x = release_bar_x + (release_bar_width - release_text_width) // 2  # Centered in wider bar
        release_y = bar_y + (bar_height - release_text_height) // 2
        dc.DrawText(left_label, release_x, release_y)
        
        # Press/Activate label (horizontal, centered in right bar)
        # Move text slightly to the left to avoid overlap with extended grey bar
        press_text_width, press_text_height = dc.GetTextExtent(right_label)
        press_x = press_bar_x + (press_bar_width - press_text_width) // 2
        press_y = bar_y + (bar_height - press_text_height) // 2
        dc.DrawText(right_label, press_x, press_y)

    def update_indicator(self):
        # Update title based on mode
        if hasattr(self.shared_state, 'is_automatic_mode') and self.shared_state.is_automatic_mode:
            self.title_label.SetLabel("FES Stimulation")
        else:
            self.title_label.SetLabel("Button Press Indicator")
        self.Refresh()

    def reset(self):
        self.shared_state.is_pressed = False
        self.shared_state.loading_phase = 0
        self.last_progress_color = wx.Colour(158, 158, 158)  # Reset to grey
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