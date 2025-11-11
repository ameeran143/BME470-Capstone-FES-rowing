# Impact of Wrong min_val/max_val on Sensor Readings

## Short Answer

**Yes, wrong min/max values CAN mess up sensor readings**, but it depends on HOW they're wrong:

## Scenarios

### 1. Range Too Wide (e.g., -10V to +10V when sensor outputs 7-9V)

**Impact:**
- ✅ **Readings still work** - DAQ can read the values
- ⚠️ **Reduced resolution** - ADC bits spread over wider range
- ⚠️ **Less precise measurements** - Each bit represents larger voltage step
- ⚠️ **More quantization noise** - Lower signal-to-noise ratio

**Example:**
- With 16-bit ADC over 20V range: ~0.305mV per bit
- With 16-bit ADC over 2V range: ~0.031mV per bit (10x better!)

**Result:** Readings are **functional but less accurate**

### 2. Range Too Narrow (e.g., 9V to 11V when sensor outputs 7-9V)

**Impact:**
- ⚠️ **Values below min_val** - May still read but with reduced accuracy
- ⚠️ **Potential clipping** - DAQ may clamp values at configured limits
- ⚠️ **Measurement errors** - Values outside range may be inaccurate
- ❌ **Possible errors** - Some DAQ devices may error on out-of-range values

**Example:**
- If sensor outputs 7V but range is 9-11V
- DAQ might read it as 9V (clamped) or return inaccurate value

**Result:** Readings may be **clipped or inaccurate**

### 3. Range Completely Wrong (e.g., Negative range when sensor is positive)

**Impact:**
- ⚠️ **Still reads** - DAQ can handle it
- ⚠️ **Poor optimization** - ADC not optimized for actual signal
- ⚠️ **Reduced accuracy** - Similar to "too wide" scenario

**Example:**
- Sensor outputs 9-11V (all positive)
- Configured as -10V to +10V
- Works but wastes resolution on negative range

**Result:** Readings work but **suboptimal**

## What Actually Happens in NI-DAQmx

### The `min_val` and `max_val` parameters:

1. **Optimize ADC resolution** - Tell DAQ how to allocate bits
2. **Enable auto-scaling** - DAQ may apply internal scaling
3. **NOT hard limits** - DAQ can still read outside range (as we saw with 10.9V > 10V)
4. **May affect accuracy** - Values outside range may have reduced precision

### Your Current Configuration:

Looking at your code:
```python
task.ai_channels.add_ai_voltage_chan("Dev2/ai16", min_val=7.0, max_val=9.5)   # Left Foot Force
task.ai_channels.add_ai_voltage_chan("Dev2/ai18", min_val=7.0, max_val=9.0)   # Right Foot Force
task.ai_channels.add_ai_voltage_chan("Dev2/ai20", min_val=8.5, max_val=10.5)  # Handle Force
task.ai_channels.add_ai_voltage_chan("Dev2/ai21", min_val=8.5, max_val=11.0)  # Handle Position
task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=-10.0, max_val=10.0)  # Seat Position
```

**Potential Issues:**

1. **ai22 (Seat Position)** - Range is -10V to +10V, but sensor outputs 9.3-10.9V
   - ✅ Will still read correctly
   - ⚠️ Losing resolution (20V range for ~1.6V signal)
   - ⚠️ Wasting ADC bits on unused negative range

2. **Other channels** - Ranges match actual outputs well
   - ✅ Should work optimally

## Best Practices

### ✅ DO:
- Set range to match actual sensor output (with ~10-20% margin)
- Use positive ranges for positive-only sensors
- Test with actual hardware to verify ranges

### ❌ DON'T:
- Use unnecessarily wide ranges (wastes resolution)
- Use ranges that don't include actual sensor output
- Set ranges based on assumptions without testing

## Testing Wrong Ranges

If you want to test what happens with wrong ranges:

1. **Too wide:** Set ai16 to -10V to +10V (currently 7-9.5V)
   - Should still read, but less precise
   
2. **Too narrow:** Set ai16 to 8.5V to 9.0V (currently 7-9.5V)
   - May clip values below 8.5V
   - May return inaccurate readings

3. **Completely wrong:** Set ai16 to -5V to -1V (sensor outputs positive)
   - May still read but with poor accuracy
   - Values might be clamped or scaled incorrectly

## Conclusion

**Wrong min/max values won't break readings**, but they will:
- Reduce measurement precision (if too wide)
- Cause clipping/errors (if too narrow)
- Waste ADC resolution (if mismatched)

**Your current config is mostly good**, except ai22 which uses a wider range than needed. The readings will work, but you're not getting optimal precision for the seat position sensor.

