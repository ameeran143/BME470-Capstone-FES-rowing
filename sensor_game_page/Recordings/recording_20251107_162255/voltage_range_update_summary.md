# Voltage Range Optimization - Update Summary

## Changes Made

All DAQ voltage range configurations have been updated from the suboptimal `-10V to +10V` range to optimized ranges based on actual sensor measurements.

## Updated Files

1. **sensor_game_page/sensor_recorder.py**
   - Updated `_read_sensor_data()` method

2. **sensor_game_page/sensor_reader.py**
   - Updated `_test_connection()` method
   - Updated `get_current_data()` method

3. **sensor_game_page/game_page.py**
   - Updated hardware sensor reading section

4. **Coaching App/hardware_test.py**
   - Updated `test_sensor_readings()` function

5. **Coaching App/game_page.py**
   - Updated hardware sensor reading section

6. **hardware_testing/hardware_test.py**
   - Updated `read_all_sensors()` function

## New Voltage Ranges

Based on recorded data analysis, the following optimized ranges are now used:

| Channel | Sensor | Old Range | New Range | Improvement |
|---------|--------|-----------|-----------|-------------|
| ai16 | Left Foot Force | -10V to +10V (20V) | 7.0V to 9.5V (2.5V) | **8x better resolution** |
| ai18 | Right Foot Force | -10V to +10V (20V) | 7.0V to 9.0V (2.0V) | **10x better resolution** |
| ai20 | Handle Force | -10V to +10V (20V) | 8.5V to 10.5V (2.0V) | **10x better resolution** |
| ai21 | Handle Position | -10V to +10V (20V) | 8.5V to 11.0V (2.5V) | **8x better resolution** |
| ai22 | Seat Position | -10V to +10V (20V) | 9.0V to 11.0V (2.0V) | **10x better resolution** |

## Benefits

1. **Improved ADC Resolution**: ~8-10x better voltage measurement precision
2. **Reduced Noise**: Better use of ADC dynamic range reduces quantization noise
3. **More Accurate Readings**: Optimized ranges match actual sensor outputs
4. **Safety Margin**: Ranges include 10% margin to accommodate variations

## Expected Impact

- **Voltage readings**: More precise and stable
- **Position calculations**: More accurate seat/handle position detection
- **Force measurements**: Better resolution for force sensors
- **No breaking changes**: All ranges accommodate actual sensor outputs with safety margin

## Testing Recommendations

1. Record new data with optimized ranges
2. Compare voltage precision/noise levels with previous recordings
3. Verify all sensors still read correctly
4. Check that saturation behavior is unchanged (sensor-level saturation at 10.9V should remain)

## Notes

- The capping at 10.9V for seat position is **sensor-level saturation**, not DAQ-related
- These optimized ranges will improve measurement quality but won't eliminate sensor saturation
- If sensor ranges change in the future, update these values accordingly

