# dashboard page
import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from button import CustomButton
import os
import json
import hashlib
import secrets
import csv
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta

# Configuration: Set to False to skip login and use demo account automatically
REQUIRE_LOGIN = True

class AccountManager:
    """Manages user accounts and authentication"""
    def __init__(self):
        # Store accounts file in the same directory as dashboard.py (Coaching App folder)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.accounts_file = os.path.join(script_dir, "user_accounts.json")
        self.accounts = self.load_accounts()
        self.ensure_account_defaults()
    
    def load_accounts(self):
        """Load accounts from file"""
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, "r") as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_accounts(self):
        """Save accounts to file"""
        try:
            with open(self.accounts_file, "w") as f:
                json.dump(self.accounts, f, indent=2)
                f.flush()  # Ensure data is written to disk
                try:
                    os.fsync(f.fileno())  # Force write to disk
                except (AttributeError, OSError):
                    pass  # fsync may not be available on all systems
        except Exception as e:
            print(f"Error saving accounts: {e}")
            import traceback
            traceback.print_exc()
    
    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt, password_hash.hex()
    
    def verify_password(self, password, salt, stored_hash):
        """Verify password against stored hash"""
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex() == stored_hash
    
    def ensure_account_defaults(self):
        """Ensure newly loaded accounts contain required default fields"""
        updated = False
        for username, data in self.accounts.items():
            if "cumulative_distance_m" not in data:
                data["cumulative_distance_m"] = 0.0
                updated = True
        if updated:
            self.save_accounts()
    
    def create_account(self, username, password, name=""):
        """Create a new user account - simplified to only require username, password, and optional name"""
        if username in self.accounts:
            return False, "Username already exists"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        salt, password_hash = self.hash_password(password)
        
        # Create simplified user data
        user_data = {
            "username": username,
            "name": name if name else username,  # Use username as name if not provided
            "password_salt": salt,
            "password_hash": password_hash,
            "created_date": datetime.now().isoformat(),
            "total_sessions": 0,
            "total_time": 0,
            "best_stroke_rate": 0,
            "cumulative_distance_m": 0.0,
            "achievements": {
                "first_session": False,
                "ten_sessions": False,
                "perfect_form": False,
                "endurance_master": False,
                "speed_demon": False,
                "week_warrior": False,
                "monthly_milestone": False,
                "consistency_king": False
            },
            "progress_level": 1,
            "last_session": None
        }
        
        self.accounts[username] = user_data
        self.save_accounts()
        return True, "Account created successfully"
    
    def authenticate(self, username, password):
        """Authenticate user login"""
        if username not in self.accounts:
            return False, "Invalid username or password"
        
        user_data = self.accounts[username]
        salt = user_data["password_salt"]
        stored_hash = user_data["password_hash"]
        
        if self.verify_password(password, salt, stored_hash):
            return True, user_data
        else:
            return False, "Invalid username or password"
    
    def update_user_data(self, username, user_data):
        """Update user data"""
        if username in self.accounts:
            self.accounts[username].update(user_data)
            self.save_accounts()
            return True
        return False

