# Seat Position (ai22) Voltage Reading Analysis

## Summary
Analysis of how seat position voltages are being read from Dev2/ai22 and whether they're being capped.

## How Voltages Are Being Read

### Code Implementation
The voltage reading is performed in `sensor_recorder.py` using the `nidaqmx` library:

```python
task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=-10.0, max_val=10.0)
data = task.read(number_of_samples_per_channel=1)
seat_position_voltage = data[4][0] if isinstance(data[4], list) else data[4]
```

### Key Points:
1. **Direct Hardware Reading**: The code reads raw voltage values directly from the NI-DAQ hardware channel `Dev2/ai22`
2. **No Software Scaling**: The recorded values are the exact voltages returned by the DAQ hardware
3. **No Post-Processing**: The values are written directly to CSV without any modification

## Voltage Range Configuration

### DAQ Configuration
- **Configured Range**: `min_val=-10.0V, max_val=10.0V`
- **Purpose**: These parameters tell the DAQ what voltage range to expect for optimal ADC resolution and calibration
- **NOT a Hard Limit**: The `min_val` and `max_val` parameters are **calibration/optimization settings**, not hard clipping limits

### Actual Measured Range
- **Minimum**: 9.333 V
- **Maximum**: 10.905 V
- **Mean**: 10.478 V
- **Std Dev**: 0.531 V

## Evidence of Capping/Saturation

### Strong Evidence of Upper Limit Saturation:
1. **51.3% of samples** (356 out of 694) are at exactly **10.904626 V**
2. **No values exceed 10.905 V** - this appears to be a hard upper limit
3. The maximum value (10.905 V) **exceeds** the configured `max_val=10.0V`, confirming the DAQ doesn't clip at 10V

### Lower Limit Analysis:
- Only **0.3% of samples** (2 out of 694) are at the minimum (9.333 V)
- This suggests the sensor rarely reaches its lower limit during this recording

### Distribution Pattern:
```
Voltage Range      | Count | Percentage
----------------------------------------
9.30 - 10.80 V    |   337 |  48.6%  (distributed values)
10.90 - 11.00 V    |   357 |  51.4%  (saturated at max)
```

## Conclusion: Where is the Capping Happening?

### ✅ Sensor-Level Saturation (Most Likely)
The capping is occurring at the **sensor/potentiometer level**, NOT in the DAQ or software:

1. **The sensor itself** appears to have a physical/electrical limit at ~10.9V
2. When the seat reaches its forward-most position, the potentiometer saturates
3. The DAQ correctly reads whatever voltage the sensor outputs (even if >10V)

### Why Not DAQ Capping?
- Values exceed the configured `max_val=10.0V` (max is 10.905V)
- If the DAQ were clipping, all values would be ≤10.0V
- The DAQ's `min_val/max_val` are optimization parameters, not hard limits

### Why Not Software Capping?
- The code reads raw voltages directly without any clamping
- No `min()` or `max()` functions applied to the voltage values
- Values are written directly to CSV as received from hardware

## Recommendations

1. **Verify Sensor Range**: Check the potentiometer specifications - it may be designed for 0-10V but can output slightly higher
2. **Check Wiring**: Ensure the potentiometer is wired correctly and not hitting a physical stop
3. **Consider Scaling**: If the sensor range is 9.3-10.9V, you may want to map this to 0-100% position
4. **Monitor Saturation**: The fact that 51% of samples are at max suggests the seat spends significant time fully forward - this may be expected behavior

## Technical Details

### DAQ Voltage Range Parameters
- `min_val` and `max_val` in NI-DAQmx are used for:
  - Optimizing ADC resolution within the expected range
  - Calibration and scaling calculations
  - **NOT** for hard clipping/saturation
  
- The DAQ can read voltages outside this range, but with potentially reduced accuracy
- In this case, readings up to 10.905V are successfully captured despite `max_val=10.0V`

### ⚠️ **CALIBRATION RANGE MISMATCH ISSUE**

**Current Configuration:**
- DAQ configured: `min_val=-10.0V, max_val=10.0V` (20V total range)
- Actual sensor output: 9.3V to 10.9V (1.6V total range)

**Problem:**
The DAQ is configured for a ±10V range, but the sensor only outputs positive voltages in a narrow 1.6V range (9.3-10.9V). This mismatch can affect:

1. **ADC Resolution**: The DAQ allocates its ADC bits across the full 20V range, but only ~8% of that range is actually used
   - Example: If DAQ has 16-bit ADC over 20V range = 0.305mV per bit
   - But signal only uses 1.6V = effectively ~13 bits of resolution instead of 16
   
2. **Measurement Accuracy**: Values near the edges of the configured range may have reduced accuracy

3. **Potential Scaling Issues**: The DAQ may apply internal scaling based on the configured range, which could introduce small errors

**Recommendation:**
Update the DAQ configuration to match the actual sensor range:
```python
# Current (suboptimal):
task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=-10.0, max_val=10.0)

# Recommended:
task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=8.0, max_val=12.0)
# Or even tighter for maximum resolution:
task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=9.0, max_val=11.0)
```

**Note:** This range mismatch is **NOT causing the capping** at 10.9V - that's sensor saturation. However, optimizing the range will improve measurement resolution and accuracy.

### Sample Rate Note
- Expected: 2000 Hz
- Actual: ~38.3 Hz (694 samples in 18.13 seconds)
- This suggests the recording loop is not achieving the target rate, but doesn't affect voltage accuracy

