"""
System monitoring functionality for System Companion.

This module provides real-time monitoring of system resources including
CPU, memory, disk, network, and process information.
"""

import time
import logging
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import psutil
import cpuinfo
import netifaces
from pathlib import Path

from ..utils.exceptions import MonitoringError


@dataclass
class CPUInfo:
    """CPU information and usage data."""
    usage_percent: float
    core_count: int
    logical_processor_count: int
    socket_count: int
    frequency_mhz: float
    base_frequency_mhz: float
    temperature_celsius: Optional[float]
    model_name: str
    architecture: str
    load_average: Tuple[float, float, float]
    core_usage: List[float]  # Usage percentage for each core
    process_count: int
    thread_count: int
    zombie_process_count: int
    uptime_seconds: float
    virtualization_enabled: bool


@dataclass
class MemoryInfo:
    """Memory usage information."""
    total_gb: float
    available_gb: float
    used_gb: float
    usage_percent: float
    swap_total_gb: float
    swap_used_gb: float
    swap_usage_percent: float


@dataclass
class DiskInfo:
    """Disk usage information."""
    device: str
    mountpoint: str
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    read_bytes_per_sec: float
    write_bytes_per_sec: float
    read_iops: float
    write_iops: float


@dataclass
class NetworkInfo:
    """Network interface information."""
    interface: str
    ip_address: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    speed_mbps: Optional[float]
    in_speed_mbps: float  # Incoming speed in Mbps
    out_speed_mbps: float  # Outgoing speed in Mbps
    utilization_percent: float  # Network utilization as percentage


@dataclass
class ProcessInfo:
    """Process information."""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    create_time: float
    username: str
    priority: int
    disk_read_total_mb: float
    disk_write_total_mb: float
    disk_read_rate_mb: float
    disk_write_rate_mb: float


