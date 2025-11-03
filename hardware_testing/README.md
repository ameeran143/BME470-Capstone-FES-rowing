# Hardware Testing Utilities

Collection of utilities for testing and debugging NI-DAQ hardware connections before running the main FES rowing application.

## 📁 Contents

- `hardware_test.py` - Basic sensor connection and reading test
- `debug_all_channels.py` - Complete channel debug utility (reads all 64 channels)

## 🚀 Usage

### Basic Hardware Test

```bash
cd hardware_testing
python hardware_test.py
```

**What it does:**
1. Tests connection to NI-DAQ device "Dev2"
2. Verifies all 5 sensor channels are accessible
3. Continuously reads and displays sensor values
4. Detects hardware issues (stuck sensors, wiring problems)

**Features:**
- Real-time sensor value display
- Automatic detection of stuck sensors (stuck at ~5.437V)
- Change detection alerts
- Troubleshooting tips on connection failure

### Debug All Channels

```bash
cd hardware_testing
python debug_all_channels.py
```

**What it does:**
1. Reads all 64 analog input channels
2. Identifies which channels are active
3. Detects stuck/floating channels
4. Provides continuous monitoring mode

**Features:**
- Complete channel scan (ai0-ai63)
- Organized display (8 channels per row)
- Channel analysis (zero, stuck, interesting values)
- Continuous monitoring mode for detecting changes

## 🔌 Hardware Requirements

**Device:** NI-DAQ Dev2

**Sensor Channel Mapping:**
| Channel | Sensor | Notes |
|---------|--------|-------|
| ai16 | Left Foot Force Sensor | Load cell |
| ai18 | Right Foot Force Sensor | Load cell |
| ai20 | Handle Force Sensor | Load cell |
| ai21 | Front Potentiometer | Handle Position |
| ai22 | Back Potentiometer | Seat Position (voltage × 100) |

**Platform Requirements:**
- Windows or Linux (macOS not supported - NI-DAQmx limitation)
- NI-DAQmx drivers installed
- NI-DAQ device connected and configured in NI MAX

## 🛠️ Troubleshooting

### Connection Failed
- Check NI-DAQ device is connected via USB/Ethernet
- Verify device name is 'Dev2' in NI MAX
- Install/update NI-DAQmx drivers
- Try running as administrator

### Sensors Stuck at ~5.437V
This indicates a hardware/wiring issue:
- Check sensor power connections
- Verify signal wires are not shorted to power
- Ensure sensors are properly grounded
- Try physically moving/pressing sensors

### No Signal Changes
- Verify sensors are properly connected
- Check sensor power supply
- Test sensors individually
- Use `debug_all_channels.py` to scan all channels

## 📝 When to Use

**Use `hardware_test.py` when:**
- Setting up hardware for the first time
- Verifying sensor connections before a session
- Quick check that all sensors are working
- Troubleshooting sensor reading issues

**Use `debug_all_channels.py` when:**
- Need to identify which channels are connected
- Suspecting channel mapping issues
- Debugging wiring problems
- Finding unused channels

## 🔗 Related Files

- `../Coaching App/` - Main application
- `../sensor_game_page/` - Live sensor testing environment
- `../real_data_testing/` - Playback testing environment

