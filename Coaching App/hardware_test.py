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
    
    try:
        while True:
            with nidaqmx.Task() as task:
                # Add each channel individually with explicit voltage range
                task.ai_channels.add_ai_voltage_chan("Dev2/ai16", min_val=-10.0, max_val=10.0)
                task.ai_channels.add_ai_voltage_chan("Dev2/ai18", min_val=-10.0, max_val=10.0) 
                task.ai_channels.add_ai_voltage_chan("Dev2/ai20", min_val=-10.0, max_val=10.0)
                task.ai_channels.add_ai_voltage_chan("Dev2/ai21", min_val=-10.0, max_val=10.0)
                task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=-10.0, max_val=10.0)
                data = task.read(number_of_samples_per_channel=1)
                
                # Extract single values from the nested list structure
                left_foot = data[0][0] if isinstance(data[0], list) else data[0]
                right_foot = data[1][0] if isinstance(data[1], list) else data[1]
                handle_force = data[2][0] if isinstance(data[2], list) else data[2]
                handle_position = data[3][0] if isinstance(data[3], list) else data[3]
                seat_position = data[4][0] if isinstance(data[4], list) else data[4]
                
                current_readings = [left_foot, right_foot, handle_force, handle_position, seat_position]
                
                print(f"Sensor Readings at {time.strftime('%H:%M:%S')}:")
                print(f"  Left Foot (ai16):    {left_foot:.3f}V")
                print(f"  Right Foot (ai18):   {right_foot:.3f}V") 
                print(f"  Handle Force (ai20):  {handle_force:.3f}V")
                print(f"  Front Potentiometer (ai21): {handle_position:.3f}V  # Handle Position")
                print(f"  Back Potentiometer (ai22):  {seat_position:.3f}V → {seat_position*100:.1f}  # Seat Position")
                
                # Check if all readings are identical and near 5V
                all_same = all(abs(val - current_readings[0]) < 0.001 for val in current_readings)
                near_5v = all(abs(val - 5.437) < 0.1 for val in current_readings)
                
                if all_same and near_5v:
                    stable_count += 1
                    if stable_count > 5:
                        print("⚠️  WARNING: All sensors stuck at ~5.437V!")
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

def main():
    print("🧪 FES-Rowing Hardware Test Utility")
    print("=" * 40)
    
    # Test 1: Hardware Connection
    if not test_hardware_connection():
        print("\n💡 Troubleshooting tips:")
        print("  - Check NI-DAQ device is connected via USB/Ethernet")
        print("  - Verify device name is 'Dev2' in NI MAX")
        print("  - Install/update NI-DAQmx drivers")
        print("  - Try running as administrator")
        sys.exit(1)
    
    # Test 2: Sensor Readings
    try:
        test_sensor_readings()
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        sys.exit(1)
    
    print("\n🎉 Hardware test completed successfully!")
    print("You can now run the main application with confidence.")

if __name__ == "__main__":
    main() 