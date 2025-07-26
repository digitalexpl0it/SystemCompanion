# Disk IOPS Chart Improvements

## Overview

The disk monitoring system has been enhanced to display separate read and write IOPS (Input/Output Operations Per Second) as distinct lines on the chart, providing much more detailed and useful disk performance information.

## Key Improvements

### 1. **Multi-Series Chart Support**
- **Before**: Single line showing total IOPS (read + write combined)
- **After**: Two separate lines showing read and write IOPS independently
- Blue line for read operations
- Orange line for write operations
- Clear visual distinction between read and write activity

### 2. **Enhanced ChartWidget**
- **Multi-Series Support**: ChartWidget now supports multiple data series with different colors
- **Legend Display**: Automatic legend showing series names and colors
- **Color Scheme**: 
  - Read operations: Blue (0.2, 0.6, 1.0)
  - Write operations: Orange (1.0, 0.4, 0.2)
  - Default: Green (0.2, 0.8, 0.4)
- **Current Value Indicators**: Separate value displays for each series

### 3. **Real-Time IOPS Monitoring**
- **Read IOPS**: Number of read operations per second
- **Write IOPS**: Number of write operations per second
- **Accurate Calculation**: Uses psutil disk I/O counters with proper time-based rate calculation
- **Multiple Disks**: Supports monitoring multiple disk partitions

### 4. **Visual Enhancements**
- **Grid Lines**: Subtle grid for easier reading
- **Axis Labels**: Clear Y-axis showing "IOPS" and X-axis showing "Time"
- **Responsive Updates**: Smooth real-time updates without UI blocking
- **Proper Scaling**: Automatic scaling based on actual data range

## Technical Implementation

### ChartWidget Changes

#### Constructor
```python
def __init__(self, title: str = "", max_points: int = 50, series_names: Optional[List[str]] = None):
    # Support multiple data series
    self.data_series: Dict[str, List[float]] = {}
    for name in self.series_names:
        self.data_series[name] = []
```

#### Data Point Addition
```python
def add_data_point(self, value: float, series_name: str = "Data") -> None:
    # Add data to specific series
    self.data_series[series_name].append(value)
```

#### Multi-Series Drawing
```python
def _draw_data_lines(self, cr: cairo.Context, margin: int, chart_width: int,
                    chart_height: int, min_val: float, max_val: float) -> None:
    # Draw each series with different colors
    for series_name, data_points in self.data_series.items():
        if len(data_points) > 1:
            self._draw_single_series(cr, margin, chart_width, chart_height, 
                                   min_val, max_val, data_points, series_name)
```

### Dashboard Integration

#### Disk Chart Creation
```python
# Full-size disk chart with read/write series
self.disk_chart = ChartWidget(title="Disk IOPS", max_points=60, series_names=["Read", "Write"])

# Mini disk chart in metrics grid
chart = ChartWidget(title=title, max_points=3, series_names=["Read", "Write"])
```

#### Data Updates
```python
def _update_disk_metrics(self) -> None:
    # Add separate data points for read and write IOPS
    self.disk_chart.add_data_point(disk_info.read_iops, "Read")
    self.disk_chart.add_data_point(disk_info.write_iops, "Write")
```

### System Monitor Integration

#### IOPS Calculation
```python
def _calculate_disk_io_rates(self, device: str) -> Tuple[float, float, float, float]:
    # Calculate read and write IOPS separately
    read_iops = (current_stats.read_count - last_stats['read_count']) / time_diff
    write_iops = (current_stats.write_count - last_stats['write_count']) / time_diff
    return read_rate, write_rate, read_iops, write_iops
```

## Usage Examples

### Dashboard Metric Cards
The mini disk chart in the metrics grid shows:
- Blue line: Read IOPS
- Orange line: Write IOPS
- 3 data points for quick overview
- Real-time updates every 3 seconds

### Full Disk Tab
The full disk monitoring tab shows:
- Blue line: Read IOPS
- Orange line: Write IOPS
- 60 data points for detailed view
- Legend showing series names
- Current value indicators for both series

### Test Application
A test application (`test_disk_iops.py`) demonstrates:
- Real-time disk IOPS monitoring
- Separate read/write visualization
- Console output showing current values

## Performance Considerations

- **Efficient Updates**: Throttled redraws prevent UI blocking
- **Memory Management**: Limited data points prevent memory growth
- **Background Processing**: Data collection doesn't block UI
- **Smooth Animations**: 1-second update intervals for fluent display

## Future Enhancements

- **Disk Selection**: Allow users to select specific disks to monitor
- **Historical Data**: Store and display longer-term IOPS trends
- **Performance Alerts**: Alert when IOPS exceed thresholds
- **Export Functionality**: Export IOPS data for analysis
- **Custom Colors**: Allow users to customize chart colors

## Testing

The implementation includes:
- **Unit Tests**: ChartWidget functionality
- **Integration Tests**: Dashboard integration
- **Manual Testing**: Test application for visual verification
- **Performance Testing**: Memory and CPU usage monitoring

## Conclusion

The disk IOPS chart improvements provide much more detailed and useful information about disk performance, allowing users to distinguish between read and write activity patterns. This is essential for performance monitoring, troubleshooting, and capacity planning. 