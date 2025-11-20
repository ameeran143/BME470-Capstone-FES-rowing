import wx
from button import CustomButton
import math
import os
from PIL import Image, ImageDraw

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
    
    def SetLabel(self, label):
        """Update the button label"""
        self.label_text = label
        self.Refresh()
    
    def Enable(self, enable=True):
        """Enable or disable the button"""
        self.enabled = enable
        if enable:
            self.bg_color = wx.Colour(255, 255, 255)
            self.text_color = wx.Colour(33, 37, 41)
            self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
            self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
            self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.bg_color = wx.Colour(230, 230, 230)
            self.text_color = wx.Colour(150, 150, 150)
            self.Unbind(wx.EVT_LEFT_DOWN)
            self.Unbind(wx.EVT_ENTER_WINDOW)
            self.Unbind(wx.EVT_LEAVE_WINDOW)
            self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
        self.SetBackgroundColour(self.bg_color)
        self.Refresh()
    
    def Disable(self):
        """Disable the button"""
        self.Enable(False)

class GameTutorialPage(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.step = 0

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Dynamic content area ---
        self.content_area = wx.Panel(self)
        self.content_area.SetBackgroundColour(wx.Colour(248, 249, 250))
        self.content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.content_area.SetSizer(self.content_sizer)

        # Use proportion 0 so content area fits to its content, not expanding vertically
        self.main_sizer.Add(self.content_area, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 20)

        # --- Explanation text ---
        # Create a container for the text labels
        self.text_container = wx.Panel(self)
        self.text_container.SetBackgroundColour(self.GetBackgroundColour())
        self.text_sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_container.SetSizer(self.text_sizer)
        
        self.text_label = wx.StaticText(self.text_container, label="", style=wx.ALIGN_LEFT)
        self.text_label.SetFont(wx.Font(26, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_sizer.Add(self.text_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 0)
        
        self.main_sizer.Add(self.text_container, 0, wx.LEFT | wx.RIGHT, 20)

        # --- Navigation buttons ---
        nav = wx.BoxSizer(wx.HORIZONTAL)
        self.back_btn = ModernCard(self, "← Back", self.on_prev, enabled=True, font_size=24)
        self.back_btn.SetMinSize((160, 70))
        self.next_btn = ModernCard(self, "Next →", self.on_next, enabled=True, font_size=24)
        self.next_btn.SetMinSize((160, 70))

        nav.Add(self.back_btn, 0, wx.ALL, 10)
        nav.AddStretchSpacer()
        nav.Add(self.next_btn, 0, wx.ALL, 10)

        self.main_sizer.Add(nav, 0, wx.EXPAND)

        self.SetSizer(self.main_sizer)

        wx.CallAfter(self.show_step)

    # ====================================================
    # HELPER: Clear content area
    # ====================================================
    def clear_content(self):
        # Stop any running timers in FES bars before destroying
        for child in self.content_area.GetChildren():
            if isinstance(child, TutorialPingPongFES):
                if child.timer and child.timer.IsRunning():
                    child.timer.Stop()
                child.is_destroyed = True
            child.Destroy()
        self.content_sizer.Clear()
        self.content_area.Layout()

    # ====================================================
    # STEP LOGIC
    # ====================================================
    def show_step(self):
        self.clear_content()

        if self.step == 0:
            # No stretch spacer for step 0 - content should fit on one page
            self.show_metrics_step()
            # Clear any existing labels in text container
            for child in self.text_container.GetChildren():
                if isinstance(child, wx.StaticText):
                    child.Destroy()
            self.text_label = wx.StaticText(self.text_container, label="", style=wx.ALIGN_LEFT)
            self.text_label.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            self.text_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Default text color
            self.text_sizer.Add(self.text_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 0)
            self.text_label.SetLabel(
                "These are your key performance metrics:\n"
                "- Time\n- Power\n- Distance\n- Timing accuracy"
            )
            self.next_btn.SetLabel("Next →")
            self.back_btn.Enable()

        elif self.step == 1:
            self.show_game_step()
            # Clear any existing labels in text container
            for child in self.text_container.GetChildren():
                if isinstance(child, wx.StaticText):
                    child.Destroy()
            self.text_label = wx.StaticText(self.text_container, label="", style=wx.ALIGN_LEFT)
            self.text_label.SetFont(wx.Font(26, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            self.text_label.SetForegroundColour(wx.Colour(33, 37, 41))  # Default text color
            self.text_sizer.Add(self.text_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 0)
            self.text_label.SetLabel(
                "This is the game screen.\nYour avatar rows as your distance increases."
            )
            self.next_btn.SetLabel("Next →")
            self.back_btn.Enable()

        elif self.step == 2:
            self.show_combined_fes()
            self.next_btn.SetLabel("Finish →")

        else:
            # End tutorial
            self.GetParent().switch_to_start_page()

        # Layout content area first, then main layout to ensure proper sizing
        self.content_area.Layout()
        self.Layout()

    # ====================================================
    # STEP 0: METRICS ONLY
    # ====================================================
    def show_metrics_step(self):
        panel = wx.Panel(self.content_area)
        panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        row = wx.BoxSizer(wx.HORIZONTAL)

        for title, value in [
            ("Time", "02:15"),
            ("Power", "135 W"),
            ("Distance", "210 m"),
            ("Accuracy", "83%")
        ]:
            card = self.create_metric_card(panel, title, value)
            row.Add(card, 1, wx.ALL, 8)  # Reduced from 10 to 8

        panel.SetSizer(row)
        self.content_sizer.Add(panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)  # Removed bottom padding

    def create_metric_card(self, parent, title, value):
        p = wx.Panel(parent)
        p.SetBackgroundColour(wx.Colour(255, 255, 255))

        s = wx.BoxSizer(wx.VERTICAL)
        t = wx.StaticText(p, label=title)
        t.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))  # Reduced from 22
        v = wx.StaticText(p, label=value)
        v.SetFont(wx.Font(34, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))  # Reduced from 38

        s.Add(t, 0, wx.ALIGN_CENTER | wx.TOP, 3)  # Reduced from 5
        s.Add(v, 1, wx.ALIGN_CENTER | wx.BOTTOM, 3)  # Reduced from 5
        p.SetSizer(s)
        return p

    # ====================================================
    # STEP 1: GAME SCREEN ONLY
    # ====================================================
    def show_game_step(self):
        panel = wx.Panel(self.content_area)
        panel.SetBackgroundColour(wx.Colour(150, 205, 255))
        panel.SetMinSize((-1, 180))

        # Load sprites for the scene
        self.load_tutorial_sprites(panel)

        panel.Bind(wx.EVT_PAINT, self.paint_scene)

        self.content_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 10)

    def load_tutorial_sprites(self, panel):
        """Load palm tree and boat sprites for tutorial"""
        self.palm_tree_sprite = None
        self.palm_tree_small_sprite = None
        self.boat_sprite = None
        
        # Try to load palm tree - match game_page.py path and sizing
        try:
            # Get the path to the palm-tree.png file (in parent directory, same as game_page.py)
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            palm_tree_path = os.path.join(script_dir, "palm-tree.png")
            
            # If not found, try assets/images path
            if not os.path.exists(palm_tree_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                palm_tree_path = os.path.join(script_dir, "assets", "images", "palm_tree.png")
                if not os.path.exists(palm_tree_path):
                    script_dir = os.path.dirname(script_dir)
                    palm_tree_path = os.path.join(script_dir, "assets", "images", "palm_tree.png")
            
            if os.path.exists(palm_tree_path):
                img = Image.open(palm_tree_path)
                
                # Convert to RGBA if not already
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Scale to match game_page.py sizing: target_height = 140 * scale
                # Full size palm tree
                target_height = 140
                aspect_ratio = img.width / img.height
                target_width = int(target_height * aspect_ratio)
                full_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                self.palm_tree_sprite = self.pil_to_wx_bitmap(full_img)
                
                # Small version (scale = 0.7)
                target_height_small = int(140 * 0.7)
                target_width_small = int(target_height_small * aspect_ratio)
                small_img = img.resize((target_width_small, target_height_small), Image.Resampling.LANCZOS)
                self.palm_tree_small_sprite = self.pil_to_wx_bitmap(small_img)
        except Exception as e:
            print(f"Could not load palm tree: {e}")
        
        # Create boat sprite
        self.boat_sprite = self.create_boat_sprite()

    def pil_to_wx_bitmap(self, pil_image):
        """Convert PIL Image to wx.Bitmap with transparency support"""
        width, height = pil_image.size
        wx_image = wx.Image(width, height)
        
        if pil_image.mode == 'RGBA':
            rgb_image = pil_image.convert('RGB')
            wx_image.SetData(rgb_image.tobytes())
            alpha_data = pil_image.split()[3].tobytes()
            wx_image.SetAlpha(alpha_data)
        else:
            rgb_image = pil_image.convert('RGB')
            wx_image.SetData(rgb_image.tobytes())
        
        return wx.Bitmap(wx_image)

    def create_boat_sprite(self):
        """Create a detailed rowing boat sprite - match game_page.py"""
        width, height = 100, 60
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        boat_y = 30
        
        # Boat hull (polygon for realistic shape)
        hull_points = [
            (15, boat_y),                    # Front point
            (20, boat_y + 15),               # Front bottom
            (80, boat_y + 15),               # Back bottom
            (85, boat_y),                    # Back point
            (82, boat_y - 3),                # Back top
            (18, boat_y - 3),                # Front top
        ]
        draw.polygon(hull_points, fill=(101, 67, 33), outline=(80, 50, 20))
        
        # Rower head
        head_x, head_y = 50, boat_y - 10
        draw.ellipse(
            [head_x - 6, head_y - 6, head_x + 6, head_y + 6],
            fill=(255, 220, 177)
        )
        
        # Body
        draw.line(
            [head_x, head_y + 6, head_x, boat_y + 5],
            fill=(50, 50, 50),
            width=3
        )
        
        # Oar
        draw.line(
            [head_x - 30, boat_y - 2, head_x + 30, boat_y + 2],
            fill=(139, 90, 43),
            width=4
        )
        
        # Oar blades
        draw.ellipse(
            [head_x - 38, boat_y - 6, head_x - 28, boat_y + 2],
            fill=(200, 200, 200)
        )
        draw.ellipse(
            [head_x + 28, boat_y - 2, head_x + 38, boat_y + 6],
            fill=(200, 200, 200)
        )
        
        return self.pil_to_wx_bitmap(img)

    def paint_scene(self, event):
        dc = wx.PaintDC(event.GetEventObject())
        w, h = event.GetEventObject().GetSize()

        # Draw sky (already set as background color)
        
        # Draw water - match game_page.py
        water_height = h // 5
        water_y = h - water_height
        dc.SetBrush(wx.Brush(wx.Colour(0, 140, 200)))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, water_y, w, water_height)
        
        # Draw beach/sand - match game_page.py positioning
        # beach_y = height - (height // 5) - (height // 6)  # Above water line
        beach_y = h - (h // 5) - (h // 6)
        beach_height = h // 4  # Match game_page.py beach_height
        dc.SetBrush(wx.Brush(wx.Colour(238, 203, 173)))  # Sandy color
        dc.DrawRectangle(0, beach_y, w, beach_height)
        
        # Draw palm trees on the beach - match game_page.py positioning
        if self.palm_tree_sprite:
            # Left palm tree
            palm_x1 = w // 4
            palm_draw_x1 = palm_x1 - self.palm_tree_sprite.GetWidth() // 2
            # Match game_page.py: palm_draw_y = beach_y - sprite_height + 20
            palm_draw_y1 = beach_y - self.palm_tree_sprite.GetHeight() + 20
            dc.DrawBitmap(self.palm_tree_sprite, palm_draw_x1, palm_draw_y1, True)
        
        if self.palm_tree_small_sprite:
            # Right palm tree (smaller)
            palm_x2 = 3 * w // 4
            palm_draw_x2 = palm_x2 - self.palm_tree_small_sprite.GetWidth() // 2
            # Match game_page.py: palm_draw_y = beach_y - sprite_height + 20
            palm_draw_y2 = beach_y - self.palm_tree_small_sprite.GetHeight() + 20
            dc.DrawBitmap(self.palm_tree_small_sprite, palm_draw_x2, palm_draw_y2, True)
        
        # Draw boat on water - match game_page.py positioning
        if self.boat_sprite:
            # Match game_page.py: boat_x = width * 0.3, boat_y = water_y + 10
            boat_x = int(w * 0.3)
            boat_y = water_y + 10
            boat_draw_x = boat_x - self.boat_sprite.GetWidth() // 2
            boat_draw_y = boat_y - self.boat_sprite.GetHeight() // 2
            dc.DrawBitmap(self.boat_sprite, boat_draw_x, boat_draw_y, True)

    # ====================================================
    # STEP 2: COMBINED FES INDICATOR (GREEN & ORANGE)
    # ====================================================
    def show_combined_fes(self):
        # Create the FES bar with callback
        self.fes_bar = TutorialPingPongFES(self.content_area, self.update_fes_text)
        self.content_sizer.Add(self.fes_bar, 0, wx.EXPAND | wx.ALL, 10)
        
        # Set initial text (orange is active when direction > 0, which is the initial state)
        # The callback will be called automatically when direction changes
        # But we need to set initial state
        self.update_fes_text(is_green=False)
    
    def update_fes_text(self, is_green):
        """Update the text label with highlighted GREEN or ORANGE"""
        # Safety check: make sure the panel and container still exist
        try:
            if not self or not self.text_container:
                return
        except:
            return
        
        # Clear existing labels and sizer
        try:
            for child in self.text_container.GetChildren():
                if isinstance(child, wx.StaticText):
                    child.Destroy()
            self.text_sizer.Clear()
        except:
            return
        
        # Create two separate labels for each instruction
        try:
            green_text = wx.StaticText(self.text_container, label="When the indicator is GREEN: Press and hold the FES button.")
            orange_text = wx.StaticText(self.text_container, label="When the indicator is ORANGE: Release the FES button.")
            
            # Set font for both
            font = wx.Font(26, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            green_text.SetFont(font)
            orange_text.SetFont(font)
            
            if is_green:
                # Highlight GREEN text (bold and green color)
                green_text.SetForegroundColour(wx.Colour(76, 175, 80))  # Green color
                green_text.SetFont(wx.Font(26, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                orange_text.SetForegroundColour(wx.Colour(100, 100, 100))  # Gray for inactive
            else:
                # Highlight ORANGE text (bold and orange color)
                orange_text.SetForegroundColour(wx.Colour(255, 152, 0))  # Orange color
                orange_text.SetFont(wx.Font(26, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                green_text.SetForegroundColour(wx.Colour(100, 100, 100))  # Gray for inactive
            
            # Add labels to sizer
            self.text_sizer.Add(green_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
            self.text_sizer.Add(orange_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 0)
            
            self.text_container.Layout()
            self.Layout()
        except:
            # If anything goes wrong (e.g., panel destroyed), just return silently
            pass


    # ====================================================
    # Navigation
    # ====================================================
    def on_next(self, event):
        self.step += 1
        self.show_step()

    def on_prev(self, event):
        if self.step == 0:
            # Go back to instructions page if on first step
            self.GetParent().switch_to_instructions_page()
        else:
            self.step -= 1
            self.show_step()

class TutorialPingPongFES(wx.Panel):
    def __init__(self, parent, callback=None):
        super().__init__(parent)

        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        # IMPORTANT: prevent flicker with proper double buffering
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)

        self.SetMinSize((-1, 150))

        self.progress = 0.0
        self.direction = 1
        self.speed = 0.01
        self.callback = callback
        self.last_direction = 1  # Track direction changes
        self.is_destroyed = False  # Flag to track if panel is being destroyed

        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(20)
        
        # Bind to window close/destroy events to clean up timer
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)

    def on_erase_background(self, event):
        # Prevent background erasure to avoid flicker
        pass
    
    def on_destroy(self, event):
        """Clean up timer when panel is destroyed"""
        self.is_destroyed = True
        if self.timer and self.timer.IsRunning():
            self.timer.Stop()
        event.Skip()

    def on_timer(self, evt):
        # Check if panel is being destroyed
        if self.is_destroyed:
            return
        
        # Check if panel still exists and is shown
        try:
            if not self or not self.IsShown():
                if self.timer and self.timer.IsRunning():
                    self.timer.Stop()
                return
        except:
            # Panel may have been destroyed
            if self.timer and self.timer.IsRunning():
                self.timer.Stop()
            return
        
        # update progress
        self.progress += self.speed * self.direction

        # ping-pong logic
        if self.progress >= 1.0:
            self.progress = 1.0
            self.direction = -1   # start shrinking (green active)
        elif self.progress <= 0.0:
            self.progress = 0.0
            self.direction = 1    # start expanding (orange active)

        # Call callback when direction changes (with safety check)
        if self.callback and self.direction != self.last_direction:
            try:
                # direction > 0 means orange (expanding), direction < 0 means green (shrinking)
                is_green = (self.direction < 0)
                self.callback(is_green)
                self.last_direction = self.direction
            except:
                # Callback may reference destroyed objects, stop timer
                if self.timer and self.timer.IsRunning():
                    self.timer.Stop()
                return

        # Use Refresh with False to avoid full repaint
        try:
            self.Refresh(False)
            self.Update()
        except:
            # Panel may have been destroyed during refresh
            if self.timer and self.timer.IsRunning():
                self.timer.Stop()

    def on_paint(self, event):
        # Use AutoBufferedPaintDC for proper double buffering
        dc = wx.AutoBufferedPaintDC(self)
        w, h = self.GetSize()

        # Clear the background
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()

        # Create GraphicsContext from the buffered DC for smooth rendering
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return

        bar_y = h // 2 - 25
        bar_height = 50
        padding = 60
        end_width = 100  # Increased from 80 to 100 (20 pixels wider)

        track_w = w - (2*padding) - (2*end_width)
        track_x = padding + end_width

        # ============ ORANGE LEFT =============
        gc.SetBrush(wx.Brush(wx.Colour(255,152,0)))
        gc.SetPen(wx.TRANSPARENT_PEN)
        path = gc.CreatePath()
        path.AddRoundedRectangle(padding, bar_y, end_width, bar_height, 25)
        gc.FillPath(path)

        # ============ GREEN RIGHT =============
        gc.SetBrush(wx.Brush(wx.Colour(76,175,80)))
        path = gc.CreatePath()
        path.AddRoundedRectangle(padding + end_width + track_w, bar_y, end_width, bar_height, 25)
        gc.FillPath(path)

        # ============ GREY TRACK =============
        gc.SetBrush(wx.Brush(wx.Colour(240,240,240)))
        path = gc.CreatePath()
        path.AddRoundedRectangle(track_x, bar_y, track_w, bar_height, 25)
        gc.FillPath(path)

        # ============ PROGRESS FILL =============
        fill_w = int(track_w * self.progress)
        if fill_w > 0:
            fill_color = wx.Colour(255,152,0) if self.direction > 0 else wx.Colour(76,175,80)
            gc.SetBrush(wx.Brush(fill_color))
            gc.SetPen(wx.TRANSPARENT_PEN)
            path = gc.CreatePath()
            path.AddRoundedRectangle(track_x, bar_y, fill_w, bar_height, 25)
            gc.FillPath(path)

        # ============ LABELS =============
        # Use DC for text rendering (more reliable than GraphicsContext text)
        dc.SetTextForeground(wx.Colour(255, 255, 255))
        dc.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        # Center text in buttons
        release_text = "RELEASE"
        press_text = "PRESS"
        release_text_width, _ = dc.GetTextExtent(release_text)
        press_text_width, _ = dc.GetTextExtent(press_text)
        # Orange button center: padding + end_width/2
        release_x = padding + (end_width - release_text_width) // 2
        # Green button center: padding + end_width + track_w + end_width/2
        press_x = padding + end_width + track_w + (end_width - press_text_width) // 2
        dc.DrawText(release_text, release_x, bar_y + 13)
        dc.DrawText(press_text, press_x, bar_y + 13)

'''
    def on_paint(self, event):
        dc = wx.PaintDC(self)
        w, h = self.GetSize()

        bar_y = h // 2 - 25
        bar_height = 50
        padding = 60
        end_width = 80

        track_w = w - (2*padding) - (2*end_width)
        track_x = padding + end_width

        # --------------------------
        # 1. LEFT ORANGE BLOCK
        # --------------------------
        dc.SetBrush(wx.Brush(wx.Colour(255, 152, 0)))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRoundedRectangle(padding, bar_y, end_width, bar_height, 25)

        # --------------------------
        # 2. RIGHT GREEN BLOCK
        # --------------------------
        dc.SetBrush(wx.Brush(wx.Colour(76, 175, 80)))
        dc.DrawRoundedRectangle(padding + end_width + track_w, bar_y,
                                end_width, bar_height, 25)

        # --------------------------
        # 3. GREY BACKGROUND TRACK
        # --------------------------
        dc.SetBrush(wx.Brush(wx.Colour(240, 240, 240)))
        dc.DrawRoundedRectangle(track_x, bar_y, track_w, bar_height, 25)
        
        # --------------------------
        # 4. PROGRESS FILL
        # --------------------------
        fill_w = int(track_w * self.progress)

        # Color depends on direction
        if self.direction > 0:
            fill_color = wx.Colour(255, 152, 0)    # filling = orange
        else:
            fill_color = wx.Colour(76, 175, 80)    # shrinking = green

        dc.SetBrush(wx.Brush(fill_color))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(track_x, bar_y, fill_w, bar_height)
        
        # --------------------------
        # 4. PROGRESS FILL (safe rounded + animated)
        # --------------------------
        fill_w = int(track_w * self.progress)

        if fill_w > 0:
            # pick color based on direction
            fill_color = wx.Colour(255, 152, 0) if self.direction > 0 else wx.Colour(76, 175, 80)

            gc = wx.GraphicsContext.Create(dc)
            gc.SetBrush(wx.Brush(fill_color))
            gc.SetPen(wx.Pen(fill_color))

            radius = 25

            # rounded clipped path
            path = gc.CreatePath()
            path.AddRoundedRectangle(track_x, bar_y, fill_w, bar_height, radius)

            # fill the rounded shape
            gc.FillPath(path)


        # --------------------------
        # 5. LABELS
        # --------------------------
        dc.SetTextForeground(wx.Colour(255, 255, 255))
        dc.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        dc.DrawText("RELEASE", padding + 12, bar_y + 13)
        dc.DrawText("PRESS", padding + end_width + track_w + 12, bar_y + 13)
'''