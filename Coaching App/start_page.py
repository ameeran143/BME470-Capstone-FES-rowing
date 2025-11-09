# start page
import wx
from button import CustomButton

class ModernCard(wx.Panel):
    """A modern card panel with shadow effect and hover interaction"""
    def __init__(self, parent, label, handler, enabled=True, font_size=38):
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
        if enabled:
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
        if self.is_hovered and self.enabled:
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
        self.is_hovered = True
        self.Refresh()
    
    def OnLeave(self, event):
        self.is_hovered = False
        self.Refresh()
    
    def OnClick(self, event):
        if self.enabled:
            self.handler(event)

class StartPage(wx.Panel):
    def __init__(self, parent):
        super(StartPage, self).__init__(parent)
        # Light gradient-like background
        self.SetBackgroundColour(wx.Colour(248, 249, 250))

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top bar with logout button
        top_bar = wx.BoxSizer(wx.HORIZONTAL)
        top_bar.AddStretchSpacer()
        
        # Logout button in top right (only visible when logged in)
        self.logout_card = ModernCard(self, "Logout", self.on_logout, enabled=True, font_size=18)
        self.logout_card.SetMinSize((120, 50))
        self.logout_card.Hide()  # Hidden by default, shown when logged in
        top_bar.Add(self.logout_card, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.RIGHT, 25)
        
        main_sizer.Add(top_bar, 0, wx.EXPAND)
        
        main_sizer.AddSpacer(50)

        # Title: "Select Mode" - more elegant
        title = wx.StaticText(self, label="Select Mode")
        title_font = wx.Font(78, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        main_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 40)

        # 2x2 grid of modern card buttons
        grid_sizer = wx.FlexGridSizer(2, 2, 40, 40)
        grid_sizer.AddGrowableCol(0, 1)
        grid_sizer.AddGrowableCol(1, 1)
        grid_sizer.AddGrowableRow(0, 1)
        grid_sizer.AddGrowableRow(1, 1)

        # Create modern cards - all enabled
        self.auto_card = ModernCard(self, "Automatic Mode", self.on_start_game, enabled=True)
        self.manual_card = ModernCard(self, "Manual Mode", self.on_start_game, enabled=True)
        self.calib_card = ModernCard(self, "Calibration", self.on_calib, enabled=True)
        self.tutorial_card = ModernCard(self, "Tutorial", self.on_tutorial, enabled=True)

        grid_sizer.Add(self.auto_card, 1, wx.EXPAND | wx.ALL, 15)
        grid_sizer.Add(self.manual_card, 1, wx.EXPAND | wx.ALL, 15)
        grid_sizer.Add(self.calib_card, 1, wx.EXPAND | wx.ALL, 15)
        grid_sizer.Add(self.tutorial_card, 1, wx.EXPAND | wx.ALL, 15)

        # Center the grid
        grid_wrap = wx.BoxSizer(wx.HORIZONTAL)
        grid_wrap.AddStretchSpacer()
        grid_wrap.Add(grid_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 80)
        grid_wrap.AddStretchSpacer()
        main_sizer.Add(grid_wrap, 1, wx.EXPAND)

        main_sizer.AddSpacer(30)

        # Bottom bar with modern card-style back button
        bottom_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.dashboard_card = ModernCard(self, "← User Dashboard", self.on_user_dashboard, enabled=True, font_size=24)
        self.dashboard_card.SetMinSize((280, 70))
        bottom_bar.Add(self.dashboard_card, 0, wx.LEFT | wx.BOTTOM, 30)
        bottom_bar.AddStretchSpacer()
        main_sizer.Add(bottom_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        self.SetSizer(main_sizer)
        
        # Flag to prevent on_show from interfering during logout/login
        self._updating_logout = False
        
        # Bind to show event to update logout button when page is shown
        self.Bind(wx.EVT_SHOW, self.on_show)
        
        # Check login state after a delay (in case dashboard logs in during initialization)
        wx.CallLater(200, self.update_logout_button)

    def on_show(self, event):
        """Called when the page is shown - update logout button visibility"""
        if event.IsShown() and not self._updating_logout:
            # Use CallAfter to ensure dashboard is ready
            wx.CallAfter(self.update_logout_button)

    def on_start_game(self, event):
        parent = self.GetParent()

        parent.game_page.shared_state.stop_writing_stats()
        parent.game_page.shared_state.create_stats_file()

        parent.game_page.reset_game()
        parent.switch_to_game_page()
    
    def on_calib(self, event):
        parent = self.GetParent()
        parent.game_page.shared_state.stop_writing_stats()
        parent.switch_to_calib_page()

    def on_tutorial(self, event):
        parent = self.GetParent()
        parent.game_page.shared_state.stop_writing_stats()
        if hasattr(parent, 'instructions_page'):
            parent.switch_to_instructions_page()
        else:
            wx.MessageBox("Tutorial coming soon.", "Info")

    def on_user_dashboard(self, event):
        parent = self.GetParent()
        parent.switch_to_dashboard_page()
    
    def on_logout(self, event):
        """Handle logout button click - logout and show login dialog"""
        parent = self.GetParent()
        # Access dashboard page to logout
        if hasattr(parent, 'dashboard_page') and parent.dashboard_page.is_logged_in:
            # Set flag to prevent on_show from interfering
            self._updating_logout = True
            
            # Logout from dashboard
            parent.dashboard_page.is_logged_in = False
            parent.dashboard_page.user_data = None
            parent.dashboard_page.current_username = None
            
            # Hide logout button (but don't layout yet - wait until after dialog)
            self.logout_card.Hide()
            
            # Show login dialog immediately
            from dashboard import LoginDialog
            login_dialog = LoginDialog(self, parent.dashboard_page.account_manager)
            result = login_dialog.ShowModal()
            
            # Save user_data before destroying dialog
            user_data = login_dialog.user_data if hasattr(login_dialog, 'user_data') else None
            login_dialog.Destroy()
            
            # Now update layout after dialog is closed
            if result == wx.ID_OK and user_data:
                # Login successful - update dashboard with new user data
                parent.dashboard_page.user_data = user_data
                parent.dashboard_page.current_username = user_data["username"]
                parent.dashboard_page.is_logged_in = True
                
                # Recreate dashboard layout with new user data
                parent.dashboard_page.DestroyChildren()
                parent.dashboard_page.create_layout()
                
                # Update logout button visibility on start page
                self.update_logout_button()
            else:
                # Login cancelled - update layout to reflect hidden logout button
                self.Layout()
                self.Refresh()
            
            # Clear the flag
            self._updating_logout = False
    
    def update_logout_button(self):
        """Update logout button visibility based on login state"""
        try:
            parent = self.GetParent()
            if parent and hasattr(parent, 'dashboard_page'):
                dashboard = parent.dashboard_page
                if dashboard and hasattr(dashboard, 'is_logged_in') and dashboard.is_logged_in:
                    self.logout_card.Show()
                else:
                    self.logout_card.Hide()
            else:
                self.logout_card.Hide()
            self.Layout()
            self.Refresh()
        except Exception as e:
            # If update fails, hide the button to be safe
            self.logout_card.Hide()
            self.Layout()