class LoginDialog(wx.Dialog):
    """Clean, modern login dialog matching app aesthetic"""
    def __init__(self, parent, account_manager):
        # Get screen size and make dialog appropriately sized
        display = wx.Display()
        screen_geometry = display.GetGeometry()
        screen_width, screen_height = screen_geometry.width, screen_geometry.height
        
        # Make dialog 40% of screen width and height, but with min/max constraints
        dialog_width = max(600, min(800, int(screen_width * 0.4)))
        dialog_height = max(1100, min(1300, int(screen_height * 0.75)))  # Increased minimum height for registration fields
        
        super(LoginDialog, self).__init__(parent, title="Login", size=(dialog_width, dialog_height))
        self.account_manager = account_manager
        self.user_data = None
        self.is_register_mode = False
        
        # Make dialog resizable
        self.SetSizeHints(dialog_width, dialog_height, -1, -1)
        
        # Match app background color
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top spacer (reduced for better fit)
        main_sizer.AddSpacer(30)
        
        # Large title matching selection screen style (slightly smaller for dialog)
        self.title_label = wx.StaticText(self, label="User Login")
        title_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title_label.SetFont(title_font)
        self.title_label.SetForegroundColour(wx.Colour(33, 37, 41))
        main_sizer.Add(self.title_label, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        # Spacer
        main_sizer.AddSpacer(20)
        
        # Form card container
        self.form_card = wx.Panel(self)
        self.form_card.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.form_card.SetMinSize((450, -1))
        
        # Bind paint event for card styling
        self.form_card.Bind(wx.EVT_PAINT, self.on_paint_card)
        
        form_sizer = wx.BoxSizer(wx.VERTICAL)
        form_sizer.AddSpacer(40)
        
        # Registration fields (hidden by default, shown first in registration mode)
        self.name_label = wx.StaticText(self.form_card, label="Name")
        self.name_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.name_label.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(self.name_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 30)
        self.name_label.Hide()
        
        self.reg_name = wx.TextCtrl(self.form_card, size=(390, 45))
        self.reg_name.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.reg_name.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.reg_name.SetForegroundColour(wx.Colour(33, 37, 41))  # Dark text color
        form_sizer.Add(self.reg_name, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 30)
        self.reg_name.Hide()
        
        # Username field
        username_label = wx.StaticText(self.form_card, label="Username")
        username_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        username_label.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(username_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 30)
        
        self.login_username = wx.TextCtrl(self.form_card, size=(390, 45))
        self.login_username.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.login_username.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.login_username.SetForegroundColour(wx.Colour(33, 37, 41))  # Dark text color
        form_sizer.Add(self.login_username, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 30)
        
        # Password field
        password_label = wx.StaticText(self.form_card, label="Password")
        password_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        password_label.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(password_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 30)
        
        self.login_password = wx.TextCtrl(self.form_card, size=(390, 45), style=wx.TE_PASSWORD)
        self.login_password.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.login_password.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.login_password.SetForegroundColour(wx.Colour(33, 37, 41))  # Dark text color
        form_sizer.Add(self.login_password, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 30)
        
        # Confirm password field (hidden by default, for registration)
        self.confirm_password_label = wx.StaticText(self.form_card, label="Confirm Password")
        self.confirm_password_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.confirm_password_label.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(self.confirm_password_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 30)
        self.confirm_password_label.Hide()
        
        self.reg_confirm = wx.TextCtrl(self.form_card, size=(390, 45), style=wx.TE_PASSWORD)
        self.reg_confirm.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.reg_confirm.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.reg_confirm.SetForegroundColour(wx.Colour(33, 37, 41))  # Dark text color
        form_sizer.Add(self.reg_confirm, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 30)
        self.reg_confirm.Hide()
        
        form_sizer.AddSpacer(20)
        
        # Error message label (initially hidden)
        self.error_label = wx.StaticText(self.form_card, label="")
        self.error_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.error_label.SetForegroundColour(wx.Colour(220, 53, 69))
        self.error_label.Hide()
        form_sizer.Add(self.error_label, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT | wx.BOTTOM, 30)
        
        form_sizer.AddSpacer(20)
        
        self.form_card.SetSizer(form_sizer)
        
        # Center the form card
        card_wrapper = wx.BoxSizer(wx.HORIZONTAL)
        card_wrapper.AddStretchSpacer()
        card_wrapper.Add(self.form_card, 0, wx.ALIGN_CENTER)
        card_wrapper.AddStretchSpacer()
        main_sizer.Add(card_wrapper, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 40)
        
        main_sizer.AddSpacer(20)
        
        # Button container
        button_container = wx.BoxSizer(wx.HORIZONTAL)
        button_container.AddStretchSpacer()
        
        # Login/Create button
        self.action_button = ModernCard(self, "Login", self.on_action_click, enabled=True, font_size=24)
        self.action_button.SetMinSize((288, 70))  # 20% wider than before (240 * 1.2 = 288)
        button_container.Add(self.action_button, 0, wx.ALIGN_CENTER)
        
        button_container.AddStretchSpacer()
        main_sizer.Add(button_container, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 40)
        
        main_sizer.AddSpacer(20)
        
        # Toggle button (Login/Create Account)
        toggle_container = wx.BoxSizer(wx.HORIZONTAL)
        toggle_container.AddStretchSpacer()
        
        self.toggle_text = wx.StaticText(self, label="Don't have an account? ")
        self.toggle_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.toggle_text.SetForegroundColour(wx.Colour(100, 100, 100))
        toggle_container.Add(self.toggle_text, 0, wx.ALIGN_CENTER_VERTICAL)
        
        self.toggle_link = wx.StaticText(self, label="Create Account")
        self.toggle_link.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.toggle_link.SetForegroundColour(wx.Colour(76, 175, 80))
        self.toggle_link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.toggle_link.Bind(wx.EVT_LEFT_DOWN, self.on_toggle_mode)
        toggle_container.Add(self.toggle_link, 0, wx.ALIGN_CENTER_VERTICAL)
        
        toggle_container.AddStretchSpacer()
        main_sizer.Add(toggle_container, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 40)
        
        # Demo account info
        demo_container = wx.BoxSizer(wx.HORIZONTAL)
        demo_container.AddStretchSpacer()
        demo_info = wx.StaticText(self, label="Demo: demo / password")
        demo_info.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        demo_info.SetForegroundColour(wx.Colour(150, 150, 150))
        demo_container.Add(demo_info, 0, wx.ALIGN_CENTER)
        demo_container.AddStretchSpacer()
        main_sizer.Add(demo_container, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 30)
        
        # Bottom spacer (reduced)
        main_sizer.AddSpacer(30)
        
        self.SetSizer(main_sizer)
        self.Layout()
        self.Centre()
    
    def on_paint_card(self, event):
        """Paint the form card with rounded corners and shadow"""
        dc = wx.PaintDC(event.GetEventObject())
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = event.GetEventObject().GetSize()
        
        # Draw shadow
        shadow_color = wx.Colour(0, 0, 0, 15)
        gc.SetBrush(wx.Brush(shadow_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(4, 4, width - 4, height - 4, 12)
        
        # Draw card background
        bg = wx.Colour(255, 255, 255)
        border = wx.Colour(220, 220, 220)
        gc.SetPen(wx.Pen(border, 2))
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(0, 0, width - 4, height - 4, 12)
    
    def on_toggle_mode(self, event):
        """Toggle between login and registration modes"""
        self.is_register_mode = not self.is_register_mode
        
        if self.is_register_mode:
            # Show registration fields
            self.name_label.Show()
            self.reg_name.Show()
            self.confirm_password_label.Show()
            self.reg_confirm.Show()
            
            # Update button text
            self.action_button.label_text = "Create Account"
            self.toggle_link.SetLabel("Back to Login")
            
            # Hide "Don't have an account?" text in registration mode
            self.toggle_text.Hide()
            
            # Update title
            self.title_label.SetLabel("Create Account")
        else:
            # Hide registration fields
            self.name_label.Hide()
            self.reg_name.Hide()
            self.confirm_password_label.Hide()
            self.reg_confirm.Hide()
            
            # Update button text
            self.action_button.label_text = "Login"
            self.toggle_link.SetLabel("Create Account")
            
            # Show "Don't have an account?" text in login mode
            self.toggle_text.Show()
            
            # Update title
            self.title_label.SetLabel("User Login")
        
        # Refresh form card layout to ensure fields are visible
        if hasattr(self, 'form_card'):
            self.form_card.Layout()
            self.form_card.Fit()
            self.form_card.Refresh()
        
        self.action_button.Refresh()
        self.Layout()
        self.Refresh()
    
    def show_error(self, message):
        """Show error message"""
        self.error_label.SetLabel(message)
        self.error_label.Show()
        self.Layout()
        self.Refresh()
    
    def hide_error(self):
        """Hide error message"""
        self.error_label.Hide()
        self.Layout()
    
    def on_action_click(self, event):
        """Handle login or registration"""
        self.hide_error()
        
        if self.is_register_mode:
            self.on_register()
        else:
            self.on_login()
    
    def on_login(self):
        """Handle login"""
        username = self.login_username.GetValue().strip()
        password = self.login_password.GetValue()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        success, result = self.account_manager.authenticate(username, password)
        
        if success:
            self.user_data = result
            self.EndModal(wx.ID_OK)
        else:
            self.show_error(result)
    
    def on_register(self):
        """Handle registration"""
        username = self.login_username.GetValue().strip()
        name = self.reg_name.GetValue().strip()
        password = self.login_password.GetValue()
        confirm = self.reg_confirm.GetValue()
        
        if not username or not password:
            self.show_error("Please enter username and password")
            return
        
        if password != confirm:
            self.show_error("Passwords do not match")
            return
        
        # Use username as name if name not provided
        if not name:
            name = username
        
        success, message = self.account_manager.create_account(username, password, name)
        
        if success:
            # Switch to login mode and fill in username
            self.is_register_mode = False
            self.name_label.Hide()
            self.reg_name.Hide()
            self.confirm_password_label.Hide()
            self.reg_confirm.Hide()
            self.action_button.label_text = "Login"
            self.toggle_link.SetLabel("Create Account")
            
            # Show "Don't have an account?" text when switching back to login mode
            self.toggle_text.Show()
            
            # Update title
            self.title_label.SetLabel("User Login")
            
            self.login_username.SetValue(username)
            self.login_password.SetValue("")
            self.reg_name.SetValue("")
            self.reg_confirm.SetValue("")
            self.action_button.Refresh()
            self.Layout()
            
            # Show success message
            self.show_error("Account created! Please log in.")
            self.error_label.SetForegroundColour(wx.Colour(40, 167, 69))
        else:
            self.show_error(message)
    
    
class ModernCard(wx.Panel):
    """A modern card panel with shadow effect and hover interaction"""
    def __init__(self, parent, label, handler=None, enabled=True, font_size=38):
        super(ModernCard, self).__init__(parent)
        self.enabled = enabled
        self.handler = handler
        self.label_text = label
        self.is_hovered = False
        self.font_size = font_size
        
        # Set base colors
        if enabled:
            self.bg_color = wx.Colour(255, 255, 255)
            self.text_color = wx.Colour(33, 37, 41)
        else:
            self.bg_color = wx.Colour(230, 230, 230)
            self.text_color = wx.Colour(150, 150, 150)
        
        self.SetBackgroundColour(self.bg_color)
        self.SetMinSize((380, 200))
        
        # Bind paint and mouse events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        if enabled and handler:
            self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
            self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
            self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        
        # Ensure the panel is shown and visible
        self.Show()
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = self.GetSize()
        
        # Ensure we have valid dimensions
        if width <= 0 or height <= 0:
            return
        
        # Draw shadow effect (subtle)
        if self.enabled and not self.is_hovered:
            shadow_color = wx.Colour(0, 0, 0, 15)
            gc.SetBrush(wx.Brush(shadow_color))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRoundedRectangle(4, 4, width - 4, height - 4, 12)
        
        # Draw card background with rounded corners
        if self.is_hovered and self.enabled and self.handler:
            # Slight elevation on hover
            bg = wx.Colour(245, 247, 250)
            border = wx.Colour(76, 175, 80)  # Green accent on hover
            gc.SetPen(wx.Pen(border, 3))
        else:
            bg = self.bg_color
            border = wx.Colour(220, 220, 220)
            gc.SetPen(wx.Pen(border, 2))
        
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(0, 0, width - 4, height - 4, 12)
        
        # Draw text with custom font size
        dc.SetFont(wx.Font(self.font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        dc.SetTextForeground(self.text_color)
        
        text_width, text_height = dc.GetTextExtent(self.label_text)
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2
        dc.DrawText(self.label_text, text_x, text_y)
    
    def OnEnter(self, event):
        if self.handler:
            self.is_hovered = True
            self.Refresh()
    
    def OnLeave(self, event):
        if self.handler:
            self.is_hovered = False
            self.Refresh()
    
    def OnClick(self, event):
        if self.enabled and self.handler:
            self.handler(event)

class UserInfoCard(wx.Panel):
    """A custom card for displaying user information"""
    def __init__(self, parent, user_data=None):
        super(UserInfoCard, self).__init__(parent)
        
        # Set base colors
        self.bg_color = wx.Colour(255, 255, 255)
        self.text_color = wx.Colour(33, 37, 41)
        self.SetBackgroundColour(self.bg_color)
        self.SetMinSize((380, 200))
        
        # Bind paint event
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        # Create a vertical sizer for the content
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title: "User Info" - centered
        title = wx.StaticText(self, label="User Info")
        title_font = wx.Font(32, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(self.text_color)
        main_sizer.Add(title, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 25)
        
        # Add spacing
        main_sizer.AddSpacer(20)
        
        # Create info fields with larger, clearer text
        info_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Label font (smaller, lighter)
        label_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        # Value font (larger, bold)
        value_font = wx.Font(22, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        
        # User Name field
        name_container = wx.BoxSizer(wx.VERTICAL)
        name_label = wx.StaticText(self, label="User Name")
        name_label.SetFont(label_font)
        name_label.SetForegroundColour(wx.Colour(120, 120, 120))
        name_container.Add(name_label, 0, wx.LEFT, 35)
        name_container.AddSpacer(3)
        
        self.name_value = wx.StaticText(self, label="")
        self.name_value.SetFont(value_font)
        self.name_value.SetForegroundColour(self.text_color)
        name_container.Add(self.name_value, 0, wx.LEFT, 35)
        info_sizer.Add(name_container, 0, wx.EXPAND)
        
        info_sizer.AddSpacer(18)
        
        # Total Sessions field
        sessions_container = wx.BoxSizer(wx.VERTICAL)
        sessions_label = wx.StaticText(self, label="Total Sessions")
        sessions_label.SetFont(label_font)
        sessions_label.SetForegroundColour(wx.Colour(120, 120, 120))
        sessions_container.Add(sessions_label, 0, wx.LEFT, 35)
        sessions_container.AddSpacer(3)
        
        self.sessions_value = wx.StaticText(self, label="")
        self.sessions_value.SetFont(value_font)
        self.sessions_value.SetForegroundColour(self.text_color)
        sessions_container.Add(self.sessions_value, 0, wx.LEFT, 35)
        info_sizer.Add(sessions_container, 0, wx.EXPAND)
        
        info_sizer.AddSpacer(18)
        
        # Longest Distance field
        distance_container = wx.BoxSizer(wx.VERTICAL)
        distance_label = wx.StaticText(self, label="Longest Distance")
        distance_label.SetFont(label_font)
        distance_label.SetForegroundColour(wx.Colour(120, 120, 120))
        distance_container.Add(distance_label, 0, wx.LEFT, 35)
        distance_container.AddSpacer(3)
        
        self.distance_value = wx.StaticText(self, label="")
        self.distance_value.SetFont(value_font)
        self.distance_value.SetForegroundColour(self.text_color)
        distance_container.Add(self.distance_value, 0, wx.LEFT, 35)
        info_sizer.Add(distance_container, 0, wx.EXPAND)
        
        main_sizer.Add(info_sizer, 1, wx.EXPAND)
        main_sizer.AddSpacer(20)
        
        self.SetSizer(main_sizer)
        
        # Update with user data if provided
        if user_data:
            self.update_user_data(user_data)
    
    def update_user_data(self, user_data):
        """Update the card with user data"""
        name = user_data.get('name', '') or user_data.get('username', 'Not provided')
        self.name_value.SetLabel(name)
        
        total_sessions = user_data.get('total_sessions', 0)
        self.sessions_value.SetLabel(str(total_sessions))
        
        longest_distance = user_data.get('longest_distance', 0.0)
        self.distance_value.SetLabel(f"{longest_distance:.2f} m")
        
        self.Layout()
        self.Refresh()
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = self.GetSize()
        
        # Draw shadow effect (subtle)
        shadow_color = wx.Colour(0, 0, 0, 15)
        gc.SetBrush(wx.Brush(shadow_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(4, 4, width - 4, height - 4, 12)
        
        # Draw card background with rounded corners
        bg = self.bg_color
        border = wx.Colour(220, 220, 220)
        gc.SetPen(wx.Pen(border, 2))
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(0, 0, width - 4, height - 4, 12)

class StatisticsCard(wx.Panel):
    """A custom card for displaying statistics with a matplotlib line graph"""
    def __init__(self, parent, session_data=None):
        super(StatisticsCard, self).__init__(parent)
        
        # Set base colors
        self.bg_color = wx.Colour(255, 255, 255)
        self.text_color = wx.Colour(33, 37, 41)
        self.SetBackgroundColour(self.bg_color)
        self.SetMinSize((380, 200))
        
        # Bind paint event for card styling
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        # Available metrics for cycling
        self.metrics = [
            {'name': 'Session Time', 'key': 'time_minutes', 'unit': 'min', 'label': 'Session Time (min)'},
            {'name': 'Average Power', 'key': 'avg_power', 'unit': 'W', 'label': 'Average Power (W)'},
            {'name': 'Total Distance', 'key': 'distance', 'unit': 'm', 'label': 'Total Distance (m)'},
            {'name': 'Average Accuracy', 'key': 'avg_accuracy', 'unit': '%', 'label': 'Average Accuracy (%)'}
        ]
        self.current_metric_index = 0
        
        # Create a vertical sizer for the content
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title row with navigation arrows
        title_row = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left arrow - clickable StaticText
        self.left_arrow = wx.StaticText(self, label="←")
        arrow_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.left_arrow.SetFont(arrow_font)
        self.left_arrow.SetForegroundColour(wx.Colour(0, 0, 0))
        self.left_arrow.Bind(wx.EVT_LEFT_DOWN, lambda e: self.on_previous_metric(e))
        self.left_arrow.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        title_row.Add(self.left_arrow, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 30)
        
        # Title: "Statistics"
        self.title_label = wx.StaticText(self, label="Statistics")
        title_font = wx.Font(32, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title_label.SetFont(title_font)
        self.title_label.SetForegroundColour(self.text_color)
        title_row.Add(self.title_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        
        # Right arrow - clickable StaticText
        self.right_arrow = wx.StaticText(self, label="→")
        self.right_arrow.SetFont(arrow_font)
        self.right_arrow.SetForegroundColour(wx.Colour(0, 0, 0))
        self.right_arrow.Bind(wx.EVT_LEFT_DOWN, lambda e: self.on_next_metric(e))
        self.right_arrow.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        title_row.Add(self.right_arrow, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        
        # Add stretch spacer to push title to left
        title_row.AddStretchSpacer()
        
        main_sizer.Add(title_row, 0, wx.EXPAND | wx.TOP, 30)
        
        # Add minimal spacing
        main_sizer.AddSpacer(5)
        
        # Create matplotlib figure and canvas with better sizing
        self.figure = Figure(figsize=(4.5, 2.0), dpi=80, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)
        main_sizer.Add(self.canvas, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 15)
        
        self.SetSizer(main_sizer)
        
        # Store session data
        self.session_data = session_data or {'sessions': []}
        
        # Create the plot
        self.create_plot()
    
    def on_previous_metric(self, event):
        """Switch to previous metric"""
        self.current_metric_index = (self.current_metric_index - 1) % len(self.metrics)
        self.create_plot()
    
    def on_next_metric(self, event):
        """Switch to next metric"""
        self.current_metric_index = (self.current_metric_index + 1) % len(self.metrics)
        self.create_plot()
        
    def create_plot(self):
        """Create the matplotlib plot showing the selected metric over time"""
        # Clear the figure
        self.figure.clear()
        
        # Create subplot
        ax = self.figure.add_subplot(111)
        
        # Get current metric
        current_metric = self.metrics[self.current_metric_index]
        metric_key = current_metric['key']
        metric_label = current_metric['label']
        
        # Get session data
        sessions = self.session_data.get('sessions', [])
        y_values = []  # Initialize to avoid scope issues
        
        if len(sessions) > 0:
            # Extract dates and metric values
            date_objects = []
            values = []
            
            for session in sessions:
                # Parse date if available
                if session.get('date'):
                    try:
                        # Parse date string to datetime object
                        date_obj = datetime.strptime(session['date'], '%Y-%m-%d')
                        date_objects.append(date_obj)
                        values.append(session.get(metric_key, 0))
                    except:
                        # Skip invalid dates
                        continue
            
            if len(date_objects) > 0:
                # Group sessions by date
                # For time: sum values, for others: average values
                date_value_dict = {}
                date_count_dict = {}
                
                for date_obj, value in zip(date_objects, values):
                    date_key = date_obj.date()
                    if date_key in date_value_dict:
                        if metric_key == 'time_minutes':
                            # Sum times for same date
                            date_value_dict[date_key] += value
                        else:
                            # Average other metrics for same date
                            date_value_dict[date_key] += value
                            date_count_dict[date_key] += 1
                    else:
                        date_value_dict[date_key] = value
                        if metric_key != 'time_minutes':
                            date_count_dict[date_key] = 1
                
                # Calculate averages for non-time metrics
                if metric_key != 'time_minutes':
                    for date_key in date_value_dict:
                        if date_key in date_count_dict and date_count_dict[date_key] > 0:
                            date_value_dict[date_key] = date_value_dict[date_key] / date_count_dict[date_key]
                
                # Sort by date
                sorted_dates = sorted(date_value_dict.keys())
                x_dates = [datetime.combine(d, datetime.min.time()) for d in sorted_dates]
                y_values = [date_value_dict[d] for d in sorted_dates]
                
                # Plot the line with area fill
                ax.plot(x_dates, y_values, color='#0066CC', linewidth=2.5, marker='o', markersize=4)
                ax.fill_between(x_dates, y_values, alpha=0.3, color='#ADD8E6')
                
                # Set x-axis to use dates
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                
                # For single date, position it on the left side of the plot
                if len(x_dates) == 1:
                    # Single date - position on left, leave room for future dates
                    first_date = x_dates[0]
                    # Add some padding before the first date (2 days) to create gap from y-axis
                    # Set x-axis limits: start 2 days before first date, extend 30 days to the right
                    ax.set_xlim(left=first_date - timedelta(days=2), right=first_date + timedelta(days=30))
                    # Show only the first date tick
                    ax.set_xticks([first_date])
                else:
                    # Multiple dates - auto-scale
                    date_min = min(x_dates)
                    date_max = max(x_dates)
                    # Add some padding (5% of date range)
                    date_range = (date_max - date_min).days
                    padding = timedelta(days=max(1, int(date_range * 0.05)))
                    ax.set_xlim(left=date_min - padding, right=date_max + padding)
                    # Auto-format date ticks
                    if date_range <= 7:
                        ax.xaxis.set_major_locator(mdates.DayLocator())
                    elif date_range <= 30:
                        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                    else:
                        ax.xaxis.set_major_locator(mdates.MonthLocator())
                
                # Rotate date labels for better readability
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            else:
                # No valid dates - show empty plot with message
                ax.text(0.5, 0.5, 'No valid session data', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=14, color='#999999')
        else:
            # No data - show empty plot with message
            ax.text(0.5, 0.5, 'No session data yet', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14, color='#999999')
        
        # Set labels
        ax.set_xlabel('Date', fontsize=14, color='#212529', fontweight='normal')
        ax.set_ylabel(metric_label, fontsize=14, color='#212529', fontweight='normal')
        
        # Style the plot
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor('white')
        
        # Remove top and right spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#212529')
        ax.spines['bottom'].set_color('#212529')
        
        # Set tick colors and smaller font
        ax.tick_params(colors='#212529', labelsize=10)
        
        # Auto-scale y-axis with some padding
        if y_values:
            y_max = max(y_values)
            y_min = min(y_values)
            # Ensure minimum is 0 for most metrics (except accuracy which can be negative in some cases)
            if metric_key != 'avg_accuracy' or y_min >= 0:
                ax.set_ylim(bottom=0, top=max(y_max * 1.1, 5))
            else:
                # For accuracy, allow negative values if needed
                ax.set_ylim(bottom=min(y_min * 1.1, -5), top=max(y_max * 1.1, 5))
        else:
            ax.set_ylim(bottom=0, top=10)
        
        # Adjust layout to fit properly in card
        self.figure.tight_layout(pad=1.0)
        
        # Set subplot parameters for better fit (more bottom space for rotated dates)
        self.figure.subplots_adjust(left=0.15, bottom=0.30, right=0.95, top=0.85)
        
        # Refresh the canvas
        self.canvas.draw()
    
    def update_session_data(self, session_data):
        """Update the graph with new session data"""
        self.session_data = session_data
        self.create_plot()
        
    def OnPaint(self, event):
        """Paint the card background with shadow and border"""
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = self.GetSize()
        
        # Draw shadow effect (subtle)
        shadow_color = wx.Colour(0, 0, 0, 15)
        gc.SetBrush(wx.Brush(shadow_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(4, 4, width - 4, height - 4, 12)
        
        # Draw card background with rounded corners
        bg = self.bg_color
        border = wx.Colour(220, 220, 220)
        gc.SetPen(wx.Pen(border, 2))
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(0, 0, width - 4, height - 4, 12)

class AchievementCard(wx.Panel):
    """Individual achievement card with icon and better display"""
    def __init__(self, parent, title, description, unlocked=False):
        super(AchievementCard, self).__init__(parent)
        import os
        self.unlocked = unlocked
        self.title = title
        self.description = description
        
        self.SetMinSize((320, 100))
        
        # Create horizontal sizer for icon and text
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSpacer(10)
        
        # Replace the icon panel block with achievement or locked icon
        # Load images from assets/images directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets", "images")
        achievement_path = os.path.join(assets_dir, "achievement.png")
        locked_path = os.path.join(assets_dir, "locked.png")
        
        if unlocked and os.path.exists(achievement_path):
            img = wx.Image(achievement_path, wx.BITMAP_TYPE_ANY)
            img = img.Scale(48, 48, wx.IMAGE_QUALITY_HIGH)
            icon = wx.StaticBitmap(self, -1, wx.Bitmap(img))
            icon.SetBackgroundColour(wx.Colour(76, 175, 80))
        elif os.path.exists(locked_path):
            img = wx.Image(locked_path, wx.BITMAP_TYPE_ANY)
            img = img.Scale(48, 48, wx.IMAGE_QUALITY_HIGH)
            icon = wx.StaticBitmap(self, -1, wx.Bitmap(img))
            icon.SetBackgroundColour(wx.Colour(200, 200, 200, 30))
        else:
            # Fallback to text if images are not found
            icon = wx.StaticText(self, label=("★" if unlocked else "●"))
            icon.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            icon.SetForegroundColour(wx.Colour(255, 215, 0) if unlocked else wx.Colour(180, 180, 180))

        main_sizer.Add(icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 8)
        
        # Text content
        text_sizer = wx.BoxSizer(wx.VERTICAL)
        text_sizer.AddSpacer(5)
        
        # Title - standardized font size
        title_text = wx.StaticText(self, label=title, style=wx.ST_NO_AUTORESIZE)
        title_font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_text.SetFont(title_font)
        title_text.Wrap(240)  
        if unlocked:
            title_text.SetForegroundColour(wx.Colour(50, 50, 50))
            title_text.SetBackgroundColour(wx.Colour(76, 175, 80))
        else:
            title_text.SetForegroundColour(wx.Colour(100, 100, 100)) 
            title_text.SetBackgroundColour(wx.Colour(200, 200, 200, 30))
        text_sizer.Add(title_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # Description - standardized font size
        desc_text = wx.StaticText(self, label=description, style=wx.ST_NO_AUTORESIZE)
        desc_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        desc_text.SetFont(desc_font)
        desc_text.Wrap(240)
        if unlocked:
            desc_text.SetForegroundColour(wx.Colour(0, 0, 0))# text color for unlocked achievements
            desc_text.SetBackgroundColour(wx.Colour(76, 175, 80))
        else:
            desc_text.SetForegroundColour(wx.Colour(120, 120, 120))
            desc_text.SetBackgroundColour(wx.Colour(200, 200, 200, 30))

        text_sizer.Add(desc_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        text_sizer.AddSpacer(5)
        main_sizer.Add(text_sizer, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.AddSpacer(10)
        
        self.SetSizer(main_sizer)
        
        # Draw border
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        width, height = self.GetSize()
        
        if self.unlocked:
            border_color = wx.Colour(0, 103, 0) 
            fill_color = wx.Colour(76, 175, 80, 30)  
        else:
            border_color = wx.Colour(150, 150, 150)  
            fill_color = wx.Colour(200, 200, 200, 30)  
        
        # Fill background
        dc.SetPen(wx.TRANSPARENT_PEN)  
        dc.SetBrush(wx.Brush(fill_color))  
        dc.DrawRoundedRectangle(2, 2, width - 4, height - 4, 10)
        
        # Draw border
        dc.SetPen(wx.Pen(border_color, 2))  
        dc.SetBrush(wx.TRANSPARENT_BRUSH)  
        dc.DrawRoundedRectangle(2, 2, width - 4, height - 4, 10)

class AchievementsCard(wx.Panel):
    """A custom card for displaying achievements with scrollable list"""
    def __init__(self, parent, user_data=None):
        super(AchievementsCard, self).__init__(parent)
        
        # Set base colors - matching dashboard style
        self.bg_color = wx.Colour(255, 255, 255)
        self.text_color = wx.Colour(33, 37, 41)
        self.SetBackgroundColour(self.bg_color)
        self.SetMinSize((380, 200))
        
        # Bind paint event for card styling
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        # Create a vertical sizer for the content
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title: "Achievements" - matching dashboard style
        title = wx.StaticText(self, label="Achievements")
        title_font = wx.Font(32, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(self.text_color)
        main_sizer.Add(title, 0, wx.LEFT | wx.TOP, 30)
        
        # Add minimal spacing
        main_sizer.AddSpacer(5)
        
        # Create scrollable panel for achievements
        self.scroll_panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self.scroll_panel.SetBackgroundColour(self.bg_color)
        self.scroll_panel.SetScrollRate(0, 10)
        
        # Create sizer for scrollable content
        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_sizer.AddSpacer(5)
        
        self.scroll_panel.SetSizer(self.scroll_sizer)
        
        # Add scroll panel to main sizer with proper sizing
        main_sizer.Add(self.scroll_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        main_sizer.AddSpacer(10)
        
        self.SetSizer(main_sizer)
        
        # Update with user data if provided
        if user_data:
            self.update_achievements(user_data)
    
    def update_achievements(self, user_data):
        """Update achievements display with user data"""
        # Clear existing achievement cards
        for child in self.scroll_panel.GetChildren():
            if isinstance(child, AchievementCard):
                child.Destroy()
        
        # Clear the sizer
        self.scroll_sizer.Clear(True)
        self.scroll_sizer.AddSpacer(5)
        
        # Get user achievements
        achievements_data = user_data.get('achievements', {})
        
        # Define achievements with more detailed descriptions
        achievements = [
            ("First Session", "Complete your first rowing session to get started on your rowing journey", 
             achievements_data.get('first_session', False)),
            ("Ten Sessions", "Complete 10 rowing sessions to build consistency and habit", 
             achievements_data.get('ten_sessions', False)),
            ("Perfect Form", "Maintain perfect rowing form for 5 consecutive minutes", 
             achievements_data.get('perfect_form', False)),
            ("Endurance Master", "Row continuously for 30+ minutes without stopping", 
             achievements_data.get('endurance_master', False)),
            ("Speed Demon", "Achieve a stroke rate of 35+ strokes per minute", 
             achievements_data.get('speed_demon', False)),
            ("Week Warrior", "Complete 7 rowing sessions in a single week", 
             achievements_data.get('week_warrior', False)),
            ("Monthly Milestone", "Complete 20 rowing sessions in a month", 
             achievements_data.get('monthly_milestone', False)),
            ("Consistency King", "Row for 5 consecutive days", 
             achievements_data.get('consistency_king', False))
        ]
        
        # Create achievement cards
        for title_text, description, unlocked in achievements:
            achievement_card = AchievementCard(self.scroll_panel, title_text, description, unlocked)
            self.scroll_sizer.Add(achievement_card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        self.scroll_sizer.AddSpacer(5)
        
        # Set virtual size for scrolling
        self.scroll_panel.SetVirtualSize(self.scroll_sizer.GetMinSize())
        self.scroll_panel.EnableScrolling(True, True)
        self.scroll_panel.Layout()
        self.Layout()
        
    def OnPaint(self, event):
        """Paint the card background with shadow and border"""
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = self.GetSize()
        
        # Draw shadow effect (subtle)
        shadow_color = wx.Colour(0, 0, 0, 15)
        gc.SetBrush(wx.Brush(shadow_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(4, 4, width - 4, height - 4, 12)
        
        # Draw card background with rounded corners
        bg = self.bg_color
        border = wx.Colour(220, 220, 220)
        gc.SetPen(wx.Pen(border, 2))
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(0, 0, width - 4, height - 4, 12)

class MapCard(wx.Panel):
    """A custom card for displaying a map with dots"""
    def __init__(self, parent, username=None):
        super(MapCard, self).__init__(parent)
        
        # Store username for distance calculation
        self.username = username
        
        # Location milestones (distance in meters to reach each location) - matching game_page.py
        self.location_milestones = [
            ("Hawaii", 0),
            ("Antarctica", 10),
            ("Amazon", 20),
            ("Japan", 30),
            ("Australia", 40),
        ]
        
        # Store references to location widgets for dynamic updates
        self.location_widgets = {}
        
        # Set base colors
        self.bg_color = wx.Colour(255, 255, 255)
        self.text_color = wx.Colour(33, 37, 41)
        self.SetBackgroundColour(self.bg_color)
        self.SetMinSize((380, 200))
        
        # Bind paint event for card styling and map drawing
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        # Create a vertical sizer for the content
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title: "Map"
        title = wx.StaticText(self, label="Map")
        title_font = wx.Font(32, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(self.text_color)
        main_sizer.Add(title, 0, wx.LEFT | wx.TOP, 30)
        
        # Add some spacing
        main_sizer.AddSpacer(10)
        
        # Add stretch spacer to push content to center
        main_sizer.AddStretchSpacer()
        
        # Create horizontal sizer for evenly spaced items - 5 equal columns
        items_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        import os
        # Load images from assets/images directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets", "images")
        
        # Helper function to create a location column
        def create_location_column(image_path, image_size, location_name, status_image_size):
            """Create a vertical sizer for a location with image, text, and status icon"""
            location_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Fixed height container for images to ensure text alignment
            # Use 95 pixels to accommodate the largest image (90px) with some padding
            fixed_image_height = 95
            image_panel = wx.Panel(self)
            image_panel.SetMinSize((-1, fixed_image_height))
            image_panel.SetMaxSize((-1, fixed_image_height))
            image_panel_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Add spacer to center image vertically
            image_panel_sizer.AddStretchSpacer()
            
            # Add location image centered in fixed-height container
            try:
                location_image = wx.Image(image_path, wx.BITMAP_TYPE_PNG)
                location_image = location_image.Scale(image_size, image_size, wx.IMAGE_QUALITY_HIGH)
                location_bitmap = wx.StaticBitmap(image_panel, bitmap=wx.Bitmap(location_image))
                image_panel_sizer.Add(location_bitmap, 0, wx.ALIGN_CENTER)
            except Exception as e:
                print(f"Error loading {image_path}: {e}")
                # Fallback to text
                placeholder = wx.StaticText(image_panel, label=location_name.upper())
                placeholder.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                placeholder.SetForegroundColour(wx.Colour(0, 100, 0))
                image_panel_sizer.Add(placeholder, 0, wx.ALIGN_CENTER)
            
            # Add spacer to center image vertically
            image_panel_sizer.AddStretchSpacer()
            
            image_panel.SetSizer(image_panel_sizer)
            image_panel_sizer.Fit(image_panel)
            
            # Add the image panel to location sizer
            location_sizer.Add(image_panel, 0, wx.ALIGN_CENTER)
            
            # Add location name text with wrapping support
            location_text = wx.StaticText(self, label=location_name, style=wx.ST_NO_AUTORESIZE)
            location_text.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            # Wrap text to fit within column width (approximately 1/5 of card width minus margins)
            location_text.Wrap(60)  # Approximate width for text wrapping
            location_sizer.Add(location_text, 0, wx.ALIGN_CENTER)
            
            # Add status image (check or lock) - will be updated dynamically
            status_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(1, 1))  # Placeholder, will be updated
            location_sizer.Add(status_bitmap, 0, wx.ALIGN_CENTER)
            
            # Store references for dynamic updates
            self.location_widgets[location_name] = {
                'text': location_text,
                'status_bitmap': status_bitmap
            }
            
            return location_sizer
        
        # Create 5 location columns, each in its own equal-width column
        # Column 1: Hawaii
        hawaii_sizer = create_location_column(
            os.path.join(assets_dir, "palm-tree.png"), 80,
            "Hawaii",
            40
        )
        items_sizer.Add(hawaii_sizer, 1, wx.EXPAND)
        
        # Column 2: Antarctica
        antarctica_sizer = create_location_column(
            os.path.join(assets_dir, "iceberg.png"), 90,
            "Antarctica",
            40
        )
        items_sizer.Add(antarctica_sizer, 1, wx.EXPAND)
        
        # Column 3: Amazon
        amazon_sizer = create_location_column(
            os.path.join(assets_dir, "jungle.png"), 70,
            "Amazon",
            40
        )
        items_sizer.Add(amazon_sizer, 1, wx.EXPAND)
        
        # Column 4: Japan
        japan_sizer = create_location_column(
            os.path.join(assets_dir, "japan.png"), 80,
            "Japan",
            40
        )
        items_sizer.Add(japan_sizer, 1, wx.EXPAND)
        
        # Column 5: Australia
        australia_sizer = create_location_column(
            os.path.join(assets_dir, "australia.png"), 80,
            "Australia",
            40
        )
        items_sizer.Add(australia_sizer, 1, wx.EXPAND)
        
        # Add the items sizer to main sizer
        main_sizer.Add(items_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 30)
        
        
        # Add stretch spacer to balance the line in center
        main_sizer.AddStretchSpacer()
        
        self.SetSizer(main_sizer)
        
        # Generate random dot positions
        self.dot_positions = self.generate_random_dots()
        
        # Update location unlock status based on distance
        self.update_location_status()
    
    def get_cumulative_distance(self):
        """Get cumulative total distance for the current user from user_accounts.json"""
        if not self.username:
            return 0.0
        
        accounts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_accounts.json")
        try:
            with open(accounts_file, "r") as f:
                accounts = json.load(f)
            user_data = accounts.get(self.username, {})
            return float(user_data.get("cumulative_distance_m", 0.0))
        except Exception as e:
            print(f"Error loading cumulative distance for {self.username}: {e}")
            return 0.0
    
    def update_location_status(self):
        """Update lock/unlock status of locations based on cumulative distance with looping"""
        cumulative_distance = self.get_cumulative_distance()
        
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets", "images")
        check_path = os.path.join(assets_dir, "check.png")
        lock_path = os.path.join(assets_dir, "lock.png")
        
        # Update each location - once unlocked, stays unlocked forever
        for i, (location_name, milestone_distance) in enumerate(self.location_milestones):
            if location_name not in self.location_widgets:
                continue
            
            # Unlock location once milestone distance has been reached
            is_unlocked = cumulative_distance >= milestone_distance
            
            widgets = self.location_widgets[location_name]
            
            # Update status image
            try:
                if is_unlocked:
                    status_image = wx.Image(check_path, wx.BITMAP_TYPE_PNG)
                    status_image = status_image.Scale(40, 40, wx.IMAGE_QUALITY_HIGH)
                    widgets['status_bitmap'].SetBitmap(wx.Bitmap(status_image))
                    widgets['text'].SetForegroundColour(wx.Colour(0, 100, 0))  # Green for unlocked
                else:
                    status_image = wx.Image(lock_path, wx.BITMAP_TYPE_PNG)
                    status_image = status_image.Scale(40, 40, wx.IMAGE_QUALITY_HIGH)
                    widgets['status_bitmap'].SetBitmap(wx.Bitmap(status_image))
                    widgets['text'].SetForegroundColour(wx.Colour(128, 128, 128))  # Grey for locked
            except Exception as e:
                print(f"Error updating location status for {location_name}: {e}")
        
        # Refresh the display
        self.Refresh()
        self.Layout()
        
    def generate_random_dots(self):
        """Generate 4 evenly spaced, staggered dot positions for path connections"""
        # Get actual card dimensions dynamically
        card_width = self.GetSize().width
        card_height = self.GetSize().height
        
        # Minimal margins - just enough for the title and borders
        margin_x = 20
        margin_y = 60  # Space for title
        available_width = card_width - 2 * margin_x
        available_height = card_height - 2 * margin_y
        
        # Calculate 10% inward margin for edge dots
        inward_margin = int(card_width * 0.1)  # 10% of section width
        
        # Create a staggered path-like layout using the full available space
        # Divide the available space into 3 horizontal sections for 4 dots
        section_width = available_width // 3
        
        dots = []
        
        # Dot 1: Start position (left edge moved inward by 10%, top level)
        x1 = margin_x + inward_margin
        y1 = margin_y + available_height // 4  # Top quarter
        dots.append((x1, y1))
        
        # Dot 2: Second position (middle-left, bottom level)
        x2 = margin_x + section_width
        y2 = margin_y + (3 * available_height) // 4  # Bottom quarter
        dots.append((x2, y2))
        
        # Dot 3: Third position (middle-right, top level)
        x3 = margin_x + 2 * section_width
        y3 = margin_y + available_height // 4  # Top quarter
        dots.append((x3, y3))
        
        # Dot 4: End position (right edge moved inward by 10%, bottom level)
        x4 = margin_x + available_width - inward_margin
        y4 = margin_y + (3 * available_height) // 4  # Bottom quarter
        dots.append((x4, y4))
        
        return dots
        
    def OnPaint(self, event):
        """Paint the card background and map dots"""
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = self.GetSize()
        
        # ----------------------------------------------------
        # Background + Shadow
        # ----------------------------------------------------
        shadow_color = wx.Colour(0, 0, 0, 15)
        gc.SetBrush(wx.Brush(shadow_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(4, 4, width - 4, height - 4, 12)
        
        bg = self.bg_color
        border = wx.Colour(220, 220, 220)
        gc.SetPen(wx.Pen(border, 2))
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(0, 0, width - 4, height - 4, 12)
        
        # ----------------------------------------------------
        # Dot positions (use existing)
        # ----------------------------------------------------
        if not hasattr(self, 'dot_positions') or not self.dot_positions:
            self.dot_positions = self.generate_random_dots()
        
        # ----------------------------------------------------
        # Helper function: convert cubic → two quadratic curves
        # ----------------------------------------------------
        def add_quadratic_from_cubic(path, c1x, c1y, c2x, c2y, ex, ey):
            """
            Convert a cubic bezier to two quadratic curves.
            Start point is taken from path.GetCurrentPoint().
            """
            x0, y0 = path.GetCurrentPoint()

            mx = (c1x + c2x) / 2
            my = (c1y + c2y) / 2

            q1x = (x0 + 2 * c1x) / 3
            q1y = (y0 + 2 * c1y) / 3

            q2x = (ex + 2 * c2x) / 3
            q2y = (ey + 2 * c2y) / 3

            path.AddQuadCurveToPoint(q1x, q1y, mx, my)
            path.AddQuadCurveToPoint(q2x, q2y, ex, ey)
        
        # Path and dots removed - no longer drawing them


class DashboardPage(wx.Panel):
    def __init__(self, parent):
        super(DashboardPage, self).__init__(parent)
        # Light gradient-like background
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        # Initialize account manager
        self.account_manager = AccountManager()
        self.user_data = None
        self.is_logged_in = False
        self.current_username = None
        
        # Create demo account for demo if no accounts exist
        self.create_demo_account()
        
        # Check if login is required
        print(f"REQUIRE_LOGIN is set to: {REQUIRE_LOGIN}")  # Debug print
        if REQUIRE_LOGIN:
            # Require login before showing dashboard
            if not self.require_login():
                # If login was cancelled, show empty dashboard
                self.create_empty_layout()
                return
        else:
            # Skip login and automatically use demo account
            self.current_username = "demo"
            self.is_logged_in = True
            # Load user account data
            if self.current_username in self.account_manager.accounts:
                self.user_data = self.account_manager.accounts[self.current_username].copy()
            else:
                # Fallback user data if account doesn't exist
                self.user_data = {
                    "name": "demo",
                    "username": "demo",
                    "total_sessions": 0,
                    "longest_distance": 0.0,
                    "achievements": {
                        "first_session": False,
                        "ten_sessions": False,
                        "perfect_form": False,
                        "endurance_master": False,
                        "speed_demon": False,
                        "week_warrior": False,
                        "monthly_milestone": False,
                        "consistency_king": False
                    }
                }
        
        # Load session data for the logged-in user (this also updates achievements and statistics)
        # update_achievements_from_sessions() is called inside load_user_session_data() and saves to JSON
        self.session_data = self.load_user_session_data(self.current_username)
        
        # Reload user account data (achievements and statistics have been updated and saved)
        if self.current_username in self.account_manager.accounts:
            self.user_data = self.account_manager.accounts[self.current_username].copy()
        
        # Create the dashboard layout
        self.create_layout()
    
    def refresh_dashboard(self):
        """Refresh dashboard data and update all cards - called when navigating to dashboard"""
        if not self.is_logged_in or not self.current_username:
            return
        
        # Reload session data for the logged-in user (this also updates achievements and statistics)
        # update_achievements_from_sessions() is called inside load_user_session_data() and saves to JSON
        self.session_data = self.load_user_session_data(self.current_username)
        
        # Reload user account data (achievements and statistics have been updated and saved)
        if self.current_username in self.account_manager.accounts:
            self.user_data = self.account_manager.accounts[self.current_username].copy()
        
        # Update all cards with fresh data
        if hasattr(self, 'section1_card') and self.section1_card:
            self.section1_card.update_user_data(self.user_data)
        
        if hasattr(self, 'section2_card') and self.section2_card:
            self.section2_card.update_session_data(self.session_data)
        
        if hasattr(self, 'section3_card') and self.section3_card:
            self.section3_card.update_achievements(self.user_data)
        
        # Update map card location unlock status
        if hasattr(self, 'section4_card') and self.section4_card:
            # Update username if it changed
            if hasattr(self.section4_card, 'username'):
                self.section4_card.username = self.current_username
            if hasattr(self.section4_card, 'update_location_status'):
                self.section4_card.update_location_status()
        
        # Update header with user name (in case it changed)
        if hasattr(self, 'header') and self.user_data:
            user_name = self.user_data.get('name', '') or self.user_data.get('username', 'User')
            self.header.SetLabel(f"Hello, {user_name}")
            self.center_header_text()
        
        # Force layout refresh
        self.Layout()
        self.Refresh()

    def update_achievements_from_sessions(self, username, sessions, total_sessions):
        """Update user achievements based on session data"""
        if username not in self.account_manager.accounts:
            print(f"Warning: Username '{username}' not found in accounts. Cannot update achievements.")
            return
        
        print(f"Updating achievements for user '{username}': {total_sessions} sessions, {len(sessions)} session records")
        
        achievements = self.account_manager.accounts[username].get('achievements', {})
        updated = False
        
        # First Session: if total_sessions >= 1
        # Recalculate from scratch - check if total_sessions >= 1
        achievements['first_session'] = (total_sessions >= 1)
        if achievements['first_session']:
            updated = True
        
        # Ten Sessions: if total_sessions >= 10
        # Recalculate from scratch - check if total_sessions >= 10
        achievements['ten_sessions'] = (total_sessions >= 10)
        if achievements['ten_sessions']:
            updated = True
        
        # Perfect Form: any session >= 5 minutes (consecutive rowing)
        # Recalculate from scratch - check if any session is >= 5 minutes
        achievements['perfect_form'] = False
        for session in sessions:
            if session.get('time_minutes', 0) >= 5.0:
                achievements['perfect_form'] = True
                updated = True
                break
        
        # Endurance Master: any session >= 30 minutes
        # Recalculate from scratch - check if any session is >= 30 minutes
        achievements['endurance_master'] = False
        for session in sessions:
            if session.get('time_minutes', 0) >= 30.0:
                achievements['endurance_master'] = True
                updated = True
                break
        
        # Speed Demon: keep False (disregard for now)
        achievements['speed_demon'] = False
        
        # Week Warrior: 7 sessions in a single week
        # Recalculate from scratch - check if any week has 7+ sessions
        achievements['week_warrior'] = False
        # Group sessions by week
        weeks = defaultdict(list)
        for session in sessions:
            date_str = session.get('date', '')
            if date_str:
                try:
                    session_date = datetime.strptime(date_str, '%Y-%m-%d')
                    # Get ISO week number and year
                    year, week, _ = session_date.isocalendar()
                    weeks[f"{year}-W{week}"].append(session)
                except:
                    continue
        
        # Check if any week has 7+ sessions
        for week_sessions in weeks.values():
            if len(week_sessions) >= 7:
                achievements['week_warrior'] = True
                updated = True
                break
        
        # Monthly Milestone: 20 sessions in a month
        # Recalculate from scratch - check if any month has 20+ sessions
        achievements['monthly_milestone'] = False
        # Group sessions by month
        months = defaultdict(list)
        for session in sessions:
            date_str = session.get('date', '')
            if date_str:
                try:
                    session_date = datetime.strptime(date_str, '%Y-%m-%d')
                    month_key = f"{session_date.year}-{session_date.month:02d}"
                    months[month_key].append(session)
                except:
                    continue
        
        # Check if any month has 20+ sessions
        for month_sessions in months.values():
            if len(month_sessions) >= 20:
                achievements['monthly_milestone'] = True
                updated = True
                break
        
        # Consistency King: 5 consecutive days
        # Recalculate from scratch - check for 5 consecutive days
        achievements['consistency_king'] = False
        # Extract unique dates and sort them
        dates = []
        for session in sessions:
            date_str = session.get('date', '')
            if date_str:
                try:
                    session_date = datetime.strptime(date_str, '%Y-%m-%d')
                    dates.append(session_date.date())
                except:
                    continue
        
        # Remove duplicates and sort
        unique_dates = sorted(set(dates))
        
        # Check for 5 consecutive days
        if len(unique_dates) >= 5:
            consecutive_count = 1
            for i in range(1, len(unique_dates)):
                days_diff = (unique_dates[i] - unique_dates[i-1]).days
                if days_diff == 1:
                    consecutive_count += 1
                    if consecutive_count >= 5:
                        achievements['consistency_king'] = True
                        updated = True
                        break
                else:
                    consecutive_count = 1
        
        # Always update achievements and statistics, then save
        # Calculate longest distance and cumulative distance from sessions
        longest_distance = 0.0
        cumulative_distance = 0.0
        for session in sessions:
            distance = session.get('distance', 0.0)
            longest_distance = max(longest_distance, distance)
            cumulative_distance += distance  # Sum all session distances
        
        # Update all statistics based on session data
        self.account_manager.accounts[username]['achievements'] = achievements
        self.account_manager.accounts[username]['total_sessions'] = total_sessions
        self.account_manager.accounts[username]['longest_distance'] = longest_distance
        self.account_manager.accounts[username]['cumulative_distance_m'] = cumulative_distance
        
        # Save updated data to file
        self.account_manager.save_accounts()
        
        # Update local user_data if it exists
        if hasattr(self, 'user_data') and self.user_data and self.user_data.get('username') == username:
            self.user_data['achievements'] = achievements.copy()
            self.user_data['total_sessions'] = total_sessions
            self.user_data['longest_distance'] = longest_distance
            self.user_data['cumulative_distance_m'] = cumulative_distance
    
    def load_user_session_data(self, username):
        """Load session data from CSV file for a user"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        user_session_dir = os.path.join(script_dir, "user_session_data", username)
        csv_file = os.path.join(user_session_dir, "session_summary.csv")
        
        print(f"Loading session data for user '{username}' from: {csv_file}")
        print(f"CSV file exists: {os.path.exists(csv_file)}")
        
        sessions = []
        total_sessions = 0
        longest_distance = 0.0
        
        if os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Skip completely empty rows (all values are empty/whitespace)
                        if not any(str(v).strip() for v in row.values() if v):
                            continue
                        
                        # Skip invalid rows (check if Date field exists and is valid)
                        date_str = row.get("Date", "").strip() if row.get("Date") else ""
                        if not date_str or date_str.startswith("//") or date_str.startswith("```"):
                            continue
                        
                        # Parse time from "min:sec" format to total minutes
                        time_str = row.get("Total Time (min:sec)", "0:00")
                        if time_str is None:
                            time_str = "0:00"
                        time_str = str(time_str).strip()
                        
                        try:
                            if ':' in time_str:
                                parts = time_str.split(':')
                                minutes = int(parts[0])
                                seconds = int(parts[1])
                                total_minutes = minutes + (seconds / 60.0)
                            else:
                                total_minutes = float(time_str) if time_str else 0.0
                        except (ValueError, TypeError, IndexError):
                            total_minutes = 0.0
                        
                        # Parse distance
                        distance = 0.0
                        try:
                            distance_str = row.get("Total Distance (m)", "0")
                            if distance_str is not None and str(distance_str).strip():
                                distance = float(distance_str)
                                longest_distance = max(longest_distance, distance)
                        except (ValueError, TypeError):
                            distance = 0.0
                        
                        # Parse average power
                        avg_power = 0.0
                        try:
                            power_str = row.get("Average Power (W)", "0")
                            if power_str is not None and str(power_str).strip():
                                avg_power = float(power_str)
                        except (ValueError, TypeError):
                            avg_power = 0.0
                        
                        # Parse average accuracy
                        avg_accuracy = 0.0
                        try:
                            accuracy_str = row.get("Average Accuracy (%)", "0")
                            if accuracy_str is not None and str(accuracy_str).strip():
                                avg_accuracy = float(accuracy_str)
                        except (ValueError, TypeError):
                            avg_accuracy = 0.0
                        
                        sessions.append({
                            'date': date_str,
                            'time_minutes': total_minutes,
                            'distance': distance,
                            'avg_power': avg_power,
                            'avg_accuracy': avg_accuracy
                        })
                        total_sessions += 1
            except Exception as e:
                print(f"Error loading session data: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"CSV file does not exist: {csv_file}")
        
        # Update achievements based on session data
        self.update_achievements_from_sessions(username, sessions, total_sessions)
        
        return {
            'sessions': sessions,
            'total_sessions': total_sessions,
            'longest_distance': longest_distance
        }
    
    def create_demo_account(self):
        """Create a demo account if it doesn't exist"""
        if "demo" not in self.account_manager.accounts:
            # Create account for demo with password "password"
            self.account_manager.create_account("demo", "password", "demo")
            # Account data will be initialized with defaults from create_account
            self.account_manager.save_accounts()
    
    def require_login(self):
        """Show login dialog and require login before proceeding"""
        login_dialog = LoginDialog(self, self.account_manager)
        result = login_dialog.ShowModal()
        
        if result == wx.ID_OK and login_dialog.user_data:
            self.user_data = login_dialog.user_data
            self.current_username = self.user_data["username"]
            self.is_logged_in = True
            login_dialog.Destroy()
            # Notify start page to show logout button - use CallLater with delay to ensure UI updates
            # Call multiple times to ensure it works (with increasing delays)
            wx.CallLater(100, self.update_start_page_logout_button)
            wx.CallLater(300, self.update_start_page_logout_button)
            return True
        else:
            login_dialog.Destroy()
            return False
    
    def update_start_page_logout_button(self):
        """Update logout button visibility on start page"""
        parent = self.GetParent()
        if hasattr(parent, 'start_page') and hasattr(parent.start_page, 'update_logout_button'):
            try:
                parent.start_page.update_logout_button()
            except Exception as e:
                # If update fails, try again after a short delay
                wx.CallLater(100, parent.start_page.update_logout_button)
    
    def create_empty_layout(self):
        """Create an empty layout when login is cancelled"""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        empty_text = wx.StaticText(self, label="Please login to view your dashboard")
        empty_text.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        empty_text.SetForegroundColour(wx.Colour(100, 100, 100))
        main_sizer.Add(empty_text, 1, wx.ALIGN_CENTER | wx.ALL, 50)
        self.SetSizer(main_sizer)
    
    def create_layout(self):
        """Create the main dashboard layout"""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create header panel for absolute text positioning
        header_panel = wx.Panel(self)
        header_panel.SetBackgroundColour(self.GetBackgroundColour())
        header_panel.SetMinSize((-1, 100))
        
        # Header: Dynamic greeting based on user name (centered on screen using absolute positioning)
        user_name = self.user_data.get('name', '') or self.user_data.get('username', 'User') if self.user_data else 'User'
        header_text = f"Hello, {user_name}"
        self.header = wx.StaticText(header_panel, label=header_text)
        header_font = wx.Font(60, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.header.SetFont(header_font)
        self.header.SetForegroundColour(wx.Colour(33, 37, 41))
        
        # Bind size event to center the header text
        header_panel.Bind(wx.EVT_SIZE, self.on_header_size)
        
        # Add header panel to main sizer with reduced top margin
        main_sizer.Add(header_panel, 0, wx.EXPAND | wx.TOP, 20)
        
        # Reduced spacing after header to give more room to cards
        main_sizer.AddSpacer(15)

        # 2x2 grid of modern card sections - takes up almost the whole page
        grid_sizer = wx.FlexGridSizer(2, 2, 3, 3)  # Reduced gap between cards
        grid_sizer.AddGrowableCol(0, 1)
        grid_sizer.AddGrowableCol(1, 1)
        grid_sizer.AddGrowableRow(0, 1)  # Equal row heights
        grid_sizer.AddGrowableRow(1, 1)  # Equal row heights

        # Create modern card sections with user data
        self.section1_card = UserInfoCard(self, self.user_data)
        self.section2_card = StatisticsCard(self, self.session_data)
        self.section3_card = AchievementsCard(self, self.user_data)
        self.section4_card = MapCard(self, self.current_username if hasattr(self, 'current_username') else None)
        

        # Add sections with reduced padding for better fit
        grid_sizer.Add(self.section1_card, 1, wx.EXPAND | wx.ALL, 8)
        grid_sizer.Add(self.section2_card, 1, wx.EXPAND | wx.ALL, 8)
        grid_sizer.Add(self.section3_card, 1, wx.EXPAND | wx.ALL, 8)
        grid_sizer.Add(self.section4_card, 1, wx.EXPAND | wx.ALL, 8)

        # Add the grid to main sizer with reduced margins for better fit
        main_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 30)

        # Add spacer before button
        main_sizer.AddSpacer(20)

        # Create bottom sizer for "Selection Screen" button in bottom right
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add stretch spacer to push button to the right
        bottom_sizer.AddStretchSpacer()
        
        # Add "Selection Screen" button in bottom right - matching User Dashboard button style
        self.selection_card = ModernCard(self, "Selection Screen →", self.on_back_to_start, enabled=True, font_size=24)
        self.selection_card.SetMinSize((350, 70))
        bottom_sizer.Add(self.selection_card, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.BOTTOM, 30)
        
        # Add bottom sizer to main sizer
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        self.SetSizer(main_sizer)
        
        # Force layout and refresh
        self.Layout()
        self.Refresh()
        
        # Ensure logout button on start page is updated after layout is created
        # self.update_start_page_logout_button()  # COMMENTED OUT: Login functionality disabled
        
        # Trigger initial centering after layout
        wx.CallAfter(self.center_header_text)
    
    def center_header_text(self):
        """Center the header text exactly on screen (button stays in sizer, not affected)"""
        if not hasattr(self, 'header'):
            return
        
        # Get the header panel
        header_panel = self.header.GetParent()
        if not header_panel:
            return
            
        width, height = header_panel.GetSize()
        if width <= 0 or height <= 0:
            return
        
        # Center the header text EXACTLY on screen (screen center)
        header_width, header_height = self.header.GetSize()
        header_x = (width - header_width) // 2  # Exact center of screen
        header_y = (height - header_height) // 2  # Vertical center
        self.header.SetPosition((header_x, header_y))
    
    def on_header_size(self, event):
        """Handle header panel size event to center the text"""
        self.center_header_text()
        event.Skip()
    
    def on_back_to_start(self, event):
        """Navigate to selection screen"""
        parent = self.GetParent()
        parent.switch_to_start_page()
    
