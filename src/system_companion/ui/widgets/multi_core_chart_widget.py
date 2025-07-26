import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, GObject, GLib
import cairo
import math
import logging
from typing import List, Dict


class MultiCoreChartWidget(Gtk.DrawingArea):
    """A chart widget that displays multiple CPU cores with different colors."""
    
    def __init__(self, title: str = "", max_points: int = 15):  # Reduced from 20 to 15
        """Initialize the multi-core chart widget."""
        super().__init__()
        
        self.title = title
        self.max_points = max_points
        self.core_data = {}
        self.core_color = (0.2, 0.6, 1.0)  # Nice blue color for all cores
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize performance counters
        self._redraw_pending = False
        self._last_redraw_time = 0
        self._debug_counter = 0
        self._error_counter = 0
        
        # Cache processor info to prevent memory leaks
        self._processor_info = self._get_processor_info()
        
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
    
    def _get_processor_info(self) -> str:
        """Get processor info once and cache it."""
        try:
            from ...core.system_monitor import SystemMonitor
            monitor = SystemMonitor()
            cpu_info = monitor.get_cpu_info()
            processor_info = cpu_info.model_name
            
            # Truncate if too long
            if len(processor_info) > 30:
                processor_info = processor_info[:27] + "..."
                
            return processor_info
        except Exception as e:
            self.logger.error(f"Error getting processor info: {e}")
            return "Unknown CPU"
    
    def cleanup(self) -> None:
        """Clean up resources to prevent memory leaks."""
        try:
            # Clear all data
            self.core_data.clear()
            
            # Reset counters
            self._redraw_pending = False
            self._last_redraw_time = 0
            self._debug_counter = 0
            self._error_counter = 0
            
            # Force garbage collection
            import gc
            gc.collect()
            
            self.logger.debug("MultiCoreChartWidget cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def add_core_data(self, core_id: int, value: float) -> None:
        """Add a new data point for a specific core."""
        try:
            if core_id not in self.core_data:
                self.core_data[core_id] = []
                self.logger.debug(f"Initialized core {core_id}")
            
            # Add new data point
            self.core_data[core_id].append(float(value))  # Ensure it's a float
            
            # Keep only the last max_points to prevent memory growth
            if len(self.core_data[core_id]) > self.max_points:
                self.core_data[core_id] = self.core_data[core_id][-self.max_points:]
            
            # Use responsive throttling for smooth updates
            current_time = GLib.get_monotonic_time()
            # Only redraw if it's been at least 500ms since last redraw
            if not self._redraw_pending and (current_time - self._last_redraw_time) > 500000:  # 500ms in microseconds
                self._redraw_pending = True
                self._last_redraw_time = current_time
                GLib.idle_add(self._delayed_redraw)
                
        except Exception as e:
            self.logger.error(f"Error adding core data: {e}")
    
    def _delayed_redraw(self) -> None:
        """Perform a delayed redraw to throttle updates."""
        try:
            # Use low priority to prevent blocking UI
            GLib.idle_add(self.queue_draw, priority=GLib.PRIORITY_LOW)
            self._redraw_pending = False
        except Exception as e:
            self.logger.error(f"Error in delayed redraw: {e}")
            self._redraw_pending = False
            
    def _draw_chart(self, drawing_area: Gtk.DrawingArea, cr: cairo.Context, 
                   width: int, height: int, user_data) -> None:
        """Draw the multi-core chart using Cairo with grid layout."""
        try:
            # Clear background with dark color
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.paint()
            
            if not self.core_data:
                self._draw_empty_chart(cr, width, height)
                return
                
            # Calculate grid layout - minimal spacing for maximum graph area
            margin = 4  # Increased margin for better padding between graphs
            title_height = 5  # Very minimal title height to eliminate top space
            available_width = width - 2 * margin
            available_height = height - 2 * margin - title_height
            
            # Determine grid dimensions based on number of cores and available space
            num_cores = len(self.core_data)
            
            # Simplified grid calculation for performance
            if num_cores <= 8:
                cols = 4
            elif num_cores <= 12:
                cols = 4
            elif num_cores <= 16:
                cols = 4
            elif num_cores <= 20:
                cols = 5
            else:
                cols = 6
                
            rows = (num_cores + cols - 1) // cols  # Ceiling division
            
            # Calculate individual graph size with larger minimum sizes
            graph_width = max(100, available_width // cols)  # Increased minimum for more space
            graph_height = max(80, available_height // rows)  # Increased minimum for more vertical space
            
            # Adjust if we need more space
            total_needed_height = title_height + rows * graph_height + 2 * margin
            if total_needed_height > height:
                # Reduce graph height to fit
                available_for_graphs = height - title_height - 2 * margin
                graph_height = max(60, available_for_graphs // rows)  # Increased minimum
            
            # Draw individual core graphs
            core_ids = sorted(self.core_data.keys())
            
            # Debug logging - reduced frequency
            if not hasattr(self, '_debug_counter'):
                self._debug_counter = 0
            self._debug_counter += 1
            if self._debug_counter % 10 == 0:  # Log every 10th draw
                self.logger.debug(f"Drawing {len(core_ids)} cores: {core_ids}")
            
            for i, core_id in enumerate(core_ids):
                    
                # Calculate position
                col = i % cols
                row = i // cols
                
                x = margin + col * graph_width
                y = margin + title_height + row * graph_height
                
                # Ensure we don't draw outside bounds
                if x + graph_width > width or y + graph_height > height:
                    continue
                
                # Draw individual core graph
                try:
                    self._draw_single_core_graph(cr, x, y, graph_width, graph_height, core_id)
                except Exception as e:
                    # Reduced error logging frequency
                    if not hasattr(self, '_error_counter'):
                        self._error_counter = 0
                    self._error_counter += 1
                    if self._error_counter % 5 == 0:  # Log every 5th error
                        self.logger.error(f"Error drawing core {core_id} graph: {e}")
                    continue
                
        except Exception as e:
            self.logger.error(f"Error drawing multi-core chart: {e}")
            import traceback
            traceback.print_exc()
            
    def _draw_empty_chart(self, cr: cairo.Context, width: int, height: int) -> None:
        """Draw an empty chart with placeholder text."""
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(12)
        
        text = "No CPU data"
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
            
    def _draw_core_lines(self, cr: cairo.Context, margin: int, chart_width: int,
                        chart_height: int, min_val: float, max_val: float) -> None:
        """Draw the data lines for each core."""
        for core_id, data_points in self.core_data.items():
            if len(data_points) < 2:
                continue
                
            # Get color for this core (single color for all cores)
            color = self.core_color
            
            # Draw curved line using Catmull-Rom splines for smoother curves
            cr.set_source_rgb(*color)
            cr.set_line_width(2.0)
            
            if len(data_points) >= 2:
                # Create smooth curve using Catmull-Rom splines
                points = []
                for i, value in enumerate(data_points):
                    x = margin + (i * chart_width / (len(data_points) - 1))
                    # Fix the Y coordinate calculation
                    normalized_value = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
                    y = margin + chart_height - (normalized_value * chart_height)
                    points.append((x, y))
                
                # Draw simplified curve for better performance
                if len(points) >= 2:
                    cr.move_to(points[0][0], points[0][1])
                    
                    # Use simple line segments for better performance
                    for i in range(1, len(points)):
                        cr.line_to(points[i][0], points[i][1])
                    
                    cr.stroke()
            
            # Draw data points (smaller and less prominent)
            cr.set_source_rgb(0.6, 0.6, 0.6)  # Light grey instead of white
            for i, value in enumerate(data_points):
                x = margin + (i * chart_width / (len(data_points) - 1))
                # Fix the Y coordinate calculation
                normalized_value = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
                y = margin + chart_height - (normalized_value * chart_height)
                
                cr.arc(x, y, 1.0, 0, 2 * math.pi)  # Even smaller dots for multi-core
                cr.fill()
                
    def _draw_title(self, cr: cairo.Context, width: int, height: int) -> None:
        """Draw the chart title."""
        cr.set_source_rgb(1.0, 1.0, 1.0)  # Pure white text
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(14)  # Reduced font size for performance
        
        # Draw "CPU" title on the left
        title = "CPU"
        cr.move_to(15, height - 8)  # Adjusted position
        cr.show_text(title)
        
        # Use cached processor info to prevent memory leaks
        processor_info = getattr(self, '_processor_info', 'Unknown CPU')
            
        extents = cr.text_extents(processor_info)
        cr.move_to(width - extents.width - 15, height - 8)  # Adjusted position
        cr.show_text(processor_info)
        
    def _draw_single_core_graph(self, cr: cairo.Context, x: int, y: int, width: int, height: int, core_id: int) -> None:
        """Draw a single core mini line graph with filled area."""
        if core_id not in self.core_data or not self.core_data[core_id]:
            return
            
        data_points = self.core_data[core_id]
        
        # Draw background
        cr.set_source_rgb(0.15, 0.15, 0.15)
        cr.rectangle(x, y, width, height)
        cr.fill()
        
        # Calculate graph area with minimal margins for maximum space usage
        graph_margin = 2  # Increased margin for better padding between graphs
        graph_width = width - 2 * graph_margin
        graph_height = height - 2 * graph_margin - 10  # Minimal space for labels to maximize graph area
        
        if graph_width <= 0 or graph_height <= 0 or len(data_points) < 2:
            return
            
        # Get color for this core (single color for all cores)
        color = self.core_color
        current_value = data_points[-1]
        
        # Calculate data range for normalization with proper bounds
        min_val = min(data_points) if data_points else 0
        max_val = max(data_points) if data_points else 100
        
        # Ensure we have a reasonable range and prevent division by zero
        if max_val == min_val:
            # If all values are the same, create a small range around the value
            min_val = max(0, min_val - 5)
            max_val = min(100, max_val + 5)
        
        # Ensure min_val is never negative and max_val never exceeds 100
        min_val = max(0, min_val)
        max_val = min(100, max_val)
        
        data_range = max_val - min_val
        
        # Draw minimal grid lines for performance
        cr.set_source_rgb(0.25, 0.25, 0.25)
        cr.set_line_width(0.5)
        
        # Only draw 1 horizontal grid line for maximum performance
        grid_y = y + graph_margin + graph_height / 2
        cr.move_to(x + graph_margin, grid_y)
        cr.line_to(x + graph_margin + graph_width, grid_y)
        cr.stroke()
        
        # Draw filled line graph - ultra simplified for performance
        if len(data_points) >= 2:
            # Create path for filled area
            cr.set_source_rgba(color[0], color[1], color[2], 0.2)  # Very transparent for performance
            
            # Start path at bottom-left
            cr.move_to(x + graph_margin, y + graph_margin + graph_height)
            
            # Draw line through data points (ultra simplified)
            for i, value in enumerate(data_points):
                point_x = x + graph_margin + (i * graph_width / (len(data_points) - 1))
                # Ensure value is within bounds and normalize properly
                clamped_value = max(0, min(100, value))
                normalized_value = (clamped_value - min_val) / data_range if data_range > 0 else 0
                # Ensure normalized value stays within 0-1 range
                normalized_value = max(0, min(1, normalized_value))
                point_y = y + graph_margin + graph_height - (normalized_value * graph_height)
                cr.line_to(point_x, point_y)
            
            # Complete the path to create filled area
            cr.line_to(x + graph_margin + graph_width, y + graph_margin + graph_height)
            cr.close_path()
            cr.fill()
            
            # Draw the line on top (ultra simplified)
            cr.set_source_rgb(*color)
            cr.set_line_width(0.8)  # Very thin line for performance
            cr.move_to(x + graph_margin, y + graph_margin + graph_height)
            
            for i, value in enumerate(data_points):
                point_x = x + graph_margin + (i * graph_width / (len(data_points) - 1))
                # Ensure value is within bounds and normalize properly
                clamped_value = max(0, min(100, value))
                normalized_value = (clamped_value - min_val) / data_range if data_range > 0 else 0
                # Ensure normalized value stays within 0-1 range
                normalized_value = max(0, min(1, normalized_value))
                point_y = y + graph_margin + graph_height - (normalized_value * graph_height)
                cr.line_to(point_x, point_y)
            
            cr.stroke()
            
            # Draw current value indicator (ultra simplified)
            if data_points:
                last_x = x + graph_margin + graph_width
                # Ensure last value is within bounds and normalize properly
                last_clamped_value = max(0, min(100, data_points[-1]))
                last_normalized = (last_clamped_value - min_val) / data_range if data_range > 0 else 0
                # Ensure normalized value stays within 0-1 range
                last_normalized = max(0, min(1, last_normalized))
                last_y = y + graph_margin + graph_height - (last_normalized * graph_height)
                
                cr.set_source_rgb(1.0, 1.0, 1.0)  # White indicator
                cr.arc(last_x, last_y, 1.0, 0, 2 * math.pi)  # Very small indicator
                cr.fill()
        
        # Draw minimal border for performance
        cr.set_source_rgb(0.4, 0.4, 0.4)
        cr.set_line_width(0.3)  # Very thin border
        cr.rectangle(x + graph_margin, y + graph_margin, graph_width, graph_height)
        cr.stroke()
        
        # Draw labels with larger, more readable text
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(11)  # Increased font size for better readability
        
        # Core label (top-left)
        core_label = f"Core {core_id}"
        cr.move_to(x + graph_margin, y + height - 3)
        cr.show_text(core_label)
        
        # Current value label (top-right) - show actual current value
        if data_points and len(data_points) > 0:
            current_value = data_points[-1]  # Get the most recent value
            value_text = f"{current_value:.0f}%"
            # Debug logging
            if core_id == 0:  # Only log for first core to avoid spam
                self.logger.debug(f"Core {core_id} current value: {current_value}, data points: {len(data_points)}")
        else:
            value_text = "0%"
        extents = cr.text_extents(value_text)
        cr.move_to(x + width - extents.width - graph_margin, y + height - 3)
        cr.show_text(value_text)
            
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
            text = f"{value:.0f}%"
            extents = cr.text_extents(text)
            cr.move_to(margin - 15 - extents.width, y + 4)
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
        text = "CPU Usage %"
        extents = cr.text_extents(text)
        x = 8
        y = margin + chart_height / 2 + extents.width / 2
        cr.save()
        cr.translate(x, y)
        cr.rotate(-math.pi / 2)  # Rotate 90 degrees
        cr.move_to(0, 0)
        cr.show_text(text)
        cr.restore() 