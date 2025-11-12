# Calibration Range Mismatch Analysis

## Summary

Yes, the calibration values (`min_val`/`max_val`) **could be affecting how the data is being read**, but NOT in the way that causes capping. Instead, they're reducing measurement resolution and accuracy.

## The Problem

### Current DAQ Configuration
```python
task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=-10.0, max_val=10.0)
```
- Configured for: **-10V to +10V** (20V total range)
- Actual sensor output: **9.3V to 10.9V** (1.6V range, all positive)

### Why This Matters

1. **Wasted ADC Resolution**
   - The DAQ distributes its ADC bits across the configured 20V range
   - Your signal only uses 1.6V (8% of the range)
   - Result: You're losing ~3 bits of resolution (from 16-bit to effectively ~13-bit)

2. **Reduced Measurement Precision**
   - With 20V range: ~0.305mV per bit
   - With optimized 2V range: ~0.031mV per bit (10x better!)

3. **Potential Internal Scaling**
   - The DAQ may apply internal calibration/scaling based on the configured range
   - This could introduce small systematic errors

## Impact on Your Data

### What It's NOT Causing:
- ❌ **NOT causing the capping at 10.9V** - that's sensor saturation
- ❌ **NOT clipping values** - DAQ can read beyond configured range

### What It IS Causing:
- ⚠️ **Reduced measurement precision** - voltage readings may have more noise/uncertainty
- ⚠️ **Suboptimal use of ADC** - wasting resolution on unused voltage range
- ⚠️ **Potential small systematic errors** - if DAQ applies internal scaling

## Solution

### Recommended DAQ Configuration

Update all sensor channels to match their actual ranges:

```python
# Seat Position (ai22) - Current range: 9.3V to 10.9V
task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=8.0, max_val=12.0)
# Or tighter for maximum resolution:
task.ai_channels.add_ai_voltage_chan("Dev2/ai22", min_val=9.0, max_val=11.0)

# Other channels should also be optimized based on their actual ranges
# Check your data to determine optimal ranges for each:
# - Left Foot Force (ai16): ~7.3V to 9.0V
# - Right Foot Force (ai18): ~7.2V to 8.7V  
# - Handle Force (ai20): ~8.9V to 10.2V
# - Handle Position (ai21): ~9.0V to 10.9V
```

### Files to Update

1. `sensor_recorder.py` - `_read_sensor_data()` method (lines 92-96)
2. `sensor_reader.py` - `get_current_data()` method (lines 120-124)
3. `game_page.py` - Any direct DAQ reads (if present)
4. `hardware_test.py` - Test functions

## Testing the Fix

After updating the ranges:

1. Record new data with optimized ranges
2. Compare voltage precision/noise levels
3. Verify readings are still accurate
4. Check if saturation behavior changes (it shouldn't - that's sensor-level)

## Conclusion

The calibration range mismatch is a **real issue** that affects measurement quality, but it's **not the cause of the capping**. The 10.9V saturation is definitely sensor-level saturation. However, optimizing the DAQ ranges will improve your measurement precision and make better use of the ADC's capabilities.

