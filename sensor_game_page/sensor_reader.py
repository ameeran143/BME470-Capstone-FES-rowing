#!/usr/bin/env python3
"""
Sensor Reader Module for Real-Time Hardware Data Collection
Reads sensor data directly from NI-DAQ hardware and provides it to the game

SENSOR CHANNEL MAPPING (NI-DAQ Dev2):
======================================
ai16: Left Foot Force Sensor
ai18: Right Foot Force Sensor
ai20: Handle Force Sensor
ai21: Front Potentiometer → Handle Position
ai22: Back Potentiometer → Seat Position (converted: voltage × 100)
"""

import nidaqmx
import time
import platform


class SensorReader:
    def __init__(self):
        """Initialize hardware sensor reader"""
        self.device_name = "Dev2"
        self.is_connected = False
        self.last_error = None
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        
        # Calibration values for seat position (will be auto-calibrated)
        # Based on typical ranges from data analysis
        self.seat_min = 17.0  # Back position (0%)
        self.seat_max = 58.0  # Front position (100%)
        
        # Check if we're on a supported platform
        self.is_mac = platform.system() == 'Darwin'
        
        if self.is_mac:
            print("⚠️  macOS detected: NI-DAQmx not supported on macOS")
            print("   Please use Windows or Linux for hardware testing")
            self.is_connected = False
        else:
            # Test connection on initialization
            self._test_connection()
    
    def _test_connection(self):
        """Test if NI-DAQ device is connected and accessible"""
        if self.is_mac:
            return False
            
        try:
            with nidaqmx.Task() as task:
                # Test with all 5 channels - using optimized voltage ranges for better ADC resolution
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai16", min_val=7.0, max_val=9.5)   # Left Foot Force
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai18", min_val=7.0, max_val=9.0)   # Right Foot Force
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai20", min_val=8.5, max_val=10.5)  # Handle Force
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai21", min_val=8.5, max_val=11.0)  # Handle Position
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai22", min_val=-10.0, max_val=10.0)  # Seat Position
                # Try reading one sample to verify connection
                task.read(number_of_samples_per_channel=1)
                
            self.is_connected = True
            self.last_error = None
            self.connection_attempts = 0
            print(f"✅ NI-DAQ device '{self.device_name}' connected and ready")
            return True
            
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            self.connection_attempts += 1
            if self.connection_attempts == 1:
                print(f"❌ Hardware connection failed: {e}")
                print("💡 Troubleshooting tips:")
                print("  - Check NI-DAQ device is connected via USB/Ethernet")
                print(f"  - Verify device name is '{self.device_name}' in NI MAX")
                print("  - Install/update NI-DAQmx drivers")
                print("  - Try running as administrator")
            return False
    
    def start(self):
        """Start sensor reading (hardware is always on, this just verifies connection)"""
        if self.is_mac:
            print("⚠️  Cannot start hardware reading on macOS")
            return False
        
        if not self.is_connected:
            success = self._test_connection()
            if success:
                print("▶️  Sensor reading started")
            return success
        else:
            print("▶️  Sensor reading active")
            return True
    
    def get_current_data(self):
        """
        Read current sensor data from hardware
        Returns data in same format as DataPlayback.get_current_data():
        {
            'left_foot': float,
            'right_foot': float,
            'handle_force': float,
            'handle_position': float,
            'seat_position': float,
            'timestamp': float,
            'index': int,
            'total_samples': int (always 0 for live data)
        }
        """
        if not self.is_connected:
            # Try to reconnect if we've had errors
            if self.connection_attempts < self.max_connection_attempts:
                self._test_connection()
            if not self.is_connected:
                return None
        
        try:
            with nidaqmx.Task() as task:
                # Add channels individually with optimized voltage ranges for better ADC resolution
                # Ranges based on actual sensor output measurements (with safety margin)
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai16", min_val=7.0, max_val=9.5)   # Left Foot Force
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai18", min_val=7.0, max_val=9.0)   # Right Foot Force
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai20", min_val=8.5, max_val=10.5)  # Handle Force
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai21", min_val=8.5, max_val=11.0)  # Handle Position
                task.ai_channels.add_ai_voltage_chan(f"{self.device_name}/ai22", min_val=-10.0, max_val=10.0)  # Seat Position
                
                # Read one sample per channel
                data = task.read(number_of_samples_per_channel=1)
                
                # Extract single values from nested list structure
                left_foot_voltage = data[0][0] if isinstance(data[0], list) else data[0]
                right_foot_voltage = data[1][0] if isinstance(data[1], list) else data[1]
                handle_force_voltage = data[2][0] if isinstance(data[2], list) else data[2]
                handle_position_voltage = data[3][0] if isinstance(data[3], list) else data[3]
                seat_position_voltage = data[4][0] if isinstance(data[4], list) else data[4]
                
                # Convert voltages to values compatible with game expectations
                # Seat position: Back Pot (ai22) - multiply by 100 to match expected range
                # This matches the format from hardware_test.py and game_page.py
                seat_position_scaled = seat_position_voltage * 100
                
                # Return data in same format as DataPlayback
                # Note: These are voltage values, the game will apply further scaling
                mapped_data = {
                    'left_foot': left_foot_voltage * 100,      # Scale to match ADC-like values
                    'right_foot': right_foot_voltage * 1000,    # Different scaling for right foot
                    'handle_force': handle_force_voltage * 100, # Scale to match ADC-like values
                    'handle_position': handle_position_voltage * 1000, # Scale to match ADC-like values
                    'seat_position': seat_position_scaled,      # Already scaled (voltage * 100)
                    'timestamp': time.time(),
                    'index': 0,  # Not applicable for live data
                    'total_samples': 0  # Not applicable for live data
                }
                
                return mapped_data
                
        except Exception as e:
            self.last_error = str(e)
            self.is_connected = False
            print(f"❌ Sensor reading error: {e}")
            print("   Attempting to reconnect on next read...")
            return None
    
    def get_progress(self):
        """Get reading progress (not applicable for live data)"""
        return 0.0, 0.0, 0.0  # No progress for live data
    
    def pause(self):
        """Pause reading (not applicable for live hardware)"""
        print("⏸️  Live sensor reading cannot be paused")
    
    def resume(self):
        """Resume reading (not applicable for live hardware)"""
        print("▶️  Live sensor reading is always active")
    
    def reset(self):
        """Reset reader (not applicable for live hardware)"""
        print("⏮️  Live sensor reading cannot be reset")
        # Re-test connection
        self._test_connection()

