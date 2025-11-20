import wx
from game_page import ModernCard
from dashboard import AccountManager

class TitlePage(wx.Panel):
    def __init__(self, parent):
        super(TitlePage, self).__init__(parent)
        # Light gradient-like background
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header panel for title
        header_panel = wx.Panel(self)
        header_panel.SetBackgroundColour(self.GetBackgroundColour())
        
        # Main Title: "RowQuest"
        self.title = wx.StaticText(header_panel, label="RowQuest")
        title_font = wx.Font(96, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)
        self.title.SetForegroundColour(wx.Colour(33, 37, 41))
        
        # Subtitle
        self.subtitle = wx.StaticText(header_panel, label="Functional Electrical Stimulation Rowing Interface")
        subtitle_font = wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.subtitle.SetFont(subtitle_font)
        self.subtitle.SetForegroundColour(wx.Colour(100, 100, 100))
        
        # Use a sizer for the header panel to center things
        header_sizer = wx.BoxSizer(wx.VERTICAL)
        header_sizer.AddStretchSpacer()
        header_sizer.Add(self.title, 0, wx.ALIGN_CENTER)
        header_sizer.Add(self.subtitle, 0, wx.ALIGN_CENTER | wx.TOP, 20)
        header_sizer.AddStretchSpacer()
        header_panel.SetSizer(header_sizer)
        
        main_sizer.Add(header_panel, 1, wx.EXPAND)
        
        # Start Button
        self.start_button = ModernCard(self, "Start", self.on_start, enabled=True, font_size=36)
        self.start_button.SetMinSize((300, 100))
        
        button_container = wx.BoxSizer(wx.HORIZONTAL)
        button_container.AddStretchSpacer()
        button_container.Add(self.start_button, 0, wx.ALIGN_CENTER)
        button_container.AddStretchSpacer()
        
        main_sizer.Add(button_container, 0, wx.EXPAND | wx.BOTTOM, 100)
        
        self.SetSizer(main_sizer)
        
    def on_start(self, event):
        parent = self.GetParent()
        parent.switch_to_login_page()


class LoginPage(wx.Panel):
    """Full screen login page adapted from LoginDialog"""
    def __init__(self, parent):
        super(LoginPage, self).__init__(parent)
        self.account_manager = AccountManager()
        self.user_data = None
        self.is_register_mode = False
        
        # Match app background color
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top spacer
        main_sizer.AddSpacer(60)
        
        # Large title
        self.title_label = wx.StaticText(self, label="User Login")
        title_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title_label.SetFont(title_font)
        self.title_label.SetForegroundColour(wx.Colour(33, 37, 41))
        main_sizer.Add(self.title_label, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        # Spacer
        main_sizer.AddSpacer(30)
        
        # Form card container
        self.form_card = wx.Panel(self)
        self.form_card.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.form_card.SetMinSize((500, -1))
        
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
        
        self.reg_name = wx.TextCtrl(self.form_card, size=(440, 45))
        self.reg_name.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.reg_name.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.reg_name.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(self.reg_name, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 30)
        self.reg_name.Hide()
        
        # Username field
        username_label = wx.StaticText(self.form_card, label="Username")
        username_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        username_label.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(username_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 30)
        
        self.login_username = wx.TextCtrl(self.form_card, size=(440, 45))
        self.login_username.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.login_username.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.login_username.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(self.login_username, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 30)
        
        # Password field
        password_label = wx.StaticText(self.form_card, label="Password")
        password_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        password_label.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(password_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 30)
        
        self.login_password = wx.TextCtrl(self.form_card, size=(440, 45), style=wx.TE_PASSWORD)
        self.login_password.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.login_password.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.login_password.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(self.login_password, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 30)
        
        # Confirm password field (hidden by default, for registration)
        self.confirm_password_label = wx.StaticText(self.form_card, label="Confirm Password")
        self.confirm_password_label.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.confirm_password_label.SetForegroundColour(wx.Colour(33, 37, 41))
        form_sizer.Add(self.confirm_password_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 30)
        self.confirm_password_label.Hide()
        
        self.reg_confirm = wx.TextCtrl(self.form_card, size=(440, 45), style=wx.TE_PASSWORD)
        self.reg_confirm.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.reg_confirm.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.reg_confirm.SetForegroundColour(wx.Colour(33, 37, 41))
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
        
        main_sizer.AddSpacer(30)
        
        # Button container
        button_container = wx.BoxSizer(wx.HORIZONTAL)
        button_container.AddStretchSpacer()
        
        # Login/Create button
        self.action_button = ModernCard(self, "Login", self.on_action_click, enabled=True, font_size=24)
        self.action_button.SetMinSize((288, 70))
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
        
        # Back button to Title Screen
        back_container = wx.BoxSizer(wx.HORIZONTAL)
        back_container.AddStretchSpacer()
        self.back_button = ModernCard(self, "Back", self.on_back, enabled=True, font_size=18)
        self.back_button.SetMinSize((150, 50))
        back_container.Add(self.back_button, 0, wx.ALIGN_CENTER)
        back_container.AddStretchSpacer()
        main_sizer.Add(back_container, 0, wx.EXPAND | wx.BOTTOM, 30)
        
        self.SetSizer(main_sizer)
        self.Layout()
    
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
            self.on_login_success(result)
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
    
    def on_login_success(self, user_data):
        """Handle successful login"""
        parent = self.GetParent()
        
        # Update DashboardPage with user data
        if hasattr(parent, 'dashboard_page'):
            parent.dashboard_page.user_data = user_data
            parent.dashboard_page.current_username = user_data["username"]
            parent.dashboard_page.is_logged_in = True
            
            # Update SharedStats
            if hasattr(parent, 'shared_state') and hasattr(parent.shared_state, 'set_user_name'):
                parent.shared_state.set_user_name(user_data["username"])
            
            # Refresh dashboard data
            parent.dashboard_page.refresh_dashboard()
            
            # Notify start page to show logout button if needed
            wx.CallLater(100, parent.dashboard_page.update_start_page_logout_button)
        
        # Switch to dashboard
        parent.switch_to_dashboard()
    
    def on_back(self, event):
        """Back to title screen"""
        parent = self.GetParent()
        parent.switch_to_title_page()

