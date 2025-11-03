# Sensor Game Page - Live Hardware Testing Environment

Standalone testing environment for running the FES rowing game display with **live sensor data** from NI-DAQ hardware.

## 📁 Contents

- `sensor_launcher.py` - Main entry point
- `sensor_reader.py` - Hardware sensor reader (replaces DataPlayback)
- `game_page.py` - Game display (modified with sensor mode)
- `button.py` - UI components
- Supporting assets: `*.jpg`, `*.wav`, `*.png`

## 🚀 Usage

```bash
cd sensor_game_page
conda run -n fes_coach_app python sensor_launcher.py
```

**Requirements:**
- Windows or Linux (macOS not supported - NI-DAQmx limitation)
- NI-DAQmx drivers installed
- NI-DAQ device "Dev2" connected and configured in NI MAX
- All sensors properly connected to channels ai16, ai18, ai20, ai21, ai22

## 🔌 Hardware Setup

### Sensor Channel Mapping

**Device:** NI-DAQ Dev2

| Channel | Sensor | Notes |
|---------|--------|-------|
| ai16 | Left Foot Force Sensor | Load cell |
| ai18 | Right Foot Force Sensor | Load cell |
| ai20 | Handle Force Sensor | Load cell |
| ai21 | Front Potentiometer | Handle Position |
| ai22 | Back Potentiometer | Seat Position (voltage × 100) |

### Data Reading Process

**How it works:**

1. **SensorReader** (`sensor_reader.py`) connects to NI-DAQ hardware
   - Tests connection on initialization
   - Reads all 5 channels simultaneously at 2000 Hz
   - Converts voltage readings to scaled values
   - Returns data in same format as playback mode

2. **SharedStats** (`game_page.py`) processes sensor data
   - Receives data from SensorReader
   - Applies scaling factors
   - Calculates position, power, distance, stroke rate
   - Updates every 100ms (10 Hz)

3. **GamePage** (`game_page.py`) displays metrics
   - Shows real-time position indicator
   - Displays power, distance, stroke rate
   - Updates UI at 10 Hz refresh rate

## 📊 Data Flow

```
NI-DAQ Hardware (2000 Hz)
    ↓
SensorReader.get_current_data()
    ↓ (scales voltages to ADC-like values)
SharedStats.update_stats()
    ↓ (calculates metrics)
GamePage.on_timer()
    ↓ (updates display)
UI Display (10 Hz)
```

## ⚙️ Data Processing

### 1. Position Information (Seat Position)

**Source:** Back Potentiometer (ai22)

**Processing:**
1. Raw voltage reading from hardware
2. Multiply by 100: `seat_position = voltage × 100`
3. Scale down: `scaled = seat_position / 100.0` → yields 17.0-58.0 range
4. Clamp to calibration range:
   - `seat_min = 17.0` (back position → 0%)
   - `seat_max = 58.0` (front position → 100%)
5. Convert to percentage: `percentage = 100 - ((scaled - 58.0) / (17.0 - 58.0)) * 100`

**Used For:**
- **Seat Position Indicator:** Visual bar (0-100%)
- **Seat Velocity:** Position change / time
- **Stroke Detection:** Peaks/troughs identify drive vs. recovery

### 2. Power Calculation

**Method:** Foot-Based Power (Leg Drive)

**Formula:**
```python
# 1. Get foot forces (scaled from voltages)
left_foot_force = abs(left_foot_voltage * 100 / 100.0)
right_foot_force = abs(right_foot_voltage * 1000 / 1000.0)
total_foot_force = left_foot_force + right_foot_force

# 2. Calculate seat velocity from position changes
seat_velocity = abs(position_change / time_delta)  # m/s

# 3. Calculate instantaneous power
raw_power = total_foot_force × seat_velocity
instantaneous_power = raw_power × 0.15  # Scaling factor

# 4. Rolling average (last 50 samples ≈ 5 seconds)
average_power = mean(last_50_power_values)

# Expected Range: 50-200W (typical rowing machine output)
```

