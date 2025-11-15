# how-to-play page
import wx
from button import CustomButton

class SectionCard(wx.Panel):
    """Dashboard-style section card with soft shadow and rounded corners"""
    def __init__(self, parent):
        super().__init__(parent)

        self.bg_color = wx.Colour(255, 255, 255)
        self.border_color = wx.Colour(220, 220, 220)

        # Use custom painting like dashboard card
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        
        width, height = self.GetSize()

        shadow_color = wx.Colour(0, 0, 0, 15)
        gc.SetBrush(wx.Brush(shadow_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(4, 4, width - 4, height - 4, 12)
        
        bg = self.bg_color
        border = wx.Colour(220, 220, 220)
        gc.SetPen(wx.Pen(border, 2))
        gc.SetBrush(wx.Brush(bg))
        gc.DrawRoundedRectangle(0, 0, width - 4, height - 4, 12)
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

class InstructionsPage(wx.Panel):
    def __init__(self, parent):
        super(InstructionsPage, self).__init__(parent)
        self.SetBackgroundColour(wx.Colour(248, 249, 250))

        # ============================================================
        # Create Scrolled Window inside this panel
        # ============================================================
        scroll = wx.ScrolledWindow(self, style=wx.VSCROLL)
        scroll.SetScrollRate(0, 20)           # speed of scrolling
        scroll.SetBackgroundColour(wx.Colour(248, 249, 250))

        # Main sizer of this panel
        outer_sizer = wx.BoxSizer(wx.VERTICAL)
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)

        # ============================================================
        # Title
        # ============================================================
        title = wx.StaticText(scroll, label="Tutorial")
        title.SetFont(wx.Font(60, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(wx.Colour(33, 37, 41))
        scroll_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 40)

        # ============================================================
        # Intro text
        # ============================================================
        intro = wx.StaticText(scroll, label=(
            "Get familiar with how to use the FES Rowing system.\n"
            "Follow the steps below to learn about each mode."
        ))
        intro.SetFont(wx.Font(26, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        intro.SetForegroundColour(wx.Colour(73, 80, 87))
        scroll_sizer.Add(intro, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 30)

        scroll_sizer.AddSpacer(40)

        # ============================================================
        # Sections
        # ============================================================
        section_sizer = wx.BoxSizer(wx.VERTICAL)
        section_sizer.Add(self.create_section(
            scroll,
            "⚙️  Calibration",
            "Set up your rowing range by sliding to the front and back positions.\n"
            "This defines motion limits and ensures accurate FES timing."
        ), 0, wx.EXPAND | wx.ALL, 15)

        section_sizer.Add(self.create_section(
            scroll,
            "🎯  Manual Mode",
            "Practice controlling your seat timing manually.\n"
            "Watch the orange–green bar and press during the green zone!"
        ), 0, wx.EXPAND | wx.ALL, 15)

        section_sizer.Add(self.create_section(
            scroll,
            "🤖  Automatic Mode",
            "The system automatically triggers FES stimulation when your seat\n"
            "reaches the calibrated positions."
        ), 0, wx.EXPAND | wx.ALL, 15)

        scroll_sizer.Add(section_sizer, 0, wx.LEFT | wx.RIGHT, 40)
        scroll_sizer.AddSpacer(30)

        # ============================================================
        # Start tutorial button
        # ============================================================
        tutorial_bar = wx.BoxSizer(wx.HORIZONTAL)
        tutorial_bar.AddStretchSpacer()
        self.start_btn = ModernCard(
            scroll, "Start Tutorial", self.on_start_tutorial, enabled=True, font_size=26
        )
        self.start_btn.SetMinSize((300, 80))
        tutorial_bar.Add(self.start_btn, 0, wx.RIGHT | wx.BOTTOM, 40)
        scroll_sizer.Add(tutorial_bar, 0, wx.EXPAND)

        # ============================================================
        # Back Button (must stay at bottom)
        # ============================================================
        back_bar = wx.BoxSizer(wx.HORIZONTAL)
        self.back_btn = ModernCard(scroll, "\u2190  Back", self.on_back, enabled=True, font_size=24)
        self.back_btn.SetMinSize((180, 70))
        back_bar.Add(self.back_btn, 0, wx.LEFT | wx.BOTTOM, 20)
        back_bar.AddStretchSpacer()
        scroll_sizer.Add(back_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        scroll.SetSizer(scroll_sizer)
        outer_sizer.Add(scroll, 1, wx.EXPAND)
        self.SetSizer(outer_sizer)

    # ============================================================
    # Section card factory
    # ============================================================
    def create_section(self, parent, title, text):
        panel = SectionCard(parent)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)

        title_label = wx.StaticText(panel, label=title)
        title_label.SetFont(wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title_label.SetForegroundColour(wx.Colour(33, 37, 41))
        sizer.Add(title_label, 0, wx.LEFT | wx.TOP, 20)
        sizer.AddSpacer(10)

        body_label = wx.StaticText(panel, label=text)
        body_label.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        body_label.SetForegroundColour(wx.Colour(73, 80, 87))
        title_label.SetBackgroundColour(wx.Colour(255, 255, 255))
        body_label.SetBackgroundColour(wx.Colour(255, 255, 255))

        sizer.Add(body_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 30)

        panel.SetSizer(sizer)
        return panel

    # ============================================================
    # Tutorial button
    # ============================================================
    def on_back(self, event):
        parent = self.GetParent()
        parent.switch_to_start_page()
    def on_start_tutorial(self, event):
        parent = self.GetParent()
        parent.switch_to_game_tutorial()
