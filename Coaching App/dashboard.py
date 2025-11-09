# dashboard page
import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from button import CustomButton
import os
import json
import hashlib
import secrets
from datetime import datetime

class AccountManager:
    """Manages user accounts and authentication"""
    def __init__(self):
        # Store accounts file in the same directory as dashboard.py (Coaching App folder)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.accounts_file = os.path.join(script_dir, "user_accounts.json")
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
        
        # Center the action button
        button_sizer.AddStretchSpacer()
        
        # Action button (Login/Register) - using ModernCard to match logout button style
        self.action_btn = ModernCard(self, "Login", self.on_action_click, enabled=True, font_size=18)
        self.action_btn.SetMinSize((100, 35))
        button_sizer.Add(self.action_btn, 0, wx.ALL, 10)
        
        button_sizer.AddStretchSpacer()

        main_sizer.Add(button_sizer, 0, wx.EXPAND)
        self.SetSizer(main_sizer)
        
        self.user_data = None
        
        # Prevent closing the dialog with the X button - users must log in
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
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
            username, password, email, name, age, None, None, gender
        )
        
        if success:
            wx.MessageBox(message, "Account Created", wx.OK | wx.ICON_INFORMATION)
            # Switch to login tab and fill in username
            self.notebook.SetSelection(0)
            self.login_username.SetValue(username)
            self.login_password.SetValue("")
            # Update button to show login
            self.action_btn.label_text = "Login"
            self.action_btn.Refresh()
        else:
            wx.MessageBox(message, "Registration Failed", wx.OK | wx.ICON_ERROR)
    
    def on_tab_changed(self, event):
        """Handle tab change event"""
        current_page = self.notebook.GetSelection()
        if current_page == 0:  # Login tab
            self.action_btn.label_text = "Login"
            self.action_btn.Refresh()
        else:  # Register tab
            self.action_btn.label_text = "Create"
            self.action_btn.Refresh()
    
    def on_action_click(self, event):
        """Handle action button click (Login or Register)"""
        current_page = self.notebook.GetSelection()
        if current_page == 0:  # Login tab
            self.on_login(event)
        else:  # Register tab
            self.on_register(event)
    
    def on_close(self, event):
        """Prevent closing the dialog - users must log in to proceed"""
        # Veto the close event to prevent the dialog from closing
        event.Veto()
        # Optionally show a message to inform the user
        wx.MessageBox("Please log in to access the dashboard.", "Login Required", wx.OK | wx.ICON_INFORMATION)
    
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
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = self.GetSize()
        
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
        
        # Title: "User Info"
        title = wx.StaticText(self, label="User Info")
        title_font = wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(self.text_color)
        main_sizer.Add(title, 0, wx.LEFT | wx.TOP, 30)
        
        # Add some spacing
        main_sizer.AddSpacer(20)
        
        # Create info fields
        info_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Store references to value labels for updating
        name_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        
        # Name field - on same line
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_label = wx.StaticText(self, label="Name:")
        name_label.SetFont(name_font)
        name_label.SetForegroundColour(self.text_color)
        name_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        self.name_value = wx.StaticText(self, label="")
        self.name_value.SetFont(name_font)
        self.name_value.SetForegroundColour(self.text_color)
        name_sizer.Add(self.name_value, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        info_sizer.Add(name_sizer, 0, wx.LEFT, 40)
        
        info_sizer.AddSpacer(15)
        
        # Total Sessions field - on same line
        sessions_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sessions_label = wx.StaticText(self, label="Total Sessions:")
        sessions_label.SetFont(name_font)
        sessions_label.SetForegroundColour(self.text_color)
        sessions_sizer.Add(sessions_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        self.sessions_value = wx.StaticText(self, label="")
        self.sessions_value.SetFont(name_font)
        self.sessions_value.SetForegroundColour(self.text_color)
        sessions_sizer.Add(self.sessions_value, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        info_sizer.Add(sessions_sizer, 0, wx.LEFT, 40)
        
        info_sizer.AddSpacer(15)
        
        # Best Stroke Rate field - on same line
        stroke_sizer = wx.BoxSizer(wx.HORIZONTAL)
        stroke_label = wx.StaticText(self, label="Best Stroke Rate:")
        stroke_label.SetFont(name_font)
        stroke_label.SetForegroundColour(self.text_color)
        stroke_sizer.Add(stroke_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        self.stroke_value = wx.StaticText(self, label="")
        self.stroke_value.SetFont(name_font)
        self.stroke_value.SetForegroundColour(self.text_color)
        stroke_sizer.Add(self.stroke_value, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        info_sizer.Add(stroke_sizer, 0, wx.LEFT, 40)
        
        main_sizer.Add(info_sizer, 1, wx.EXPAND)
        main_sizer.AddSpacer(30)
        
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
        
        best_stroke_rate = user_data.get('best_stroke_rate', 0)
        self.stroke_value.SetLabel(f"{best_stroke_rate} spm")
        
        self.Layout()
        
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
    def __init__(self, parent):
        super(StatisticsCard, self).__init__(parent)
        
        # Set base colors
        self.bg_color = wx.Colour(255, 255, 255)
        self.text_color = wx.Colour(33, 37, 41)
        self.SetBackgroundColour(self.bg_color)
        self.SetMinSize((380, 200))
        
        # Bind paint event for card styling
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        # Create a vertical sizer for the content
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title: "Statistics"
        title = wx.StaticText(self, label="Statistics")
        title_font = wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(self.text_color)
        main_sizer.Add(title, 0, wx.LEFT | wx.TOP, 30)
        
        # Add minimal spacing
        main_sizer.AddSpacer(2)
        
        # Create matplotlib figure and canvas (smaller to fit labels)
        self.figure = Figure(figsize=(3.2, 0.72), dpi=80, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)
        main_sizer.Add(self.canvas, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        
        # Add minimal bottom spacing
        main_sizer.AddSpacer(5)
        
        self.SetSizer(main_sizer)
        
        # Sample data for the graph (average power over days)
        self.days = list(range(1, 17))  # Days 1-16
        self.power_data = [20, 25, 18, 30, 35, 28, 40, 45, 38, 50, 55, 48, 60, 65, 58, 70]
        
        # Create the plot
        self.create_plot()
        
    def create_plot(self):
        """Create the matplotlib plot"""
        # Clear the figure
        self.figure.clear()
        
        # Create subplot
        ax = self.figure.add_subplot(111)
        
        # Plot the line with area fill
        ax.plot(self.days, self.power_data, color='#0066CC', linewidth=3, label='Average Power')
        ax.fill_between(self.days, self.power_data, alpha=0.3, color='#ADD8E6')
        
        # Set labels
        ax.set_xlabel('Weeks', fontsize=20, color='#212529', fontweight='normal')
        ax.set_ylabel('Average Power', fontsize=20, color='#212529', fontweight='normal')
        
        # Style the plot
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('white')
        
        # Remove top and right spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#212529')
        ax.spines['bottom'].set_color('#212529')
        
        # Set tick colors
        ax.tick_params(colors='#212529')
        
        # Adjust layout with more constrained margins to fit in smaller box
        self.figure.tight_layout(pad=0.5)
        
        # Set subplot parameters to ensure labels are visible in smaller constrained space
        self.figure.subplots_adjust(left=0.15, bottom=0.2, right=0.95, top=0.9)
        
        # Refresh the canvas
        self.canvas.draw()
        
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
        # Load images from root directory (parent of Coaching App)
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        achievement_path = os.path.join(script_dir, "achievement.png")
        locked_path = os.path.join(script_dir, "locked.png")
        
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
        
        # Title - using dashboard font style but adjusted size
        title_text = wx.StaticText(self, label=title, style=wx.ST_NO_AUTORESIZE)
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_text.SetFont(title_font)
        title_text.Wrap(240)  
        if unlocked:
            title_text.SetForegroundColour(wx.Colour(0, 0, 0))
            title_text.SetBackgroundColour(wx.Colour(76, 175, 80))
        else:
            title_text.SetForegroundColour(wx.Colour(100, 100, 100)) 
            title_text.SetBackgroundColour(wx.Colour(200, 200, 200, 30)) 
        text_sizer.Add(title_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        # Description - using dashboard font style but adjusted size
        desc_text = wx.StaticText(self, label=description, style=wx.ST_NO_AUTORESIZE)
        desc_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        desc_text.SetFont(desc_font)
        desc_text.Wrap(240)
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
        title_font = wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
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
    def __init__(self, parent):
        super(MapCard, self).__init__(parent)
        
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
        title_font = wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
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
        # Use the same approach as game_page.py
        script_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Helper function to create a location column
        def create_location_column(image_path, image_size, location_name, status_image_path, status_image_size):
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
            location_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            # Set text color: grey for locked locations, green for unlocked
            if "lock" in status_image_path.lower():
                location_text.SetForegroundColour(wx.Colour(128, 128, 128))  # Grey for locked
            else:
                location_text.SetForegroundColour(wx.Colour(0, 100, 0))  # Green for unlocked
            # Wrap text to fit within column width (approximately 1/5 of card width minus margins)
            location_text.Wrap(60)  # Approximate width for text wrapping
            location_sizer.Add(location_text, 0, wx.ALIGN_CENTER)
            
            # Add status image (check or lock)
            try:
                status_image = wx.Image(status_image_path, wx.BITMAP_TYPE_PNG)
                status_image = status_image.Scale(status_image_size, status_image_size, wx.IMAGE_QUALITY_HIGH)
                status_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(status_image))
                location_sizer.Add(status_bitmap, 0, wx.ALIGN_CENTER)
            except Exception as e:
                print(f"Error loading {status_image_path}: {e}")
                # Fallback to emoji
                status_text = wx.StaticText(self, label="✓" if "check" in status_image_path.lower() else "🔒")
                status_text.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
                status_text.SetForegroundColour(wx.Colour(0, 150, 0) if "check" in status_image_path.lower() else wx.Colour(100, 100, 100))
                location_sizer.Add(status_text, 0, wx.ALIGN_CENTER)
            
            return location_sizer
        
        # Create 5 location columns, each in its own equal-width column
        # Column 1: Hawaii
        hawaii_sizer = create_location_column(
            os.path.join(script_dir, "palm-tree.png"), 80,
            "Hawaii",
            os.path.join(script_dir, "check.png"), 40
        )
        items_sizer.Add(hawaii_sizer, 1, wx.EXPAND)
        
        # Column 2: Antarctica
        antarctica_sizer = create_location_column(
            os.path.join(script_dir, "iceberg.png"), 90,
            "Antarctica",
            os.path.join(script_dir, "lock.png"), 40
        )
        items_sizer.Add(antarctica_sizer, 1, wx.EXPAND)
        
        # Column 3: Amazon
        amazon_sizer = create_location_column(
            os.path.join(script_dir, "jungle.png"), 70,
            "Amazon",
            os.path.join(script_dir, "lock.png"), 40
        )
        items_sizer.Add(amazon_sizer, 1, wx.EXPAND)
        
        # Column 4: Japan
        japan_sizer = create_location_column(
            os.path.join(script_dir, "japan.png"), 80,
            "Japan",
            os.path.join(script_dir, "lock.png"), 40
        )
        items_sizer.Add(japan_sizer, 1, wx.EXPAND)
        
        # Column 5: Australia
        australia_sizer = create_location_column(
            os.path.join(script_dir, "australia.png"), 80,
            "Australia",
            os.path.join(script_dir, "lock.png"), 40
        )
        items_sizer.Add(australia_sizer, 1, wx.EXPAND)
        
        # Add the items sizer to main sizer
        main_sizer.Add(items_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 30)
        
        
        # Add stretch spacer to balance the line in center
        main_sizer.AddStretchSpacer()
        
        self.SetSizer(main_sizer)
        
        # Generate random dot positions
        self.dot_positions = self.generate_random_dots()
        
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
        
        # Use existing dot positions (don't regenerate each time)
        if not hasattr(self, 'dot_positions') or not self.dot_positions:
            self.dot_positions = self.generate_random_dots()
        
        # Draw the curved path first (behind the dots)
        if len(self.dot_positions) >= 4:
            path_color = wx.Colour(135, 206, 250)  # Light blue color like the image
            gc.SetPen(wx.Pen(path_color, 16))  # Slightly thicker for more presence
            
            # Create an organic, flowing path like the light blue curves in the image
            path = gc.CreatePath()
            
            # Get the dot positions
            x1, y1 = self.dot_positions[0]  # Start
            x2, y2 = self.dot_positions[1]  # Second
            x3, y3 = self.dot_positions[2]  # Third  
            x4, y4 = self.dot_positions[3]  # End
            
            # Create a flowing S-curve that meanders past the dots
            # Start at first dot
            path.MoveToPoint(x1, y1)
            
            # First curve: S-shaped curve down to second dot
            # Control point 1 - curves down and right
            ctrl1_x = x1 + (x2 - x1) // 3
            ctrl1_y = y1 + 40  # Curve down significantly
            # Control point 2 - curves back up to second dot
            ctrl2_x = x1 + 2 * (x2 - x1) // 3
            ctrl2_y = y2 - 20  # Curve up to approach second dot
            path.AddCubicCurveToPoint(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, x2, y2)
            
            # Second curve: C-shaped curve up to third dot
            # Control point 1 - curves up and right
            ctrl3_x = x2 + (x3 - x2) // 3
            ctrl3_y = y2 - 35  # Curve up significantly
            # Control point 2 - curves down to third dot
            ctrl4_x = x2 + 2 * (x3 - x2) // 3
            ctrl4_y = y3 + 15  # Curve down to approach third dot
            path.AddCubicCurveToPoint(ctrl3_x, ctrl3_y, ctrl4_x, ctrl4_y, x3, y3)
            
            # Third curve: S-shaped curve down to fourth dot
            # Control point 1 - curves down and right
            ctrl5_x = x3 + (x4 - x3) // 3
            ctrl5_y = y3 + 30  # Curve down
            # Control point 2 - curves back up to fourth dot
            ctrl6_x = x3 + 2 * (x4 - x3) // 3
            ctrl6_y = y4 - 10  # Curve up to approach fourth dot
            path.AddCubicCurveToPoint(ctrl5_x, ctrl5_y, ctrl6_x, ctrl6_y, x4, y4)
            
            # Draw the path
            gc.StrokePath(path)
        
        # Draw the 4 dots on top of the path
        dot_color = wx.Colour(76, 175, 80)  # Green color for dots
        gc.SetBrush(wx.Brush(dot_color))
        gc.SetPen(wx.Pen(dot_color, 2))
        
        # Make sure dots are visible by drawing them with a solid fill
        for x, y in self.dot_positions:
            # Draw a filled circle for each dot
            gc.DrawEllipse(x - 6, y - 6, 12, 12)  # 12x12 pixel dots
            # Also draw a smaller inner circle to make sure they're visible
            gc.DrawEllipse(x - 4, y - 4, 8, 8)  # 8x8 pixel inner circle

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
        
        # Create demo account if no accounts exist
        self.create_demo_account()
        
        # Require login before showing dashboard
        if not self.require_login():
            # If login was cancelled, show empty dashboard
            self.create_empty_layout()
            return
        
        # Create the dashboard layout
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
        
        # Create header sizer for title and login button
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add stretch spacer to center the title
        header_sizer.AddStretchSpacer()
        
        # Header: Dynamic greeting based on user name
        user_name = self.user_data.get('name', '') or self.user_data.get('username', 'User')
        header_text = f"Hello, {user_name}"
        self.header = wx.StaticText(self, label=header_text)
        header_font = wx.Font(36, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.header.SetFont(header_font)
        self.header.SetForegroundColour(wx.Colour(33, 37, 41))
        header_sizer.Add(self.header, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Add stretch spacer to center the title
        header_sizer.AddStretchSpacer()
        
        # Add header sizer to main sizer
        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 25)
        
        # Add elegant spacing after header
        main_sizer.AddSpacer(20)

        # 2x2 grid of modern card sections - takes up almost the whole page
        grid_sizer = wx.FlexGridSizer(2, 2, 5, 5)
        grid_sizer.AddGrowableCol(0, 1)
        grid_sizer.AddGrowableCol(1, 1)
        grid_sizer.AddGrowableRow(0, 35)  # Top row gets 35% of height
        grid_sizer.AddGrowableRow(1, 65)  # Bottom row gets 65% of height

        # Create modern card sections with user data
        self.section1_card = UserInfoCard(self, self.user_data)
        self.section2_card = StatisticsCard(self)
        self.section3_card = AchievementsCard(self, self.user_data)
        self.section4_card = MapCard(self)
        

        # Add sections with minimal padding to maximize space
        grid_sizer.Add(self.section1_card, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer.Add(self.section2_card, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer.Add(self.section3_card, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer.Add(self.section4_card, 1, wx.EXPAND | wx.ALL, 10)

        # Add the grid to main sizer with minimal margins
        main_sizer.Add(grid_sizer, 1, wx.EXPAND | wx.ALL, 20)

        # Small bottom spacer
        main_sizer.AddSpacer(20)

        # Create bottom sizer for "Selection Screen" button in bottom right
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add stretch spacer to push button to the right
        bottom_sizer.AddStretchSpacer()
        
        # Add "Selection Screen" button in bottom right - using ModernCard like start page
        self.selection_card = ModernCard(self, "Selection Screen", self.on_back_to_start, enabled=True, font_size=18)
        self.selection_card.SetMinSize((220, 50))  # 10% wider (200 * 1.1 = 220)
        bottom_sizer.Add(self.selection_card, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Add bottom sizer to main sizer
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 25)

        self.SetSizer(main_sizer)
        
        # Ensure logout button on start page is updated after layout is created
        self.update_start_page_logout_button()
    
    def on_back_to_start(self, event):
        parent = self.GetParent()
        parent.switch_to_start_page()
    
