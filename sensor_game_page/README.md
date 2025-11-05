# FES Rowing System - Debugging Guide

This folder contains debugging tools and testing environments for validating the FES rowing system with live sensor data from NI-DAQ hardware before deployment in the lab.

## 🎯 Purpose

The `sensor_game_page` folder provides a complete testing environment to:
- Verify hardware connections and sensor readings
- Test the game interface with live sensor data
- Calibrate sensor ranges for individual users
- Record and analyze sensor data during rowing sessions
- Debug issues before lab testing

## 📋 Debugging Workflow

### Step 1: Hardware Connection Testing
**Tool:** `../hardware_testing/hardware_test.py`

**Purpose:** Verify NI-DAQ hardware is connected and all sensors are working.

**Usage:**
```bash
cd ../hardware_testing
python hardware_test.py
```

**What it does:**
- Tests connection to NI-DAQ device "Dev2"
- Reads all 5 sensor channels (ai16, ai18, ai20, ai21, ai22)
- Displays real-time voltage values with min/max tracking
- Identifies stuck sensors or wiring issues

**When to use:** Before starting any testing session, verify hardware is working.

---

### Step 2: Sensor Calibration
**Tool:** `sensor_launcher.py` → Calibration Page

**Purpose:** Define the seat position range (min/max) for each user.

**Usage:**
```bash
cd sensor_game_page
python sensor_launcher.py
# Select "Calibration" from start page
```

**Process:**
1. Enter user information (ID, Age, Height, Weight)
2. Click "Begin Calibration"
3. Move to **most back position** → hold → click "Confirm Back Position"
4. Move to **most forward position** → hold → click "Confirm Front Position"
5. Calibration values are stored in `SharedStats` and persist for the session

**What it saves:**
- `back_max_pos` - Minimum seat position value (0%)
- `front_max_pos` - Maximum seat position value (100%)
- These values are used by the game page for position calculations

**When to use:** First time setup or when switching users.

---

### Step 3: Game Interface Testing
**Tool:** `sensor_launcher.py` → Game Page

**Purpose:** Test the complete game interface with live sensor data.

**Usage:**
```bash
cd sensor_game_page
python sensor_launcher.py
# Select "Automatic Mode" or "Manual Mode" from start page
```

**What it tests:**
- Real-time sensor data reading (10 Hz update rate)
- Position indicator bar (0-100% based on calibration)
- Power calculation (foot-based, 50-200W expected range)
- Distance calculation (momentum/coasting model)
- Stroke rate detection
- UI responsiveness and display updates

**Expected behavior:**
- Position indicator moves smoothly as rower moves
- Power values increase during drive phase
- Distance accumulates during rowing
- Stroke rate updates based on seat position cycles

**When to use:** After calibration, test that all game features work correctly.

---

### Step 4: Data Recording and Analysis
**Tool:** `sensor_recorder.py`

**Purpose:** Record raw sensor data during rowing sessions for analysis and debugging.

**Usage:**
```bash
cd sensor_game_page
python sensor_recorder.py
```

**Process:**
1. Click "Start Recording" → Recording begins (status turns red)
2. Perform rowing exercises → Data recorded at 2000 Hz
3. Click "Stop Recording" → Data saved and plots generated automatically

**Output:**
Creates folder: `Recordings/recording_YYYYMMDD_HHMMSS/`
- `sensor_data.csv` - Raw voltage data (timestamp + 5 channels)
- `sensor_data_overview.png` - Plot visualization (similar to `rowing_data_overview.png`)
- `recording_summary.txt` - Statistics summary

**When to use:**
- Capture data during test sessions
- Debug sensor reading issues
- Analyze stroke patterns
- Validate sensor ranges and behavior

---


## 🔄 Data Flow

```
NI-DAQ Hardware (2000 Hz)
    ↓
SensorReader.get_current_data()
    ↓ (reads raw voltages, scales to game format)
SharedStats.update_stats()
    ↓ (calculates: position, power, distance, stroke rate)
GamePage.on_timer() (10 Hz)
    ↓ (updates display)
UI Display
```

**Key Points:**
- Hardware samples at 2000 Hz
- Game updates at 10 Hz (every 100ms)
- Recording captures at 2000 Hz (full hardware rate)

---


## 📊 Expected Sensor Ranges

Based on data analysis, typical voltage ranges:

| Sensor | Expected Range | Notes |
|--------|---------------|-------|
| Left Foot (ai16) | Variable | Load cell - varies with force |
| Right Foot (ai18) | Variable | Load cell - varies with force |
| Handle Force (ai20) | Variable | Load cell - varies with force |
| Handle Position (ai21) | Variable | Potentiometer - position dependent |
| Seat Position (ai22) | ~0.17V - 0.58V | Potentiometer - converts to 17.0-58.0 |

**Note:** Actual ranges may vary based on hardware setup. Use calibration to set user-specific ranges.

---


## 📝 Testing Checklist

Before lab testing, verify:

- [ ] Hardware connects successfully (`hardware_test.py`)
- [ ] All 5 sensors produce changing values
- [ ] Calibration completed successfully
- [ ] Game page displays position indicator correctly
- [ ] Power values appear reasonable (50-200W during rowing)
- [ ] Distance accumulates during rowing
- [ ] Recording works and generates plots

---

