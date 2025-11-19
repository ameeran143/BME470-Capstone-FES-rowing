# session summary page
import wx
from button import CustomButton

class SessionSummaryPage(wx.Panel):
    def __init__(self, parent, summary_data):
        super(SessionSummaryPage, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(248, 249, 250))  # Light gray background matching game screen
        self.summary_data = summary_data
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddStretchSpacer()
        
        # Title: "Great Job, [Name]"
        user_name = summary_data.get("user_name", "User")
        title_text = f"Great Job, {user_name}!"
        title = wx.StaticText(self, label=title_text)
        title_font = wx.Font(72, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        main_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 40)
        
        main_sizer.AddSpacer(60)
        
        # Session Summary label
        summary_label = wx.StaticText(self, label="Session Summary")
        summary_label_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        summary_label.SetFont(summary_label_font)
        summary_label.SetForegroundColour(wx.Colour(128, 128, 128))
        main_sizer.Add(summary_label, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        main_sizer.AddSpacer(40)
        
        # Metrics panel (similar to ModernStatsDisplay from game screen)
        self.metrics_panel = self.create_metrics_panel()
        main_sizer.Add(self.metrics_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 80)
        
        main_sizer.AddStretchSpacer()
        
        # Exit button (bottom-right)
        button_container = wx.BoxSizer(wx.HORIZONTAL)
        button_container.AddStretchSpacer()
        
        self.exit_button = CustomButton(self, label="\nExit\n", size=(220, 70), font=30, handler=self.on_exit)
        button_container.Add(self.exit_button, 0, wx.ALL, 20)
        
        main_sizer.Add(button_container, 0, wx.EXPAND | wx.ALL, 0)
        main_sizer.AddStretchSpacer()
        
        self.SetSizer(main_sizer)
    
    def create_metrics_panel(self):
        """Create metrics display panel matching game screen design"""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        # Create main horizontal sizer for the four metric cards
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Format values from summary_data
        total_time_min = self.summary_data.get("total_time", 0)
        minutes = int(total_time_min)
        seconds = int((total_time_min - minutes) * 60)
        time_str = f"{minutes:02d}:{seconds:02d}:00"
        
        avg_power = self.summary_data.get("avg_power", 0)
        power_str = f"{int(avg_power)} W"
        
        total_distance = self.summary_data.get("total_distance", 0)
        if total_distance >= 1000:
            distance_str = f"{total_distance/1000:.1f} km"
        else:
            distance_str = f"{int(total_distance)} m"
        
        avg_accuracy = self.summary_data.get("avg_accuracy", 0)
        accuracy_str = f"{int(avg_accuracy)}%"
        
        # Total Time Card
        time_card = self.create_metric_card(panel, "Total Time", time_str, wx.Colour(255, 255, 255))
        main_sizer.Add(time_card, 1, wx.EXPAND | wx.RIGHT, 15)
        
        # Average Power Card
        power_card = self.create_metric_card(panel, "Average Power", power_str, wx.Colour(255, 255, 255))
        main_sizer.Add(power_card, 1, wx.EXPAND | wx.RIGHT, 15)
        
        # Total Distance Card
        distance_card = self.create_metric_card(panel, "Total Distance", distance_str, wx.Colour(255, 255, 255))
        main_sizer.Add(distance_card, 1, wx.EXPAND | wx.RIGHT, 15)
        
        # Average Accuracy Card
        accuracy_card = self.create_metric_card(panel, "Average Accuracy", accuracy_str, wx.Colour(255, 255, 255))
        main_sizer.Add(accuracy_card, 1, wx.EXPAND)
        
        panel.SetSizer(main_sizer)
        return panel
    
    def create_metric_card(self, parent, title, value, bg_color):
        """Create a metric card matching the game screen design"""
        # Create panel for the card
        card_panel = wx.Panel(parent)
        card_panel.SetBackgroundColour(bg_color)
        
        # Create sizer for card content
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        card_sizer.AddStretchSpacer()  # Top flexible space
        
        # Title label - much larger
        title_label = wx.StaticText(card_panel, label=title)
        title_label.SetForegroundColour(wx.Colour(128, 128, 128))
        title_label.SetFont(wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        card_sizer.Add(title_label, 0, wx.ALIGN_CENTER)
        card_sizer.AddSpacer(20)
        
        # Value label - much larger
        value_label = wx.StaticText(card_panel, label=value)
        value_label.SetForegroundColour(wx.Colour(64, 64, 64))
        value_label.SetFont(wx.Font(72, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        card_sizer.Add(value_label, 0, wx.ALIGN_CENTER)
        card_sizer.AddStretchSpacer()  # Bottom flexible space
        
        card_panel.SetSizer(card_sizer)
        
        # Set accuracy color based on value
        if title == "Average Accuracy":
            accuracy_value = self.summary_data.get("avg_accuracy", 0)
            if accuracy_value >= 90:
                value_label.SetForegroundColour(wx.Colour(76, 175, 80))  # Green
            elif accuracy_value >= 70:
                value_label.SetForegroundColour(wx.Colour(255, 193, 7))  # Amber
            else:
                value_label.SetForegroundColour(wx.Colour(244, 67, 54))  # Red
        
        return card_panel
    
    def on_exit(self, event):
        """Handle exit button click - navigate to dashboard"""
        parent = self.GetParent()
        parent.switch_to_dashboard()

