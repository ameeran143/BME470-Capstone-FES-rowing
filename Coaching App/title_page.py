import wx
from game_page import ModernCard
from dashboard import AccountManager
from settings_manager import SettingsManager

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
        
        main_sizer.Add(button_container, 0, wx.EXPAND | wx.BOTTOM, 20)
        # Clinician Button
        clinician_container = wx.BoxSizer(wx.HORIZONTAL)
        clinician_container.AddStretchSpacer()
        self.clinician_link = wx.StaticText(self, label="Clinician Login")
        self.clinician_link.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT,
                                        wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.clinician_link.SetForegroundColour(wx.Colour(0, 102, 204))
        self.clinician_link.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.clinician_link.Bind(wx.EVT_LEFT_DOWN, self.on_clinician_start)
        clinician_container.Add(self.clinician_link, 0, wx.ALIGN_CENTER_VERTICAL)

        clinician_container.AddStretchSpacer()
        main_sizer.Add(clinician_container, 0, wx.EXPAND | wx.BOTTOM, 100)
        
        self.SetSizer(main_sizer)
        
    def on_start(self, event):
        parent = self.GetParent()
        parent.switch_to_login_page()

    def on_clinician_start(self, event):
        parent = self.GetParent()
        parent.switch_to_login_page_clinician()

class ClinicianLoginPage(wx.Panel):
    """Full screen login page for Clinicians"""
    def __init__(self, parent):
        super(ClinicianLoginPage, self).__init__(parent)
        self.account_manager = AccountManager()
        self.user_data = None
        
        # Match app background color
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top spacer
        main_sizer.AddSpacer(60)
        
        # Large title
        self.title_label = wx.StaticText(self, label="Clinician Login")
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
        
        # Login button
        self.action_button = ModernCard(self, "Login", self.on_action_click, enabled=True, font_size=24)
        self.action_button.SetMinSize((288, 70))
        button_container.Add(self.action_button, 0, wx.ALIGN_CENTER)
        
        button_container.AddStretchSpacer()
        main_sizer.Add(button_container, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 40)
        
        main_sizer.AddSpacer(20)
        
        # Demo account info
        demo_container = wx.BoxSizer(wx.HORIZONTAL)
        demo_container.AddStretchSpacer()
        demo_info = wx.StaticText(self, label="Default: admin / admin")
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
        """Handle login"""
        self.hide_error()
        self.on_login()
    
    def on_login(self):
        """Handle login"""
        username = self.login_username.GetValue().strip()
        password = self.login_password.GetValue()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        success, result = self.account_manager.authenticate_clinician(username, password)
        
        if success:
            self.on_login_success(result)
        else:
            self.show_error(result)
    
    def on_login_success(self, user_data):
        """Handle successful login"""
        parent = self.GetParent()
        
        # Proceed to Patient Selection
        if hasattr(parent, 'switch_to_patient_selection_page'):
            parent.switch_to_patient_selection_page()
        else:
            wx.MessageBox("Navigation error: switch_to_patient_selection_page not found", "Error")

    def on_back(self, event):
        """Back to title screen"""
        parent = self.GetParent()
        parent.switch_to_title_page()