**Why Foot-Based?**
- Legs generate ~60% of total rowing power
- More stable signal than handle force
- Directly correlates with seat motion during drive phase

### 3. Distance Calculation

**Method:** Momentum/Coasting Model (Realistic Boat Physics)

The boat continues moving after power input stops (coasting effect):

```python
# Each update (10 Hz):
# 1. Acceleration from power
if power > 10W:
    velocity_increase = (power / 75.0) × time_delta
    boat_velocity += velocity_increase

# 2. Drag/Resistance (natural slowdown)
boat_velocity *= 0.92  # ~8% velocity loss per update

# 3. Apply limits
boat_velocity = clamp(boat_velocity, 0.0, 6.0)  # Max 6 m/s

# 4. Accumulate distance
total_distance += boat_velocity × time_delta
```

## 🎮 Display Metrics

The game screen displays:
- **Distance** - Calculated using momentum/coasting model
- **Power** - Foot-based calculation (50-200W typical range)
- **Seat Position Indicator** - Visual bar showing 0-100% position
- **Stroke Rate** - Strokes per minute (from seat position cycles)
- **Time Elapsed** - Session duration

## ⚠️ Error Handling

The system includes comprehensive error handling:

1. **Connection Testing:**
   - Tests hardware connection on startup
   - Verifies all 5 channels are accessible
   - Shows detailed error messages if connection fails

2. **Runtime Errors:**
   - Catches and logs sensor reading errors
   - Attempts automatic reconnection
   - Falls back gracefully if hardware disconnects

3. **Platform Detection:**
   - Detects macOS and warns user (NI-DAQmx not supported)
   - Only runs on Windows/Linux

## 🔧 Troubleshooting

### Hardware connection failed
- Check NI-DAQ device is connected via USB/Ethernet
- Verify device name is 'Dev2' in NI MAX
- Install/update NI-DAQmx drivers
- Try running as administrator
- Ensure you're on Windows or Linux (not macOS)

### Power values unrealistic
→ Adjust `POWER_SCALING_FACTOR` in `game_page.py` line 196

### Seat indicator doesn't use full range
→ May need to adjust calibration values `seat_min` and `seat_max` in `sensor_reader.py` (lines 19-20)

### Sensor readings stuck at same value
→ Check sensor wiring and power connections
→ Verify sensors are properly grounded
→ Try physically moving/pressing sensors

## 📝 Technical Notes

### Update Rate
- **Hardware sampling:** 2000 Hz (hardware capability)
- **Game updates:** 10 Hz (every 100ms)
- **UI refresh:** 10 Hz (synced with game updates)

### Sensor Scaling
Hardware provides voltage values (typically -10V to +10V range). The system scales these to match the expected format:
- **Seat Position:** voltage × 100 (then scaled down by 100)
- **Handle Force:** voltage × 100 (then scaled down by 100)
- **Left Foot:** voltage × 100 (then scaled down by 100)
- **Right Foot:** voltage × 1000 (then scaled down by 1000)
- **Handle Position:** voltage × 1000 (then scaled down by 1000)

### Calibration
Default calibration values are based on typical sensor ranges:
- Back position: 17.0 (0%)
- Front position: 58.0 (100%)

These may need adjustment based on actual hardware setup.

## 🔄 Differences from Playback Mode

| Feature | Playback Mode | Sensor Mode |
|---------|--------------|-------------|
| Data Source | .ANC file | Live hardware |
| Timing | File-based | Real-time |
| Pause/Resume | Supported | Not applicable |
| Reset | Supported | Not applicable |
| Error Handling | File errors | Hardware connection errors |
| Calibration | Auto from file | Fixed values |

## 📚 Related Files

- `../real_data_testing/` - Playback testing environment
- `../Coaching App/hardware_test.py` - Hardware testing utility
- `../cursor_context.md` - Project documentation

