#!/usr/bin/env python3
"""
Complete Channel Debug Utility for FES-Rowing Application
This script reads ALL 64 analog input channels to identify working sensors.

Use this to:
- Find which channels are actually connected
- Identify stuck/floating channels
- Verify sensor mapping
"""

import nidaqmx
import time
import sys

def test_all_channels():
    """Read and display all 64 analog input channels"""
    print("🔍 Reading ALL 64 channels on Dev2...")
    print("=" * 80)
    
    try:
        with nidaqmx.Task() as task:
            # Add all 64 channels (ai0 through ai63)
            channels = []
            for i in range(64):
                channel_name = f"Dev2/ai{i}"
                try:
                    task.ai_channels.add_ai_voltage_chan(channel_name, min_val=-10.0, max_val=10.0)
                    channels.append(channel_name)
                except Exception as e:
                    print(f"❌ Failed to add {channel_name}: {e}")
            
            print(f"✅ Successfully added {len(channels)} channels")
            print("Reading values...\n")
            
            # Read all channels
            data = task.read(number_of_samples_per_channel=1)
            
            # Display results in organized format
            print(f"Channel Readings at {time.strftime('%H:%M:%S')}:")
            print("-" * 80)
            
            # Group by 8 channels per row for readability
            for row in range(0, len(channels), 8):
                # Header row
                header = ""
                values = ""
                
                for col in range(8):
                    if row + col < len(channels):
                        channel_num = row + col
                        voltage = data[channel_num][0] if isinstance(data[channel_num], list) else data[channel_num]
                        
                        header += f"ai{channel_num:2d}      "
                        values += f"{voltage:6.3f}V  "
                
                print(header)
                print(values)
                print()
            
            # Analysis
            print("=" * 80)
            print("ANALYSIS:")
            
            # Find channels with interesting values (not 0, not stuck at 5V)
            interesting_channels = []
            stuck_at_5v = []
            zero_channels = []
            
            for i, channel in enumerate(channels):
                voltage = data[i][0] if isinstance(data[i], list) else data[i]
                
                if abs(voltage) < 0.001:
                    zero_channels.append((i, voltage))
                elif abs(voltage - 5.437) < 0.1:  # Near 5.437V (your stuck value)
                    stuck_at_5v.append((i, voltage))
                else:
                    interesting_channels.append((i, voltage))
            
            print(f"📊 Channel Summary:")
            print(f"   Zero/Ground channels: {len(zero_channels)}")
            print(f"   Stuck at ~5.437V: {len(stuck_at_5v)}")
            print(f"   Interesting values: {len(interesting_channels)}")
            
            if interesting_channels:
                print(f"\n✨ Channels with varying signals:")
                for ch, voltage in interesting_channels:
                    print(f"   ai{ch}: {voltage:.3f}V")
            
            if stuck_at_5v:
                print(f"\n⚠️  Channels stuck at ~5.437V:")
                for ch, voltage in stuck_at_5v:
                    print(f"   ai{ch}: {voltage:.3f}V")
                    
            # Expected sensor channels
            expected_sensors = [17, 19, 21, 22, 23]
            print(f"\n🎯 Expected sensor channels:")
            for ch in expected_sensors:
                if ch < len(data):
                    voltage = data[ch][0] if isinstance(data[ch], list) else data[ch]
                    status = "✅" if ch in [i for i, v in interesting_channels] else "❌"
                    print(f"   ai{ch}: {voltage:.3f}V {status}")
                    
    except Exception as e:
        print(f"❌ Error reading channels: {e}")
        return False
        
    return True

def continuous_monitoring():
    """Continuously monitor all channels for changes"""
    print("\n🔄 Continuous monitoring mode (Press Ctrl+C to stop)")
    print("Only showing channels that change...\n")
    
    previous_values = {}
    
    try:
        while True:
            with nidaqmx.Task() as task:
                # Add all channels
                for i in range(64):
                    try:
                        task.ai_channels.add_ai_voltage_chan(f"Dev2/ai{i}", min_val=-10.0, max_val=10.0)
                    except:
                        pass
                
                data = task.read(number_of_samples_per_channel=1)
                
                changes_detected = False
                for i, channel_data in enumerate(data):
                    voltage = channel_data[0] if isinstance(channel_data, list) else channel_data
                    
                    if i in previous_values:
                        if abs(voltage - previous_values[i]) > 0.01:  # 10mV threshold
                            print(f"📈 ai{i}: {previous_values[i]:.3f}V → {voltage:.3f}V (Δ{voltage-previous_values[i]:+.3f}V)")
                            changes_detected = True
                    
                    previous_values[i] = voltage
                
                if changes_detected:
                    print("-" * 40)
                
                time.sleep(0.1)  # 10 Hz sampling
                
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")

def main():
    print("🔧 Complete Channel Debug Utility")
    print("=" * 40)
    
    # Test 1: Read all channels once
    if not test_all_channels():
        sys.exit(1)
    
    # Ask user if they want continuous monitoring
    print("\nWould you like to start continuous monitoring? (y/n): ", end="")
    try:
        response = input().strip().lower()
        if response in ['y', 'yes']:
            continuous_monitoring()
    except KeyboardInterrupt:
        pass
    
    print("\n🎉 Debug session completed!")

if __name__ == "__main__":
    main() 