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
from button import CustomButton
import nidaqmx
# import pygame
import csv
import math
from PIL import Image, ImageDraw
from scipy import signal

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
        
        # Try auto-load CSV data on macOS if file exists
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))
            csv_path = os.path.join(project_root, "Test_Recordings", "hikaru", "sensor_data.csv")
            if os.path.exists(csv_path):
                self.load_sensor_csv(csv_path)
                # Enable playback mode by default on mac if hardware is disabled
                if self.is_mac:
                    self.anc_playback_mode = True
        except Exception as e:
            print(f"CSV init load failed: {e}")
    
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
            writer.writerow(["Time Elapsed (min)", "Stroke Rate", "Average Power", "Score", "Misses", "Handle Force (ai20)", "Handle Position (ai21)", "Raw Seat Position (ai22)", "Converted Seat Position", "Left Foot Force (ai16)", "Right Foot Force (ai18)"])

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

            if self.anc_data:
                self._process_seat_position()
                self.plot_anc_data(file_path)
                print(f"Loaded CSV playback samples: {len(self.anc_data)} from {file_path}")
                print(f"Estimated sampling rate: {self.anc_sampling_rate:.2f} Hz; playback step: {self.anc_index_step}")
        except Exception as e:
            print(f"Failed to load sensor CSV: {e}")

    def _process_seat_position(self):
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
            
            # Calculate 10th and 90th percentiles for color threshold
            import numpy as np
            seat_array = np.array(remapped_seat)
            self.seat_position_p10 = np.percentile(seat_array, 15)  #the optimal timing for anterior position is not defined yet, so set to 15th percentile for now 
            self.seat_position_p90 = max(seat_array) - 140  #set it to 140 mm seat position from the front, max(seat_array) would be based on the calibrated values in practice
            
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
            print(f"Applied {cutoff:.1f} Hz Butterworth filter and remapped seat position:")
            print(f"  Force input range: {min_force_raw:.2f}-{max_force_raw:.2f} {force_units}")
            print(f"  Force output range: {min(remapped_force):.2f}-{max(remapped_force):.2f} {force_units} (offset)")
            print(f"  Seat input range: {min_seat_raw:.2f}-{max_seat_raw:.2f} {source_units}")
            print(f"  Seat output range: {min(remapped_seat):.2f}-{max(remapped_seat):.2f} mm")
            print(f"  Handle input range: {min_handle_raw:.2f}-{max_handle_raw:.2f} {source_units}")
            print(f"  Handle output range: {min(remapped_handle):.2f}-{max(remapped_handle):.2f} mm")
            if self.anc_source_type == "csv_voltage":
                print(f"  Force final range (shifted): 0-{max(remapped_force):.2f} {force_units}")
                print(f"  Seat final range (shifted): 0-{max(remapped_seat):.2f} mm")
                print(f"  Handle final range (shifted): 0-{max(remapped_handle):.2f} mm")
            print(f"  10th percentile: {self.seat_position_p10:.2f} mm")
            print(f"  90th percentile: {self.seat_position_p90:.2f} mm")
            
        except Exception as e:
            print(f"Failed to process seat position: {e}")

    @staticmethod
    def _convert_handle_force_voltage(voltage):
        """Convert handle force sensor voltage to force (N) using calibration."""

        #this conversoin is done by the following equation
        #recorded voltage / (sensitivity*excitation voltage ) * rated capacity mass (kg) * gravity (m/s^2)
        #note that sensitivity is 2.0 mv/V and excitation voltage is 5.0 V, rated capacity mass is 250 kg and gravity is 9.81 m/s^2
        try:
            return (voltage / (2.0 * 5.0)) * 250.0 * 9.81
        except Exception:
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
            print(f"Saved CSV plot to: {out_path}")
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
        self.time_elapsed = int(time.time() - self.time_start) / 60

        # CSV playback mode (replay from CSV file)
        if self.anc_playback_mode and self.anc_data:
            try:
                # Initialize playback start time
                if self.anc_playback_start_time is None:
                    self.anc_playback_start_time = time.time()
                
                # Downsample: skip samples to simulate real-time playback
                if self.anc_index >= len(self.anc_data):
                    # End of data, disable playback
                    self.anc_playback_mode = False
                    return
                
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
                if self.raw_seat_pos:
                    if self.raw_seat_pos[-1] <= self.back_max_pos:
                        self.raw_seat_pos[-1] = self.back_max_pos
                    elif self.raw_seat_pos[-1] >= self.front_max_pos:
                        self.raw_seat_pos[-1] = self.front_max_pos
                    self.converted_seat_position.append(self.convert_raw_to_scale(self.raw_seat_pos[-1]))
                
                if self.anc_power_series and current_idx < len(self.anc_power_series):
                    power_val = self.anc_power_series[current_idx]
                    self.temp_power.append(power_val)
                    self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                elif len(self.handle_force) > 1 and len(self.handle_position) > 1 and len(self.temp_time) > 1:
                    self.temp_power.append(((self.handle_force[-1]+self.handle_force[-2])/2)*abs(self.handle_position[-1]-self.handle_position[-2])/(self.temp_time[-1]-self.temp_time[-2]))
                    self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                self.hardware_connected = False
                return
            except Exception as e:
                print(f"CSV playback error: {e}")
                # Fallback to simulation
                self.anc_playback_mode = False

        # Hardware sensor data collection (Windows/Linux only)
        if not self.is_mac and self.hardware_mode:
            try:
                with nidaqmx.Task() as task:
                    # Add channels individually with explicit voltage range
                    task.ai_channels.add_ai_voltage_chan("Dev2/ai16", min_val=-10.0, max_val=10.0)  # Left foot
                    task.ai_channels.add_ai_voltage_chan("Dev2/ai18", min_val=-10.0, max_val=10.0)  # Right foot
                    task.ai_channels.add_ai_voltage_chan("Dev2/ai20", min_val=-10.0, max_val=10.0)  # Handle force
                    task.ai_channels.add_ai_voltage_chan("Dev2/ai21", min_val=-10.0, max_val=10.0)  # Handle position
                    task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=-10.0, max_val=10.0)  # Seat position
                    data = task.read(number_of_samples_per_channel=1)
                    
                    # Extract single values from nested list structure
                    left_foot = data[0][0] if isinstance(data[0], list) else data[0]
                    right_foot = data[1][0] if isinstance(data[1], list) else data[1]
                    handle_force = data[2][0] if isinstance(data[2], list) else data[2]
                    handle_position = data[3][0] if isinstance(data[3], list) else data[3]
                    seat_position = data[4][0] if isinstance(data[4], list) else data[4]
                    
                    self.pos = seat_position * 100  # Back potentiometer (ai22) - seat position
                    
                    self.raw_seat_pos.append(self.pos)  # Back potentiometer (ai22)
                    self.handle_position.append(handle_position)  # Front potentiometer (ai21)
                    self.handle_force.append(self._convert_handle_force_voltage(handle_force))  # Handle force sensor (ai20)
                    self.L_foot_force.append(left_foot)  # Left foot force (ai16)
                    self.R_foot_force.append(right_foot)  # Right foot force (ai18)
                    # Note: switch_press removed - no switch sensor in new mapping
                    self.temp_time.append(time.time())
                    self.hardware_connected = True

                # update power (need to verify)
                if len(self.raw_seat_pos) > 1 and hasattr(self, 'temp_time'):
                    self.temp_power.append(((self.handle_force[-1]+self.handle_force[-2])/2)*abs(self.handle_position[-1]-self.handle_position[-2])/(self.temp_time[-1]-self.temp_time[-2]))
                    self.avg_power.append(sum(self.temp_power)/len(self.temp_power))
                    
                return  # Exit early if hardware read was successful
            except Exception as e:
                print(f"Hardware error: {e}")
                self.hardware_connected = False
                # Fall through to simulation mode
        
        # Simulation mode (always used on macOS, fallback for Windows/Linux, unless CSV playback)
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
    
    def load_cloud_sprite(self):
        """Load cloud sprite from PNG file"""
        try:
            # Get the path to the cloud.png file (in parent directory)
            script_dir = os.path.dirname(os.path.dirname(__file__))
            cloud_path = os.path.join(script_dir, "cloud.png")
            
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
        outer_sizer.Add(self.stats_panel, 2, wx.EXPAND | wx.ALL, 20)

        # initialize location and progress display panel - new section
        self.location_progress_panel = LocationProgressPanel(self, self.shared_state)
        outer_sizer.Add(self.location_progress_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)

        # initialize gamified rowing scene - middle section
        self.rowing_scene_panel = RowingScenePanel(self, self.shared_state)
        outer_sizer.Add(self.rowing_scene_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 20)

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
        
        # Only simulate data if hardware is not connected and not in CSV playback mode
        if not self.shared_state.hardware_connected and not getattr(self.shared_state, 'anc_playback_mode', False):
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
            
            # Generate realistic fake power data (only in simulation mode)
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
        
        # Calculate realistic distance (for both hardware and simulation mode)
        self.shared_state.calculate_distance()
        
        self.stats_panel.update_stats()
        self.location_progress_panel.update_display()
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

