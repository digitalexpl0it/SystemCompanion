import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, GObject, GLib
import cairo
import math
import logging
from typing import List, Tuple, Optional, Dict


class ChartWidget(Gtk.DrawingArea):
    """A custom chart widget that draws line graphs using GTK4 DrawingArea."""
    
    def __init__(self, title: str = "", max_points: int = 50, series_names: Optional[List[str]] = None):
        super().__init__()
        self.title = title
        self.max_points = max_points
        self.series_names = series_names or ["Data"]
        
        # Support multiple data series
        self.data_series: Dict[str, List[float]] = {}
        for name in self.series_names:
            self.data_series[name] = []
        
        # Color scheme for different series
        self.series_colors = {
            "Data": (0.2, 0.8, 0.4),  # Green (default)
            "Read": (0.2, 0.6, 1.0),   # Blue for read operations
            "Write": (1.0, 0.4, 0.2),  # Orange for write operations
            "IOPS": (0.2, 0.8, 0.4),   # Green for total IOPS
            "Memory": (0.2, 0.8, 0.4), # Green for memory
            "Network": (0.2, 0.8, 0.4) # Green for network
        }
        
        self.logger = logging.getLogger(__name__)
        
        # Set up the drawing area
        self.set_draw_func(self._draw_chart, None)
        self.set_size_request(200, 80)
        
        # Start with empty data and clear any initial data
        for series in self.data_series.values():
            series.clear()
        
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        for series in self.data_series.values():
            series.clear()
        self.logger.info("ChartWidget cleaned up")
        
    def add_data_point(self, value: float, series_name: str = "Data") -> None:
        """Add a new data point to the specified series."""
        if series_name not in self.data_series:
            self.data_series[series_name] = []
            
        self.data_series[series_name].append(value)
        
        # Keep only the last max_points
        if len(self.data_series[series_name]) > self.max_points:
            self.data_series[series_name] = self.data_series[series_name][-self.max_points:]
        
        # Use moderate throttling - redraw every 1 second
        if not hasattr(self, '_redraw_pending'):
            self._redraw_pending = False
            self._last_redraw_time = 0
            
        current_time = GLib.get_monotonic_time()
        # Only redraw if it's been at least 1 second since last redraw
        if not self._redraw_pending and (current_time - self._last_redraw_time) > 1000000:  # 1 second in microseconds
            self._redraw_pending = True
            self._last_redraw_time = current_time
            GLib.idle_add(self._delayed_redraw)
            
    def _delayed_redraw(self) -> None:
        """Perform a delayed redraw to throttle updates."""
        self.queue_draw()
        self._redraw_pending = False
        

        
    def _draw_chart(self, drawing_area: Gtk.DrawingArea, cr: cairo.Context, 
                   width: int, height: int, user_data) -> None:
        """Draw the chart using Cairo."""
        try:
            # Clear background with dark color
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.paint()
            
            # Check if any series has data
            has_data = any(len(series) > 0 for series in self.data_series.values())
            
            if not has_data:
                self._draw_empty_chart(cr, width, height)
                return
                
            # Calculate chart area (with larger margins for text)
            margin = 50  # Increased margin for text to prevent clipping
            chart_width = width - 2 * margin
            chart_height = height - 2 * margin
            
            if chart_width <= 0 or chart_height <= 0:
                return
                
            # Find data range across all series
            all_values = []
            for series in self.data_series.values():
                all_values.extend(series)
                
            min_val = min(all_values) if all_values else 0
            max_val = max(all_values) if all_values else 100
            
            # For IOPS, ensure we have a reasonable range
            if max_val > 1000:  # Likely IOPS data
                if max_val == min_val:
                    max_val = min_val + 100
                # Add some padding for better visualization
                max_val = max_val * 1.1
            else:
                # Ensure we have a proper range for percentage data
                if max_val == min_val:
                    max_val = min_val + 1
                
                # For percentage data, ensure we have a meaningful range
                # If the range is too small, expand it to show the data better
                range_val = max_val - min_val
                if range_val < 5:  # If range is less than 5%
                    # Center the range around the current values
                    center = (max_val + min_val) / 2
                    min_val = max(0, center - 10)  # At least 10% range, don't go below 0
                    max_val = min(100, center + 10)  # At most 100%, don't go above 100
                
            # Draw axis labels
            self._draw_axis_labels(cr, margin, chart_width, chart_height, min_val, max_val)
            
            # Draw data lines for each series
            self._draw_data_lines(cr, margin, chart_width, chart_height, min_val, max_val)
                
        except Exception as e:
            self.logger.error(f"Error drawing chart: {e}")
            import traceback
            traceback.print_exc()
            
    def _draw_empty_chart(self, cr: cairo.Context, width: int, height: int) -> None:
        """Draw an empty chart with placeholder text."""
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(12)
        
        text = "No data"
        extents = cr.text_extents(text)
        x = (width - extents.width) / 2
        y = height / 2
        cr.move_to(x, y)
        cr.show_text(text)
        
    def _draw_grid(self, cr: cairo.Context, margin: int, chart_width: int, 
                  chart_height: int, min_val: float, max_val: float) -> None:
        """Draw the grid lines."""
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
            
    def _draw_data_lines(self, cr: cairo.Context, margin: int, chart_width: int,
                       chart_height: int, min_val: float, max_val: float) -> None:
        """Draw line graphs for all data series."""
        if not any(len(series) > 0 for series in self.data_series.values()):
            return
            
        # Draw grid lines
        self._draw_grid(cr, margin, chart_width, chart_height, min_val, max_val)
        
        # Draw each series
        for series_name, data_points in self.data_series.items():
            if len(data_points) > 1:
                self._draw_single_series(cr, margin, chart_width, chart_height, 
                                       min_val, max_val, data_points, series_name)
        
        # Draw current value indicators
        self._draw_current_values(cr, margin, chart_width, chart_height, min_val, max_val)
        
    def _draw_single_series(self, cr: cairo.Context, margin: int, chart_width: int,
                           chart_height: int, min_val: float, max_val: float, 
                           data_points: List[float], series_name: str) -> None:
        """Draw a single data series."""
        # Get color for this series
        color = self.series_colors.get(series_name, (0.2, 0.8, 0.4))
        
            # Calculate x step
        x_step = chart_width / (len(data_points) - 1) if len(data_points) > 1 else chart_width
            
        # Create path for filled area (only for single series or first series)
        if len(self.data_series) == 1 or series_name == list(self.data_series.keys())[0]:
            cr.set_source_rgba(color[0], color[1], color[2], 0.3)  # Semi-transparent fill
            cr.set_line_width(2.0)
            
            # Start at bottom left
            cr.move_to(margin, margin + chart_height)
            
            # Draw line to each data point
            for i, value in enumerate(data_points):
                x = margin + (i * x_step)
                y = margin + chart_height - ((value - min_val) / (max_val - min_val) * chart_height)
                cr.line_to(x, y)
            
            # Close the path to bottom right
            cr.line_to(margin + chart_width, margin + chart_height)
            cr.close_path()
            cr.fill()
        
        # Draw the line
        cr.set_source_rgb(*color)
        cr.set_line_width(2.0)
            
        # Draw line to each data point
        for i, value in enumerate(data_points):
            x = margin + (i * x_step)
            y = margin + chart_height - ((value - min_val) / (max_val - min_val) * chart_height)
            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        
        cr.stroke()
            
    def _draw_axis_labels(self, cr: cairo.Context, margin: int, chart_width: int,
                         chart_height: int, min_val: float, max_val: float) -> None:
        """Draw axis labels and values."""
        cr.set_source_rgb(1.0, 1.0, 1.0)  # Pure white text for maximum contrast
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(14)  # Much larger font size for better readability
        
        # Y-axis labels (left side)
        for i in range(6):  # 0%, 20%, 40%, 60%, 80%, 100%
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
            cr.set_source_rgb(1.0, 1.0, 1.0)  # Pure white text
            if max_val > 1000:  # IOPS data
                text = f"{value:.0f}"
            else:  # Percentage data
                text = f"{value:.0f}%"
            extents = cr.text_extents(text)
            cr.move_to(margin - 20 - extents.width, y + 4)
            cr.show_text(text)
        
        # X-axis label (bottom)
        cr.set_source_rgb(1.0, 1.0, 1.0)  # Pure white text
        cr.set_font_size(16)  # Much larger font
        text = "Time"
        extents = cr.text_extents(text)
        x = margin + (chart_width - extents.width) / 2
        y = margin + chart_height + 20
        cr.move_to(x, y)
        cr.show_text(text)
        
        # Y-axis label (left side, rotated)
        cr.set_source_rgb(1.0, 1.0, 1.0)  # Pure white text
        cr.set_font_size(16)  # Much larger font
        if max_val > 1000:  # IOPS data
            text = "IOPS"
        else:  # Percentage data
            text = "Usage %"
        extents = cr.text_extents(text)
        x = 15  # Moved further right to avoid clipping
        y = margin + chart_height / 2 + extents.width / 2
        cr.save()
        cr.translate(x, y)
        cr.rotate(-math.pi / 2)  # Rotate 90 degrees
        cr.move_to(0, 0)
        cr.show_text(text)
        cr.restore()
        
    def _draw_current_values(self, cr: cairo.Context, margin: int, chart_width: int,
                           chart_height: int, min_val: float, max_val: float) -> None:
        """Draw current value indicators for all series."""
        if not any(len(series) > 0 for series in self.data_series.values()):
            return
            
        # Draw legend if multiple series
        if len(self.data_series) > 1:
            self._draw_legend(cr, margin, chart_width, chart_height, min_val, max_val)
        
        # Draw current value for each series
        for i, (series_name, data_points) in enumerate(self.data_series.items()):
            if not data_points:
                continue
            current_value = data_points[-1]
            color = self.series_colors.get(series_name, (0.2, 0.8, 0.4))

            # Calculate position
            x = margin + chart_width
            y = margin + chart_height - ((current_value - min_val) / (max_val - min_val) * chart_height)

            # Draw value background
            if max_val > 1000:  # IOPS data
                text = f"{current_value:.0f}"
            else:  # Percentage data
                text = f"{current_value:.1f}%"
            extents = cr.text_extents(text)
            padding = 6

            # Draw rounded rectangle background with better contrast
            cr.set_source_rgb(0.15, 0.15, 0.15)  # Darker background
            cr.rectangle(x + 5, y - extents.height/2 - padding, 
                        extents.width + padding * 2, extents.height + padding * 2)
            cr.fill()

            # Draw border with series color
            cr.set_source_rgb(*color)
            cr.set_line_width(1.0)
            cr.rectangle(x + 5, y - extents.height/2 - padding, 
                        extents.width + padding * 2, extents.height + padding * 2)
            cr.stroke()

            # Draw text
            cr.set_source_rgb(1.0, 1.0, 1.0)  # Pure white text
            cr.set_font_size(14)  # Much larger font
            cr.move_to(x + 5 + padding, y + extents.height/2)
            cr.show_text(text)
            
    def _draw_legend(self, cr: cairo.Context, margin: int, chart_width: int, chart_height: int, min_val: float, max_val: float) -> None:
        """Draw legend for multiple series."""
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(12)
        
        legend_x = margin + 10
        legend_y = margin + 10
        line_height = 20
        
        for i, (series_name, data_points) in enumerate(self.data_series.items()):
            if not data_points:
                continue
                
            color = self.series_colors.get(series_name, (0.2, 0.8, 0.4))
            
            # Draw color indicator
            cr.set_source_rgb(*color)
            cr.rectangle(legend_x, legend_y + i * line_height - 8, 12, 3)
            cr.fill()
            
            # Draw series name
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.move_to(legend_x + 20, legend_y + i * line_height)
            cr.show_text(series_name)
            
    def _draw_title(self, cr: cairo.Context, width: int, height: int) -> None:
        """Draw the chart title."""
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(10)
        
        extents = cr.text_extents(self.title)
        x = (width - extents.width) / 2
        y = 15
        cr.move_to(x, y)
        cr.show_text(self.title) 