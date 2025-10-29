#!/usr/bin/env python3
"""
Data Playback Module for Real Rowing Data Testing
Reads .ANC file and provides sensor data for game simulation
"""

import numpy as np
import time


class DataPlayback:
    def __init__(self, filepath):
        """Initialize playback from .ANC file"""
        self.filepath = filepath
        self.timestamps = None
        self.data = None
        self.channels = []
        self.sample_rate = 2000  # Hz
        self.current_index = 0
        self.start_time = None
        self.is_playing = True
        self.is_paused = False
        
        # Parse the file
        self._parse_anc_file()
        
    def _parse_anc_file(self):
        """Parse the .ANC file format"""
        print("📂 Loading playback data from .ANC file...")
        
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
        
        # Parse header information
        header_info = {}
        data_start = 0
        
        for i, line in enumerate(lines):
            if 'Duration' in line:
                duration = line.split('Duration(Sec.):')[1].split('#')[0].strip()
                header_info['duration'] = float(duration)
            if 'PreciseRate' in line:
                rate = line.split('PreciseRate:')[1].strip()
                header_info['sample_rate'] = float(rate)
                self.sample_rate = float(rate)
            if '#Channels' in line:
                n_channels = line.split('#Channels:')[1].split()[0].strip()
                header_info['n_channels'] = int(n_channels)
            if line.startswith('Name'):
                # Channel names
                channels = line.strip().split('\t')[1:]  # Skip 'Name'
                channels = [ch.strip() for ch in channels if ch.strip()]
                self.channels = channels
                header_info['n_channels'] = len(channels)
                data_start = i + 3  # Skip Name, Rate, Range lines
                break
        
        # Parse data
        data = []
        timestamps = []
        
        for line in lines[data_start:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= header_info['n_channels'] + 1:
                try:
                    timestamps.append(float(parts[0]))
                    values = [int(parts[i]) for i in range(1, header_info['n_channels'] + 1)]
                    data.append(values)
                except ValueError:
                    continue
        
        self.data = np.array(data)
        self.timestamps = np.array(timestamps)
        
        # FIXED CALIBRATION for seat position to avoid outlier issues
        # Based on analysis of Back Pot data - setting hard thresholds
        # Raw ADC range: 1700 (back/start) to 5800 (front/end)
        # These are divided by 100 when used in the game
        self.seat_min = 1700 / 100.0  # 17.0 - Back position (0%)
        self.seat_max = 5800 / 100.0  # 58.0 - Front position (100%)
        
        # For debugging - show what we're filtering
        back_pot_idx = 6  # Back Pot is the 7th channel (index 6)
        seat_positions_raw = self.data[:, back_pot_idx]
        actual_min = np.min(seat_positions_raw)
        actual_max = np.max(seat_positions_raw)
        
        # Count outliers
        outliers_low = np.sum(seat_positions_raw < 1700)
        outliers_high = np.sum(seat_positions_raw > 5800)
        
        print(f"  ✅ Loaded {len(self.data)} samples")
        print(f"  Duration: {self.timestamps[-1]:.2f} seconds")
        print(f"  Channels: {self.channels}")
        print(f"  Sample rate: {self.sample_rate} Hz")
        print(f"  📊 Seat position calibration: {self.seat_min:.1f} to {self.seat_max:.1f} (FIXED)")
        print(f"     Raw data range: {actual_min} to {actual_max}")
        print(f"     Outliers filtered: {outliers_low} low, {outliers_high} high")
        
    def start(self):
        """Start playback"""
        self.start_time = time.time()
        self.is_playing = True
        self.is_paused = False
        print("▶️  Playback started")
        
    def pause(self):
        """Pause playback"""
        self.is_paused = True
        print("⏸️  Playback paused")
        
    def resume(self):
        """Resume playback"""
        if self.is_paused:
            # Adjust start time to account for pause duration
            elapsed_data_time = self.timestamps[self.current_index]
            self.start_time = time.time() - elapsed_data_time
            self.is_paused = False
            print("▶️  Playback resumed")
    
    def toggle_pause(self):
        """Toggle between pause and play"""
        if self.is_paused:
            self.resume()
        else:
            self.pause()
    
    def reset(self):
        """Reset playback to beginning"""
        self.current_index = 0
        self.start_time = time.time()
        self.is_paused = False
        print("⏮️  Playback reset")
        
    def get_current_data(self):
        """
        Get sensor data at current playback time
        Returns data mapped to expected 5 channels:
        - ai16 (Left Foot) <- LC2
        - ai18 (Right Foot) <- LC4  
        - ai20 (Handle Force) <- Handle
        - ai21 (Handle Position) <- Front Pot
        - ai22 (Seat Position) <- Back Pot
        """
        if self.is_paused:
            # Return last valid data if paused
            if self.current_index < len(self.data):
                return self._map_channels(self.current_index)
            else:
                return None
        
        if not self.is_playing or self.start_time is None:
            return None
        
        # Calculate current time in the recording
        elapsed_real_time = time.time() - self.start_time
        
        # Find corresponding data index
        # Binary search for efficiency
        target_index = np.searchsorted(self.timestamps, elapsed_real_time)
        
        if target_index >= len(self.data):
            # End of data reached
            print("⏹️  Playback complete")
            self.is_playing = False
            return None
        
        self.current_index = target_index
        return self._map_channels(target_index)
    
    def _map_channels(self, index):
        """
        Map 7-channel .ANC data to 5-channel game format
        .ANC channels: LC1, LC2, LC3, LC4, Handle, Front Pot, Back Pot
        Game expects: ai16, ai18, ai20, ai21, ai22
        
        For now, using raw ADC values directly (no voltage conversion)
        """
        row = self.data[index]
        
        # Channel mapping based on analysis:
        # LC1=row[0], LC2=row[1], LC3=row[2], LC4=row[3], 
        # Handle=row[4], Front_Pot=row[5], Back_Pot=row[6]
        
        mapped_data = {
            'left_foot': row[1],      # LC2 (major axis, most signal)
            'right_foot': row[3],     # LC4 (major axis, most signal)
            'handle_force': row[4],   # Handle
            'handle_position': row[5], # Front Pot
            'seat_position': row[6],   # Back Pot
            'timestamp': self.timestamps[index],
            'index': index,
            'total_samples': len(self.data)
        }
        
        return mapped_data
    
    def get_progress(self):
        """Get playback progress information"""
        if len(self.data) == 0:
            return 0.0, 0.0, 0.0
        
        current_time = self.timestamps[self.current_index] if self.current_index < len(self.timestamps) else self.timestamps[-1]
        total_time = self.timestamps[-1]
        progress_percent = (self.current_index / len(self.data)) * 100
        
        return current_time, total_time, progress_percent
    
    def seek(self, percent):
        """Seek to a specific position in the data (0-100%)"""
        target_index = int((percent / 100.0) * len(self.data))
        target_index = max(0, min(target_index, len(self.data) - 1))
        
        self.current_index = target_index
        
        # Adjust start time to maintain sync
        if not self.is_paused:
            elapsed_data_time = self.timestamps[self.current_index]
            self.start_time = time.time() - elapsed_data_time
        
        print(f"⏩ Seeked to {percent:.1f}%")


if __name__ == "__main__":
    # Test the playback module
    filepath = "../Data_Analysis/rowing_data/rowing01.ANC"
    
    playback = DataPlayback(filepath)
    playback.start()
    
    print("\n🧪 Testing data playback for 3 seconds...")
    test_start = time.time()
    
    while time.time() - test_start < 3.0:
        data = playback.get_current_data()
        if data:
            print(f"Time: {data['timestamp']:.3f}s | Seat: {data['seat_position']} | Handle Force: {data['handle_force']}")
        time.sleep(0.1)  # 10Hz like the game
    
    print("\n✅ Playback test complete!")