class LocationProgressPanel(wx.Panel):
    """Panel to display current location and progress to next milestone"""
    def __init__(self, parent, shared_state):
        super(LocationProgressPanel, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.shared_state = shared_state
        self.SetMinSize((-1, 130))
        
        # Location milestones (distance in meters to reach each location)
        self.location_milestones = [
            ("Hawaii", 0),
            ("Fiji", 500),
            ("Tahiti", 1000),
            ("Bora Bora", 1500),
            ("Maldives", 2000),
        ]
        
        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSpacer(20)
        
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
        main_sizer.AddSpacer(15)
        
        # Progress section - horizontal layout
        progress_container = wx.BoxSizer(wx.HORIZONTAL)
        progress_container.AddSpacer(100)  # Left padding
        
        # Progress bar with percentage label
        progress_bar_container = wx.BoxSizer(wx.VERTICAL)
        
        # Percentage indicator (small, above progress bar)
        self.percentage_label = wx.StaticText(self, label="2%")
        self.percentage_label.SetForegroundColour(wx.Colour(150, 150, 150))
        self.percentage_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        progress_bar_container.Add(self.percentage_label, 0, wx.ALIGN_LEFT)
        progress_bar_container.AddSpacer(3)
        
        # Progress bar (custom drawn)
        self.progress_bar_panel = wx.Panel(self, size=(-1, 20))
        self.progress_bar_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.progress_bar_panel.Bind(wx.EVT_PAINT, self.OnPaintProgressBar)
        progress_bar_container.Add(self.progress_bar_panel, 1, wx.EXPAND)
        
        progress_container.Add(progress_bar_container, 1, wx.EXPAND)
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
        
        progress_container.Add(next_location_container, 0, wx.ALIGN_CENTER_VERTICAL)
        progress_container.AddSpacer(100)  # Right padding
        
        main_sizer.Add(progress_container, 0, wx.EXPAND)
        main_sizer.AddSpacer(20)
        
        self.SetSizer(main_sizer)
        
        # Store current progress for drawing
        self.current_progress = 0.0
    
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
        """Update location and progress display"""
        current_distance = self.shared_state.total_distance
        
        # Find current and next location
        current_location_name = "Hawaii"
        next_location_name = None
        progress_to_next = 0.0
        
        for i, (location_name, milestone_distance) in enumerate(self.location_milestones):
            if current_distance >= milestone_distance:
                current_location_name = location_name
                # Check if there's a next location
                if i + 1 < len(self.location_milestones):
                    next_location_name, next_milestone = self.location_milestones[i + 1]
                    # Calculate progress to next location
                    distance_between = next_milestone - milestone_distance
                    distance_covered = current_distance - milestone_distance
                    progress_to_next = min(1.0, distance_covered / distance_between) if distance_between > 0 else 0.0
        
        # Update location label
        self.location_label.SetLabel(current_location_name)
        
        # Update progress
        self.current_progress = progress_to_next
        
        # Update percentage label
        self.percentage_label.SetLabel(f"{int(progress_to_next * 100)}%")
        
        # Update next location display
        if next_location_name:
            self.next_location_label.SetLabel(next_location_name)
        else:
            self.next_location_label.SetLabel("Finish!")
        
        # Refresh progress bar
        self.progress_bar_panel.Refresh()
        self.Layout()

# ------------------------------------------------------------------------------------------------------------

class RowingScenePanel(wx.Panel):
    def __init__(self, parent, shared_state):
        super(RowingScenePanel, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(135, 206, 250))  # Sky blue background
        self.shared_state = shared_state
        self.SetMinSize((-1, 200))
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
        
        # Location milestones (distance in meters to reach each location)
        self.location_milestones = [
            ("Hawaii", 0),
            ("Fiji", 500),
            ("Tahiti", 1000),
            ("Bora Bora", 1500),
            ("Maldives", 2000),
        ]
        
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
            }
        }

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
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
        """Draw clouds in the sky (for palm tree locations)"""
        if theme["features"] == "palms":
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
        
        # Update location based on distance (for map theme changes)
        current_distance = self.shared_state.total_distance
        for location_name, milestone_distance in self.location_milestones:
            if current_distance >= milestone_distance:
                self.current_location = location_name
        
        self.Refresh()

    def reset(self):
        """Reset the scene"""
        self.background_offset = 0.0  # Reset background scroll
        self.cumulative_distance = 0.0  # Reset distance
        self.current_location = "Hawaii"  # Reset to starting location
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
        # Use ANC percentiles if available, otherwise use 0-100 scale
        if hasattr(self.shared_state, 'seat_position_p10') and hasattr(self.shared_state, 'seat_position_p90'):
            # Use ANC-based percentiles with mm position
            if self.shared_state.seat_position_mm:
                current_pos_mm = self.shared_state.seat_position_mm[-1]  # position in mm
                p10 = self.shared_state.seat_position_p10
                p90 = self.shared_state.seat_position_p90
                
                # Map position to 0-1 scale based on percentiles
                if p90 > p10:
                    # Map [p10, p90] to [0, 1]
                    current_progress = (current_pos_mm - p10) / (p90 - p10)
                    current_progress = max(0.0, min(1.0, current_progress))  # Clamp to [0, 1]
                else:
                    current_progress = 0.0
            else:
                current_progress = 0.0
        else:
            # Fallback to 0-100 scale
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