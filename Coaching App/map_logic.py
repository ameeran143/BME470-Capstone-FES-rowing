"""
Shared map logic for consistent location and progress calculation
across game screen and dashboard.
"""

class MapLogic:
    """
    Centralized logic for calculating current location and progress.
    Originally based on distance, now supports time-based switching.
    """
    
    # Location names in order
    LOCATION_NAMES = [
        "Hawaii",
        "Antarctica",
        "Amazon",
        "Japan",
        "Australia"
    ]
    
    # Legacy distance milestones (can keep for reference or fallback)
    LOCATION_MILESTONES = [
        ("Hawaii", 0),
        ("Antarctica", 20),
        ("Amazon", 40),
        ("Japan", 60),
        ("Australia", 80),
    ]
    
    LOCATION_INTERVAL = 20.0  # Distance between locations in meters
    CYCLE_DISTANCE = LOCATION_INTERVAL * len(LOCATION_MILESTONES)  # Total distance per cycle (100m)
    
    @classmethod
    def get_current_location_info_by_time(cls, cumulative_time_seconds, interval_minutes):
        """
        Calculate current location and progress based on cumulative time.
        
        Args:
            cumulative_time_seconds: Total time rowed in seconds
            interval_minutes: Minutes required to unlock next map
            
        Returns:
            dict with keys for location info
        """
        interval_seconds = interval_minutes * 60
        if interval_seconds <= 0:
            interval_seconds = 300 # Default 5 min to avoid div by zero
            
        # Total cycle time (all maps)
        cycle_seconds = interval_seconds * len(cls.LOCATION_NAMES)
        
        # Position in current cycle
        position_in_cycle = cumulative_time_seconds % cycle_seconds
        
        # Current index
        current_index = int(position_in_cycle // interval_seconds)
        current_index = min(current_index, len(cls.LOCATION_NAMES) - 1)
        
        current_location_name = cls.LOCATION_NAMES[current_index]
        next_index = (current_index + 1) % len(cls.LOCATION_NAMES)
        next_location_name = cls.LOCATION_NAMES[next_index]
        
        # Distance into current segment (time based)
        time_into_segment = position_in_cycle - (current_index * interval_seconds)
        
        # Progress (0.0 to 1.0)
        progress_to_next = min(1.0, time_into_segment / interval_seconds)
        
        return {
            'current_location': current_location_name,
            'current_index': current_index,
            'next_location': next_location_name,
            'next_index': next_index,
            'progress_to_next': progress_to_next,
            # Legacy/Compat keys (mapped to time values or dummy distance)
            'position_in_cycle': position_in_cycle, 
            'segment_length': interval_seconds,
            'distance_into_segment': time_into_segment,
            'distance_to_next': interval_seconds - time_into_segment,
        }

    @classmethod
    def get_unlocked_locations_by_time(cls, cumulative_time_seconds, interval_minutes):
        """
        Get list of unlocked locations based on cumulative time.
        
        Args:
            cumulative_time_seconds: Total time rowed in seconds
            interval_minutes: Minutes per map
            
        Returns:
            list of tuples: [(location_name, milestone_seconds, is_unlocked), ...]
        """
        interval_seconds = interval_minutes * 60
        if interval_seconds <= 0: interval_seconds = 300
            
        unlocked = []
        for i, location_name in enumerate(cls.LOCATION_NAMES):
            milestone_seconds = i * interval_seconds
            # First map (Hawaii) is always unlocked (0 seconds)
            # Others unlock when cumulative time >= milestone
            is_unlocked = cumulative_time_seconds >= milestone_seconds
            unlocked.append((location_name, milestone_seconds, is_unlocked))
            
        return unlocked

    @classmethod
    def get_current_location_info(cls, cumulative_distance):
        """
        Legacy method for distance-based calculation.
        """
        # Calculate position within the current cycle (0 to CYCLE_DISTANCE)
        position_in_cycle = cumulative_distance % cls.CYCLE_DISTANCE if cls.CYCLE_DISTANCE > 0 else 0.0
        
        # Find current location index
        current_index = 0
        for i, (_, milestone_distance) in enumerate(cls.LOCATION_MILESTONES):
            if position_in_cycle >= milestone_distance:
                current_index = i
            else:
                break
        
        # Get current and next location names
        current_location_name = cls.LOCATION_MILESTONES[current_index][0]
        next_index = (current_index + 1) % len(cls.LOCATION_MILESTONES)
        next_location_name = cls.LOCATION_MILESTONES[next_index][0]
        
        # Calculate segment length and progress
        current_milestone = cls.LOCATION_MILESTONES[current_index][1]
        next_milestone = cls.LOCATION_MILESTONES[next_index][1]
        
        if next_milestone > current_milestone:
            segment_length = next_milestone - current_milestone
        else:
            segment_length = cls.CYCLE_DISTANCE - current_milestone
        
        distance_into_segment = position_in_cycle - current_milestone
        if distance_into_segment < 0:
            distance_into_segment += cls.CYCLE_DISTANCE
        
        progress_to_next = min(1.0, distance_into_segment / segment_length) if segment_length > 0 else 0.0
        
        distance_to_next = segment_length - distance_into_segment
        
        return {
            'current_location': current_location_name,
            'current_index': current_index,
            'next_location': next_location_name,
            'next_index': next_index,
            'progress_to_next': progress_to_next,
            'position_in_cycle': position_in_cycle,
            'distance_into_segment': distance_into_segment,
            'distance_to_next': distance_to_next,
            'segment_length': segment_length,
            'cumulative_distance': cumulative_distance,
        }
    
    @classmethod
    def get_unlocked_locations(cls, cumulative_distance):
        """Legacy distance-based unlock"""
        unlocked = []
        for location_name, milestone_distance in cls.LOCATION_MILESTONES:
            is_unlocked = cumulative_distance >= milestone_distance
            unlocked.append((location_name, milestone_distance, is_unlocked))
        return unlocked
