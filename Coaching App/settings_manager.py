import os
import json

class SettingsManager:
    """Manages application-wide settings"""
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(script_dir, "app_settings.json")
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    return json.load(f)
        except:
            pass
        return {"map_unlock_interval_minutes": 5}
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def get_map_interval(self):
        """Get map unlock interval in minutes"""
        return self.settings.get("map_unlock_interval_minutes", 5)
        
    def set_map_interval(self, minutes):
        """Set map unlock interval in minutes"""
        self.settings["map_unlock_interval_minutes"] = int(minutes)
        self.save_settings()

