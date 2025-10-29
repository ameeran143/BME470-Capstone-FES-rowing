# Real Data Testing Environment

Standalone testing environment for validating the FES rowing game display with recorded sensor data from actual rowing sessions.

## 📁 Contents

- `test_launcher.py` - Main entry point
- `data_playback.py` - .ANC file parser and playback controller
- `game_page.py` - Game display (modified with playback mode)
- `button.py` - UI components
- Supporting assets: `*.jpg`, `*.wav`, `*.png`

## 🚀 Usage

```bash
cd real_data_testing
conda run -n fes_coach_app python test_launcher.py
```

## 📊 Data Source

**File:** `../Data_Analysis/rowing_data/rowing01.ANC`
- **Duration:** 20 seconds
- **Sample Rate:** 2000 Hz
- **Format:** Analog R/C ASCII (16-bit, Bipolar)

## 🔌 Sensor Channel Mapping

### .ANC File Channels → Game Channels
```
.ANC File (7 channels)          →  Game Expected (5 channels)
─────────────────────────────────────────────────────────────
LC1 (Load Cell 1 - Left foot)   →  [Not used]
LC2 (Load Cell 2 - Left foot)   →  ai16 (Left Foot Force)
LC3 (Load Cell 3 - Right foot)  →  [Not used]  
LC4 (Load Cell 4 - Right foot)  →  ai18 (Right Foot Force)
Handle                          →  ai20 (Handle Force)
Front Pot (Potentiometer)       →  ai21 (Handle Position)
Back Pot (Potentiometer)        →  ai22 (Seat Position)
```

**Note:** LC2 and LC4 are the dominant vertical force components. LC1 and LC3 (shear/horizontal forces) are not used in calculations.

## ⚙️ Data Scaling & Calibration

### Raw ADC to Application Values

All raw ADC integer values are scaled down before use:

| Sensor | Raw Range | Scaling | Application Range |
|--------|-----------|---------|-------------------|
| **Seat Position** (Back Pot) | 1700-5800 ADC | ÷ 100 | 17.0-58.0 |
| **Handle Position** (Front Pot) | Variable | ÷ 1000 | Scaled |
| **Handle Force** | Variable | ÷ 100 | Scaled |
| **Left Foot Force** (LC2) | Variable | ÷ 100 | Scaled |
| **Right Foot Force** (LC4) | Variable | ÷ 1000 | Scaled |

### Seat Position Calibration

**Fixed Thresholds** (to filter outliers):
```
Raw ADC:      [1700, 5800]
Scaled:       [17.0, 58.0]
Indicator:    [0%, 100%]

1700 ADC (17.0) → Back position  → 0% (left side of indicator)
5800 ADC (58.0) → Front position → 100% (right side of indicator)
```

**Outlier Filtering:** Values outside this range are clamped to prevent sharp dips/spikes from affecting calculations.

## 📐 Position Determination

### Seat Position (0-100% scale)
```python
# 1. Raw ADC value from Back Pot (index 6 in data)
raw_adc = data['seat_position']

# 2. Scale down
scaled = raw_adc / 100.0

# 3. Clamp to calibration range
if scaled < 17.0: scaled = 17.0
if scaled > 58.0: scaled = 58.0

# 4. Convert to 0-100 percentage
percentage = 100 - ((scaled - 58.0) / (17.0 - 58.0)) * 100

# Result: 0% = back, 100% = front
```

## ⚡ Power Calculation

**Method:** Foot-Based Power (Leg Drive)

```python
# 1. Get foot forces (absolute values from LC2 and LC4)
left_foot_force = abs(LC2_value / 100.0)
right_foot_force = abs(LC4_value / 1000.0)
total_foot_force = left_foot_force + right_foot_force

# 2. Calculate seat velocity
seat_velocity = abs(position_change / time_delta)  # meters/second

# 3. Calculate raw power
raw_power = total_foot_force × seat_velocity

# 4. Apply empirical scaling for realistic watts
POWER_SCALING_FACTOR = 0.15
instantaneous_power = raw_power × 0.15  # Watts

# 5. Rolling average (last 50 samples ~5 seconds)
average_power = mean(last_50_power_values)

# Expected Range: 50-200W (typical rowing machine output)
```

**Why Foot-Based?**
- Legs generate ~60% of rowing power
- More stable signal than handle force
- Directly correlates with seat motion

## 🚤 Distance Calculation

**Method:** Momentum/Coasting Model (Realistic Boat Physics)

```python
# Initialize
boat_velocity = 0.0  # m/s
total_distance = 0.0  # meters

# Each update (10 Hz):

# 1. Acceleration from power
if power > 10W:  # Threshold to reduce noise
    BOAT_MASS_FACTOR = 75.0
    velocity_increase = (power / BOAT_MASS_FACTOR) × time_delta
    boat_velocity += velocity_increase

# 2. Drag/Resistance (boat slows down)
DRAG_COEFFICIENT = 0.92  # ~8% velocity loss per update
boat_velocity *= DRAG_COEFFICIENT

# 3. Velocity limits
if boat_velocity < 0.01: boat_velocity = 0.0      # Stop threshold
if boat_velocity > 6.0: boat_velocity = 6.0       # Max speed cap

# 4. Distance accumulation
distance_increment = boat_velocity × time_delta
total_distance += distance_increment

# Result: Distance continues to increase after rowing stops (coasting)
```

**Key Parameters:**
- `BOAT_MASS_FACTOR = 75.0` - Controls acceleration responsiveness
- `DRAG_COEFFICIENT = 0.92` - Controls coasting duration (higher = longer coast)
- `MAX_VELOCITY = 6.0 m/s` - Elite rower speed limit

## 🎮 Playback Controls

### Available Controls
- **Pause/Play** - Toggle data playback
- **Reset** - Restart from beginning
- **Progress Bar** - Visual indicator of current position in recording

### Playback Timing
- Data: 2000 Hz (0.5ms intervals)
- Game Update: 10 Hz (100ms intervals)
- Playback: Real-time synchronized (20s recording plays in 20s)

## 🔧 Tuning Parameters

If metrics need adjustment, modify these in `game_page.py`:

| Parameter | Current Value | Effect |
|-----------|---------------|--------|
| `POWER_SCALING_FACTOR` | 0.15 | Power magnitude (↑ = more watts) |
| `BOAT_MASS_FACTOR` | 75.0 | Acceleration rate (↓ = faster response) |
| `DRAG_COEFFICIENT` | 0.92 | Coasting duration (↑ = longer coast) |

## 📝 Technical Notes

### Update Rate
The game updates at 10 Hz (every 100ms). Playback interpolates from 2000 Hz data to match this rate.

### Data Flow
```
.ANC File (2000 Hz raw ADC)
    ↓
DataPlayback (parse, scale, interpolate)
    ↓
SharedStats (calculate power, velocity, distance)
    ↓
GamePage (update display at 10 Hz)
```

### Outlier Handling
- **Seat Position:** Clamped to [1700, 5800] ADC range
- Sharp negative dips in raw data are automatically filtered
- Protects velocity and power calculations from noise

## 🐛 Troubleshooting

### Power values unrealistic
→ Adjust `POWER_SCALING_FACTOR` in `game_page.py` line 185

### Boat coasts too long/short
→ Adjust `DRAG_COEFFICIENT` in `game_page.py` line 313

### Seat indicator doesn't use full range
→ Verify calibration thresholds in `data_playback.py` lines 82-83

### Playback timing issues
→ Check console for "Playback paused/resumed" messages
→ Ensure system clock is stable
