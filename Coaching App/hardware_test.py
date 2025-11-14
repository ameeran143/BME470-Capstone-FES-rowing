#!/usr/bin/env python3
"""
Hardware Testing Utility for FES-Rowing Application
Run this script to test sensor connections before using the main application.

SENSOR CHANNEL MAPPING (NI-DAQ Dev1):
======================================
ai0-ai15: [UNUSED]
ai16: Left Foot Force Sensor
ai17: [UNUSED]
ai18: Right Foot Force Sensor
ai19: [UNUSED]
ai20: Handle Force Sensor
ai21: Front Potentiometer → Handle Position
ai22: Back Potentiometer → Seat Position (converted: voltage * 100)

"""

import nidaqmx
import time
import sys
import statistics
import csv
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Sensor channel mapping
SENSORS = {
    "1": {"name": "Left Foot Force Sensor", "channel": "Dev1/ai16"},
    "2": {"name": "Right Foot Force Sensor", "channel": "Dev1/ai18"},
    "3": {"name": "Handle Force Sensor", "channel": "Dev1/ai20"},
    "4": {"name": "Front Potentiometer (Handle Position)", "channel": "Dev1/ai21"},
    "5": {"name": "Back Potentiometer (Seat Position)", "channel": "Dev1/ai22"},
}

def test_hardware_connection():
    """Test if NI-DAQ device is connected and responsive"""
    try:
        with nidaqmx.Task() as task:
            # Test with the new channel mapping - add each channel individually
            task.ai_channels.add_ai_voltage_chan("Dev1/ai16")
            task.ai_channels.add_ai_voltage_chan("Dev1/ai18") 
            task.ai_channels.add_ai_voltage_chan("Dev1/ai20")
            task.ai_channels.add_ai_voltage_chan("Dev1/ai21")
            task.ai_channels.add_ai_voltage_chan("Dev1/ai22")
            print("✅ NI-DAQ device 'Dev1' found and accessible")
            return True
    except Exception as e:
        print(f"❌ Hardware connection failed: {e}")
        return False

