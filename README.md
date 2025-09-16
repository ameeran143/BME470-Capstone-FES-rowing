# FES-Rowing Coaching Application

A visual interface for Functional Electrical Stimulation (FES) rowing training that provides real-time feedback and performance tracking to help users optimize their FES timing during rowing exercises.

## Overview

This coaching application is designed to help users learn the optimal timing for FES activation during rowing strokes. It provides a gamified training experience with visual cues, real-time performance metrics, and comprehensive data logging for rehabilitation and performance enhancement.

## Features

### 🎯 Core Functionality
- **Real-time FES timing feedback** with visual color-coded cues
- **Performance tracking** with stroke rate, power output, and scoring
- **User calibration system** for personalized training zones
- **Comprehensive data logging** for progress analysis
- **Hardware integration** with National Instruments DAQ systems

### 🖥️ User Interface
- **Three-page architecture**: Start, Calibration, and Training pages
- **Visual rowing machine representation** with animated seat position
- **Real-time statistics display** in organized grid format
- **Loading bar indicators** for timing precision
- **Audio feedback** for success/failure (optional)

## Architecture

### Application Structure
```
main.py                 # Entry point and main window management
├── start_page.py       # Mode selection and user entry
├── calib_page.py       # User calibration and setup
├── game_page.py        # Main training interface
└── button.py           # Custom UI components
```

### Key Components

#### 1. **StartPage**
- Manual/Auto mode selection
- Navigation to calibration
- Session initialization

#### 2. **CalibPage** 
- User demographics collection (ID, age, height, weight)
- Seat position calibration (front/back limits)
- Personalized FES zone calculation

#### 3. **GamePage**
- Real-time training interface
- Performance statistics display
- FES button visualization
- Seat position animation
- Data logging controls

#### 4. **SharedStats**
- Centralized state management
- Sensor data processing
- Performance calculations
- File I/O operations

## Hardware Integration

### National Instruments DAQ Setup
The application interfaces with NI-DAQ hardware using the `nidaqmx` library:

```python
# 8-Channel Configuration (Dev4/ai0:7)
Channel 0: Switch press (0V=pressed, 5V=released)
Channel 2: Left foot force sensor
Channel 4: Right foot force sensor  
Channel 5: Handle force sensor
Channel 6: Handle position sensor
Channel 7: Seat position sensor (primary)
```

### Sensor Data Processing
- **Raw Data Collection**: 100ms sampling interval
- **Position Conversion**: Raw sensor values → 0-100% scale
- **Power Calculation**: Handle force × position change / time
- **Stroke Detection**: Based on seat position cycles

## FES Training Logic

### Core Concept
Users learn to activate FES at the optimal point in their rowing stroke:

1. **FES Activation Zone**: `96.5 ± 93.3mm` from front seat position
2. **Visual Feedback**:
   - 🟠 **Orange**: Approaching FES zone (ready state)
   - 🟢 **Green**: In FES zone (activate now)
3. **Scoring System**: Points for correct timing, penalties for misses

### Training Workflow
1. **Calibration**: Record personal seat position limits
2. **Training**: Row while following visual timing cues
3. **Feedback**: Immediate success/failure indication
4. **Analysis**: Review performance metrics and progress

## Installation & Setup

### Prerequisites
- Python 3.11+
- Anaconda/Miniconda (recommended)
- National Instruments DAQmx drivers (for hardware)

### Environment Setup
```bash
# Create conda environment from provided file
conda env create -f Coaching\ App/fes_coach_app.yml

# Activate environment
conda activate fes_coach_app
```

### Key Dependencies
- `wxpython`: GUI framework
- `nidaqmx-python`: NI hardware interface
- `numpy`: Numerical computations
- `pillow`: Image processing
- `pandas`: Data handling (via csv module)

## Usage

### Running the Application
```bash
cd "Coaching App"
python main.py
```

### Training Session Steps

1. **Start**: Select "Manual Mode" or "Calibration"
2. **Calibration** (first-time users):
   - Enter personal information
   - Follow on-screen positioning instructions
   - System records seat position limits
3. **Training**:
   - Begin rowing motion
   - Watch FES button color changes
   - Press FES button when green (in optimal zone)
   - Monitor real-time performance statistics
4. **Data Review**: Check `Training_Data/` folder for session logs

## Data Output

### Performance Metrics
- **Time Elapsed**: Session duration (minutes)
- **Stroke Rate**: Strokes per minute
- **Average Power**: Calculated from force and position
- **Score**: Correct FES activations
- **Misses**: Incorrect timing attempts

### Data Files
Training sessions are automatically saved as CSV files:
```
Training_Data/[UserID]_rowing_stats_[YYYYMMDD]_[HHMMSS].csv
```

### Data Schema
```csv
Time Elapsed (min), Stroke Rate, Average Power, Score, Misses, 
Handle Force, Handle Position, Raw Seat Position, 
Converted Seat Position, Left Foot Force, Right Foot Force
```

## Configuration

### Calibration Parameters
- **Front Max Position**: Forward-most seat position
- **Back Max Position**: Rearward-most seat position  
- **FES Active Position**: `front_max_pos - 96.5mm`
- **Tolerance Zone**: `±93.3mm` around FES position

### Timing Settings
- **Update Frequency**: 100ms (10 Hz)
- **Data Sampling**: Real-time sensor polling
- **Response Latency**: <100ms visual feedback

## Development & Customization

### Key Classes
- `RowingApp`: Main application controller
- `MainFrame`: Window management and page switching
- `SharedStats`: Data model and business logic
- `FESButton`: Visual feedback component
- `SeatPos`: Rowing machine visualization

### Extending Functionality
- **Custom Scoring**: Modify `update_stats()` in SharedStats
- **New Sensors**: Add channels in NI-DAQ configuration
- **UI Themes**: Customize colors in component constructors
- **Audio Cues**: Uncomment pygame sound integration

## Troubleshooting

### Common Issues
1. **Hardware Not Detected**: Verify NI-DAQ drivers and device connection
2. **Permission Errors**: Run as administrator (Windows) or check device permissions
3. **Performance Lag**: Reduce timer frequency or optimize sensor polling
4. **Data Not Saving**: Check write permissions in Training_Data directory

### Debug Mode
Enable debug output by uncommenting print statements in `on_timer()` method.

## Research Applications

This application is designed for:
- **Rehabilitation Research**: FES timing optimization studies
- **Performance Analysis**: Rowing technique improvement
- **Motor Learning**: Skill acquisition in FES-assisted movement
- **Biomechanics Research**: Movement pattern analysis

## Contributing

When contributing to this codebase:
1. Maintain the existing wxPython architecture
2. Preserve data logging compatibility
3. Test with both simulation and hardware modes
4. Document any new sensor integrations

## License

[Add appropriate license information]

## Contact

[Add contact information for project maintainers]

---

**Note**: This application includes simulation modes for development and testing without requiring physical hardware setup. 