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
                    settings = json.load(f)
                    # Ensure hardware settings exist with defaults
                    if "hardware_settings" not in settings:
                        settings["hardware_settings"] = self.get_default_hardware_settings()
                    # Ensure button_push_window_mm exists with default
                    if "button_push_window_mm" not in settings:
                        settings["button_push_window_mm"] = 70
                    return settings
        except:
            pass
        return {
            "map_unlock_interval_minutes": 5,
            "button_push_window_mm": 70,
            "hardware_settings": self.get_default_hardware_settings()
        }
    
    def get_default_hardware_settings(self):
        """Get default hardware settings"""
        return {
            "dev_number": 1,
            "voltage_v": 5.0,
            "left_foot_force_channel": 16,
            "right_foot_force_channel": 18,
            "handle_force_channel": 20,
            "front_potentiometer_channel": 21,
            "back_potentiometer_channel": 22
        }
    
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
    
    def get_button_push_window(self):
        """Get button push window one side in mm"""
        return self.settings.get("button_push_window_mm", 70)
    
    def set_button_push_window(self, mm):
        """Set button push window one side in mm"""
        self.settings["button_push_window_mm"] = float(mm)
        self.save_settings()
    
    def get_hardware_settings(self):
        """Get hardware settings"""
        if "hardware_settings" not in self.settings:
            self.settings["hardware_settings"] = self.get_default_hardware_settings()
        return self.settings["hardware_settings"]
    
    def set_hardware_settings(self, hardware_settings):
        """Set hardware settings"""
        self.settings["hardware_settings"] = hardware_settings
        self.save_settings()
    
    def get_hardware_setting(self, key):
        """Get a specific hardware setting"""
        hardware_settings = self.get_hardware_settings()
        return hardware_settings.get(key, self.get_default_hardware_settings().get(key))
    
    def set_hardware_setting(self, key, value):
        """Set a specific hardware setting"""
        hardware_settings = self.get_hardware_settings()
        hardware_settings[key] = value
        self.set_hardware_settings(hardware_settings)

