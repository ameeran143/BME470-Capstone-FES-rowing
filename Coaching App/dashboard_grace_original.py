# dashboard page
import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from button import CustomButton

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
    def __init__(self, parent):
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
        
        # Name field - on same line
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_label = wx.StaticText(self, label="Name:")
        name_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        name_label.SetFont(name_font)
        name_label.SetForegroundColour(self.text_color)
        name_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        name_value = wx.StaticText(self, label="John Doe")
        name_value.SetFont(name_font)
        name_value.SetForegroundColour(self.text_color)
        name_sizer.Add(name_value, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        info_sizer.Add(name_sizer, 0, wx.LEFT, 40)
        
        info_sizer.AddSpacer(15)
        
        # Longest Distance field - on same line
        distance_sizer = wx.BoxSizer(wx.HORIZONTAL)
        distance_label = wx.StaticText(self, label="Longest Distance:")
        distance_label.SetFont(name_font)
        distance_label.SetForegroundColour(self.text_color)
        distance_sizer.Add(distance_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        distance_value = wx.StaticText(self, label="2.5 km")
        distance_value.SetFont(name_font)
        distance_value.SetForegroundColour(self.text_color)
        distance_sizer.Add(distance_value, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        info_sizer.Add(distance_sizer, 0, wx.LEFT, 40)
        
        info_sizer.AddSpacer(15)
        
        # Longest Time field - on same line
        time_sizer = wx.BoxSizer(wx.HORIZONTAL)
        time_label = wx.StaticText(self, label="Longest Time:")
        time_label.SetFont(name_font)
        time_label.SetForegroundColour(self.text_color)
        time_sizer.Add(time_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        time_value = wx.StaticText(self, label="15:30")
        time_value.SetFont(name_font)
        time_value.SetForegroundColour(self.text_color)
        time_sizer.Add(time_value, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        info_sizer.Add(time_sizer, 0, wx.LEFT, 40)
        
        main_sizer.Add(info_sizer, 1, wx.EXPAND)
        main_sizer.AddSpacer(30)
        
        self.SetSizer(main_sizer)
        
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

class AchievementsCard(wx.Panel):
    """A custom card for displaying achievements with medal images"""
    def __init__(self, parent):
        super(AchievementsCard, self).__init__(parent)
        
        # Set base colors
        self.bg_color = wx.Colour(255, 255, 255)
        self.text_color = wx.Colour(33, 37, 41)
        self.SetBackgroundColour(self.bg_color)
        self.SetMinSize((380, 200))
        
        # Load medal images
        self.medal_images = self.load_medal_images()
        
        # Bind paint event for card styling
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
        # Create a vertical sizer for the content
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title: "Achievements"
        title = wx.StaticText(self, label="Achievements")
        title_font = wx.Font(28, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title.SetForegroundColour(self.text_color)
        main_sizer.Add(title, 0, wx.LEFT | wx.TOP, 30)
        
        # Add minimal spacing (medals moved up more)
        main_sizer.AddSpacer(5)
        
        # Create medals row with bronze left, gold center, silver right
        medals_row = wx.BoxSizer(wx.HORIZONTAL)
        
        # Calculate 30% of panel width for the medal size
        panel_width = 380  # Approximate panel width
        target_width = int(panel_width * 0.3)  # 30% of panel width
        
        # Add bronze medal with text below (to the left)
        bronze_container = wx.BoxSizer(wx.VERTICAL)
        
        bronze_bitmap = self.medal_images.get('bronze')
        if bronze_bitmap:
            # Get original image dimensions
            original_width = bronze_bitmap.GetWidth()
            original_height = bronze_bitmap.GetHeight()
            
            # Calculate scale factor to fit target width while preserving aspect ratio
            scale_factor = target_width / original_width
            target_height = int(original_height * scale_factor)
            
            # Scale the bronze image
            scaled_image = bronze_bitmap.ConvertToImage()
            scaled_image = scaled_image.Scale(target_width, target_height, wx.IMAGE_QUALITY_HIGH)
            bronze_scaled_bitmap = scaled_image.ConvertToBitmap()
            
            # Create the bronze medal display
            bronze_medal_ctrl = wx.StaticBitmap(self, -1, bronze_scaled_bitmap)
            bronze_container.Add(bronze_medal_ctrl, 0, wx.ALIGN_CENTER)
        else:
            # Fallback for bronze
            bronze_placeholder = wx.StaticText(self, label="BRONZE")
            bronze_placeholder_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            bronze_placeholder.SetFont(bronze_placeholder_font)
            bronze_placeholder.SetForegroundColour(self.text_color)
            bronze_container.Add(bronze_placeholder, 0, wx.ALIGN_CENTER)
        
        # Add text below bronze medal
        bronze_text = wx.StaticText(self, label="First 2km")
        bronze_text_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        bronze_text.SetFont(bronze_text_font)
        bronze_text.SetForegroundColour(self.text_color)
        bronze_container.Add(bronze_text, 0, wx.ALIGN_CENTER | wx.TOP, 25)  # Same spacing as gold text
        
        medals_row.Add(bronze_container, 0, wx.ALIGN_CENTER)
        
        # Add spacing between medals (tripled)
        medals_row.AddSpacer(60)
        
        # Add gold medal with text below (centered)
        gold_container = wx.BoxSizer(wx.VERTICAL)
        
        gold_bitmap = self.medal_images.get('gold')
        if gold_bitmap:
            # Get original image dimensions
            original_width = gold_bitmap.GetWidth()
            original_height = gold_bitmap.GetHeight()
            
            # Calculate scale factor to fit target width while preserving aspect ratio
            scale_factor = target_width / original_width
            target_height = int(original_height * scale_factor)
            
            # Scale the gold image
            scaled_image = gold_bitmap.ConvertToImage()
            scaled_image = scaled_image.Scale(target_width, target_height, wx.IMAGE_QUALITY_HIGH)
            gold_scaled_bitmap = scaled_image.ConvertToBitmap()
            
            # Create the gold medal display
            gold_medal_ctrl = wx.StaticBitmap(self, -1, gold_scaled_bitmap)
            gold_container.Add(gold_medal_ctrl, 0, wx.ALIGN_CENTER)
        else:
            # Fallback for gold
            gold_placeholder = wx.StaticText(self, label="GOLD")
            gold_placeholder_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            gold_placeholder.SetFont(gold_placeholder_font)
            gold_placeholder.SetForegroundColour(self.text_color)
            gold_container.Add(gold_placeholder, 0, wx.ALIGN_CENTER)
        
        # Add text below gold medal
        gold_text = wx.StaticText(self, label="First 30min session")
        gold_text_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)  # Slightly larger than half size
        gold_text.SetFont(gold_text_font)
        gold_text.SetForegroundColour(self.text_color)
        gold_container.Add(gold_text, 0, wx.ALIGN_CENTER | wx.TOP, 25)  # More spacing to move text further down
        
        medals_row.Add(gold_container, 0, wx.ALIGN_CENTER)
        
        # Add spacing between medals (tripled)
        medals_row.AddSpacer(60)
        
        # Add silver medal with text below (to the right)
        silver_container = wx.BoxSizer(wx.VERTICAL)
        
        silver_bitmap = self.medal_images.get('silver')
        if silver_bitmap:
            # Get original image dimensions
            original_width = silver_bitmap.GetWidth()
            original_height = silver_bitmap.GetHeight()
            
            # Calculate scale factor to fit target width while preserving aspect ratio
            scale_factor = target_width / original_width
            target_height = int(original_height * scale_factor)
            
            # Scale the silver image
            scaled_image = silver_bitmap.ConvertToImage()
            scaled_image = scaled_image.Scale(target_width, target_height, wx.IMAGE_QUALITY_HIGH)
            silver_scaled_bitmap = scaled_image.ConvertToBitmap()
            
            # Create the silver medal display
            silver_medal_ctrl = wx.StaticBitmap(self, -1, silver_scaled_bitmap)
            silver_container.Add(silver_medal_ctrl, 0, wx.ALIGN_CENTER)
        else:
            # Fallback for silver
            silver_placeholder = wx.StaticText(self, label="SILVER")
            silver_placeholder_font = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            silver_placeholder.SetFont(silver_placeholder_font)
            silver_placeholder.SetForegroundColour(self.text_color)
            silver_container.Add(silver_placeholder, 0, wx.ALIGN_CENTER)
        
        # Add text below silver medal
        silver_text = wx.StaticText(self, label="First 3km")
        silver_text_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        silver_text.SetFont(silver_text_font)
        silver_text.SetForegroundColour(self.text_color)
        silver_container.Add(silver_text, 0, wx.ALIGN_CENTER | wx.TOP, 25)  # Same spacing as gold text
        
        medals_row.Add(silver_container, 0, wx.ALIGN_CENTER)
        
        # Center the medals row (this keeps gold centered, silver to the right)
        center_sizer = wx.BoxSizer(wx.HORIZONTAL)
        center_sizer.AddStretchSpacer()
        center_sizer.Add(medals_row, 0, wx.ALIGN_CENTER)
        center_sizer.AddStretchSpacer()
        
        main_sizer.Add(center_sizer, 1, wx.EXPAND)
        main_sizer.AddSpacer(20)
        
        self.SetSizer(main_sizer)
        
    def load_medal_images(self):
        """Load medal images directly from PNG files without any modifications"""
        import os
        
        medal_images = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define medal image file names
        medal_files = {
            'gold': 'gold_medal.png',
            'silver': 'silver_medal.png', 
            'bronze': 'bronze_medal.png'
        }
        
        for medal_type, filename in medal_files.items():
            try:
                # Try to load from the same directory as the script
                image_path = os.path.join(script_dir, filename)
                if os.path.exists(image_path):
                    # Load PNG directly with wxPython - no modifications
                    wx_img = wx.Image(image_path)
                    if wx_img.IsOk():
                        medal_images[medal_type] = wx_img.ConvertToBitmap()
                    else:
                        print(f"Failed to load medal image: {image_path}")
                        medal_images[medal_type] = None
                else:
                    print(f"Medal image not found: {image_path}")
                    medal_images[medal_type] = None
            except Exception as e:
                print(f"Error loading medal image {filename}: {e}")
                medal_images[medal_type] = None
        
        return medal_images
        
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
        
        # Create horizontal sizer for evenly spaced items
        items_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add stretch spacer for even spacing
        items_sizer.AddStretchSpacer()
        
        # Create vertical sizer for palm tree and Hawaii text
        palm_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add palm tree
        try:
            import os
            # Use the same approach as game_page.py
            script_dir = os.path.dirname(os.path.dirname(__file__))
            palm_tree_path = os.path.join(script_dir, "palm-tree.png")
            
            palm_tree_image = wx.Image(palm_tree_path, wx.BITMAP_TYPE_PNG)
            palm_tree_image = palm_tree_image.Scale(80, 80, wx.IMAGE_QUALITY_HIGH)
            palm_tree_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(palm_tree_image))
            palm_sizer.Add(palm_tree_bitmap, 0, wx.ALIGN_CENTER)
        except Exception as e:
            print(f"Error loading palm tree: {e}")
            # Fallback to text
            palm_tree_placeholder = wx.StaticText(self, label="PALM TREE")
            palm_tree_placeholder.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            palm_tree_placeholder.SetForegroundColour(wx.Colour(0, 150, 0))  # Green color
            palm_sizer.Add(palm_tree_placeholder, 0, wx.ALIGN_CENTER)
        
        # Add "Hawaii" text below palm tree
        hawaii_text = wx.StaticText(self, label="Hawaii")
        hawaii_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        hawaii_text.SetForegroundColour(wx.Colour(0, 100, 0))  # Dark green color
        palm_sizer.Add(hawaii_text, 0, wx.ALIGN_CENTER)
        
        # Add check image below Hawaii text
        try:
            check_path = os.path.join(script_dir, "check.png")
            check_image = wx.Image(check_path, wx.BITMAP_TYPE_PNG)
            check_image = check_image.Scale(40, 40, wx.IMAGE_QUALITY_HIGH)
            check_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(check_image))
            palm_sizer.Add(check_bitmap, 0, wx.ALIGN_CENTER)
        except Exception as e:
            print(f"Error loading check image: {e}")
            # Fallback to text
            check_text = wx.StaticText(self, label="✓")
            check_text.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            check_text.SetForegroundColour(wx.Colour(0, 150, 0))  # Green color
            palm_sizer.Add(check_text, 0, wx.ALIGN_CENTER)
        
        # Add the palm sizer to the main items sizer with top alignment to keep palm tree at same level
        items_sizer.Add(palm_sizer, 0, wx.ALIGN_TOP)
        
        # Add stretch spacer for even spacing
        items_sizer.AddStretchSpacer()
        
        # Create vertical sizer for iceberg and Antarctica text
        iceberg_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add iceberg
        try:
            # Use the same approach as palm tree
            iceberg_path = os.path.join(script_dir, "iceberg.png")
            
            iceberg_image = wx.Image(iceberg_path, wx.BITMAP_TYPE_PNG)
            iceberg_image = iceberg_image.Scale(90, 90, wx.IMAGE_QUALITY_HIGH)
            iceberg_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(iceberg_image))
            iceberg_sizer.Add(iceberg_bitmap, 0, wx.ALIGN_CENTER)
        except Exception as e:
            print(f"Error loading iceberg: {e}")
            # Fallback to text
            iceberg_placeholder = wx.StaticText(self, label="ICEBERG")
            iceberg_placeholder.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            iceberg_placeholder.SetForegroundColour(wx.Colour(0, 100, 200))  # Blue color
            iceberg_sizer.Add(iceberg_placeholder, 0, wx.ALIGN_CENTER)
        
        # Add "Antarctica" text below iceberg
        antarctica_text = wx.StaticText(self, label="Antarctica")
        antarctica_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        antarctica_text.SetForegroundColour(wx.Colour(0, 0, 150))  # Blue color
        iceberg_sizer.Add(antarctica_text, 0, wx.ALIGN_CENTER)
        
        # Add lock image below Antarctica text
        try:
            lock_path = os.path.join(script_dir, "lock.png")
            lock_image = wx.Image(lock_path, wx.BITMAP_TYPE_PNG)
            lock_image = lock_image.Scale(40, 40, wx.IMAGE_QUALITY_HIGH)
            lock_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(lock_image))
            iceberg_sizer.Add(lock_bitmap, 0, wx.ALIGN_CENTER)
        except Exception as e:
            print(f"Error loading lock image: {e}")
            # Fallback to emoji
            lock_text = wx.StaticText(self, label="🔒")
            lock_text.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            iceberg_sizer.Add(lock_text, 0, wx.ALIGN_CENTER)
        
        # Add the iceberg sizer to the main items sizer with top alignment
        items_sizer.Add(iceberg_sizer, 0, wx.ALIGN_TOP)
        
        # Add stretch spacer for even spacing
        items_sizer.AddStretchSpacer()
        
        # Create vertical sizer for jungle and Amazon text
        jungle_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add jungle
        try:
            # Use the same approach as other images
            jungle_path = os.path.join(script_dir, "jungle.png")
            
            jungle_image = wx.Image(jungle_path, wx.BITMAP_TYPE_PNG)
            jungle_image = jungle_image.Scale(70, 70, wx.IMAGE_QUALITY_HIGH)
            jungle_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(jungle_image))
            jungle_sizer.Add(jungle_bitmap, 0, wx.ALIGN_CENTER)
        except Exception as e:
            print(f"Error loading jungle: {e}")
            # Fallback to text
            jungle_placeholder = wx.StaticText(self, label="JUNGLE")
            jungle_placeholder.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            jungle_placeholder.SetForegroundColour(wx.Colour(0, 150, 0))  # Green color
            jungle_sizer.Add(jungle_placeholder, 0, wx.ALIGN_CENTER)
        
        # Add "Amazon" text below jungle
        amazon_text = wx.StaticText(self, label="Amazon")
        amazon_text.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        amazon_text.SetForegroundColour(wx.Colour(0, 100, 0))  # Green color (same as Hawaii)
        jungle_sizer.Add(amazon_text, 0, wx.ALIGN_CENTER)
        
        # Add lock image below Amazon text
        try:
            lock_path = os.path.join(script_dir, "lock.png")
            lock_image = wx.Image(lock_path, wx.BITMAP_TYPE_PNG)
            lock_image = lock_image.Scale(40, 40, wx.IMAGE_QUALITY_HIGH)
            lock_bitmap = wx.StaticBitmap(self, bitmap=wx.Bitmap(lock_image))
            jungle_sizer.Add(lock_bitmap, 0, wx.ALIGN_CENTER)
        except Exception as e:
            print(f"Error loading lock image: {e}")
            # Fallback to emoji
            lock_text2 = wx.StaticText(self, label="🔒")
            lock_text2.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            jungle_sizer.Add(lock_text2, 0, wx.ALIGN_CENTER)
        
        # Add the jungle sizer to the main items sizer with top alignment
        items_sizer.Add(jungle_sizer, 0, wx.ALIGN_TOP)
        
        # Add stretch spacer for even spacing
        items_sizer.AddStretchSpacer()
        
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

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create header sizer for title
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add stretch spacer to center the title
        header_sizer.AddStretchSpacer()
        
        # Header: "Hello, John" - aesthetically pleasing and centered
        header = wx.StaticText(self, label="Hello, John")
        header_font = wx.Font(36, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        header.SetForegroundColour(wx.Colour(33, 37, 41))
        header_sizer.Add(header, 0, wx.ALIGN_CENTER_VERTICAL)
        
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

        # Create modern card sections - much bigger, empty boxes
        self.section1_card = UserInfoCard(self)
        self.section2_card = StatisticsCard(self)
        self.section3_card = AchievementsCard(self)
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

    def on_back_to_start(self, event):
        parent = self.GetParent()
        parent.switch_to_start_page()
    