def test_sensor_readings():
    """Read and display sensor values for verification"""
    print("\n🔍 Testing sensor readings...")
    print("Press Ctrl+C to stop\n")
    
    # Create output folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(os.path.dirname(__file__), "Test_Recordings", f"test_{timestamp}")
    os.makedirs(output_folder, exist_ok=True)
    csv_file = os.path.join(output_folder, "sensor_data.csv")
    
    print(f"📁 Recording data to: {output_folder}\n")
    
    # Data recording lists
    timestamps = []
    data_buffer = []
    start_time = time.time()
    
    # Store previous readings to detect changes
    previous_readings = [0, 0, 0, 0, 0]
    stable_count = 0
    convergence_warning_shown = False
    sample_count = 0
    
    # Track convergence behavior
    initial_readings = None
    convergence_values = []
    
    # Display timing (1 Hz = every 1 second)
    last_display_time = None
    display_interval = 1.0  # Display every 1 second
    
    # Create CSV file and write header
    csv_writer = None
    csv_file_handle = None
    try:
        csv_file_handle = open(csv_file, 'w', newline='')
        csv_writer = csv.writer(csv_file_handle)
        csv_writer.writerow(['Time (s)', 'Left Foot (ai16)', 'Right Foot (ai18)', 'Handle Force (ai20)', 
                            'Handle Position (ai21)', 'Seat Position (ai22)'])
    except Exception as e:
        print(f"⚠️  Warning: Could not create CSV file: {e}")
    
    # Create task once and reuse it (like Cortex does)
    # This prevents task recreation overhead and settling issues
    task = nidaqmx.Task()
    try:
        # Configure channels with explicit terminal configuration (RSE - Referenced Single-Ended)
        # This matches typical Cortex configuration for single-ended sensors
        # RSE uses AI GND as reference, which is standard for potentiometers and load cells
        task.ai_channels.add_ai_voltage_chan("Dev1/ai16", 
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Left Foot Force
        task.ai_channels.add_ai_voltage_chan("Dev1/ai18",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Right Foot Force
        task.ai_channels.add_ai_voltage_chan("Dev1/ai20",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Handle Force
        task.ai_channels.add_ai_voltage_chan("Dev1/ai21",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Handle Position
        task.ai_channels.add_ai_voltage_chan("Dev1/ai22",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Seat Position (0-10V as in Cortex)
        
        print("✅ Task configured with RSE (Referenced Single-Ended) terminal configuration")
        print("   Voltage range: 0.0V to 10.0V (matching Cortex configuration)")
        print("   Recording at 2000 Hz, displaying at 1 Hz\n")
        
        # Target: 2000 Hz (0.0005 seconds between samples)
        target_interval = 1.0 / 2000.0
        
        while True:
            loop_start = time.time()
            
            # Read data using the persistent task
            data = task.read(number_of_samples_per_channel=1)
            
            # Extract single values from the nested list structure
            left_foot = data[0][0] if isinstance(data[0], list) else data[0]
            right_foot = data[1][0] if isinstance(data[1], list) else data[1]
            handle_force = data[2][0] if isinstance(data[2], list) else data[2]
            handle_position = data[3][0] if isinstance(data[3], list) else data[3]
            seat_position = data[4][0] if isinstance(data[4], list) else data[4]
            
            current_readings = [left_foot, right_foot, handle_force, handle_position, seat_position]
            sample_count += 1
            
            # Record data to CSV and lists at 2000 Hz
            timestamp = time.time() - start_time
            timestamps.append(timestamp)
            data_buffer.append(current_readings.copy())
            
            if csv_writer:
                try:
                    csv_writer.writerow([timestamp, left_foot, right_foot, handle_force, handle_position, seat_position])
                    # Flush periodically (every 100 samples) to reduce I/O overhead
                    if sample_count % 100 == 0:
                        csv_file_handle.flush()
                except Exception as e:
                    print(f"⚠️  Warning: Error writing to CSV: {e}")
            
            # Display at 1 Hz (every 1 second)
            current_time = time.time()
            should_display = False
            if last_display_time is None:
                should_display = True
                last_display_time = current_time
            elif (current_time - last_display_time) >= display_interval:
                should_display = True
                last_display_time = current_time
            
            if should_display:
                # Capture initial readings (first display)
                if initial_readings is None:
                    initial_readings = current_readings.copy()
                    print("📊 Initial readings captured:")
                    print(f"  Left Foot (ai16):    {left_foot:.6f}V")
                    print(f"  Right Foot (ai18):   {right_foot:.6f}V") 
                    print(f"  Handle Force (ai20):  {handle_force:.6f}V")
                    print(f"  Front Pot (ai21):    {handle_position:.6f}V")
                    print(f"  Back Pot (ai22):     {seat_position:.6f}V")
                    print()
                
                print(f"[Sample {sample_count}] Sensor Readings at {time.strftime('%H:%M:%S')}:")
                print(f"  Left Foot (ai16):    {left_foot:.6f}V  (Δ: {left_foot - initial_readings[0]:+.6f}V)")
                print(f"  Right Foot (ai18):   {right_foot:.6f}V  (Δ: {right_foot - initial_readings[1]:+.6f}V)") 
                print(f"  Handle Force (ai20):  {handle_force:.6f}V  (Δ: {handle_force - initial_readings[2]:+.6f}V)")
                print(f"  Front Pot (ai21):    {handle_position:.6f}V  (Δ: {handle_position - initial_readings[3]:+.6f}V)")
                print(f"  Back Pot (ai22):     {seat_position:.6f}V  (Δ: {seat_position - initial_readings[4]:+.6f}V)")
                
                # Check for convergence (all values moving toward same value)
                if sample_count > 2000:  # Need enough samples for convergence check
                    # Calculate standard deviation of recent readings (last 2000 samples)
                    recent_data = np.array(data_buffer[-2000:]) if len(data_buffer) >= 2000 else np.array(data_buffer)
                    std_dev = np.std(recent_data, axis=0).mean()
                    mean_val = np.mean(recent_data)
                    
                    # Check if values are converging (std dev decreasing)
                    if len(convergence_values) > 0:
                        prev_std = convergence_values[-1]
                        if std_dev < prev_std and std_dev < 0.1:  # Converging and very close
                            if not convergence_warning_shown:
                                print("\n⚠️  WARNING: Sensors converging to same value!")
                                print(f"   Mean: {mean_val:.6f}V, Std Dev: {std_dev:.6f}V")
                                print("\n   Possible causes:")
                                print("   1. FLOATING INPUTS (most likely)")
                                print("      • Sensors not connected or disconnected")
                                print("      • Signal wires not connected to sensors")
                                print("      • Check: Are sensors physically connected?")
                                print()
                                print("   2. SHARED GROUND ISSUE")
                                print("      • All sensors sharing a floating/common ground")
                                print("      • Ground wire disconnected or not connected to DAQ")
                                print("      • Check: Is ground properly connected?")
                                print()
                                print("   3. POWER SUPPLY ISSUE")
                                print("      • Sensors not powered or power disconnected")
                                print("      • Power supply settling to common voltage")
                                print("      • Check: Are sensors receiving power?")
                                print()
                                print("   4. WIRING SHORT")
                                print("      • Signal wires shorted together")
                                print("      • All channels reading same physical connection")
                                print("      • Check: Are signal wires properly isolated?")
                                print()
                                print("   Diagnostic steps:")
                                print("   • Test each sensor individually (mode 2)")
                                print("   • Check physical connections")
                                print("   • Verify sensor power supply")
                                print("   • Test with multimeter if available")
                                convergence_warning_shown = True
                    
                    convergence_values.append(std_dev)
                    if len(convergence_values) > 10:
                        convergence_values.pop(0)
                
                # Check if all readings are identical and near 5V
                all_same = all(abs(val - current_readings[0]) < 0.001 for val in current_readings)
                near_5v = all(abs(val - 5.437) < 0.1 for val in current_readings)
                
                if all_same and near_5v:
                    stable_count += 1
                    if stable_count > 5:
                        print("\n⚠️  WARNING: All sensors stuck at ~5.437V!")
                        print("   This suggests a hardware/wiring issue:")
                        print("   • Check sensor power connections")
                        print("   • Verify signal wires are not shorted to power")
                        print("   • Ensure sensors are properly grounded")
                        print("   • Try physically moving/pressing sensors")
                else:
                    stable_count = 0
                
                # Check for changes from previous reading
                changes = [abs(curr - prev) > 0.01 for curr, prev in zip(current_readings, previous_readings)]
                if any(changes):
                    print("📈 Changes detected!")
                
                previous_readings = current_readings
                print("-" * 50)
            
            # Maintain 2000 Hz sampling rate
            elapsed = time.time() - loop_start
            sleep_time = max(0, target_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\n✅ Sensor testing completed")
    except Exception as e:
        print(f"\n❌ Sensor reading error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close CSV file
        if csv_file_handle:
            try:
                csv_file_handle.flush()  # Ensure all data is written
                csv_file_handle.close()
            except:
                pass
        
        # Generate plots if we have data
        if timestamps and data_buffer:
            try:
                print(f"\n📊 Generating plots...")
                _generate_plots(timestamps, data_buffer, output_folder)
                print(f"✅ Plot saved to: {os.path.join(output_folder, 'sensor_voltages_over_time.png')}")
            except Exception as e:
                print(f"⚠️  Warning: Could not generate plots: {e}")
                import traceback
                traceback.print_exc()
        
        # Clean up task
        try:
            task.close()
        except:
            pass
        
        if timestamps:
            print(f"\n📁 Data saved to: {output_folder}")
            print(f"   CSV: {csv_file}")
            print(f"   Total samples: {len(timestamps)}")

def _generate_plots(timestamps, data_buffer, output_folder):
    """Generate plots of all sensor voltages over time"""
    timestamps_arr = np.array(timestamps)
    data_arr = np.array(data_buffer)
    
    # Channel names
    channel_names = [
        'Left Foot Force (ai16)',
        'Right Foot Force (ai18)',
        'Handle Force (ai20)',
        'Handle Position (ai21)',
        'Seat Position (ai22)'
    ]
    
    # Create overview plot
    n_channels = len(channel_names)
    fig, axes = plt.subplots(n_channels, 1, figsize=(15, 2.5*n_channels))
    fig.suptitle('Sensor Voltages Over Time', fontsize=14, fontweight='bold')
    
    colors = plt.cm.tab10(np.linspace(0, 1, n_channels))
    
    for i, (ax, channel, color) in enumerate(zip(axes, channel_names, colors)):
        ax.plot(timestamps_arr, data_arr[:, i], linewidth=0.8, color=color, alpha=0.8)
        ax.set_ylabel(f'{channel}\n(Voltage)', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        if len(timestamps_arr) > 0:
            ax.set_xlim(timestamps_arr[0], timestamps_arr[-1])
        
        # Add stats
        mean_val = np.mean(data_arr[:, i])
        std_val = np.std(data_arr[:, i])
        min_val = np.min(data_arr[:, i])
        max_val = np.max(data_arr[:, i])
        ax.text(0.02, 0.95, f'μ={mean_val:.3f}V, σ={std_val:.3f}V\nmin={min_val:.3f}V, max={max_val:.3f}V',
                transform=ax.transAxes, fontsize=8, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    axes[-1].set_xlabel('Time (seconds)', fontsize=11)
    plt.tight_layout()
    
    plot_filename = os.path.join(output_folder, "sensor_voltages_over_time.png")
    plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
    plt.close()

def continuous_single_sensor(sensor_key):
    """Continuously read and display voltage from a single selected sensor"""
    if sensor_key not in SENSORS:
        print(f"❌ Invalid sensor selection: {sensor_key}")
        return
    
    sensor_info = SENSORS[sensor_key]
    channel = sensor_info["channel"]
    name = sensor_info["name"]
    
    print(f"\n📊 Continuous reading: {name}")
    print(f"   Channel: {channel}")
    print("   Press Ctrl+C to stop\n")
    
    # Create task once and reuse it (like Cortex does)
    task = nidaqmx.Task()
    try:
        # Configure with RSE terminal configuration and 0-10V range (matching Cortex)
        task.ai_channels.add_ai_voltage_chan(channel,
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)
        
        while True:
            data = task.read(number_of_samples_per_channel=1)
            
            # Extract single value
            voltage = data[0][0] if isinstance(data[0], list) else data[0]
            
            # Simple output: just the voltage value
            print(f"{voltage:.6f}")
            
            time.sleep(0.1)  # Update every 100ms for faster sampling
            
    except KeyboardInterrupt:
        print("\n✅ Continuous reading stopped")
    except Exception as e:
        print(f"\n❌ Sensor reading error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up task
        try:
            task.close()
        except:
            pass

def main():
    print("🧪 FES-Rowing Hardware Test Utility")
    print("=" * 40)
    
    # Test Hardware Connection
    if not test_hardware_connection():
        print("\n💡 Troubleshooting tips:")
        print("  - Check NI-DAQ device is connected via USB/Ethernet")
        print("  - Verify device name is 'Dev1' in NI MAX")
        print("  - Install/update NI-DAQmx drivers")
        print("  - Try running as administrator")
        sys.exit(1)
    
    # Mode selection
    print("\n📋 Select mode:")
    print("  1. Test all sensors (detailed output)")
    print("  2. Continuous single sensor (voltage values only)")
    print()
    
    try:
        mode = input("Enter mode (1 or 2): ").strip()
        
        if mode == "1":
            # Test all sensors
            try:
                test_sensor_readings()
            except Exception as e:
                print(f"❌ Testing failed: {e}")
                sys.exit(1)
            print("\n🎉 Hardware test completed successfully!")
            print("You can now run the main application with confidence.")
            
        elif mode == "2":
            # Continuous single sensor mode
            print("\n📡 Available sensors:")
            for key, info in SENSORS.items():
                print(f"  {key}. {info['name']} ({info['channel']})")
            print()
            
            sensor_choice = input("Select sensor (1-5): ").strip()
            if sensor_choice in SENSORS:
                try:
                    continuous_single_sensor(sensor_choice)
                except Exception as e:
                    print(f"❌ Continuous reading failed: {e}")
                    sys.exit(1)
            else:
                print(f"❌ Invalid sensor selection: {sensor_choice}")
                sys.exit(1)
        else:
            print(f"❌ Invalid mode selection: {mode}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
        sys.exit(0)
    except EOFError:
        # Handle case where input is piped or redirected
        print("\n⚠️  Interactive mode requires terminal input")
        print("Running default mode: Test all sensors")
        try:
            test_sensor_readings()
        except Exception as e:
            print(f"❌ Testing failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main() 