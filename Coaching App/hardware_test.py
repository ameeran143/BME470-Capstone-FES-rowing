#!/usr/bin/env python3
"""
Hardware Testing Utility for FES-Rowing Application
Run this script to test sensor connections before using the main application.

SENSOR CHANNEL MAPPING (NI-DAQ Dev2):
======================================
ai0-ai16: [UNUSED]
ai17: Left Foot Force Sensor
ai18: [UNUSED]
ai19: Right Foot Force Sensor
ai20: [UNUSED]
ai21: Handle Force Sensor
ai22: Front Potentiometer → Handle Position
ai23: Back Potentiometer → Seat Position (converted: voltage * 100)


"""

import nidaqmx
import time
import sys

def test_hardware_connection():
    """Test if NI-DAQ device is connected and responsive"""
    try:
        with nidaqmx.Task() as task:
            # Test with the new channel mapping - add each channel individually
            task.ai_channels.add_ai_voltage_chan("Dev2/ai17")
            task.ai_channels.add_ai_voltage_chan("Dev2/ai19") 
            task.ai_channels.add_ai_voltage_chan("Dev2/ai21")
            task.ai_channels.add_ai_voltage_chan("Dev2/ai22")
            task.ai_channels.add_ai_voltage_chan("Dev2/ai23")
            print("✅ NI-DAQ device 'Dev2' found and accessible")
            return True
    except Exception as e:
        print(f"❌ Hardware connection failed: {e}")
        return False

def test_sensor_readings():
    """Read and display sensor values for verification"""
    print("\n🔍 Testing sensor readings...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            with nidaqmx.Task() as task:
                # Add each channel individually
                task.ai_channels.add_ai_voltage_chan("Dev2/ai17")
                task.ai_channels.add_ai_voltage_chan("Dev2/ai19") 
                task.ai_channels.add_ai_voltage_chan("Dev2/ai21")
                task.ai_channels.add_ai_voltage_chan("Dev2/ai22")
                task.ai_channels.add_ai_voltage_chan("Dev2/ai23")
                data = task.read(number_of_samples_per_channel=1)
                
                print(f"Sensor Readings at {time.strftime('%H:%M:%S')}:")
                print(f"  Left Foot (ai17):    {data[0]:.3f}V")
                print(f"  Right Foot (ai19):   {data[1]:.3f}V") 
                print(f"  Handle Force (ai21):  {data[2]:.3f}V")
                print(f"  Front Potentiometer (ai22): {data[3]:.3f}V  # Handle Position")
                print(f"  Back Potentiometer (ai23):  {data[4]:.3f}V → {data[4]*100:.1f}  # Seat Position")
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