class SystemMonitor:
    """Main system monitoring class."""
    
    def __init__(self) -> None:
        """Initialize the system monitor."""
        self.logger = logging.getLogger("system_companion.core.system_monitor")
        self._cpu_info_cache = None
        self._last_network_stats = {}
        self._last_disk_stats = {}
        
        # Initialize monitoring
        self._initialize_monitoring()
        
        self.logger.info("System monitor initialized")
    
    def _initialize_monitoring(self) -> None:
        """Initialize monitoring systems."""
        try:
            # Get initial CPU info
            self._cpu_info_cache = cpuinfo.get_cpu_info()
            
            # Initialize network stats
            for interface in netifaces.interfaces():
                try:
                    stats = psutil.net_io_counters(pernic=True).get(interface, None)
                    if stats:
                        self._last_network_stats[interface] = {
                            'bytes_sent': stats.bytes_sent,
                            'bytes_recv': stats.bytes_recv,
                            'packets_sent': stats.packets_sent,
                            'packets_recv': stats.packets_recv,
                            'timestamp': time.time()
                        }
                except Exception as e:
                    self.logger.warning(f"Could not initialize network stats for {interface}: {e}")
            
            # Initialize disk stats
            for partition in psutil.disk_partitions():
                try:
                    # Map partition device to disk I/O counter device name
                    io_device = partition.device.replace('/dev/', '')
                    stats = psutil.disk_io_counters(perdisk=True).get(io_device, None)
                    if stats:
                        self._last_disk_stats[io_device] = {
                            'read_bytes': stats.read_bytes,
                            'write_bytes': stats.write_bytes,
                            'read_count': stats.read_count,
                            'write_count': stats.write_count,
                            'timestamp': time.time()
                        }
                except Exception as e:
                    self.logger.warning(f"Could not initialize disk stats for {io_device}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring: {e}")
            raise MonitoringError(f"Failed to initialize monitoring: {e}")
    
    def get_cpu_info(self) -> CPUInfo:
        """Get current CPU information and usage."""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get per-core CPU usage - this is crucial for multi-core display
            core_usage = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # Get CPU frequency
            freq = psutil.cpu_freq()
            frequency_mhz = freq.current if freq else 0.0
            
            # Get base frequency from CPU info (more accurate than freq.min)
            if self._cpu_info_cache:
                # Try multiple sources for base frequency
                base_freq = None
                
                # Try hz_advertised_raw first
                if 'hz_advertised_raw' in self._cpu_info_cache:
                    base_freq = self._cpu_info_cache['hz_advertised_raw']
                # Try hz_advertised_friendly
                elif 'hz_advertised_friendly' in self._cpu_info_cache:
                    freq_str = self._cpu_info_cache['hz_advertised_friendly']
                    # Parse "2.6 GHz" format
                    if 'GHz' in freq_str:
                        try:
                            freq_val = float(freq_str.replace(' GHz', ''))
                            base_freq = freq_val * 1000000000  # Convert to Hz
                        except:
                            pass
                # Try brand_raw for frequency info
                elif 'brand_raw' in self._cpu_info_cache:
                    brand = self._cpu_info_cache['brand_raw']
                    if '@' in brand:
                        freq_part = brand.split('@')[-1].strip()
                        if 'GHz' in freq_part:
                            try:
                                freq_val = float(freq_part.replace(' GHz', ''))
                                base_freq = freq_val * 1000000000  # Convert to Hz
                            except:
                                pass
                
                if base_freq:
                    # Convert from Hz to MHz
                    base_frequency_mhz = base_freq / 1000000
                else:
                    # Fallback to freq.min if available
                    base_frequency_mhz = freq.min if freq else 0.0
            else:
                base_frequency_mhz = freq.min if freq else 0.0
            
            # Get load average
            load_avg = psutil.getloadavg()
            
            # Get CPU temperature (if available)
            temperature = self._get_cpu_temperature()
            
            # Get CPU info from cache
            if not self._cpu_info_cache:
                self._cpu_info_cache = cpuinfo.get_cpu_info()
            
            # Get additional system information
            process_count = len(psutil.pids())
            thread_count = psutil.cpu_count(logical=True)
            zombie_process_count = self._count_zombie_processes()
            
            # Get uptime
            uptime_seconds = time.time() - psutil.boot_time()
            
            # Check virtualization (simplified check)
            virtualization_enabled = self._check_virtualization()
            
            # Get socket count (simplified - usually 1 for most systems)
            socket_count = 1  # Could be enhanced with more detailed detection
            
            return CPUInfo(
                usage_percent=cpu_percent,
                core_count=psutil.cpu_count(logical=False),  # Physical cores
                logical_processor_count=psutil.cpu_count(logical=True),  # Logical cores
                socket_count=socket_count,
                frequency_mhz=frequency_mhz,
                base_frequency_mhz=base_frequency_mhz,
                temperature_celsius=temperature,
                model_name=self._cpu_info_cache.get('brand_raw', 'Unknown CPU'),
                architecture=self._cpu_info_cache.get('arch', 'Unknown'),
                load_average=load_avg,
                core_usage=core_usage,
                process_count=process_count,
                thread_count=thread_count,
                zombie_process_count=zombie_process_count,
                uptime_seconds=uptime_seconds,
                virtualization_enabled=virtualization_enabled
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get CPU info: {e}")
            raise MonitoringError(f"Failed to get CPU info: {e}")
    
    def get_memory_info(self) -> MemoryInfo:
        """Get current memory usage information."""
        try:
            # Get virtual memory info
            vm = psutil.virtual_memory()
            
            # Get swap memory info
            swap = psutil.swap_memory()
            
            return MemoryInfo(
                total_gb=vm.total / (1024**3),
                available_gb=vm.available / (1024**3),
                used_gb=vm.used / (1024**3),
                usage_percent=vm.percent,
                swap_total_gb=swap.total / (1024**3),
                swap_used_gb=swap.used / (1024**3),
                swap_usage_percent=swap.percent
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get memory info: {e}")
            raise MonitoringError(f"Failed to get memory info: {e}")
    
    def get_disk_info(self) -> List[DiskInfo]:
        """Get disk usage information for all mounted partitions (similar to df -h)."""
        try:
            disk_info_list = []
            
            for partition in psutil.disk_partitions():
                try:
                    # Skip certain filesystem types and loop devices
                    if (partition.fstype in ['tmpfs', 'devtmpfs', 'sysfs', 'proc', 'efivarfs'] or
                        partition.device.startswith('/dev/loop') or
                        partition.device.startswith('/dev/shm') or
                        partition.device.startswith('/run/')):
                        continue
                    
                    # Get disk usage
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Calculate I/O rates and IOPS
                    # Map partition device to disk I/O counter device name
                    io_device = partition.device.replace('/dev/', '')
                    read_rate, write_rate, read_iops, write_iops = self._calculate_disk_io_rates(io_device)
                    
                    disk_info = DiskInfo(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        total_gb=usage.total / (1024**3),
                        used_gb=usage.used / (1024**3),
                        free_gb=usage.free / (1024**3),
                        usage_percent=usage.percent,
                        read_bytes_per_sec=read_rate,
                        write_bytes_per_sec=write_rate,
                        read_iops=read_iops,
                        write_iops=write_iops
                    )
                    
                    disk_info_list.append(disk_info)
                    
                except Exception as e:
                    self.logger.warning(f"Could not get disk info for {partition.mountpoint}: {e}")
                    continue
            
            return disk_info_list
            
        except Exception as e:
            self.logger.error(f"Failed to get disk info: {e}")
            raise MonitoringError(f"Failed to get disk info: {e}")
    
    def get_network_info(self) -> List[NetworkInfo]:
        """Get network interface information."""
        try:
            network_info_list = []
            
            for interface in netifaces.interfaces():
                try:
                    # Get interface addresses
                    addrs = netifaces.ifaddresses(interface)
                    
                    # Get IP address
                    ip_address = "N/A"
                    if netifaces.AF_INET in addrs:
                        ip_address = addrs[netifaces.AF_INET][0]['addr']
                    
                    # Get network stats
                    stats = psutil.net_io_counters(pernic=True).get(interface, None)
                    if not stats:
                        continue
                    
                    # Calculate network speeds
                    speed = self._calculate_network_speed(interface, stats)
                    in_speed, out_speed = self._calculate_network_in_out_speeds(interface, stats)
                    
                    # Calculate network utilization percentage
                    utilization = self._calculate_network_utilization(interface, stats)
                    
                    network_info = NetworkInfo(
                        interface=interface,
                        ip_address=ip_address,
                        bytes_sent=stats.bytes_sent,
                        bytes_recv=stats.bytes_recv,
                        packets_sent=stats.packets_sent,
                        packets_recv=stats.packets_recv,
                        speed_mbps=speed,
                        in_speed_mbps=in_speed,
                        out_speed_mbps=out_speed,
                        utilization_percent=utilization
                    )
                    
                    network_info_list.append(network_info)
                    
                except Exception as e:
                    self.logger.warning(f"Could not get network info for {interface}: {e}")
                    continue
            
            return network_info_list
            
        except Exception as e:
            self.logger.error(f"Failed to get network info: {e}")
            raise MonitoringError(f"Failed to get network info: {e}")
    
    def get_top_processes(self, limit: int = 10) -> List[ProcessInfo]:
        """Get top processes by CPU and memory usage."""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time', 'username', 'nice']):
                try:
                    info = proc.info
                    
                    # Get disk I/O information
                    try:
                        io_counters = proc.io_counters()
                        disk_read_total_mb = io_counters.read_bytes / (1024**2) if io_counters else 0.0
                        disk_write_total_mb = io_counters.write_bytes / (1024**2) if io_counters else 0.0
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        disk_read_total_mb = 0.0
                        disk_write_total_mb = 0.0
                    
                    # Calculate disk I/O rates (we'll need to track this over time)
                    disk_read_rate_mb = 0.0  # TODO: Implement rate calculation
                    disk_write_rate_mb = 0.0  # TODO: Implement rate calculation
                    
                    process_info = ProcessInfo(
                        pid=info['pid'],
                        name=info['name'],
                        cpu_percent=info['cpu_percent'],
                        memory_percent=info['memory_percent'],
                        memory_mb=info['memory_info'].rss / (1024**2) if info['memory_info'] else 0.0,
                        status=info['status'],
                        create_time=info['create_time'],
                        username=info.get('username', 'N/A'),
                        priority=info.get('nice', 0),
                        disk_read_total_mb=disk_read_total_mb,
                        disk_write_total_mb=disk_write_total_mb,
                        disk_read_rate_mb=disk_read_rate_mb,
                        disk_write_rate_mb=disk_write_rate_mb
                    )
                    
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage and return top processes
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            return processes[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get top processes: {e}")
            raise MonitoringError(f"Failed to get top processes: {e}")
    
    def get_user_processes(self, limit: int = 50) -> List[ProcessInfo]:
        """Get all processes for the current user."""
        try:
            processes = []
            current_user = os.getenv('USER', 'unknown')
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time', 'username', 'nice']):
                try:
                    info = proc.info
                    
                    # Only include processes for current user
                    if info.get('username') != current_user:
                        continue
                    
                    # Get disk I/O information
                    try:
                        io_counters = proc.io_counters()
                        disk_read_total_mb = io_counters.read_bytes / (1024**2) if io_counters else 0.0
                        disk_write_total_mb = io_counters.write_bytes / (1024**2) if io_counters else 0.0
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        disk_read_total_mb = 0.0
                        disk_write_total_mb = 0.0
                    
                    # Calculate disk I/O rates (we'll need to track this over time)
                    disk_read_rate_mb = 0.0  # TODO: Implement rate calculation
                    disk_write_rate_mb = 0.0  # TODO: Implement rate calculation
                    
                    process_info = ProcessInfo(
                        pid=info['pid'],
                        name=info['name'],
                        cpu_percent=info['cpu_percent'],
                        memory_percent=info['memory_percent'],
                        memory_mb=info['memory_info'].rss / (1024**2) if info['memory_info'] else 0.0,
                        status=info['status'],
                        create_time=info['create_time'],
                        username=info.get('username', 'N/A'),
                        priority=info.get('nice', 0),
                        disk_read_total_mb=disk_read_total_mb,
                        disk_write_total_mb=disk_write_total_mb,
                        disk_read_rate_mb=disk_read_rate_mb,
                        disk_write_rate_mb=disk_write_rate_mb
                    )
                    
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by memory usage and return processes
            processes.sort(key=lambda x: x.memory_mb, reverse=True)
            return processes[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get user processes: {e}")
            raise MonitoringError(f"Failed to get user processes: {e}")
    
    def get_system_health_score(self) -> float:
        """Calculate overall system health score (0-100)."""
        try:
            score = 100.0
            
            # CPU health (30% weight)
            cpu_info = self.get_cpu_info()
            if cpu_info.usage_percent > 90:
                score -= 30
            elif cpu_info.usage_percent > 80:
                score -= 20
            elif cpu_info.usage_percent > 70:
                score -= 10
            
            # Memory health (30% weight)
            memory_info = self.get_memory_info()
            if memory_info.usage_percent > 90:
                score -= 30
            elif memory_info.usage_percent > 80:
                score -= 20
            elif memory_info.usage_percent > 70:
                score -= 10
            
            # Disk health (20% weight)
            disk_info_list = self.get_disk_info()
            for disk in disk_info_list:
                if disk.usage_percent > 95:
                    score -= 20
                elif disk.usage_percent > 90:
                    score -= 15
                elif disk.usage_percent > 80:
                    score -= 10
            
            # Network health (20% weight)
            # This is more complex and would need baseline data
            # For now, we'll just check if interfaces are up
            
            return max(0.0, score)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate system health score: {e}")
            return 50.0  # Return neutral score on error
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature if available."""
        try:
            # Try to read from common temperature files
            temp_files = [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/hwmon/hwmon0/temp1_input",
                "/proc/acpi/thermal_zone/THM0/temperature"
            ]
            
            for temp_file in temp_files:
                if Path(temp_file).exists():
                    with open(temp_file, 'r') as f:
                        temp_raw = f.read().strip()
                        if temp_raw.isdigit():
                            # Convert from millidegrees to degrees Celsius
                            return float(temp_raw) / 1000.0
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Could not read CPU temperature: {e}")
            return None
    
    def _check_virtualization(self) -> bool:
        """Check if virtualization is enabled."""
        try:
            # Check for common virtualization indicators
            if Path("/proc/cpuinfo").exists():
                with open("/proc/cpuinfo", 'r') as f:
                    cpu_info = f.read()
                    # Check for common virtualization indicators
                    if any(indicator in cpu_info.lower() for indicator in ['vmx', 'svm', 'hypervisor']):
                        return True
            
            # Check product name for virtualization indicators
            if Path("/sys/devices/virtual/dmi/id/product_name").exists():
                with open("/sys/devices/virtual/dmi/id/product_name", 'r') as f:
                    product_name = f.read().strip().lower()
                    if any(indicator in product_name for indicator in ['vmware', 'virtualbox', 'kvm', 'xen']):
                        return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Could not check virtualization: {e}")
            return False
    
    def _count_zombie_processes(self) -> int:
        """Count the number of zombie processes in the system."""
        try:
            zombie_count = 0
            for proc in psutil.process_iter(['pid', 'status']):
                try:
                    info = proc.info
                    if info['status'] == psutil.STATUS_ZOMBIE:
                        zombie_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return zombie_count
            
        except Exception as e:
            self.logger.debug(f"Could not count zombie processes: {e}")
            return 0
    
    def _calculate_disk_io_rates(self, device: str) -> Tuple[float, float, float, float]:
        """Calculate disk I/O rates in bytes per second and IOPS."""
        try:
            current_stats = psutil.disk_io_counters(perdisk=True).get(device, None)
            if not current_stats:
                return 0.0, 0.0, 0.0, 0.0
            
            current_time = time.time()
            
            if device in self._last_disk_stats:
                last_stats = self._last_disk_stats[device]
                time_diff = current_time - last_stats['timestamp']
                
                if time_diff > 0:
                    read_rate = (current_stats.read_bytes - last_stats['read_bytes']) / time_diff
                    write_rate = (current_stats.write_bytes - last_stats['write_bytes']) / time_diff
                    read_iops = (current_stats.read_count - last_stats['read_count']) / time_diff
                    write_iops = (current_stats.write_count - last_stats['write_count']) / time_diff
                else:
                    read_rate = write_rate = read_iops = write_iops = 0.0
            else:
                read_rate = write_rate = read_iops = write_iops = 0.0
            
            # Update last stats
            self._last_disk_stats[device] = {
                'read_bytes': current_stats.read_bytes,
                'write_bytes': current_stats.write_bytes,
                'read_count': current_stats.read_count,
                'write_count': current_stats.write_count,
                'timestamp': current_time
            }
            
            return read_rate, write_rate, read_iops, write_iops
            
        except Exception as e:
            self.logger.debug(f"Could not calculate disk I/O rates for {device}: {e}")
            return 0.0, 0.0
    
    def _calculate_network_speed(self, interface: str, current_stats) -> Optional[float]:
        """Calculate network speed in Mbps."""
        try:
            current_time = time.time()
            
            if interface in self._last_network_stats:
                last_stats = self._last_network_stats[interface]
                time_diff = current_time - last_stats['timestamp']
                
                if time_diff > 0:
                    # Calculate total bytes transferred
                    bytes_diff = (current_stats.bytes_sent + current_stats.bytes_recv) - \
                               (last_stats['bytes_sent'] + last_stats['bytes_recv'])
                    
                    # Convert to Mbps
                    speed_mbps = (bytes_diff * 8) / (time_diff * 1000000)
                else:
                    speed_mbps = 0.0
            else:
                speed_mbps = 0.0
            
            # Note: Stats are updated in _calculate_network_in_out_speeds() to avoid conflicts
            return speed_mbps
            
        except Exception as e:
            self.logger.debug(f"Could not calculate network speed for {interface}: {e}")
            return None
    
    def _calculate_network_in_out_speeds(self, interface: str, current_stats) -> Tuple[float, float]:
        """Calculate network incoming and outgoing speeds in Mbps."""
        try:
            current_time = time.time()
            
            if interface in self._last_network_stats:
                last_stats = self._last_network_stats[interface]
                time_diff = current_time - last_stats['timestamp']
                
                if time_diff > 0.1:  # Require at least 0.1 seconds for meaningful calculation
                    # Calculate incoming and outgoing bytes separately
                    in_bytes_diff = current_stats.bytes_recv - last_stats['bytes_recv']
                    out_bytes_diff = current_stats.bytes_sent - last_stats['bytes_sent']
                    
                    # Convert to Mbps
                    in_speed_mbps = (in_bytes_diff * 8) / (time_diff * 1000000)
                    out_speed_mbps = (out_bytes_diff * 8) / (time_diff * 1000000)
                    

                else:
                    in_speed_mbps = out_speed_mbps = 0.0
            else:
                # First time seeing this interface, initialize stats but return 0
                in_speed_mbps = out_speed_mbps = 0.0
            
            # Update last stats
            self._last_network_stats[interface] = {
                'bytes_sent': current_stats.bytes_sent,
                'bytes_recv': current_stats.bytes_recv,
                'packets_sent': current_stats.packets_sent,
                'packets_recv': current_stats.packets_recv,
                'timestamp': current_time
            }
            
            return in_speed_mbps, out_speed_mbps
            
        except Exception as e:
            self.logger.debug(f"Could not calculate network in/out speeds for {interface}: {e}")
            return 0.0, 0.0
    
    def _calculate_network_utilization(self, interface: str, current_stats) -> float:
        """Calculate network utilization as a percentage based on activity."""
        try:
            current_time = time.time()
            
            if interface in self._last_network_stats:
                last_stats = self._last_network_stats[interface]
                time_diff = current_time - last_stats['timestamp']
                
                if time_diff > 0:
                    # Calculate total bytes transferred
                    bytes_diff = (current_stats.bytes_sent + current_stats.bytes_recv) - \
                               (last_stats['bytes_sent'] + last_stats['bytes_recv'])
                    
                    # Calculate current speed in Mbps
                    current_speed_mbps = (bytes_diff * 8) / (time_diff * 1000000)
                    
                    # Use a more reasonable baseline for percentage calculation
                    # For typical home/office networks, use 100 Mbps as baseline
                    # This will give more meaningful percentages
                    baseline_mbps = 100.0  # 100 Mbps baseline
                    utilization = min(100.0, (current_speed_mbps / baseline_mbps) * 100)
                    
                    return utilization
                else:
                    return 0.0
            else:
                return 0.0
            
        except Exception as e:
            self.logger.debug(f"Could not calculate network utilization for {interface}: {e}")
            return 0.0 