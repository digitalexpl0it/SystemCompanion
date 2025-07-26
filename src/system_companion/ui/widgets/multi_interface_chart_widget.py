import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, GObject, GLib
import cairo
import math
import logging
from typing import List, Dict


class MultiInterfaceChartWidget(Gtk.DrawingArea):
    """A chart widget that displays multiple network interfaces with different colors."""
    
    def __init__(self, title: str = "", max_points: int = 15):
        """Initialize the multi-interface chart widget."""
        super().__init__()
        
        self.title = title
        self.max_points = max_points
        self.interface_data = {}  # Dict[interface_name, Dict[data_type, List[float]]]
        self.interface_colors = {}  # Dict[interface_name, Tuple[float, float, float]]
        
        # Color palette for interfaces
        self.color_palette = [
            (0.2, 0.6, 1.0),   # Blue
            (1.0, 0.4, 0.2),   # Orange
            (0.2, 0.8, 0.4),   # Green
            (0.8, 0.2, 0.8),   # Purple
            (1.0, 0.8, 0.2),   # Yellow
            (0.2, 0.8, 0.8),   # Cyan
            (1.0, 0.6, 0.8),   # Pink
            (0.6, 0.8, 0.2),   # Lime
        ]
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize performance counters
        self._redraw_pending = False
        self._last_redraw_time = 0
        self._debug_counter = 0
        self._error_counter = 0
        
        # Set up drawing
        self.set_draw_func(self._draw_chart, None)
        
        # Set minimum size
        self.set_size_request(400, 300)
        
        # Log memory usage for debugging
        self._log_memory_usage()
    
    def _log_memory_usage(self) -> None:
        """Log memory usage for debugging memory leaks."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            self.logger.debug(f"Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB")
        except Exception as e:
            self.logger.debug(f"Could not log memory usage: {e}")
    
    def _get_interface_color(self, interface_name: str) -> tuple:
        """Get or assign a color for an interface."""
        if interface_name not in self.interface_colors:
            # Assign next available color
            color_index = len(self.interface_colors) % len(self.color_palette)
            self.interface_colors[interface_name] = self.color_palette[color_index]
            self.logger.debug(f"Assigned color {self.color_palette[color_index]} to interface {interface_name}")
        
        return self.interface_colors[interface_name]
    
    def add_interface_data(self, interface_name: str, data_type: str, value: float) -> None:
        """Add a new data point for a specific interface and data type."""
        try:
            if interface_name not in self.interface_data:
                self.interface_data[interface_name] = {}
            
            if data_type not in self.interface_data[interface_name]:
                self.interface_data[interface_name][data_type] = []
            
            # Add new data point
            self.interface_data[interface_name][data_type].append(float(value))
            
            # Keep only the last max_points to prevent memory growth
            if len(self.interface_data[interface_name][data_type]) > self.max_points:
                self.interface_data[interface_name][data_type] = self.interface_data[interface_name][data_type][-self.max_points:]
            
            # Use responsive throttling for smooth updates
            current_time = GLib.get_monotonic_time()
            # Only redraw if it's been at least 500ms since last redraw
            if not self._redraw_pending and (current_time - self._last_redraw_time) > 500000:  # 500ms in microseconds
                self._redraw_pending = True
                self._last_redraw_time = current_time
                GLib.idle_add(self._delayed_redraw)
                
        except Exception as e:
            self.logger.error(f"Error adding interface data: {e}")
    
    def _delayed_redraw(self) -> None:
        """Perform a delayed redraw to throttle updates."""
        try:
            # Use low priority to prevent blocking UI
            GLib.idle_add(self.queue_draw, priority=GLib.PRIORITY_LOW)
            self._redraw_pending = False
        except Exception as e:
            self.logger.error(f"Error in delayed redraw: {e}")
            self._redraw_pending = False
    
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        try:
            self.interface_data.clear()
            self.interface_colors.clear()
            self.logger.info("MultiInterfaceChartWidget cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _draw_chart(self, drawing_area: Gtk.DrawingArea, cr: cairo.Context, 
                   width: int, height: int, user_data) -> None:
        """Draw the multi-interface chart using Cairo."""
        try:
            # Clear background with dark color
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.paint()
            
            if not self.interface_data:
                self._draw_empty_chart(cr, width, height)
                return
            
            # Calculate chart area
            margin = 35
            chart_width = width - 2 * margin
            chart_height = height - 2 * margin
            
            if chart_width <= 0 or chart_height <= 0:
                return
            
            # Find data range across all interfaces and data types
            all_values = []
            for interface_data in self.interface_data.values():
                for data_points in interface_data.values():
                    all_values.extend(data_points)
            
            min_val = min(all_values) if all_values else 0
            max_val = max(all_values) if all_values else 100
            
            # Ensure we have a reasonable range
            if max_val == min_val:
                max_val = min_val + 0.1  # Smaller increment for network data
            
            # For network data, use a more appropriate scale
            if self.interface_data:  # Network data
                # If max_val is very small, scale it up for better visibility
                if max_val < 0.1:
                    max_val = 0.1  # Set minimum scale to 0.1 Mbps
                elif max_val < 1.0:
                    max_val = 1.0  # Set minimum scale to 1.0 Mbps
                else:
                    # Add some padding for better visualization
                    max_val = max_val * 1.2
            else:
                # Add some padding for better visualization (percentage data)
                max_val = max_val * 1.1
            
            # Draw grid
            self._draw_grid(cr, margin, chart_width, chart_height)
            
            # Draw axis labels
            self._draw_axis_labels(cr, margin, chart_width, chart_height, min_val, max_val)
            
            # Draw interface graphs
            self._draw_interface_graphs(cr, margin, chart_width, chart_height, min_val, max_val)
            
            # Draw legend
            self._draw_legend(cr, margin, chart_width, chart_height)
            
        except Exception as e:
            self.logger.error(f"Error drawing chart: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_empty_chart(self, cr: cairo.Context, width: int, height: int) -> None:
        """Draw an empty chart with placeholder text."""
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(12)
        
        text = "No network data"
        extents = cr.text_extents(text)
        x = (width - extents.width) / 2
        y = height / 2
        cr.move_to(x, y)
        cr.show_text(text)
    
    def _draw_grid(self, cr: cairo.Context, margin: int, chart_width: int, chart_height: int) -> None:
        """Draw grid lines."""
        cr.set_source_rgb(0.3, 0.3, 0.3)  # Light grey
        cr.set_line_width(0.5)
        
        # Horizontal grid lines
        for i in range(5):
            y = margin + (i * chart_height / 4)
            cr.move_to(margin, y)
            cr.line_to(margin + chart_width, y)
            cr.stroke()
        
        # Vertical grid lines
        for i in range(5):
            x = margin + (i * chart_width / 4)
            cr.move_to(x, margin)
            cr.line_to(x, margin + chart_height)
            cr.stroke()
    
    def _draw_axis_labels(self, cr: cairo.Context, margin: int, chart_width: int,
                         chart_height: int, min_val: float, max_val: float) -> None:
        """Draw axis labels and values."""
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(12)
        
        # Y-axis labels (left side)
        for i in range(6):
            y_percent = i / 5.0
            y = margin + chart_height - (y_percent * chart_height)
            value = min_val + (y_percent * (max_val - min_val))
            
            # Draw horizontal line
            cr.set_source_rgb(0.4, 0.4, 0.4)  # Darker grey for axis lines
            cr.set_line_width(0.5)
            cr.move_to(margin - 5, y)
            cr.line_to(margin, y)
            cr.stroke()
            
            # Draw value label
            cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
            # Check if this is network data by looking at the data structure
            if self.interface_data:  # If we have interface data, it's network data
                text = f"{value:.3f}"
            else:  # Percentage data
                text = f"{value:.0f}%"
            extents = cr.text_extents(text)
            cr.move_to(margin - 15 - extents.width, y + 4)
            cr.show_text(text)
        
        # X-axis label (bottom)
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.set_font_size(14)
        text = "Time"
        extents = cr.text_extents(text)
        x = margin + (chart_width - extents.width) / 2
        y = margin + chart_height + 20
        cr.move_to(x, y)
        cr.show_text(text)
        
        # Y-axis label (left side, rotated)
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.set_font_size(14)
        # Check if this is network data by looking at the data structure
        if self.interface_data:  # If we have interface data, it's network data
            text = "Mbps"
        else:  # Percentage data
            text = "Usage %"
        extents = cr.text_extents(text)
        x = 8
        y = margin + chart_height / 2 + extents.width / 2
        cr.save()
        cr.translate(x, y)
        cr.rotate(-math.pi / 2)  # Rotate 90 degrees
        cr.move_to(0, 0)
        cr.show_text(text)
        cr.restore()
    
    def _draw_interface_graphs(self, cr: cairo.Context, margin: int, chart_width: int,
                              chart_height: int, min_val: float, max_val: float) -> None:
        """Draw graphs for all interfaces."""
        try:
            for interface_name, interface_data in self.interface_data.items():
                color = self._get_interface_color(interface_name)
                
                # Draw each data type for this interface
                for data_type, data_points in interface_data.items():
                    if len(data_points) > 1:
                        self._draw_single_interface_line(cr, margin, chart_width, chart_height,
                                                       min_val, max_val, data_points, color, data_type)
                        
        except Exception as e:
            self.logger.error(f"Error drawing interface graphs: {e}")
    
    def _draw_single_interface_line(self, cr: cairo.Context, margin: int, chart_width: int,
                                   chart_height: int, min_val: float, max_val: float,
                                   data_points: List[float], color: tuple, data_type: str) -> None:
        """Draw a single interface line graph."""
        try:
            # Calculate x step
            x_step = chart_width / (len(data_points) - 1) if len(data_points) > 1 else chart_width
            
            # Set line style based on data type
            if data_type == "in":
                # Solid line for incoming data
                cr.set_source_rgb(*color)
                cr.set_line_width(2.0)
            else:  # "out"
                # Dashed line for outgoing data
                cr.set_source_rgb(*color)
                cr.set_line_width(2.0)
                cr.set_dash([5, 3])  # Dashed line pattern
            
            # Draw line through data points
            for i, value in enumerate(data_points):
                x = margin + (i * x_step)
                # Ensure value is within bounds and normalize properly
                clamped_value = max(0, value)
                normalized_value = (clamped_value - min_val) / (max_val - min_val) if (max_val - min_val) > 0 else 0
                # Ensure normalized value stays within 0-1 range
                normalized_value = max(0, min(1, normalized_value))
                y = margin + chart_height - (normalized_value * chart_height)
                
                if i == 0:
                    cr.move_to(x, y)
                else:
                    cr.line_to(x, y)
            
            cr.stroke()
            
            # Reset dash pattern
            cr.set_dash([])
            
        except Exception as e:
            self.logger.error(f"Error drawing single interface line: {e}")
    
    def _draw_legend(self, cr: cairo.Context, margin: int, chart_width: int, chart_height: int) -> None:
        """Draw legend for interfaces."""
        try:
            cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(10)
            
            legend_x = margin + 10
            legend_y = margin + 10
            line_height = 16
            
            interface_count = 0
            for interface_name, interface_data in self.interface_data.items():
                color = self._get_interface_color(interface_name)
                
                # Draw interface name
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.move_to(legend_x, legend_y + interface_count * line_height)
                cr.show_text(f"{interface_name}:")
                
                # Draw data type indicators
                data_type_y = legend_y + interface_count * line_height + 12
                for data_type in interface_data.keys():
                    if data_type == "in":
                        # Solid line indicator
                        cr.set_source_rgb(*color)
                        cr.set_line_width(2.0)
                        cr.set_dash([])
                        cr.move_to(legend_x + 80, data_type_y)
                        cr.line_to(legend_x + 120, data_type_y)
                        cr.stroke()
                        
                        # Label
                        cr.set_source_rgb(1.0, 1.0, 1.0)
                        cr.move_to(legend_x + 125, data_type_y + 4)
                        cr.show_text("In")
                        
                    elif data_type == "out":
                        # Dashed line indicator
                        cr.set_source_rgb(*color)
                        cr.set_line_width(2.0)
                        cr.set_dash([3, 2])
                        cr.move_to(legend_x + 80, data_type_y + 8)
                        cr.line_to(legend_x + 120, data_type_y + 8)
                        cr.stroke()
                        cr.set_dash([])  # Reset dash
                        
                        # Label
                        cr.set_source_rgb(1.0, 1.0, 1.0)
                        cr.move_to(legend_x + 125, data_type_y + 12)
                        cr.show_text("Out")
                
                interface_count += 1
                
        except Exception as e:
            self.logger.error(f"Error drawing legend: {e}") 