class PatientSelectionPage(wx.Panel):
    """Page for clinician to select a patient"""
    def __init__(self, parent):
        super(PatientSelectionPage, self).__init__(parent)
        self.account_manager = AccountManager()
        self.settings_manager = SettingsManager()
        
        # Match app background color
        self.SetBackgroundColour(wx.Colour(248, 249, 250))
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSpacer(50)
        
        # Title
        self.title_label = wx.StaticText(self, label="Configuration")
        title_font = wx.Font(48, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title_label.SetFont(title_font)
        self.title_label.SetForegroundColour(wx.Colour(33, 37, 41))
        main_sizer.Add(self.title_label, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        
        main_sizer.AddSpacer(30)
        
        # Card container
        self.card = wx.Panel(self)
        self.card.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.card.SetMinSize((600, 600)) # Increased height to fit all buttons comfortably
        self.card.Bind(wx.EVT_PAINT, self.on_paint_card)
        
        card_sizer = wx.BoxSizer(wx.VERTICAL)
        card_sizer.AddSpacer(50)
        
        # Label
        lbl = wx.StaticText(self.card, label="Select a patient")
        lbl.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        card_sizer.Add(lbl, 0, wx.ALIGN_CENTER)
        
        card_sizer.AddSpacer(30)
        
        # Dropdown
        self.patient_choice = wx.Choice(self.card, size=(400, 50))
        # Increase font size for the dropdown (Choice control font)
        self.patient_choice.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.patient_choice.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        self.patient_choice.SetBackgroundColour(wx.Colour(255, 255, 255))  # White background
        card_sizer.Add(self.patient_choice, 0, wx.ALIGN_CENTER)
        
        card_sizer.AddSpacer(40)
        
        # Add Patient Button
        self.add_btn = ModernCard(self.card, "+ Add New Patient", self.on_add_patient, enabled=True, font_size=20)
        self.add_btn.SetMinSize((300, 60))
        card_sizer.Add(self.add_btn, 0, wx.ALIGN_CENTER)
        
        card_sizer.AddSpacer(20)
        
        # Remove Patient Button
        self.remove_btn = ModernCard(self.card, "Remove Patient", self.on_remove_patient, enabled=True, font_size=20)
        self.remove_btn.SetMinSize((300, 60))
        card_sizer.Add(self.remove_btn, 0, wx.ALIGN_CENTER)
        
        card_sizer.AddSpacer(20)
        
        # Game Settings Button
        self.settings_btn = ModernCard(self.card, "Game Settings", self.on_settings, enabled=True, font_size=20)
        self.settings_btn.SetMinSize((300, 60))
        card_sizer.Add(self.settings_btn, 0, wx.ALIGN_CENTER)
        
        card_sizer.AddSpacer(20)
        
        # Hardware Settings Button
        self.hardware_settings_btn = ModernCard(self.card, "Hardware Settings", self.on_hardware_settings, enabled=True, font_size=20)
        self.hardware_settings_btn.SetMinSize((300, 60))
        card_sizer.Add(self.hardware_settings_btn, 0, wx.ALIGN_CENTER)
        
        card_sizer.AddSpacer(50)
        self.card.SetSizer(card_sizer)
        
        # Add card to main sizer
        main_sizer.Add(self.card, 0, wx.ALIGN_CENTER)
        
        main_sizer.AddSpacer(40)
        
        # Bottom buttons
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Back button (logout clinician)
        self.back_btn = ModernCard(self, "Logout", self.on_logout, enabled=True, font_size=20)
        self.back_btn.SetMinSize((150, 60))
        bottom_sizer.Add(self.back_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        
        bottom_sizer.AddStretchSpacer()
        
        # Proceed button
        self.proceed_btn = ModernCard(self, "Proceed →", self.on_proceed, enabled=True, font_size=24)
        self.proceed_btn.SetMinSize((200, 70))
        bottom_sizer.Add(self.proceed_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.BOTTOM, 40)
        
        self.SetSizer(main_sizer)
        
        # Populate list
        self.refresh_patient_list()
        
    def on_paint_card(self, event):
        dc = wx.PaintDC(event.GetEventObject())
        gc = wx.GraphicsContext.Create(dc)
        width, height = event.GetEventObject().GetSize()
        
        # Shadow
        gc.SetBrush(wx.Brush(wx.Colour(0,0,0,15)))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(4, 4, width-4, height-4, 12)
        
        # Background
        gc.SetPen(wx.Pen(wx.Colour(220,220,220), 2))
        gc.SetBrush(wx.Brush(wx.Colour(255,255,255)))
        gc.DrawRoundedRectangle(0, 0, width-4, height-4, 12)

    def refresh_patient_list(self):
        self.account_manager.accounts = self.account_manager.load_accounts()
        patients = self.account_manager.get_all_patients()
        self.patient_choice.Clear()
        self.patient_usernames = []
        
        for p in patients:
            label = f"{p['name']} ({p['username']})"
            self.patient_choice.Append(label)
            self.patient_usernames.append(p['username'])
            
        if patients:
            self.patient_choice.SetSelection(0)

    def on_add_patient(self, event):
        dlg = AddPatientDialog(self, self.account_manager)
        if dlg.ShowModal() == wx.ID_OK:
            self.refresh_patient_list()
            # Select the newly added patient
            if hasattr(dlg, 'new_username') and dlg.new_username in self.patient_usernames:
                idx = self.patient_usernames.index(dlg.new_username)
                self.patient_choice.SetSelection(idx)
        dlg.Destroy()
        
    def on_remove_patient(self, event):
        sel = self.patient_choice.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox("Please select a patient to remove.", "Info")
            return
        
        username = self.patient_usernames[sel]
        
        # First confirmation
        if wx.MessageBox(f"Are you sure you want to remove patient '{username}'?", 
                         "Confirm Remove", wx.YES_NO | wx.ICON_WARNING) == wx.YES:
            # Second confirmation
            if wx.MessageBox(f"This will permanently delete all data for '{username}'. This action cannot be undone. Proceed?", 
                             "Final Confirmation", wx.YES_NO | wx.ICON_ERROR) == wx.YES:
                if self.account_manager.delete_account(username):
                    wx.MessageBox("Patient removed successfully.", "Success")
                    self.refresh_patient_list()
                else:
                    wx.MessageBox("Error removing patient.", "Error")
        
    def on_settings(self, event):
        dlg = SettingsDialog(self, self.settings_manager)
        dlg.ShowModal()
        dlg.Destroy()
    
    def on_hardware_settings(self, event):
        dlg = HardwareSettingsDialog(self, self.settings_manager)
        dlg.ShowModal()
        dlg.Destroy()

    def on_logout(self, event):
        parent = self.GetParent()
        parent.switch_to_login_page()

    def on_proceed(self, event):
        sel = self.patient_choice.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox("Please select a patient first.", "Info")
            return
            
        username = self.patient_usernames[sel]
        
        # Load user data (no password required)
        # AccountManager.authenticate is not needed since we trust the clinician
        user_data = self.account_manager.accounts.get(username)
        
        if user_data:
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
            
            parent.switch_to_dashboard()
        else:
            wx.MessageBox("Error loading patient data", "Error")


class AddPatientDialog(wx.Dialog):
    def __init__(self, parent, account_manager):
        super(AddPatientDialog, self).__init__(parent, title="Add New Patient", size=(500, 400))
        self.account_manager = account_manager
        self.new_username = None
        
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
        
        title = wx.StaticText(self, label="Add New Patient")
        title.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)
        
        # Name
        sizer.Add(wx.StaticText(self, label="Full Name"), 0, wx.LEFT, 40)
        self.name_ctrl = wx.TextCtrl(self, size=(400, 40))
        sizer.Add(self.name_ctrl, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 40)
        
        # Username
        sizer.Add(wx.StaticText(self, label="Username (unique ID)"), 0, wx.LEFT, 40)
        self.username_ctrl = wx.TextCtrl(self, size=(400, 40))
        sizer.Add(self.username_ctrl, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 40)
        
        # Error label
        self.error_lbl = wx.StaticText(self, label="")
        self.error_lbl.SetForegroundColour(wx.Colour(220, 53, 69))
        sizer.Add(self.error_lbl, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 20)
        
        save_btn = wx.Button(self, label="Save")
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sizer.Add(save_btn, 0)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)
        
        self.SetSizer(sizer)
        self.CenterOnParent()

    def on_save(self, event):
        name = self.name_ctrl.GetValue().strip()
        username = self.username_ctrl.GetValue().strip()
        
        if not name or not username:
            self.error_lbl.SetLabel("Please fill in all fields")
            return
            
        success, msg = self.account_manager.create_account(username, password=None, name=name)
        
        if success:
            self.new_username = username
            self.EndModal(wx.ID_OK)
        else:
            self.error_lbl.SetLabel(msg)

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, settings_manager):
        super(SettingsDialog, self).__init__(parent, title="Game Settings", size=(600, 400))
        self.settings_manager = settings_manager
        
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
        
        title = wx.StaticText(self, label="Game Settings")
        title.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.BOTTOM, 30)
        
        # Map Unlock Interval
        map_sizer = wx.BoxSizer(wx.HORIZONTAL)
        map_label = wx.StaticText(self, label="Map Unlock Interval (min):")
        map_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        map_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        map_label.SetMinSize((250, -1))
        map_sizer.Add(map_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        
        current_interval = self.settings_manager.get_map_interval()
        self.interval_ctrl = wx.SpinCtrl(self, value=str(current_interval), min=1, max=120)
        self.interval_ctrl.SetMinSize((150, 35))
        self.interval_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        map_sizer.Add(self.interval_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        
        sizer.Add(map_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        
        # Button Push Window One Side
        button_window_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_window_label = wx.StaticText(self, label="Button Push Window One Side (mm):")
        button_window_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        button_window_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        button_window_label.SetMinSize((250, -1))
        button_window_sizer.Add(button_window_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        
        current_button_window = self.settings_manager.get_button_push_window()
        self.button_window_ctrl = wx.SpinCtrlDouble(self, value=str(current_button_window), min=0.0, max=500.0, inc=1.0)
        self.button_window_ctrl.SetDigits(0)
        self.button_window_ctrl.SetMinSize((150, 35))
        self.button_window_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        button_window_sizer.Add(self.button_window_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        
        sizer.Add(button_window_sizer, 0, wx.EXPAND | wx.BOTTOM, 40)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        cancel_btn.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        cancel_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
        cancel_btn.SetOwnBackgroundColour(wx.Colour(240, 240, 240))  # Ensure background is only on button
        cancel_btn.SetOwnForegroundColour(wx.Colour(33, 37, 41))  # Force text color
        cancel_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        cancel_btn.Refresh()
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 20)
        
        save_btn = wx.Button(self, label="Save")
        save_btn.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        save_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
        save_btn.SetOwnBackgroundColour(wx.Colour(240, 240, 240))  # Ensure background is only on button
        save_btn.SetOwnForegroundColour(wx.Colour(33, 37, 41))  # Force text color
        save_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        save_btn.Refresh()
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sizer.Add(save_btn, 0)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)
        
        self.SetSizer(sizer)
        self.CenterOnParent()
        
    def on_save(self, event):
        interval = self.interval_ctrl.GetValue()
        button_window = self.button_window_ctrl.GetValue()
        self.settings_manager.set_map_interval(interval)
        self.settings_manager.set_button_push_window(button_window)
        self.EndModal(wx.ID_OK)


class HardwareSettingsDialog(wx.Dialog):
    def __init__(self, parent, settings_manager):
        super(HardwareSettingsDialog, self).__init__(parent, title="Hardware Settings", size=(600, 650))
        self.settings_manager = settings_manager
        
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(20)
        
        title = wx.StaticText(self, label="Hardware Settings")
        title.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        sizer.Add(title, 0, wx.ALIGN_CENTER | wx.BOTTOM, 30)
        
        # Get current hardware settings
        hw_settings = self.settings_manager.get_hardware_settings()
        
        # Dev Number
        dev_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dev_label = wx.StaticText(self, label="Dev Number:")
        dev_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dev_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        dev_label.SetMinSize((250, -1))
        dev_sizer.Add(dev_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        self.dev_number_ctrl = wx.SpinCtrl(self, value=str(hw_settings.get("dev_number", 1)), min=1, max=10)
        self.dev_number_ctrl.SetMinSize((150, 35))
        self.dev_number_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        dev_sizer.Add(self.dev_number_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        sizer.Add(dev_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        
        # Voltage [V]
        voltage_sizer = wx.BoxSizer(wx.HORIZONTAL)
        voltage_label = wx.StaticText(self, label="Voltage [V]:")
        voltage_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        voltage_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        voltage_label.SetMinSize((250, -1))
        voltage_sizer.Add(voltage_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        self.voltage_ctrl = wx.SpinCtrlDouble(self, value=str(hw_settings.get("voltage_v", 5.0)), min=0.0, max=10.0, inc=0.1)
        self.voltage_ctrl.SetDigits(1)
        self.voltage_ctrl.SetMinSize((150, 35))
        self.voltage_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        voltage_sizer.Add(self.voltage_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        sizer.Add(voltage_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        
        # Left Foot Force Channel
        left_foot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        left_foot_label = wx.StaticText(self, label="Left Foot Force Channel:")
        left_foot_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        left_foot_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        left_foot_label.SetMinSize((250, -1))
        left_foot_sizer.Add(left_foot_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        self.left_foot_ctrl = wx.SpinCtrl(self, value=str(hw_settings.get("left_foot_force_channel", 16)), min=0, max=31)
        self.left_foot_ctrl.SetMinSize((150, 35))
        self.left_foot_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        left_foot_sizer.Add(self.left_foot_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        sizer.Add(left_foot_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        
        # Right Foot Force Channel
        right_foot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        right_foot_label = wx.StaticText(self, label="Right Foot Force Channel:")
        right_foot_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        right_foot_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        right_foot_label.SetMinSize((250, -1))
        right_foot_sizer.Add(right_foot_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        self.right_foot_ctrl = wx.SpinCtrl(self, value=str(hw_settings.get("right_foot_force_channel", 18)), min=0, max=31)
        self.right_foot_ctrl.SetMinSize((150, 35))
        self.right_foot_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        right_foot_sizer.Add(self.right_foot_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        sizer.Add(right_foot_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        
        # Handle Force Channel
        handle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        handle_label = wx.StaticText(self, label="Handle Force Channel:")
        handle_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        handle_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        handle_label.SetMinSize((250, -1))
        handle_sizer.Add(handle_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        self.handle_ctrl = wx.SpinCtrl(self, value=str(hw_settings.get("handle_force_channel", 20)), min=0, max=31)
        self.handle_ctrl.SetMinSize((150, 35))
        self.handle_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        handle_sizer.Add(self.handle_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        sizer.Add(handle_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        
        # Front Potentiometer Channel
        front_pot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        front_pot_label = wx.StaticText(self, label="Front Potentiometer Channel:")
        front_pot_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        front_pot_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        front_pot_label.SetMinSize((250, -1))
        front_pot_sizer.Add(front_pot_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        self.front_pot_ctrl = wx.SpinCtrl(self, value=str(hw_settings.get("front_potentiometer_channel", 21)), min=0, max=31)
        self.front_pot_ctrl.SetMinSize((150, 35))
        self.front_pot_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        front_pot_sizer.Add(self.front_pot_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        sizer.Add(front_pot_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        
        # Back Potentiometer Channel
        back_pot_sizer = wx.BoxSizer(wx.HORIZONTAL)
        back_pot_label = wx.StaticText(self, label="Back Potentiometer Channel:")
        back_pot_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        back_pot_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        back_pot_label.SetMinSize((250, -1))
        back_pot_sizer.Add(back_pot_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 40)
        self.back_pot_ctrl = wx.SpinCtrl(self, value=str(hw_settings.get("back_potentiometer_channel", 22)), min=0, max=31)
        self.back_pot_ctrl.SetMinSize((150, 35))
        self.back_pot_ctrl.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        back_pot_sizer.Add(self.back_pot_ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 40)
        sizer.Add(back_pot_sizer, 0, wx.EXPAND | wx.BOTTOM, 20)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        cancel_btn.SetMinSize((100, 40))
        cancel_btn.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        cancel_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
        cancel_btn.SetOwnBackgroundColour(wx.Colour(240, 240, 240))  # Ensure background is only on button
        cancel_btn.SetOwnForegroundColour(wx.Colour(33, 37, 41))  # Force text color
        cancel_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        cancel_btn.Refresh()
        btn_sizer.Add(cancel_btn, 0, wx.RIGHT, 20)
        
        save_btn = wx.Button(self, label="Save")
        save_btn.SetMinSize((100, 40))
        save_btn.SetForegroundColour(wx.Colour(33, 37, 41))  # Explicit text color for visibility
        save_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
        save_btn.SetOwnBackgroundColour(wx.Colour(240, 240, 240))  # Ensure background is only on button
        save_btn.SetOwnForegroundColour(wx.Colour(33, 37, 41))  # Force text color
        save_btn.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        save_btn.Refresh()
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sizer.Add(save_btn, 0)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)
        
        self.SetSizer(sizer)
        self.CenterOnParent()
        
    def on_save(self, event):
        # Get values from controls
        dev_number = self.dev_number_ctrl.GetValue()
        voltage = self.voltage_ctrl.GetValue()
        left_foot = self.left_foot_ctrl.GetValue()
        right_foot = self.right_foot_ctrl.GetValue()
        handle = self.handle_ctrl.GetValue()
        front_pot = self.front_pot_ctrl.GetValue()
        back_pot = self.back_pot_ctrl.GetValue()
        
        # Build hardware settings dictionary
        hardware_settings = {
            "dev_number": int(dev_number),
            "voltage_v": float(voltage),
            "left_foot_force_channel": int(left_foot),
            "right_foot_force_channel": int(right_foot),
            "handle_force_channel": int(handle),
            "front_potentiometer_channel": int(front_pot),
            "back_potentiometer_channel": int(back_pot)
        }
        
        # Save settings
        self.settings_manager.set_hardware_settings(hardware_settings)
        self.EndModal(wx.ID_OK)
