#!/usr/bin/env python3
"""
Hardware Testing Utility for FES-Rowing Application
Interactive script to test sensor connections and view voltage ranges.

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
import os
from collections import defaultdict

# Sensor channel mapping
SENSORS = {
    '1': {'name': 'Left Foot Force Sensor', 'channel': 'ai16', 'key': 'left_foot'},
    '2': {'name': 'Right Foot Force Sensor', 'channel': 'ai18', 'key': 'right_foot'},
    '3': {'name': 'Handle Force Sensor', 'channel': 'ai20', 'key': 'handle_force'},
    '4': {'name': 'Front Potentiometer (Handle Position)', 'channel': 'ai21', 'key': 'handle_position'},
    '5': {'name': 'Back Potentiometer (Seat Position)', 'channel': 'ai22', 'key': 'seat_position'}
}

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def read_all_sensors():
    """Read all sensor values from hardware"""
    try:
        with nidaqmx.Task() as task:
            # Add each channel individually with optimized voltage ranges for better ADC resolution
            # Ranges based on actual sensor output measurements (with safety margin)
            task.ai_channels.add_ai_voltage_chan("Dev2/ai16", min_val=7.0, max_val=9.5)   # Left Foot Force
            task.ai_channels.add_ai_voltage_chan("Dev2/ai18", min_val=7.0, max_val=9.0)   # Right Foot Force
            task.ai_channels.add_ai_voltage_chan("Dev2/ai20", min_val=8.5, max_val=10.5)  # Handle Force
            task.ai_channels.add_ai_voltage_chan("Dev2/ai21", min_val=8.5, max_val=11.0)  # Handle Position
            task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=9.0, max_val=11.0)  # Seat Position
            data = task.read(number_of_samples_per_channel=1)
            
            # Extract single values from the nested list structure
            readings = {
                'left_foot': data[0][0] if isinstance(data[0], list) else data[0],
                'right_foot': data[1][0] if isinstance(data[1], list) else data[1],
                'handle_force': data[2][0] if isinstance(data[2], list) else data[2],
                'handle_position': data[3][0] if isinstance(data[3], list) else data[3],
                'seat_position': data[4][0] if isinstance(data[4], list) else data[4]
            }
            return readings
    except Exception as e:
        print(f"❌ Error reading sensors: {e}")
        return None

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

def display_home_screen(stats):
    """Display the home screen with sensor min/max table"""
    clear_screen()
    print("=" * 70)
    print("🧪 FES-Rowing Hardware Test Utility - Sensor Overview")
    print("=" * 70)
    print()
    
    # Display min/max table
    print("Sensor Voltage Ranges:")
    print("-" * 70)
    print(f"{'Sensor':<45} {'Min (V)':<12} {'Max (V)':<12}")
    print("-" * 70)
    
    for sensor_id, sensor_info in SENSORS.items():
        key = sensor_info['key']
        name = sensor_info['name']
        
        if stats['count'] > 0:
            min_val = stats['min'][key]
            max_val = stats['max'][key]
            min_str = f"{min_val:.3f}" if min_val != float('inf') else "N/A"
            max_str = f"{max_val:.3f}" if max_val != float('-inf') else "N/A"
        else:
            min_str = "N/A"
            max_str = "N/A"
        
        print(f"{sensor_id}. {name:<40} {min_str:<12} {max_str:<12}")
    
    print("-" * 70)
    print(f"Total readings: {stats['count']}")
    print()
    
    # Display menu options
    print("Options:")
    print("  1-5: View detailed readings for sensor 1-5")
    print("  r:   Refresh sensor readings (update min/max)")
    print("  s:   Start continuous monitoring (updates min/max)")
    print("  q:   Quit and show summary")
    print()

def view_sensor_detail(sensor_id, stats):
    """View detailed readings for a specific sensor"""
    if sensor_id not in SENSORS:
        print("❌ Invalid sensor selection")
        input("Press Enter to continue...")
        return
    
    sensor_info = SENSORS[sensor_id]
    sensor_key = sensor_info['key']
    sensor_name = sensor_info['name']
    
    print(f"\n📊 Viewing: {sensor_name} ({sensor_info['channel']})")
    print("=" * 70)
    
    update_count = 0
    try:
        while True:
            readings = read_all_sensors()
            if readings is None:
                print("❌ Failed to read sensors.")
                input("Press Enter to continue...")
                return
            
            current_value = readings[sensor_key]
            
            # Update stats
            stats['min'][sensor_key] = min(stats['min'][sensor_key], current_value)
            stats['max'][sensor_key] = max(stats['max'][sensor_key], current_value)
            stats['count'] += 1
            update_count += 1
            
            # Display current reading
            clear_screen()
            print("=" * 70)
            print(f"📊 {sensor_name} ({sensor_info['channel']})")
            print("=" * 70)
            print(f"Current Value: {current_value:.3f}V")
            print(f"Min Value:     {stats['min'][sensor_key]:.3f}V")
            print(f"Max Value:     {stats['max'][sensor_key]:.3f}V")
            print(f"Range:         {stats['max'][sensor_key] - stats['min'][sensor_key]:.3f}V")
            print(f"Updates:       {update_count}")
            print(f"Total Readings: {stats['count']}")
            print()
            print("Options:")
            print("  [Enter] Continue monitoring")
            print("  b       Go back to home")
            print("  Ctrl+C  Return to home")
            print("-" * 70)
            
            # Get user input with timeout
            import threading
            
            user_input = [None]
            def get_input():
                try:
                    user_input[0] = input("Choice: ").strip().lower()
                except:
                    pass
            
            input_thread = threading.Thread(target=get_input, daemon=True)
            input_thread.start()
            input_thread.join(timeout=2.0)  # Wait up to 2 seconds for input
            
            if user_input[0] == 'b':
                return
            elif user_input[0] is None:
                # Timeout - continue monitoring
                continue
            
    except KeyboardInterrupt:
        return
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to continue...")
        return

def continuous_monitoring(stats):
    """Continuously monitor all sensors and update min/max"""
    print("\n🔄 Continuous Monitoring Mode")
    print("=" * 70)
    print("Monitoring all sensors and updating min/max values...")
    print("Press Ctrl+C to stop and return to home screen")
    print("-" * 70)
    
    try:
        while True:
            readings = read_all_sensors()
            if readings is None:
                print("❌ Failed to read sensors")
                time.sleep(1)
                continue
            
            # Update stats for all sensors
            for sensor_key, value in readings.items():
                stats['min'][sensor_key] = min(stats['min'][sensor_key], value)
                stats['max'][sensor_key] = max(stats['max'][sensor_key], value)
            stats['count'] += 1
            
            # Display current readings and updated ranges
            clear_screen()
            print("=" * 70)
            print("🔄 Continuous Monitoring Mode")
            print("=" * 70)
            print(f"Time: {time.strftime('%H:%M:%S')} | Total Readings: {stats['count']}")
            print("-" * 70)
            print(f"{'Sensor':<45} {'Current':<12} {'Min':<12} {'Max':<12}")
            print("-" * 70)
            
            for sensor_id, sensor_info in SENSORS.items():
                key = sensor_info['key']
                name = sensor_info['name']
                current = readings[key]
                min_val = stats['min'][key]
                max_val = stats['max'][key]
                
                print(f"{sensor_id}. {name:<40} {current:>10.3f}V  {min_val:>10.3f}V  {max_val:>10.3f}V")
            
            print("-" * 70)
            print("Press Ctrl+C to stop and return to home screen")
            
            time.sleep(0.5)  # Update every 500ms
            
    except KeyboardInterrupt:
        return

def refresh_readings(stats):
    """Take a single reading to update min/max values"""
    print("\n🔄 Refreshing sensor readings...")
    readings = read_all_sensors()
    
    if readings is None:
        print("❌ Failed to read sensors")
        input("\nPress Enter to continue...")
        return
    
    # Update stats for all sensors
    for sensor_key, value in readings.items():
        stats['min'][sensor_key] = min(stats['min'][sensor_key], value)
        stats['max'][sensor_key] = max(stats['max'][sensor_key], value)
    stats['count'] += 1
    
    print("✅ Readings updated!")
    print(f"   Total readings: {stats['count']}")
    time.sleep(1)

def display_summary(stats):
    """Display final summary report"""
    clear_screen()
    print("=" * 70)
    print("📊 Final Sensor Test Summary")
    print("=" * 70)
    print()
    
    if stats['count'] == 0:
        print("⚠️  No sensor readings were collected.")
        return
    
    print("Sensor Voltage Ranges:")
    print("-" * 70)
    print(f"{'Sensor':<45} {'Min (V)':<12} {'Max (V)':<12} {'Range (V)':<12}")
    print("-" * 70)
    
    for sensor_id, sensor_info in SENSORS.items():
        key = sensor_info['key']
        name = sensor_info['name']
        
        min_val = stats['min'][key]
        max_val = stats['max'][key]
        range_val = max_val - min_val
        
        print(f"{sensor_id}. {name:<40} {min_val:>10.3f}V  {max_val:>10.3f}V  {range_val:>10.3f}V")
    
    print("-" * 70)
    print(f"Total readings collected: {stats['count']}")
    print()
    print("✅ Hardware test completed successfully!")
    print("You can now run the main application with confidence.")

def main():
    """Main interactive loop"""
    # Initialize statistics tracking
    stats = {
        'min': defaultdict(lambda: float('inf')),
        'max': defaultdict(lambda: float('-inf')),
        'count': 0
    }
    
    print("🧪 FES-Rowing Hardware Test Utility")
    print("=" * 70)
    
    # Test hardware connection
    if not test_hardware_connection():
        print("\n💡 Troubleshooting tips:")
        print("  - Check NI-DAQ device is connected via USB/Ethernet")
        print("  - Verify device name is 'Dev2' in NI MAX")
        print("  - Install/update NI-DAQmx drivers")
        print("  - Try running as administrator")
        sys.exit(1)
    
    # Initial reading to populate stats
    print("\n📡 Taking initial sensor reading...")
    readings = read_all_sensors()
    if readings:
        for sensor_key, value in readings.items():
            stats['min'][sensor_key] = value
            stats['max'][sensor_key] = value
        stats['count'] = 1
        print("✅ Initial reading successful")
    else:
        print("⚠️  Initial reading failed - continuing anyway")
    
    time.sleep(1)
    
    # Main interactive loop
    while True:
        display_home_screen(stats)
        
        try:
            choice = input("Enter your choice: ").strip().lower()
            
            if choice in SENSORS:
                # View specific sensor
                view_sensor_detail(choice, stats)
            elif choice == 'r':
                # Refresh readings
                refresh_readings(stats)
            elif choice == 's':
                # Start continuous monitoring
                continuous_monitoring(stats)
            elif choice == 'q':
                # Quit and show summary
                break
            else:
                print("❌ Invalid choice. Please try again.")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted. Showing summary...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")
    
    # Display final summary
    display_summary(stats)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
        sys.exit(0)
