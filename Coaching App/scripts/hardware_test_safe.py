#!/usr/bin/env python3
"""
Hardware Testing Utility for FES-Rowing Application
Run this script to test sensor connections before using the main application.

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

"""

import nidaqmx
import time
import sys
import statistics

# Sensor channel mapping
SENSORS = {
    "1": {"name": "Left Foot Force Sensor", "channel": "Dev2/ai16"},
    "2": {"name": "Right Foot Force Sensor", "channel": "Dev2/ai18"},
    "3": {"name": "Handle Force Sensor", "channel": "Dev2/ai20"},
    "4": {"name": "Front Potentiometer (Handle Position)", "channel": "Dev2/ai21"},
    "5": {"name": "Back Potentiometer (Seat Position)", "channel": "Dev2/ai22"},
}

def test_hardware_connection():
    """Test if NI-DAQ device is connected and responsive"""
    try:
        with nidaqmx.Task() as task:
            # Test with the new channel mapping - add each channel individually
            task.ai_channels.add_ai_voltage_chan("Dev2/ai16")
            task.ai_channels.add_ai_voltage_chan("Dev2/ai18") 
            task.ai_channels.add_ai_voltage_chan("Dev2/ai20")
            task.ai_channels.add_ai_voltage_chan("Dev2/ai21")
            task.ai_channels.add_ai_voltage_chan("Dev2/ai22")
            print("✅ NI-DAQ device 'Dev2' found and accessible")
            return True
    except Exception as e:
        print(f"❌ Hardware connection failed: {e}")
        return False

def test_sensor_readings():
    """Read and display sensor values for verification"""
    print("\n🔍 Testing sensor readings...")
    print("Press Ctrl+C to stop\n")
    
    # Store previous readings to detect changes
    previous_readings = [0, 0, 0, 0, 0]
    stable_count = 0
    convergence_warning_shown = False
    sample_count = 0
    
    # Track convergence behavior
    initial_readings = None
    convergence_values = []
    
    # Create task once and reuse it (like Cortex does)
    # This prevents task recreation overhead and settling issues
    task = nidaqmx.Task()
    try:
        # Configure channels with explicit terminal configuration (RSE - Referenced Single-Ended)
        # This matches typical Cortex configuration for single-ended sensors
        # RSE uses AI GND as reference, which is standard for potentiometers and load cells
        task.ai_channels.add_ai_voltage_chan("Dev2/ai16", 
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Left Foot Force
        task.ai_channels.add_ai_voltage_chan("Dev2/ai18",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Right Foot Force
        task.ai_channels.add_ai_voltage_chan("Dev2/ai20",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Handle Force
        task.ai_channels.add_ai_voltage_chan("Dev2/ai21",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Handle Position
        task.ai_channels.add_ai_voltage_chan("Dev2/ai22",
                                             terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                             min_val=0.0, max_val=10.0)   # Seat Position (0-10V as in Cortex)
        
        print("✅ Task configured with RSE (Referenced Single-Ended) terminal configuration")
        print("   Voltage range: 0.0V to 10.0V (matching Cortex configuration)\n")
        
        while True:
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
            
            # Capture initial readings (first sample)
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
            if sample_count > 3:
                # Calculate standard deviation of current readings
                std_dev = statistics.stdev(current_readings)
                mean_val = statistics.mean(current_readings)
                
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
            
            time.sleep(0.5)  # Update every 500ms
                
    except KeyboardInterrupt:
        print("\n✅ Sensor testing completed")
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
        print("  - Verify device name is 'Dev2' in NI MAX")
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