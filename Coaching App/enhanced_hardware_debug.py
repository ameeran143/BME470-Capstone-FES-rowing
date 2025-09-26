#!/usr/bin/env python3
"""
Enhanced Hardware Debugging Utility for FES-Rowing Application
Alternative to NI MAX for device detection and comprehensive hardware testing.

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
import nidaqmx.system
import time
import sys
import platform
from tabulate import tabulate

class HardwareDebugger:
    def __init__(self):
        self.system_info = None
        self.devices = []
        self.expected_device = "Dev2"
        
    def get_system_info(self):
        """Get comprehensive system information"""
        print("🔍 SYSTEM INFORMATION")
        print("=" * 50)
        
        try:
            system = nidaqmx.system.System.local()
            self.system_info = {
                'NI-DAQmx Version': system.driver_version,
                'Operating System': platform.system() + " " + platform.release(),
                'Python Version': platform.python_version(),
                'Platform': platform.platform()
            }
            
            for key, value in self.system_info.items():
                print(f"  {key:<20}: {value}")
                
        except Exception as e:
            print(f"❌ Failed to get system info: {e}")
            return False
        return True
    
    def discover_devices(self):
        """Discover all NI-DAQ devices (alternative to NI MAX device list)"""
        print("\n🔍 DEVICE DISCOVERY")
        print("=" * 50)
        
        try:
            system = nidaqmx.system.System.local()
            self.devices = system.devices
            
            if not self.devices:
                print("❌ No NI-DAQ devices found")
                return False
                
            device_table = []
            for device in self.devices:
                try:
                    device_info = {
                        'Name': device.name,
                        'Product Type': device.product_type,
                        'Product Number': device.product_num,
                        'Serial Number': device.dev_serial_num,
                        'Is Simulated': device.dev_is_simulated
                    }
                    device_table.append([
                        device_info['Name'],
                        device_info['Product Type'], 
                        device_info['Product Number'],
                        device_info['Serial Number'],
                        'Yes' if device_info['Is Simulated'] else 'No'
                    ])
                except Exception as e:
                    device_table.append([device.name, 'Error', f'Failed: {e}', '', ''])
            
            headers = ['Device Name', 'Product Type', 'Product Number', 'Serial Number', 'Simulated']
            print(tabulate(device_table, headers=headers, tablefmt='grid'))
            
            # Check for expected device
            device_names = [dev.name for dev in self.devices]
            if self.expected_device in device_names:
                print(f"✅ Expected device '{self.expected_device}' found!")
            else:
                print(f"⚠️  Expected device '{self.expected_device}' not found")
                print(f"   Available devices: {device_names}")
                
        except Exception as e:
            print(f"❌ Device discovery failed: {e}")
            return False
        return True
    
    def analyze_device_capabilities(self, device_name):
        """Analyze specific device capabilities (alternative to NI MAX device properties)"""
        print(f"\n🔍 DEVICE ANALYSIS: {device_name}")
        print("=" * 50)
        
        try:
            system = nidaqmx.system.System.local()
            device = system.devices[device_name]
            
            capabilities = {
                'Analog Input Channels': len(device.ai_physical_chans),
                'Analog Output Channels': len(device.ao_physical_chans), 
                'Digital Input Lines': len(device.di_lines),
                'Digital Output Lines': len(device.do_lines),
                'Counter Input Channels': len(device.ci_physical_chans),
                'Counter Output Channels': len(device.co_physical_chans)
            }
            
            for capability, count in capabilities.items():
                status = "✅" if count > 0 else "❌"
                print(f"  {status} {capability:<25}: {count}")
            
            # Analog input channel details (most important for rowing app)
            if device.ai_physical_chans:
                print(f"\n📊 ANALOG INPUT CHANNELS:")
                ai_table = []
                for i, chan in enumerate(device.ai_physical_chans):
                    ai_table.append([
                        chan.name,
                        f"ai{i}",
                        "Voltage" if hasattr(chan, 'ai_voltage_rng') else "Unknown"
                    ])
                headers = ['Channel Name', 'Channel ID', 'Measurement Type']
                print(tabulate(ai_table, headers=headers, tablefmt='grid'))
            
        except Exception as e:
            print(f"❌ Device analysis failed: {e}")
            return False
        return True
    
    def test_channel_connectivity(self, device_name="Dev2"):
        """Test individual channel connectivity"""
        print(f"\n🔍 CHANNEL CONNECTIVITY TEST")
        print("=" * 50)
        
        channel_mapping = {
            'ai17': 'Left Foot Force',
            'ai19': 'Right Foot Force',
            'ai21': 'Handle Force',
            'ai22': 'Front Potentiometer (Handle Position)', 
            'ai23': 'Back Potentiometer (Seat Position)'
        }
        
        connectivity_results = []
        
        for channel, description in channel_mapping.items():
            try:
                with nidaqmx.Task() as task:
                    full_channel = f"{device_name}/{channel}"
                    task.ai_channels.add_ai_voltage_chan(full_channel)
                    
                    # Test read
                    data = task.read(number_of_samples_per_channel=1)
                    voltage = data if isinstance(data, (int, float)) else data[0]
                    
                    connectivity_results.append([
                        channel,
                        description,
                        f"{voltage:.3f}V",
                        "✅ Connected"
                    ])
                    
            except Exception as e:
                connectivity_results.append([
                    channel, 
                    description,
                    "N/A",
                    f"❌ Error: {str(e)[:30]}..."
                ])
        
        headers = ['Channel', 'Sensor Type', 'Current Reading', 'Status']
        print(tabulate(connectivity_results, headers=headers, tablefmt='grid'))
    
    def test_rowing_specific_sensors(self, device_name="Dev2", duration=10):
        """Test rowing-specific sensor functionality with live monitoring"""
        print(f"\n🚣 ROWING SENSOR LIVE TEST ({duration}s)")
        print("=" * 50)
        print("Move the seat, press the switch, and apply force to sensors...")
        print("Press Ctrl+C to stop early\n")
        
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                with nidaqmx.Task() as task:
                    task.ai_channels.add_ai_voltage_chan(f"{device_name}/ai17,ai19,ai21:23")
                    data = task.read(number_of_samples_per_channel=1)
                    
                    # Extract key sensor values (new mapping)
                    left_foot = data[0] if isinstance(data[0], (int, float)) else data[0][-1]  # ai17
                    right_foot = data[1] if isinstance(data[1], (int, float)) else data[1][-1]  # ai19
                    handle_force = data[2] if isinstance(data[2], (int, float)) else data[2][-1]  # ai21
                    handle_pos = data[3] if isinstance(data[3], (int, float)) else data[3][-1]  # ai22
                    seat_pos_raw = data[4] if isinstance(data[4], (int, float)) else data[4][-1]  # ai23
                    seat_pos_converted = seat_pos_raw * 100
                    
                    print(f"\r🔄 L.Foot: {left_foot:5.2f} | R.Foot: {right_foot:5.2f} | Handle: {handle_force:5.2f} | Seat: {seat_pos_converted:6.1f}", end="")
                    time.sleep(0.2)
                    
        except KeyboardInterrupt:
            print("\n✅ Test stopped by user")
        except Exception as e:
            print(f"\n❌ Sensor test failed: {e}")
    
    def comprehensive_hardware_test(self):
        """Run complete hardware diagnostic suite"""
        print("🧪 FES-ROWING COMPREHENSIVE HARDWARE TEST")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("System Information", self.get_system_info),
            ("Device Discovery", self.discover_devices), 
            ("Device Capabilities", lambda: self.analyze_device_capabilities(self.expected_device)),
            ("Channel Connectivity", self.test_channel_connectivity),
        ]
        
        test_results = {}
        
        for test_name, test_func in tests:
            print(f"\n⏳ Running: {test_name}")
            try:
                result = test_func()
                test_results[test_name] = "✅ PASSED" if result else "❌ FAILED"
            except Exception as e:
                test_results[test_name] = f"❌ ERROR: {e}"
        
        # Results summary
        print(f"\n📊 TEST SUMMARY")
        print("=" * 30)
        for test, result in test_results.items():
            print(f"  {test:<20}: {result}")
        
        # Offer live sensor test
        if all("✅" in result for result in test_results.values()):
            response = input("\n🚣 Run live sensor test? (y/n): ").strip().lower()
            if response == 'y':
                self.test_rowing_specific_sensors()


def main():
    """Main execution function"""
    debugger = HardwareDebugger()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "discover":
            debugger.get_system_info()
            debugger.discover_devices()
        elif command == "analyze":
            device = sys.argv[2] if len(sys.argv) > 2 else "Dev2"
            debugger.analyze_device_capabilities(device)
        elif command == "test":
            debugger.test_channel_connectivity()
        elif command == "live":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            debugger.test_rowing_specific_sensors(duration=duration)
        else:
            print("Usage: python enhanced_hardware_debug.py [discover|analyze|test|live]")
    else:
        debugger.comprehensive_hardware_test()


if __name__ == "__main__":
    main() 