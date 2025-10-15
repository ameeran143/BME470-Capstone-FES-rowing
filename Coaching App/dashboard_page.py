# dashboard page
import wx
import wx.lib.plot as plot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import os
from datetime import datetime, timedelta
import json
import hashlib
import secrets

class AccountManager:
    """Manages user accounts and authentication"""
    def __init__(self):
        self.accounts_file = "user_accounts.json"
        self.accounts = self.load_accounts()
    
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
        except:
            pass
    
    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt, password_hash.hex()
    
    def verify_password(self, password, salt, stored_hash):
        """Verify password against stored hash"""
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex() == stored_hash
    
    def create_account(self, username, password, email="", name="", age=None, height=None, weight=None, gender=""):
        """Create a new user account"""
        if username in self.accounts:
            return False, "Username already exists"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        salt, password_hash = self.hash_password(password)
        
        # Create default user data
        user_data = {
            "username": username,
            "email": email,
            "name": name,
            "age": age,
            "height": height,  # in cm
            "weight": weight,  # in kg
            "gender": gender,
            "password_salt": salt,
            "password_hash": password_hash,
            "created_date": datetime.now().isoformat(),
            "total_sessions": 0,
            "total_time": 0,
            "best_stroke_rate": 0,
            "achievements": {
                "first_session": False,
                "ten_sessions": False,
                "perfect_form": False,
                "endurance_master": False,
                "speed_demon": False
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
    """Enhanced login dialog with registration support"""
    def __init__(self, parent, account_manager):
        super(LoginDialog, self).__init__(parent, title="User Account", size=(500, 400))
        self.account_manager = account_manager
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        # Create notebook for login/register tabs
        self.notebook = wx.Notebook(self)
        
        # Login tab
        self.login_panel = self.create_login_panel()
        self.notebook.AddPage(self.login_panel, "Login")
        
        # Register tab
        self.register_panel = self.create_register_panel()
        self.notebook.AddPage(self.register_panel, "Create Account")
        
        # Bind tab change event
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_changed)
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 20)
        
        # Bottom buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add stretch spacer to push action button to the right
        button_sizer.AddStretchSpacer()

        # Cancel button
        self.cancel_btn = wx.Button(self, label="Cancel", size=(100, 35))
        self.cancel_btn.SetBackgroundColour(wx.Colour(158, 158, 158))
        self.cancel_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.cancel_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        button_sizer.Add(self.cancel_btn, 0, wx.ALL, 10)
        
        
        
        # Action button (Login/Register)
        self.action_btn = wx.Button(self, label="Login", size=(100, 35))
        self.action_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        self.action_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.action_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_action_click)
        button_sizer.Add(self.action_btn, 0, wx.ALL, 10)

        main_sizer.Add(button_sizer, 0, wx.EXPAND)
        self.SetSizer(main_sizer)
        
        self.user_data = None
    
    def create_login_panel(self):
        """Create login panel"""
        panel = wx.Panel(self.notebook)
        panel.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        
        # Title
        title = wx.StaticText(panel, label="Login to Your Account")
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        # Username field
        username_label = wx.StaticText(panel, label="Username:")
        username_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(username_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.login_username = wx.TextCtrl(panel, size=(300, 30))
        self.login_username.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.login_username, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        
        # Password field
        password_label = wx.StaticText(panel, label="Password:")
        password_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(password_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.login_password = wx.TextCtrl(panel, size=(300, 30), style=wx.TE_PASSWORD)
        self.login_password.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.login_password, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        
        
        
        # Demo account info
        demo_info = wx.StaticText(panel, label="Demo Account: username='demo', password='demo123'")
        demo_info.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        demo_info.SetForegroundColour(wx.Colour(100, 100, 100))
        sizer.Add(demo_info, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel
    
    def create_register_panel(self):
        """Create registration panel"""
        panel = wx.Panel(self.notebook)
        panel.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        # Create scrollable panel for more fields
        scroll_panel = wx.ScrolledWindow(panel)
        scroll_panel.SetScrollRate(0, 10)
        scroll_panel.SetMinSize((500, 400))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        
        # Title
        title = wx.StaticText(scroll_panel, label="Create New Account")
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 15)
        
        # Name field
        name_label = wx.StaticText(scroll_panel, label="Full Name:")
        name_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(name_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.reg_name = wx.TextCtrl(scroll_panel, size=(300, 30))
        self.reg_name.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_name, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Username field
        username_label = wx.StaticText(scroll_panel, label="Username:")
        username_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(username_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.reg_username = wx.TextCtrl(scroll_panel, size=(300, 30))
        self.reg_username.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_username, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Password section
        password_label = wx.StaticText(scroll_panel, label="Password (min 6 characters):")
        password_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(password_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 20)
        
        self.reg_password = wx.TextCtrl(scroll_panel, size=(300, 30), style=wx.TE_PASSWORD)
        self.reg_password.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_password, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Confirm password field
        confirm_label = wx.StaticText(scroll_panel, label="Confirm Password:")
        confirm_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(confirm_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.reg_confirm = wx.TextCtrl(scroll_panel, size=(300, 30), style=wx.TE_PASSWORD)
        self.reg_confirm.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_confirm, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        # Email field
        email_label = wx.StaticText(scroll_panel, label="Email (optional):")
        email_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(email_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.reg_email = wx.TextCtrl(scroll_panel, size=(300, 30))
        self.reg_email.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_email, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Personal info section
        personal_label = wx.StaticText(scroll_panel, label="Personal Information (optional):")
        personal_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        personal_label.SetFont(personal_font)
        personal_label.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(personal_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 20)
        
        # Age field
        age_label = wx.StaticText(scroll_panel, label="Age:")
        age_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(age_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 15)
        
        self.reg_age = wx.SpinCtrl(scroll_panel, size=(100, 30), min=1, max=120, initial=25)
        self.reg_age.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_age, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Gender field
        gender_label = wx.StaticText(scroll_panel, label="Gender:")
        gender_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(gender_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.reg_gender = wx.Choice(scroll_panel, size=(150, 30), choices=["", "Male", "Female", "Other", "Prefer not to say"])
        self.reg_gender.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_gender, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Height field
        height_label = wx.StaticText(scroll_panel, label="Height (cm):")
        height_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(height_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.reg_height = wx.SpinCtrl(scroll_panel, size=(100, 30), min=50, max=250, initial=170)
        self.reg_height.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_height, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Weight field
        weight_label = wx.StaticText(scroll_panel, label="Weight (kg):")
        weight_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(weight_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.reg_weight = wx.SpinCtrl(scroll_panel, size=(100, 30), min=20, max=300, initial=70)
        self.reg_weight.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.reg_weight, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        

        
        scroll_panel.SetSizer(sizer)
        
        # Main panel sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(scroll_panel, 1, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(main_sizer)
        
        return panel
    
    def on_login(self, event):
        """Handle login button click"""
        username = self.login_username.GetValue().strip()
        password = self.login_password.GetValue()
        
        if not username or not password:
            wx.MessageBox("Please enter both username and password", "Login Error", wx.OK | wx.ICON_ERROR)
            return
        
        success, result = self.account_manager.authenticate(username, password)
        
        if success:
            self.user_data = result
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(result, "Login Failed", wx.OK | wx.ICON_ERROR)
    
    def on_register(self, event):
        """Handle registration button click"""
        username = self.reg_username.GetValue().strip()
        email = self.reg_email.GetValue().strip()
        name = self.reg_name.GetValue().strip()
        age = self.reg_age.GetValue()
        height = self.reg_height.GetValue()
        weight = self.reg_weight.GetValue()
        gender = self.reg_gender.GetStringSelection()
        password = self.reg_password.GetValue()
        confirm = self.reg_confirm.GetValue()
        
        if not username or not password:
            wx.MessageBox("Please enter username and password", "Registration Error", wx.OK | wx.ICON_ERROR)
            return
        
        if password != confirm:
            wx.MessageBox("Passwords do not match", "Registration Error", wx.OK | wx.ICON_ERROR)
            return
        
        # Convert empty strings to None for optional fields
        if not name:
            name = ""
        if not email:
            email = ""
        if not gender:
            gender = ""
        
        success, message = self.account_manager.create_account(
            username, password, email, name, age, height, weight, gender
        )
        
        if success:
            wx.MessageBox(message, "Account Created", wx.OK | wx.ICON_INFORMATION)
            # Switch to login tab and fill in username
            self.notebook.SetSelection(0)
            self.login_username.SetValue(username)
            self.login_password.SetValue("")
            # Update button to show login
            self.action_btn.SetLabel("Login")
            self.action_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        else:
            wx.MessageBox(message, "Registration Failed", wx.OK | wx.ICON_ERROR)
    
    def on_tab_changed(self, event):
        """Handle tab change event"""
        current_page = self.notebook.GetSelection()
        if current_page == 0:  # Login tab
            self.action_btn.SetLabel("Login")
            self.action_btn.SetBackgroundColour(wx.Colour(76, 175, 80))  # Green
        else:  # Register tab
            self.action_btn.SetLabel("Create")
            self.action_btn.SetBackgroundColour(wx.Colour(33, 150, 243))  # Blue
    
    def on_action_click(self, event):
        """Handle action button click (Login or Register)"""
        current_page = self.notebook.GetSelection()
        if current_page == 0:  # Login tab
            self.on_login(event)
        else:  # Register tab
            self.on_register(event)
    
    def on_cancel(self, event):
        """Handle cancel button click"""
        self.EndModal(wx.ID_CANCEL)

class AchievementCard(wx.Panel):
    """Individual achievement card with icon and better display"""
    def __init__(self, parent, title, description, unlocked=False):
        super(AchievementCard, self).__init__(parent)
        self.unlocked = unlocked
        self.title = title
        self.description = description
        
        # Set background color based on unlock status
        #if unlocked:
         #   self.SetBackgroundColour(wx.Colour(76, 175, 80, 30))  # Light green
            
        #else:
         #   self.SetBackgroundColour(wx.Colour(200, 200, 200, 30))  # Light gray
        
        self.SetMinSize((300, 100))
        
        # Create horizontal sizer for icon and text
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSpacer(10)
        
        # Achievement icon
        #icon_panel = wx.Panel(self)
        #icon_panel.SetMinSize((60, 60))
        #if unlocked:
         #   icon_panel.SetBackgroundColour(wx.Colour(76, 175, 80))
        #else:
         #   icon_panel.SetBackgroundColour(wx.Colour(150, 150, 150))
        
        # Create icon (using text symbol for now)
        '''
        if unlocked:
            icon_text = wx.StaticText(icon_panel, label="★")
            icon_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            icon_text.SetForegroundColour(wx.Colour(255, 215, 0))  # Gold color
        else:
            icon_text = wx.StaticText(icon_panel, label="●")
            icon_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            icon_text.SetForegroundColour(wx.Colour(200, 200, 200))  # Gray color
        
        icon_text.SetFont(icon_font)
        
        icon_sizer = wx.BoxSizer(wx.VERTICAL)
        icon_sizer.Add(icon_text, 1, wx.ALIGN_CENTER)
        icon_panel.SetSizer(icon_sizer)
        
        main_sizer.Add(icon_panel, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        '''
        # Replace the icon panel block with achievement or locked icon
        if unlocked and os.path.exists("achievement.png"):
            img = wx.Image("achievement.png", wx.BITMAP_TYPE_ANY)
            img = img.Scale(48, 48, wx.IMAGE_QUALITY_HIGH)
            icon = wx.StaticBitmap(self, -1, wx.Bitmap(img))
            icon.SetBackgroundColour(wx.Colour(76, 175, 80))
        elif os.path.exists("locked.png"):
            img = wx.Image("locked.png", wx.BITMAP_TYPE_ANY)
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
        
        # Title
        title_text = wx.StaticText(self, label=title, style=wx.ST_NO_AUTORESIZE)
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_text.SetFont(title_font)
        title_text.Wrap(280)  
        if unlocked:
            title_text.SetForegroundColour(wx.Colour(0, 0, 0))  # 76, 175, 80
            title_text.SetBackgroundColour(wx.Colour(76, 175, 80))
        else:
            title_text.SetForegroundColour(wx.Colour(100, 100, 100)) 
            title_text.SetBackgroundColour(wx.Colour(200, 200, 200, 30)) 
        text_sizer.Add(title_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # Description
        desc_text = wx.StaticText(self, label=description, style=wx.ST_NO_AUTORESIZE)
        desc_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        desc_text.SetFont(desc_font)
        desc_text.Wrap(500)
        if unlocked:
            desc_text.SetForegroundColour(wx.Colour(50, 50, 50))
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

class DashboardPage(wx.Panel):
    def __init__(self, parent):
        super(DashboardPage, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.account_manager = AccountManager()
        self.user_data = None
        self.is_logged_in = False
        self.current_username = None
        
        # Create main layout
        self.create_layout()
        
    def create_demo_account(self):
        """Create a demo account if no accounts exist"""
        if not self.account_manager.accounts:
            self.account_manager.create_account("demo", "demo123", "demo@example.com")
            # Add some demo data
            demo_data = self.account_manager.accounts["demo"]
            demo_data.update({
                "total_sessions": 15,
                "total_time": 120,
                "best_stroke_rate": 32,
                "achievements": {
                    "first_session": True,
                    "ten_sessions": True,
                    "perfect_form": False,
                    "endurance_master": False,
                    "speed_demon": True
                },
                "progress_level": 3,
                "last_session": "2024-01-15"
            })
            self.account_manager.save_accounts()
    
    def create_layout(self):
        """Create the main dashboard layout"""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top bar with login/logout
        top_bar = wx.BoxSizer(wx.HORIZONTAL)
        
        # Title
        self.title = wx.StaticText(self, label="User Dashboard")
        title_font = wx.Font(34, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)
        self.title.SetForegroundColour(wx.Colour(33, 37, 41))
        top_bar.Add(self.title, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        top_bar.AddStretchSpacer()
        
        # Login/Logout button
        self.auth_btn = wx.Button(self, label="Login", size=(100, 40))
        self.auth_btn.SetBackgroundColour(wx.Colour(76, 175, 80))
        self.auth_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.auth_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.auth_btn.Bind(wx.EVT_BUTTON, self.on_auth_click)
        top_bar.Add(self.auth_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        
        main_sizer.Add(top_bar, 0, wx.EXPAND)
        
        # Main content area - 2x2 grid with smaller spacing
        content_sizer = wx.FlexGridSizer(2, 2, 5, 5)
        content_sizer.AddGrowableCol(0, 1)
        content_sizer.AddGrowableCol(1, 1)
        content_sizer.AddGrowableRow(0, 1)
        content_sizer.AddGrowableRow(1, 1)
        
        # Top Left: User Dashboard Info
        self.user_info_panel = self.create_user_info_panel()
        content_sizer.Add(self.user_info_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # Top Right: Graphs
        self.graphs_panel = self.create_graphs_panel()
        content_sizer.Add(self.graphs_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # Bottom Left: Achievements
        self.achievements_panel = self.create_achievements_panel()
        content_sizer.Add(self.achievements_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # Bottom Right: Map
        self.map_panel = self.create_map_panel()
        content_sizer.Add(self.map_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(content_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        main_sizer.AddSpacer(10)
        
        # Back button
        back_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.back_btn = wx.Button(self, label="← Main Menu", size=(200, 50))
        self.back_btn.SetBackgroundColour(wx.Colour(158, 158, 158))
        self.back_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        self.back_btn.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.back_btn.Bind(wx.EVT_BUTTON, self.on_back)
        back_sizer.Add(self.back_btn, 0, wx.LEFT | wx.BOTTOM, 20)
        back_sizer.AddStretchSpacer()
        main_sizer.Add(back_sizer, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        self.update_display()
    
    def create_user_info_panel(self):
        """Create user information panel (top left)"""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        panel.SetMinSize((400, 300))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        
        # Panel title
        title = wx.StaticText(panel, label="User Information")
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.user_info_scroll = wx.ScrolledWindow(panel)
        self.user_info_scroll.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.user_info_scroll.SetScrollRate(0, 10)

        # User info content
        self.user_info_content = wx.StaticText(self.user_info_scroll, label="Please login to view your information")
        self.user_info_content.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.user_info_content.SetForegroundColour(wx.Colour(100, 100, 100))
        sizer.Add(self.user_info_scroll, 1, wx.EXPAND | wx.ALL, 10)
        
        self.user_info_content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.user_info_content_sizer.Add(self.user_info_content, 1, wx.EXPAND | wx.ALL, 20)
        self.user_info_scroll.SetSizer(self.user_info_content_sizer)

        panel.SetSizer(sizer)
        return panel
    
    def create_graphs_panel(self):
        """Create graphs panel (top right)"""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        panel.SetMinSize((400, 300))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        
        # Panel title
        title = wx.StaticText(panel, label="Performance Graphs")
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        # Create scrollable window for graphs
        self.graphs_scroll = wx.ScrolledWindow(panel)
        self.graphs_scroll.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.graphs_scroll.SetScrollRate(10, 10)
        
        # Graph placeholder
        self.graph_placeholder = wx.StaticText(self.graphs_scroll, label="Login to view your performance data")
        self.graph_placeholder.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.graph_placeholder.SetForegroundColour(wx.Colour(100, 100, 100))
        
        # Create sizer for scrollable content
        self.graphs_content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.graphs_content_sizer.Add(self.graph_placeholder, 1, wx.EXPAND | wx.ALL, 20)
        self.graphs_scroll.SetSizer(self.graphs_content_sizer)
        
        
        sizer.Add(self.graphs_scroll, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel
    
    def create_achievements_panel(self):
        """Create achievements panel (bottom left)"""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        panel.SetMinSize((400, 300))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        
        # Panel title
        title = wx.StaticText(panel, label="Achievements")
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        # Achievements scroll area
        self.achievements_scroll = wx.ScrolledWindow(panel)
        self.achievements_scroll.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.achievements_scroll.SetScrollRate(0, 10)
        
        self.achievements_sizer = wx.BoxSizer(wx.VERTICAL)
        self.achievements_scroll.SetSizer(self.achievements_sizer)
        
        sizer.Add(self.achievements_scroll, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel
    
    def create_map_panel(self):
        """Create map panel (bottom right)"""
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        panel.SetMinSize((400, 300))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        
        # Panel title
        title = wx.StaticText(panel, label="Progress Map")
        title_font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        # Map content
        self.map_content = wx.Panel(panel)
        self.map_content.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        self.map_sizer = wx.BoxSizer(wx.VERTICAL)
        self.map_content.SetSizer(self.map_sizer)

        # Placeholder (visible before login)
        self.map_placeholder = wx.StaticText(self.map_content, label="Login to unlock the map")
        self.map_placeholder.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.map_placeholder.SetForegroundColour(wx.Colour(100, 100, 100))
        #self.map_sizer.AddStretchSpacer()
        self.map_sizer.Add(self.map_placeholder, 1, wx.EXPAND | wx.ALL, 20)
        #self.map_sizer.AddStretchSpacer()

        sizer.Add(self.map_content, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        return panel
    
    def on_auth_click(self, event):
        """Handle login/logout button click"""
        if not self.is_logged_in:
            # Create demo account if no accounts exist
            self.create_demo_account()
            
            # Show login dialog
            login_dialog = LoginDialog(self, self.account_manager)
            result = login_dialog.ShowModal()
            
            if result == wx.ID_OK and login_dialog.user_data:
                self.user_data = login_dialog.user_data
                self.current_username = self.user_data["username"]
                self.is_logged_in = True
                self.auth_btn.SetLabel("Logout")
                self.auth_btn.SetBackgroundColour(wx.Colour(244, 67, 54))  # Red for logout
                self.update_display()
            
            login_dialog.Destroy()
        else:
            # Logout
            self.is_logged_in = False
            self.user_data = None
            self.current_username = None
            self.auth_btn.SetLabel("Login")
            self.auth_btn.SetBackgroundColour(wx.Colour(76, 175, 80))  # Green for login
            self.update_display()
    
    def update_display(self):
        """Update the display based on login status"""
        if self.is_logged_in:
            self.update_user_info()
            self.update_graphs()
            self.update_achievements()
            self.update_map()
        else:
            self.user_info_content.SetLabel("Please login to view your information")
            self.clear_graphs()
            self.clear_map()
            self.clear_achievements()
    
    def update_user_info(self):
        """Update user information display"""
        if self.user_data:
            last_session = self.user_data.get('last_session', 'Never')
            if last_session:
                last_session = last_session.split('T')[0] if 'T' in str(last_session) else str(last_session)
            else:
                last_session = 'Never'
            
            # Format personal information
            name = self.user_data.get('name', 'DEMO USER')
            email = self.user_data.get('email', 'abcd@gmail.com')
            age = self.user_data.get('age', '51')
            height = self.user_data.get('height', '175')
            weight = self.user_data.get('weight', '70')
            gender = self.user_data.get('gender', 'Male')
            
            # Format height and weight with units
            if height != 'Not provided' and height is not None:
                height = f"{height} cm"
            if weight != 'Not provided' and weight is not None:
                weight = f"{weight} kg"
            if age != 'Not provided' and age is not None:
                age = f"{age} years"
                
            info_text = f"""Name: {name}
Username: {self.user_data['username']}
Email: {email}

Personal Info:
Age: {age}
Height: {height}
Weight: {weight}
Gender: {gender}

Rowing Stats:
Total Sessions: {self.user_data['total_sessions']}
Total Time: {self.user_data['total_time']} minutes
Best Stroke Rate: {self.user_data['best_stroke_rate']} spm
Progress Level: {self.user_data['progress_level']}/5

Last Session: {last_session}
Account Created: {self.user_data.get('created_date', 'Unknown').split('T')[0]}"""
            
            self.user_info_content.SetLabel(info_text)
            self.user_info_content.SetForegroundColour(wx.Colour(33, 37, 41))
            self.user_info_scroll.Layout()
            self.user_info_scroll.FitInside()

    def update_graphs(self):
        """Update graphs display"""
        # Hide placeholder when logged in
        self.graph_placeholder.Hide()
        
        # Create a simple matplotlib graph
        try:
            # Clear existing content from scroll area
            for child in self.graphs_scroll.GetChildren():
                if isinstance(child, FigureCanvas):
                    child.Destroy()
            
            # Get scroll area size for auto-fitting
            scroll_size = self.graphs_scroll.GetSize()
            if scroll_size.width > 0 and scroll_size.height > 0:
                # Calculate figure size based on available space
                dpi = 80
                fig_width = 6
                fig_height = max(4, scroll_size.height / dpi)
            else:
                # Default size if scroll area not ready
                fig_width, fig_height = 6, 4
                dpi = 80
            
            # Create figure that fits the available space
            fig = Figure(figsize=(fig_width, fig_height), dpi=dpi)
            ax = fig.add_subplot(111)
            
            # Generate sample data based on user progress
            days = np.arange(1, 8)
            stroke_rates = np.random.normal(self.user_data['best_stroke_rate'], 2, 7)
            stroke_rates = np.clip(stroke_rates, 20, 40)  # Realistic range
            
            ax.plot(days, stroke_rates, 'b-o', linewidth=2, markersize=6)
            ax.set_title('Weekly Stroke Rate', fontsize=12, fontweight='bold')
            ax.set_xlabel('Day', fontsize=10)
            ax.set_ylabel('Stroke Rate (spm)', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(20, 40)
            
            # Auto-fit the plot to the figure
            fig.tight_layout(pad=1.0)
            
            # Create canvas
            canvas = FigureCanvas(self.graphs_scroll, -1, fig)
            
            # Add canvas to scroll area with proper sizing
            self.graphs_content_sizer.Add(canvas, 1, wx.EXPAND | wx.ALL, 5)
            
            # Update scroll area layout
            self.graphs_scroll.FitInside()
            self.graphs_scroll.Layout()
            
        except Exception as e:
            # Show error in placeholder
            self.graph_placeholder.Show()
            self.graph_placeholder.SetLabel(f"Graph display error: {str(e)}")
            self.graphs_scroll.FitInside()
    

    def clear_graphs(self):
        if not self.is_logged_in or not self.user_data:
            # Clear any existing graphs first
            for child in self.graphs_scroll.GetChildren():
                if isinstance(child, FigureCanvas):
                    child.Destroy()
            
            # Show placeholder when not logged in
            self.graphs_scroll.Show()
            self.graph_placeholder.Show()
            self.graph_placeholder.SetLabel("Login to view your performance data")
            self.graphs_scroll.FitInside()
            return

    def update_achievements(self):
        """Update achievements display"""
        # Clear existing achievements
        self.clear_achievements()
        
        # Define achievements with more detailed descriptions
        achievements = [
            ("First Session", "Complete your first rowing session to get started on your rowing journey", self.user_data['achievements']['first_session']),
            ("Ten Sessions", "Complete 10 rowing sessions to build consistency and habit", self.user_data['achievements']['ten_sessions']),
            ("Perfect Form", "Maintain perfect rowing form for 5 consecutive minutes", self.user_data['achievements']['perfect_form']),
            ("Endurance Master", "Row continuously for 30+ minutes without stopping", self.user_data['achievements']['endurance_master']),
            ("Speed Demon", "Achieve a stroke rate of 35+ strokes per minute", self.user_data['achievements']['speed_demon']),
            ("Week Warrior", "Complete 7 rowing sessions in a single week", self.user_data['achievements'].get('week_warrior', False)),
            ("Monthly Milestone", "Complete 20 rowing sessions in a month", self.user_data['achievements'].get('monthly_milestone', False)),
            ("Consistency King", "Row for 5 consecutive days", self.user_data['achievements'].get('consistency_king', False))
        ]
        
        # Add some spacing at the top
        self.achievements_sizer.AddSpacer(10)
        
        # Create achievement cards
        for title, description, unlocked in achievements:
            card = AchievementCard(self.achievements_scroll, title, description, unlocked)
            self.achievements_sizer.Add(card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        
        # Add spacing at the bottom
        self.achievements_sizer.AddSpacer(10)
        
        self.achievements_scroll.Layout()
        self.achievements_scroll.FitInside()
    
    def clear_achievements(self):
        """Clear all achievement cards"""
        for child in self.achievements_scroll.GetChildren():
            if isinstance(child, AchievementCard):
                child.Destroy()
        self.achievements_scroll.Layout()
    
    def update_map(self):
        """Update the progress map visualization showing the user's journey through different milestones"""
        # Hide placeholder
        if hasattr(self, 'map_placeholder'):
            self.map_placeholder.Hide()

        # Clear map content
        for child in self.map_content.GetChildren():
            if child != self.map_placeholder:
                child.Destroy()

        map_sizer = wx.BoxSizer(wx.VERTICAL)

        milestones = [
            ("Beginner's Beach", "Complete your first session", 1),
            ("Training Bay", "Complete 5 sessions", 2),
            ("Technique Lagoon", "Maintain good form", 3),
            ("Endurance Island", "Row for 30+ minutes", 4),
            ("Champion's Coast", "Master all challenges", 5)
        ]
        current_level = self.user_data.get('progress_level', 0)

        if current_level >= 1:
            scroll = wx.ScrolledWindow(self.map_content)
            scroll.SetBackgroundColour(wx.Colour(240, 240, 240))
            scroll.SetScrollRate(20, 20)
            content_sizer = wx.BoxSizer(wx.VERTICAL)
            content_sizer.AddSpacer(20)

            for i, (location, requirement, level) in enumerate(milestones):
                milestone_sizer = wx.BoxSizer(wx.HORIZONTAL)
                milestone_sizer.AddSpacer(40)

                image_file = "palm-tree.png" if level <= current_level else "locked.png"
                if os.path.exists(image_file):
                    img = wx.Image(image_file, wx.BITMAP_TYPE_ANY)
                    img = img.Scale(32, 32, wx.IMAGE_QUALITY_HIGH)
                    icon = wx.StaticBitmap(scroll, -1, wx.Bitmap(img))
                else:
                    icon = wx.StaticText(scroll, label="●")
                    icon.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

                milestone_sizer.Add(icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

                text_sizer = wx.BoxSizer(wx.VERTICAL)
                location_text = wx.StaticText(scroll, label=location)
                location_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                location_text.SetForegroundColour(wx.Colour(76, 175, 80) if level <= current_level else wx.Colour(150, 150, 150))
                text_sizer.Add(location_text)

                req_text = wx.StaticText(scroll, label=requirement)
                req_text.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                text_sizer.Add(req_text, 0, wx.TOP, 2)
                milestone_sizer.Add(text_sizer, 1, wx.EXPAND | wx.ALL, 5)

                if level <= current_level:
                    status = wx.StaticText(scroll, label="✓")
                    status.SetForegroundColour(wx.Colour(76, 175, 80))
                else:
                    status = wx.StaticText(scroll, label=f"Level {level}")
                    status.SetForegroundColour(wx.Colour(150, 150, 150))
                status.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                milestone_sizer.Add(status, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
                content_sizer.Add(milestone_sizer, 0, wx.EXPAND | wx.ALL, 5)

                if i < len(milestones) - 1:
                    line = wx.StaticLine(scroll, style=wx.LI_HORIZONTAL)
                    content_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 80)

            content_sizer.AddSpacer(20)
            scroll.SetSizer(content_sizer)
            map_sizer.Add(scroll, 1, wx.EXPAND)

        else:
            self.map_placeholder.SetLabel("Complete your first session to begin your journey!")
            self.map_placeholder.Show()
            map_sizer.Add(self.map_placeholder, 1, wx.EXPAND | wx.ALL, 20)

        self.map_content.SetSizer(map_sizer)
        self.map_content.Layout()


    def clear_map(self):
        """Clear map and restore placeholder after logout"""
        for child in self.map_content.GetChildren():
            child.Destroy()

        empty_sizer = wx.BoxSizer(wx.VERTICAL)
        empty_sizer.AddStretchSpacer()
        self.map_placeholder = wx.StaticText(self.map_content, label="Login to unlock the map")
        self.map_placeholder.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.map_placeholder.SetForegroundColour(wx.Colour(100, 100, 100))
        empty_sizer.Add(self.map_placeholder, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        empty_sizer.AddStretchSpacer()

        self.map_content.SetSizer(empty_sizer)
        self.map_content.Layout()

    def on_back(self, event):
        """Handle back button click"""
        parent = self.GetParent()
        if hasattr(parent, 'switch_to_start_page'):
            parent.switch_to_start_page()
        else:
            wx.MessageBox("Navigation not available", "Info")
