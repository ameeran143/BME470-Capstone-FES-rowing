# FES-Rowing Coaching App

## Overview

The game page operates in two modes:
1. **CSV Playback Mode** - Replays recorded sensor data
2. **Hardware Sensor Mode** - Reads live sensors (if enabled)

**Note:** Simulation mode has been removed. The app only works with real sensor data or CSV playback.

## CSV Data

**File Location:** `../Test_Recordings/hikaru/sensor_data.csv`

**Format:**
- Columns: `Time (s)`, `Left Foot (ai16)`, `Right Foot (ai18)`, `Handle Force (ai20)`, `Handle Position (ai21)`, `Seat Position (ai22)`
- Units: Voltages (0-10V) except Time
- Processing: Trims first/last 5 seconds, estimates sampling rate, downsamples to ~10 Hz

## Value Calculations

### Handle Force (N)
```
Force = (voltage / (2.0 × 5.0)) × 250.0 × 9.81
```
Calibration: 2.0 mV/V sensitivity, 5V excitation, 250kg capacity

### Power (W)
```
Power = (avg_force × handle_displacement) / time_delta
```
- `avg_force = (force[t] + force[t-1]) / 2`
- `handle_displacement = |handle_pos[t] - handle_pos[t-1]|` (mm)
- Average Power: Running average of all power values

### Stroke Rate (strokes/min)
```
Stroke Rate = 60 / stroke_duration
```
Detected when `seat_position >= front_max_pos`

### Seat Position
- **Raw → 0-100 scale:**
  ```
  converted = 100 - (raw_pos - front_max_pos) / (back_max_pos - front_max_pos) × 100
  ```
- **CSV Processing:**
  - 10 Hz Butterworth low-pass filter
  - Voltage → mm: `mm = voltage × (2032.0 / 10.0)`
  - Shifted to start at 0mm

### Distance (meters)
```
distance_increment = (power / 120) × time_delta
```
Only counts if power > 10W

### Accuracy (%)
```
Accuracy = (score / (score + misses)) × 100
```

## Data Flow

**CSV Playback:**
1. Load CSV → filter → convert units → pre-compute power
2. Each update: read next sample → append to lists → calculate metrics
3. When CSV ends → playback stops (no fallback)

**Hardware:**
- Reads 5 channels from NI-DAQ (Dev2/ai16-ai22)
- Converts voltages → physical units
- Calculates metrics same as CSV mode

