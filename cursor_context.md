This project aims to create a user interface for a Functional electrical stimulation rowing machine used for spinal cord patient rehabiliation. 

## Coaching App (User Interface) Layout
1. User dashboard
2. Selection screen
3. Game screen

## Game Screen
The game screen is the main screen of the rowing machine. 

## Hardware Sensor Mapping
**Device:** NI-DAQ Dev2

| Channel | Sensor | Notes |
|---------|--------|-------|
| ai0-ai15 | [UNUSED] | - |
| ai16 | Left Foot Force Sensor | - |
| ai17 | [UNUSED] | - |
| ai18 | Right Foot Force Sensor | - |
| ai19 | [UNUSED] | - |
| ai20 | Handle Force Sensor | - |
| ai21 | Front Potentiometer | Handle Position |
| ai22 | Back Potentiometer | Seat Position (converted: voltage × 100) |

## Sensor Data Reading and Processing

### How We Read Sensor Data
**Sampling Rate:** 2000 Hz (from hardware)  
**Game Update Rate:** 10 Hz (every 100ms)

The system reads all 5 active channels simultaneously using NI-DAQmx:
```python
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev2/ai16")  # Left Foot
    task.ai_channels.add_ai_voltage_chan("Dev2/ai18")  # Right Foot
    task.ai_channels.add_ai_voltage_chan("Dev2/ai20")  # Handle Force
    task.ai_channels.add_ai_voltage_chan("Dev2/ai21")  # Handle Position
    task.ai_channels.add_ai_voltage_chan("Dev2/ai22")  # Seat Position
    data = task.read(number_of_samples_per_channel=1)
```

### 1. Position Information (Seat Position)

**Source:** Back Potentiometer (ai22)

**Processing Pipeline:**
1. **Raw ADC value** from Back Potentiometer (typical range: 1700-5800 ADC units)
2. **Scale down:** `scaled = raw_adc / 100.0` → yields 17.0-58.0
3. **Clamp to calibration range** to filter outliers:
   - `seat_min = 17.0` (back position)
   - `seat_max = 58.0` (front position)
4. **Convert to percentage:** `percentage = 100 - ((scaled - 58.0) / (17.0 - 58.0)) * 100`
   - 0% = rower at back (catch position)
   - 100% = rower at front (finish position)

**Used For:**
- **Seat Position Indicator:** Visual bar showing rower's position on the slide
- **Seat Velocity:** `velocity = |position_change / time_delta|` (meters/second)
- **Stroke Detection:** Peaks and troughs identify drive vs. recovery phases

**Key Finding from Data Analysis:**
- The back potentiometer shows clear cyclical patterns during rowing strokes
- Strong correlation with other sensors during drive phase
- Most reliable sensor for stroke phase detection

### 2. Power Calculation

**Method:** Foot-Based Power (Leg Drive)

**Why Foot Forces?**
- Legs generate ~60% of total rowing power
- More stable signal than handle force alone
- Directly correlates with seat motion during drive phase

**Formula:**
```python
# 1. Get foot forces (from load cells LC2 and LC4)
left_foot_force = abs(ai16_value / 100.0)
right_foot_force = abs(ai18_value / 1000.0)
total_foot_force = left_foot_force + right_foot_force

# 2. Calculate seat velocity from position changes
seat_velocity = abs(position_change / time_delta)  # m/s

# 3. Calculate instantaneous power
raw_power = total_foot_force × seat_velocity
instantaneous_power = raw_power × 0.15  # Empirical scaling factor

# 4. Rolling average (last 50 samples ≈ 5 seconds)
average_power = mean(last_50_power_values)

# Expected Range: 50-200W (typical rowing machine output)
```

**Tuning Parameters:**
- `POWER_SCALING_FACTOR = 0.15` - Adjust for realistic wattage values
- Higher value = more watts displayed
- Lower value = less sensitive to force changes

### 3. Distance Calculation

**Method:** Momentum/Coasting Model (Realistic Boat Physics)

The system simulates realistic boat behavior where the boat continues moving (coasting) after power input stops:

```python
# Initialize
boat_velocity = 0.0  # m/s
total_distance = 0.0  # meters

# Each update (10 Hz):
# 1. Acceleration from power
if power > 10W:  # Threshold to reduce noise
    velocity_increase = (power / 75.0) × time_delta
    boat_velocity += velocity_increase

# 2. Drag/Resistance (boat naturally slows down)
boat_velocity *= 0.92  # ~8% velocity loss per update

# 3. Apply limits
boat_velocity = clamp(boat_velocity, 0.0, 6.0)  # Max 6 m/s

# 4. Accumulate distance
total_distance += boat_velocity × time_delta
```

**Tuning Parameters:**
- `BOAT_MASS_FACTOR = 75.0` - Controls acceleration responsiveness (lower = faster)
- `DRAG_COEFFICIENT = 0.92` - Controls coasting duration (higher = longer coast)
- `MAX_VELOCITY = 6.0 m/s` - Elite rower speed limit

### Game Screen Display Metrics
The game screen uses this sensor data to display:
- **Distance** - Calculated using momentum/coasting model with drag
- **Power** - Foot-based calculation (50-200W typical range)
- **Seat Position Indicator** - Visual bar showing 0-100% position
- **Stroke Rate** - Strokes per minute (derived from seat position cycles)
- **Time Elapsed** - Session duration
