#!/usr/bin/env python3
"""
Individual network interface chart widget with percentage display.
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import cairo
import math
import logging
from typing import List, Optional

class NetworkInterfaceChartWidget(Gtk.DrawingArea):
    """Individual network interface chart widget with percentage display."""
    
    def __init__(self, interface_name: str, max_points: int = 15):
        """Initialize the network interface chart widget."""
        super().__init__()
        
        self.interface_name = interface_name
        self.max_points = max_points
        self.logger = logging.getLogger(f"system_companion.ui.network_interface_chart_widget.{interface_name}")
        
        # Data storage
        self.in_data = []  # Incoming data points
        self.out_data = []  # Outgoing data points
        self.max_speed = 0.0  # Track maximum speed for percentage calculation
        
        # Colors
        self.in_color = (0.2, 0.8, 0.2)  # Green for incoming
        self.out_color = (0.2, 0.6, 0.9)  # Blue for outgoing
        self.grid_color = (0.3, 0.3, 0.3)
        self.text_color = (1.0, 1.0, 1.0)
        
        # Setup drawing
        self.set_draw_func(self._draw_chart, None)
        self.set_vexpand(True)
        self.set_hexpand(True)
        
        # Add CSS class for styling
        self.add_css_class("network-interface-chart")
        
        self.logger.debug(f"Network interface chart widget initialized for {interface_name}")
    
    def add_data(self, in_speed_mbps: float, out_speed_mbps: float) -> None:
        """Add incoming and outgoing speed data points."""
        try:
            # Add data points
            self.in_data.append(in_speed_mbps)
            self.out_data.append(out_speed_mbps)
            
            # Keep only the last max_points
            if len(self.in_data) > self.max_points:
                self.in_data = self.in_data[-self.max_points:]
            if len(self.out_data) > self.max_points:
                self.out_data = self.out_data[-self.max_points:]
            
            # Update maximum speed for percentage calculation
            current_max = max(max(self.in_data) if self.in_data else 0, 
                            max(self.out_data) if self.out_data else 0)
            if current_max > self.max_speed:
                self.max_speed = current_max
            
            # Queue redraw
            self.queue_draw()
            
        except Exception as e:
            self.logger.error(f"Error adding data for {self.interface_name}: {e}")
    
    def _draw_chart(self, drawing_area: Gtk.DrawingArea, cr: cairo.Context, 
                   width: int, height: int, user_data) -> None:
        """Draw the network interface chart."""
        try:
            # Clear background
            cr.set_source_rgb(0.1, 0.1, 0.1)
            cr.paint()
            
            if not self.in_data and not self.out_data:
                self._draw_empty_chart(cr, width, height)
                return
            
            # Calculate chart area
            margin = 60
            chart_width = width - 2 * margin
            chart_height = height - 2 * margin
            
            if chart_width <= 0 or chart_height <= 0:
                return
            
            # Calculate data range
            all_data = self.in_data + self.out_data
            if not all_data:
                return
            
            min_val = 0.0
            max_val = max(all_data) if all_data else 1.0
            
            # Ensure we have a reasonable range
            if max_val == min_val:
                max_val = min_val + 0.1
            
            # Add some padding for better visualization
            max_val = max_val * 1.2
            
            # Draw grid
            self._draw_grid(cr, margin, chart_width, chart_height)
            
            # Draw axis labels
            self._draw_axis_labels(cr, margin, chart_width, chart_height, min_val, max_val)
            
            # Draw data lines
            self._draw_data_lines(cr, margin, chart_width, chart_height, min_val, max_val)
            
            # Draw legend
            self._draw_legend(cr, margin, chart_width, chart_height)
            
            # Draw current values
            self._draw_current_values(cr, margin, chart_width, chart_height, min_val, max_val)
            
        except Exception as e:
            self.logger.error(f"Error drawing chart for {self.interface_name}: {e}")
    
    def _draw_empty_chart(self, cr: cairo.Context, width: int, height: int) -> None:
        """Draw empty chart state."""
        cr.set_source_rgb(*self.text_color)
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(16)
        
        text = f"No data for {self.interface_name}"
        extents = cr.text_extents(text)
        x = (width - extents.width) / 2
        y = height / 2
        cr.move_to(x, y)
        cr.show_text(text)
    
    def _draw_grid(self, cr: cairo.Context, margin: int, chart_width: int, chart_height: int) -> None:
        """Draw grid lines."""
        cr.set_source_rgb(*self.grid_color)
        cr.set_line_width(0.5)
        
        # Vertical grid lines
        for i in range(6):
            x = margin + (i * chart_width / 5)
            cr.move_to(x, margin)
            cr.line_to(x, margin + chart_height)
            cr.stroke()
        
        # Horizontal grid lines
        for i in range(6):
            y = margin + (i * chart_height / 5)
            cr.move_to(margin, y)
            cr.line_to(margin + chart_width, y)
            cr.stroke()
    
    def _draw_axis_labels(self, cr: cairo.Context, margin: int, chart_width: int,
                         chart_height: int, min_val: float, max_val: float) -> None:
        """Draw axis labels and values."""
        cr.set_source_rgb(*self.text_color)
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(10)
        
        # Y-axis labels (left side)
        for i in range(6):
            y_percent = i / 5.0
            y = margin + chart_height - (y_percent * chart_height)
            value = min_val + (y_percent * (max_val - min_val))
            
            # Draw horizontal line
            cr.set_source_rgb(*self.grid_color)
            cr.set_line_width(0.5)
            cr.move_to(margin - 5, y)
            cr.line_to(margin, y)
            cr.stroke()
            
            # Draw value label
            cr.set_source_rgb(*self.text_color)
            text = f"{value:.2f}"
            extents = cr.text_extents(text)
            cr.move_to(margin - 10 - extents.width, y + 3)
            cr.show_text(text)
        
        # X-axis label (bottom)
        cr.set_source_rgb(*self.text_color)
        cr.set_font_size(12)
        text = "Time"
        extents = cr.text_extents(text)
        x = margin + (chart_width - extents.width) / 2
        y = margin + chart_height + 20
        cr.move_to(x, y)
        cr.show_text(text)
        
        # Y-axis label (left side, rotated)
        cr.set_source_rgb(*self.text_color)
        cr.set_font_size(12)
        text = "Mbps"
        extents = cr.text_extents(text)
        x = 8
        y = margin + chart_height / 2 + extents.width / 2
        cr.save()
        cr.translate(x, y)
        cr.rotate(-math.pi / 2)  # Rotate 90 degrees
        cr.move_to(0, 0)
        cr.show_text(text)
        cr.restore()
    
    def _draw_data_lines(self, cr: cairo.Context, margin: int, chart_width: int,
                        chart_height: int, min_val: float, max_val: float) -> None:
        """Draw incoming and outgoing data as filled areas."""
        try:
            # Draw incoming data (filled area)
            if len(self.in_data) > 1:
                self._draw_filled_area(cr, margin, chart_width, chart_height, 
                                     min_val, max_val, self.in_data, is_incoming=True)
            
            # Draw outgoing data (filled area)
            if len(self.out_data) > 1:
                self._draw_filled_area(cr, margin, chart_width, chart_height, 
                                     min_val, max_val, self.out_data, is_incoming=False)
                
        except Exception as e:
            self.logger.error(f"Error drawing data areas for {self.interface_name}: {e}")
    
    def _draw_filled_area(self, cr: cairo.Context, margin: int, chart_width: int,
                         chart_height: int, min_val: float, max_val: float,
                         data_points: List[float], is_incoming: bool) -> None:
        """Draw a filled area chart from bottom up."""
        try:
            # Calculate x step
            x_step = chart_width / (len(data_points) - 1) if len(data_points) > 1 else chart_width
            
            # Create gradient for filled area
            if is_incoming:
                # Green gradient for incoming data
                gradient = cairo.LinearGradient(margin, margin + chart_height, 
                                              margin, margin)
                gradient.add_color_stop_rgba(0.0, 0.2, 0.8, 0.2, 0.3)  # Transparent at bottom
                gradient.add_color_stop_rgba(1.0, 0.2, 0.8, 0.2, 0.8)  # More opaque at top
            else:
                # Blue gradient for outgoing data
                gradient = cairo.LinearGradient(margin, margin + chart_height, 
                                              margin, margin)
                gradient.add_color_stop_rgba(0.0, 0.2, 0.6, 0.9, 0.3)  # Transparent at bottom
                gradient.add_color_stop_rgba(1.0, 0.2, 0.6, 0.9, 0.8)  # More opaque at top
            
            cr.set_source(gradient)
            
            # Draw filled area from bottom up
            cr.move_to(margin, margin + chart_height)  # Start at bottom-left
            
            # Draw line through data points
            for i, value in enumerate(data_points):
                x = margin + (i * x_step)
                # Normalize value to chart height
                if max_val > min_val:
                    normalized_value = (value - min_val) / (max_val - min_val)
                else:
                    normalized_value = 0.0
                y = margin + chart_height - (normalized_value * chart_height)
                cr.line_to(x, y)
            
            # Close the path back to bottom
            cr.line_to(margin + chart_width, margin + chart_height)
            cr.close_path()
            
            # Fill the area
            cr.fill()
            
            # Draw the top line with appropriate color
            if is_incoming:
                cr.set_source_rgb(*self.in_color)
            else:
                cr.set_source_rgb(*self.out_color)
            cr.set_line_width(2.0)
            
            if not is_incoming:
                cr.set_dash([5, 3])  # Dashed line for outgoing
            
            # Draw just the top line
            for i, value in enumerate(data_points):
                x = margin + (i * x_step)
                # Normalize value to chart height
                if max_val > min_val:
                    normalized_value = (value - min_val) / (max_val - min_val)
                else:
                    normalized_value = 0.0
                y = margin + chart_height - (normalized_value * chart_height)
                
                if i == 0:
                    cr.move_to(x, y)
                else:
                    cr.line_to(x, y)
            
            cr.stroke()
            
        except Exception as e:
            self.logger.error(f"Error drawing filled area for {self.interface_name}: {e}")
    
    def _draw_legend(self, cr: cairo.Context, margin: int, chart_width: int, chart_height: int) -> None:
        """Draw legend for incoming and outgoing data."""
        cr.set_source_rgb(*self.text_color)
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(10)
        
        # Legend background
        cr.set_source_rgba(0.1, 0.1, 0.1, 0.8)
        legend_width = 120
        legend_height = 50
        legend_x = margin + 10
        legend_y = margin + 10
        cr.rectangle(legend_x, legend_y, legend_width, legend_height)
        cr.fill()
        
        # Legend border
        cr.set_source_rgb(0.5, 0.5, 0.5)  # Neutral gray border
        cr.set_line_width(1.0)
        cr.rectangle(legend_x, legend_y, legend_width, legend_height)
        cr.stroke()
        
        # Legend text
        cr.set_source_rgb(*self.text_color)
        
        # Interface name
        cr.set_font_size(12)
        # Note: cairo doesn't have set_font_weight, using size for emphasis
        text = self.interface_name
        cr.move_to(legend_x + 5, legend_y + 15)
        cr.show_text(text)
        
        # Incoming area
        cr.set_font_size(10)
        # Draw filled rectangle for incoming (green)
        cr.set_source_rgba(0.2, 0.8, 0.2, 0.6)
        cr.rectangle(legend_x + 5, legend_y + 28, 15, 4)
        cr.fill()
        
        # Draw solid line on top
        cr.set_source_rgb(*self.in_color)
        cr.set_line_width(2.0)
        cr.move_to(legend_x + 5, legend_y + 30)
        cr.line_to(legend_x + 20, legend_y + 30)
        cr.stroke()
        
        cr.set_source_rgb(*self.text_color)
        cr.move_to(legend_x + 25, legend_y + 33)
        cr.show_text("In")
        
        # Outgoing area
        # Draw filled rectangle for outgoing (blue)
        cr.set_source_rgba(0.2, 0.6, 0.9, 0.4)
        cr.rectangle(legend_x + 5, legend_y + 43, 15, 4)
        cr.fill()
        
        # Draw dashed line on top
        cr.set_source_rgb(*self.out_color)
        cr.set_line_width(2.0)
        cr.set_dash([3, 2])
        cr.move_to(legend_x + 5, legend_y + 45)
        cr.line_to(legend_x + 20, legend_y + 45)
        cr.stroke()
        
        cr.set_source_rgb(*self.text_color)
        cr.move_to(legend_x + 25, legend_y + 48)
        cr.show_text("Out")
    
    def _draw_current_values(self, cr: cairo.Context, margin: int, chart_width: int,
                           chart_height: int, min_val: float, max_val: float) -> None:
        """Draw current values and percentages."""
        if not self.in_data and not self.out_data:
            return
        
        cr.set_source_rgb(*self.text_color)
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(10)
        
        # Get current values
        current_in = self.in_data[-1] if self.in_data else 0.0
        current_out = self.out_data[-1] if self.out_data else 0.0
        
        # Calculate percentages
        in_percent = (current_in / self.max_speed * 100) if self.max_speed > 0 else 0.0
        out_percent = (current_out / self.max_speed * 100) if self.max_speed > 0 else 0.0
        
        # Draw current values box
        box_x = margin + chart_width - 150
        box_y = margin + 10
        box_width = 140
        box_height = 60
        
        # Box background
        cr.set_source_rgba(0.1, 0.1, 0.1, 0.8)
        cr.rectangle(box_x, box_y, box_width, box_height)
        cr.fill()
        
        # Box border
        cr.set_source_rgb(0.5, 0.5, 0.5)  # Neutral gray border
        cr.set_line_width(1.0)
        cr.rectangle(box_x, box_y, box_width, box_height)
        cr.stroke()
        
        # Current values text
        cr.set_source_rgb(*self.text_color)
        cr.set_font_size(10)
        
        # Incoming
        cr.move_to(box_x + 5, box_y + 15)
        cr.show_text(f"In: {current_in:.3f} Mbps ({in_percent:.1f}%)")
        
        # Outgoing
        cr.move_to(box_x + 5, box_y + 30)
        cr.show_text(f"Out: {current_out:.3f} Mbps ({out_percent:.1f}%)")
        
        # Total
        total = current_in + current_out
        total_percent = (total / self.max_speed * 100) if self.max_speed > 0 else 0.0
        cr.move_to(box_x + 5, box_y + 45)
        cr.show_text(f"Total: {total:.3f} Mbps ({total_percent:.1f}%)")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.in_data.clear()
            self.out_data.clear()
            self.max_speed = 0.0
            self.logger.debug(f"Cleaned up network interface chart for {self.interface_name}")
        except Exception as e:
            self.logger.error(f"Error cleaning up chart for {self.interface_name}: {e}") 