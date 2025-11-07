#!/usr/bin/env python3
"""
Sensor Data Recording Utility
Standalone script to record sensor data from NI-DAQ hardware and generate plots.

Usage:
    python sensor_recorder.py
"""

import wx
import sys
import os
import time
import csv
import threading
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from sensor_reader import SensorReader


class SensorRecorder:
    """Handles recording sensor data"""
    def __init__(self, sensor_reader):
        self.sensor_reader = sensor_reader
        self.is_recording = False
        self.recording_thread = None
        self.data_buffer = []
        self.timestamps = []
        self.start_time = None
        self.recording_folder = None
        
        # Persistent DAQ task (created once and reused, like Cortex)
        self.daq_task = None
        
        # Channel names for 5 sensors
        self.channel_names = [
            'Left Foot Force (ai16)',
            'Right Foot Force (ai18)',
            'Handle Force (ai20)',
            'Handle Position (ai21)',
            'Seat Position (ai22)'
        ]
    
    def start_recording(self):
        """Start recording sensor data"""
        if self.is_recording:
            return False
        
        # Create recording folder with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording_folder = os.path.join(os.path.dirname(__file__), "Recordings", f"recording_{timestamp}")
        os.makedirs(self.recording_folder, exist_ok=True)
        
        self.is_recording = True
        self.data_buffer = []
        self.timestamps = []
        self.start_time = time.time()
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
        self.recording_thread.start()
        
        return True
    
    def stop_recording(self):
        """Stop recording and save data"""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        
        # Save data to CSV
        csv_file = self._save_to_csv()
        
        # Generate plots
        self._generate_plots()
        
        # Clean up DAQ task after recording
        self._cleanup_daq_task()
        
        return self.recording_folder
    
    def _init_daq_task(self):
        """Initialize persistent DAQ task (created once and reused, like Cortex)"""
        import nidaqmx
        if self.daq_task is None:
            self.daq_task = nidaqmx.Task()
            # Configure channels with explicit terminal configuration (RSE - Referenced Single-Ended)
            # This matches typical Cortex configuration for single-ended sensors
            # RSE uses AI GND as reference, which is standard for potentiometers and load cells
            self.daq_task.ai_channels.add_ai_voltage_chan("Dev2/ai16", 
                                                          terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                          min_val=0.0, max_val=10.0)   # Left Foot Force
            self.daq_task.ai_channels.add_ai_voltage_chan("Dev2/ai18",
                                                          terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                          min_val=0.0, max_val=10.0)   # Right Foot Force
            self.daq_task.ai_channels.add_ai_voltage_chan("Dev2/ai20",
                                                          terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                          min_val=0.0, max_val=10.0)   # Handle Force
            self.daq_task.ai_channels.add_ai_voltage_chan("Dev2/ai21",
                                                          terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                          min_val=0.0, max_val=10.0)   # Handle Position
            self.daq_task.ai_channels.add_ai_voltage_chan("Dev2/ai22",
                                                          terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                                          min_val=0.0, max_val=10.0)   # Seat Position (0-10V as in Cortex)
    
    def _cleanup_daq_task(self):
        """Clean up DAQ task"""
        if self.daq_task is not None:
            try:
                self.daq_task.close()
            except:
                pass
            self.daq_task = None
    
    def _read_sensor_data(self):
        """Read sensor data from Dev2 hardware - returns raw voltage values"""
        import nidaqmx
        try:
            # Initialize task if not already created
            self._init_daq_task()
            
            # Read data using the persistent task (exactly like hardware_test.py)
            data = self.daq_task.read(number_of_samples_per_channel=1)
            
            # Extract single values from the nested list structure (exactly like hardware_test.py)
            left_foot_voltage = data[0][0] if isinstance(data[0], list) else data[0]
            right_foot_voltage = data[1][0] if isinstance(data[1], list) else data[1]
            handle_force_voltage = data[2][0] if isinstance(data[2], list) else data[2]
            handle_position_voltage = data[3][0] if isinstance(data[3], list) else data[3]
            seat_position_voltage = data[4][0] if isinstance(data[4], list) else data[4]
            
            return {
                'left_foot': left_foot_voltage,
                'right_foot': right_foot_voltage,
                'handle_force': handle_force_voltage,
                'handle_position': handle_position_voltage,
                'seat_position': seat_position_voltage
            }
        except Exception as e:
            raise Exception(f"Error reading from Dev2: {e}")
    
    def test_sensors(self, num_samples=5):
        """Test sensor reading - reads multiple samples and displays them"""
        print("\n" + "=" * 70)
        print("🔍 TESTING SENSOR DATA READING FROM Dev2")
        print("=" * 70)
        
        results = []
        errors = []
        
        try:
            for i in range(num_samples):
                try:
                    data = self._read_sensor_data()
                    results.append(data)
                    print(f"\nSample {i+1}/{num_samples}:")
                    print(f"  Left Foot Force (ai16):    {data['left_foot']:8.4f} V")
                    print(f"  Right Foot Force (ai18):   {data['right_foot']:8.4f} V")
                    print(f"  Handle Force (ai20):       {data['handle_force']:8.4f} V")
                    print(f"  Handle Position (ai21):    {data['handle_position']:8.4f} V")
                    print(f"  Seat Position (ai22):      {data['seat_position']:8.4f} V")
                    time.sleep(0.1)  # Small delay between samples
                except Exception as e:
                    errors.append(str(e))
                    print(f"\n❌ Sample {i+1}/{num_samples} failed: {e}")
        finally:
            # Clean up DAQ task after testing
            self._cleanup_daq_task()
        
        if results:
            print("\n" + "-" * 70)
            print("📊 SUMMARY STATISTICS:")
            print("-" * 70)
            
            # Calculate statistics
            for channel_name, key in zip(self.channel_names, 
                                        ['left_foot', 'right_foot', 'handle_force', 'handle_position', 'seat_position']):
                values = [r[key] for r in results]
                print(f"\n{channel_name}:")
                print(f"  Mean:   {np.mean(values):8.4f} V")
                print(f"  Std:    {np.std(values):8.4f} V")
                print(f"  Min:    {np.min(values):8.4f} V")
                print(f"  Max:    {np.max(values):8.4f} V")
                print(f"  Range:  {np.max(values) - np.min(values):8.4f} V")
            
            print("\n✅ Sensor reading test PASSED - Dev2 is responding correctly!")
            print("=" * 70 + "\n")
            return True
        else:
            print("\n❌ Sensor reading test FAILED - Could not read any data from Dev2")
            if errors:
                print("Errors encountered:")
                for error in errors:
                    print(f"  - {error}")
            print("=" * 70 + "\n")
            return False
    
    def _recording_loop(self):
        """Main recording loop - runs in separate thread"""
        # Target: 2000 Hz (0.0005 seconds between samples)
        target_interval = 1.0 / 2000.0
        
        while self.is_recording:
            loop_start = time.time()
            
            # Read sensor data directly from hardware (raw voltage values)
            try:
                data = self._read_sensor_data()
                
                # Record raw voltage values
                timestamp = time.time() - self.start_time  # Relative time in seconds
                self.timestamps.append(timestamp)
                self.data_buffer.append([
                    data['left_foot'],
                    data['right_foot'],
                    data['handle_force'],
                    data['handle_position'],
                    data['seat_position']
                ])
            except Exception as e:
                print(f"Warning: Error reading sensor data: {e}")
            
            # Maintain 2000 Hz sampling rate
            elapsed = time.time() - loop_start
            sleep_time = max(0, target_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _save_to_csv(self):
        """Save recorded data to CSV file"""
        if not self.data_buffer:
            return None
        
        csv_filename = os.path.join(self.recording_folder, "sensor_data.csv")
        
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Time (s)'] + self.channel_names)
            
            # Write data
            for timestamp, data_row in zip(self.timestamps, self.data_buffer):
                writer.writerow([timestamp] + data_row)
        
        print(f"✅ Saved {len(self.data_buffer)} samples to {csv_filename}")
        return csv_filename
    
    def _generate_plots(self):
        """Generate plots similar to rowing_data_overview.png"""
        if not self.data_buffer:
            print("⚠️  No data to plot")
            return
        
        print("\n📊 Generating plots...")
        
        # Convert to numpy arrays
        timestamps = np.array(self.timestamps)
        data = np.array(self.data_buffer)
        
        # Create overview plot
        n_channels = len(self.channel_names)
        fig, axes = plt.subplots(n_channels, 1, figsize=(15, 2.5*n_channels))
        fig.suptitle('Full Recording - All Sensor Channels', fontsize=14, fontweight='bold')
        
        colors = plt.cm.tab10(np.linspace(0, 1, n_channels))
        
        for i, (ax, channel, color) in enumerate(zip(axes, self.channel_names, colors)):
            ax.plot(timestamps, data[:, i], linewidth=0.5, color=color, alpha=0.8)
            ax.set_ylabel(f'{channel}\n(Voltage)', fontsize=10)
            ax.grid(True, alpha=0.3)
            
            if len(timestamps) > 0:
                ax.set_xlim(timestamps[0], timestamps[-1])
            
            # Add stats
            mean_val = np.mean(data[:, i])
            std_val = np.std(data[:, i])
            min_val = np.min(data[:, i])
            max_val = np.max(data[:, i])
            ax.text(0.02, 0.95, f'μ={mean_val:.3f}V, σ={std_val:.3f}V\nmin={min_val:.3f}V, max={max_val:.3f}V',
                    transform=ax.transAxes, fontsize=8, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        axes[-1].set_xlabel('Time (seconds)', fontsize=11)
        plt.tight_layout()
        
        plot_filename = os.path.join(self.recording_folder, "sensor_data_overview.png")
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved plot to {plot_filename}")
        
        # Generate summary info
        self._generate_summary(timestamps, data)
    
    def _generate_summary(self, timestamps, data):
        """Generate a text summary of the recording"""
        summary_filename = os.path.join(self.recording_folder, "recording_summary.txt")
        
        with open(summary_filename, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("Sensor Data Recording Summary\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Recording Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {timestamps[-1]:.2f} seconds\n")
            f.write(f"Total Samples: {len(data)}\n")
            f.write(f"Average Sample Rate: {len(data) / timestamps[-1]:.1f} Hz\n")
            f.write(f"Expected Sample Rate: 2000 Hz\n\n")
            
            f.write("Channel Statistics:\n")
            f.write("-" * 70 + "\n")
            for i, channel in enumerate(self.channel_names):
                channel_data = data[:, i]
                f.write(f"{channel}:\n")
                f.write(f"  Mean: {np.mean(channel_data):.3f}V\n")
                f.write(f"  Std:  {np.std(channel_data):.3f}V\n")
                f.write(f"  Min:  {np.min(channel_data):.3f}V\n")
                f.write(f"  Max:  {np.max(channel_data):.3f}V\n")
                f.write(f"  Range: {np.max(channel_data) - np.min(channel_data):.3f}V\n\n")
        
        print(f"✅ Saved summary to {summary_filename}")


class RecordingControlPanel(wx.Frame):
    """GUI control panel for sensor recording"""
    def __init__(self):
        super(RecordingControlPanel, self).__init__(None, title="Sensor Data Recorder", size=(550, 350))
        self.Centre()
        
        print("=" * 60)
        print("📹 SENSOR DATA RECORDER")
        print("=" * 60)
        
        # Initialize sensor reader
        try:
            self.sensor_reader = SensorReader()
            
            if not self.sensor_reader.start():
                error_msg = (
                    "Failed to connect to NI-DAQ hardware.\n\n"
                    "Troubleshooting:\n"
                    "• Check NI-DAQ device is connected\n"
                    "• Verify device name is 'Dev2' in NI MAX\n"
                    "• Install/update NI-DAQmx drivers\n"
                    "• Try running as administrator\n"
                    "• Ensure you're on Windows or Linux (macOS not supported)\n\n"
                )
                if self.sensor_reader.last_error:
                    error_msg += f"Error: {self.sensor_reader.last_error}"
                
                wx.MessageBox(error_msg, "Hardware Connection Error", wx.OK | wx.ICON_ERROR)
                print("❌ Hardware connection failed - exiting")
                sys.exit(1)
            
            print("✅ Sensor reader initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize sensor reader: {e}")
            import traceback
            traceback.print_exc()
            wx.MessageBox(
                f"Failed to initialize sensor reader:\n{e}",
                "Initialization Error",
                wx.OK | wx.ICON_ERROR
            )
            sys.exit(1)
        
        # Initialize recorder
        self.recorder = SensorRecorder(self.sensor_reader)
        
        # Test sensors on startup
        print("\n🔍 Testing sensor connection to Dev2...")
        test_success = self.recorder.test_sensors(num_samples=3)
        
        # Create UI
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(panel, label="Sensor Data Recorder")
        title_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        # Status display
        self.status_label = wx.StaticText(panel, label="Status: Ready")
        status_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.status_label.SetFont(status_font)
        self.status_label.SetForegroundColour(wx.Colour(0, 128, 0))
        sizer.Add(self.status_label, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        # Recording info
        self.info_label = wx.StaticText(panel, label="Press Start to begin recording")
        self.info_label.SetForegroundColour(wx.Colour(100, 100, 100))
        sizer.Add(self.info_label, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        # Timer display
        self.timer_label = wx.StaticText(panel, label="")
        timer_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.timer_label.SetFont(timer_font)
        self.timer_label.SetForegroundColour(wx.Colour(200, 0, 0))
        sizer.Add(self.timer_label, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        sizer.AddStretchSpacer()
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.test_button = wx.Button(panel, label="Test Sensors", size=(130, 50))
        self.test_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.test_button.SetBackgroundColour(wx.Colour(33, 150, 243))
        self.test_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.test_button.Bind(wx.EVT_BUTTON, self.on_test)
        button_sizer.Add(self.test_button, 0, wx.ALL, 10)
        
        self.start_button = wx.Button(panel, label="Start Recording", size=(150, 50))
        self.start_button.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.start_button.SetBackgroundColour(wx.Colour(76, 175, 80))
        self.start_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start)
        button_sizer.Add(self.start_button, 0, wx.ALL, 10)
        
        self.stop_button = wx.Button(panel, label="Stop Recording", size=(150, 50))
        self.stop_button.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.stop_button.SetBackgroundColour(wx.Colour(244, 67, 54))
        self.stop_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop)
        self.stop_button.Disable()
        button_sizer.Add(self.stop_button, 0, wx.ALL, 10)
        
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        sizer.AddStretchSpacer()
        
        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Recording at 2000 Hz\nData will be saved automatically when stopped"
        )
        instructions.SetForegroundColour(wx.Colour(100, 100, 100))
        sizer.Add(instructions, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        
        # Timer for updating UI
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.recording_start_time = None
        
        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        print("\n▶️  Recording control panel ready")
        print("   Press Start to begin recording")
        print("   Press Stop to save data and generate plots\n")
    
    def on_test(self, event):
        """Test sensor reading"""
        self.test_button.Disable()
        self.status_label.SetLabel("Status: Testing Sensors...")
        self.status_label.SetForegroundColour(wx.Colour(33, 150, 243))
        self.info_label.SetLabel("Reading sensor data from Dev2...")
        wx.Yield()
        
        # Run test
        test_success = self.recorder.test_sensors(num_samples=5)
        
        if test_success:
            self.status_label.SetLabel("Status: Sensors OK")
            self.status_label.SetForegroundColour(wx.Colour(0, 128, 0))
            self.info_label.SetLabel("Dev2 is responding correctly - ready to record")
            wx.MessageBox(
                "Sensor test PASSED!\n\n"
                "All 5 channels on Dev2 are responding correctly.\n"
                "Check console for detailed sensor readings.",
                "Test Successful",
                wx.OK | wx.ICON_INFORMATION
            )
        else:
            self.status_label.SetLabel("Status: Test Failed")
            self.status_label.SetForegroundColour(wx.Colour(244, 67, 54))
            self.info_label.SetLabel("Could not read from Dev2 - check hardware connection")
            wx.MessageBox(
                "Sensor test FAILED!\n\n"
                "Could not read data from Dev2.\n"
                "Check console for error details.\n\n"
                "Troubleshooting:\n"
                "• Verify Dev2 is connected\n"
                "• Check NI-DAQmx drivers\n"
                "• Ensure device name is 'Dev2' in NI MAX",
                "Test Failed",
                wx.OK | wx.ICON_ERROR
            )
        
        self.test_button.Enable()
    
    def on_start(self, event):
        """Start recording"""
        if self.recorder.start_recording():
            self.status_label.SetLabel("Status: RECORDING")
            self.status_label.SetForegroundColour(wx.Colour(244, 67, 54))
            self.info_label.SetLabel(f"Recording to: {os.path.basename(self.recorder.recording_folder)}")
            self.start_button.Disable()
            self.stop_button.Enable()
            self.test_button.Disable()
            self.recording_start_time = time.time()
            self.timer.Start(100)  # Update every 100ms
            print("🔴 Recording started")
        else:
            wx.MessageBox("Already recording!", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_stop(self, event):
        """Stop recording"""
        self.timer.Stop()
        self.stop_button.Disable()
        self.status_label.SetLabel("Status: Saving...")
        self.status_label.SetForegroundColour(wx.Colour(255, 152, 0))
        self.timer_label.SetLabel("")
        wx.Yield()
        
        # Stop recording
        recording_folder = self.recorder.stop_recording()
        
        if recording_folder:
            self.status_label.SetLabel("Status: Complete")
            self.status_label.SetForegroundColour(wx.Colour(0, 128, 0))
            self.info_label.SetLabel(f"Saved to: {recording_folder}")
            self.start_button.Enable()
            self.test_button.Enable()
            
            wx.MessageBox(
                f"Recording complete!\n\n"
                f"Data saved to:\n{recording_folder}\n\n"
                f"Plots generated automatically.",
                "Recording Complete",
                wx.OK | wx.ICON_INFORMATION
            )
            print(f"✅ Recording saved to {recording_folder}")
        else:
            self.status_label.SetLabel("Status: Error")
            self.status_label.SetForegroundColour(wx.Colour(244, 67, 54))
            self.test_button.Enable()
            wx.MessageBox("Error saving recording", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_timer(self, event):
        """Update timer display"""
        if self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.timer_label.SetLabel(f"{minutes:02d}:{seconds:02d}")
    
    def on_close(self, event):
        """Handle window close"""
        if self.recorder.is_recording:
            response = wx.MessageBox(
                "Recording in progress. Stop recording before closing?",
                "Recording Active",
                wx.YES_NO | wx.ICON_WARNING
            )
            if response == wx.YES:
                self.on_stop(None)
            else:
                return  # Don't close
        
        # Clean up DAQ task before closing
        self.recorder._cleanup_daq_task()
        
        print("\n👋 Closing recorder...")
        self.Destroy()


def main():
    """Main entry point"""
    app = wx.App(False)
    
    try:
        frame = RecordingControlPanel()
        frame.Show()
        app.MainLoop()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

