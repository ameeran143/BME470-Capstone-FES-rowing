"""
Shared map logic for consistent location and progress calculation
across game screen and dashboard.
"""

class MapLogic:
    """
    Centralized logic for calculating current location and progress
    based on cumulative distance traveled.
    """
    
    # Location milestones (distance in meters to reach each location)
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
    def get_current_location_info(cls, cumulative_distance):
        """
        Calculate current location and progress to next location.
        
        Args:
            cumulative_distance: Total distance traveled in meters (can be > CYCLE_DISTANCE)
        
        Returns:
            dict with keys:
                - current_location: Name of current location
                - current_index: Index of current location (0-4)
                - next_location: Name of next location
                - next_index: Index of next location (0-4)
                - progress_to_next: Progress to next location (0.0 to 1.0)
                - position_in_cycle: Position within current cycle (0 to CYCLE_DISTANCE)
                - distance_to_next: Meters remaining to next location
                - segment_length: Length of current segment in meters
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
            # Normal case: next milestone is after current
            segment_length = next_milestone - current_milestone
        else:
            # Wrap-around case: we're at the last location, next is the first
            segment_length = cls.CYCLE_DISTANCE - current_milestone
        
        # Calculate distance into current segment
        distance_into_segment = position_in_cycle - current_milestone
        if distance_into_segment < 0:
            distance_into_segment += cls.CYCLE_DISTANCE
        
        # Calculate progress as fraction (0.0 to 1.0)
        progress_to_next = min(1.0, distance_into_segment / segment_length) if segment_length > 0 else 0.0
        
        # Calculate distance remaining to next location
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
        """
        Get list of unlocked locations based on cumulative distance.
        Locations stay unlocked permanently once reached.
        
        Args:
            cumulative_distance: Total distance traveled in meters
        
        Returns:
            list of tuples: [(location_name, milestone_distance, is_unlocked), ...]
        """
        unlocked = []
        for location_name, milestone_distance in cls.LOCATION_MILESTONES:
            is_unlocked = cumulative_distance >= milestone_distance
            unlocked.append((location_name, milestone_distance, is_unlocked))
        return unlocked

