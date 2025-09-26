#!/usr/bin/env python3
"""
Hardware Testing Utility for FES-Rowing Application
Run this script to test sensor connections before using the main application.
"""

import nidaqmx
import time
import sys

def test_hardware_connection():
    """Test if NI-DAQ device is connected and responsive"""
    try:
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev4/ai0:7")
            print("✅ NI-DAQ device 'Dev4' found and accessible")
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
                task.ai_channels.add_ai_voltage_chan("Dev4/ai0:7")
                data = task.read(number_of_samples_per_channel=1)
                
                print(f"Sensor Readings at {time.strftime('%H:%M:%S')}:")
                print(f"  Switch (ai0):      {data[0][-1]:.3f}V {'(PRESSED)' if data[0][-1] < 2.5 else '(RELEASED)'}")
                print(f"  Left Foot (ai2):   {data[2][-1]:.3f}V")
                print(f"  Right Foot (ai4):  {data[4][-1]:.3f}V") 
                print(f"  Handle Force (ai5): {data[5][-1]:.3f}V")
                print(f"  Handle Pos (ai6):  {data[6][-1]:.3f}V")
                print(f"  Seat Pos (ai7):    {data[7][-1]:.3f}V → {data[7][-1]*100:.1f}")
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
        print("  - Verify device name is 'Dev4' in NI MAX")
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