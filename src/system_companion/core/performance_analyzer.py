"""
Performance analysis functionality for System Companion.

This module provides detailed performance analysis, recommendations,
and optimization suggestions based on system monitoring data.
"""

import logging
import time
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import psutil
import subprocess
import json
from pathlib import Path

from .system_monitor import SystemMonitor, CPUInfo, MemoryInfo, DiskInfo, NetworkInfo
from ..utils.exceptions import PerformanceAnalysisError


class Severity(Enum):
    """Severity levels for performance issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(Enum):
    """Types of performance issues."""
    CPU_HIGH_USAGE = "cpu_high_usage"
    MEMORY_HIGH_USAGE = "memory_high_usage"
    DISK_HIGH_USAGE = "disk_high_usage"
    DISK_SLOW_IO = "disk_slow_io"
    NETWORK_SLOW = "network_slow"
    PROCESS_HOG = "process_hog"
    TEMPERATURE_HIGH = "temperature_high"
    SWAP_HIGH_USAGE = "swap_high_usage"
    BOOT_TIME_SLOW = "boot_time_slow"
    SYSTEM_LOAD_HIGH = "system_load_high"


@dataclass
class PerformanceIssue:
    """Represents a performance issue."""
    issue_type: IssueType
    severity: Severity
    title: str
    description: str
    recommendation: str
    current_value: str
    threshold_value: str
    timestamp: datetime
    affected_component: str


@dataclass
class PerformanceRecommendation:
    """Represents a performance recommendation."""
    title: str
    description: str
    impact: str
    difficulty: str
    estimated_time: str
    commands: List[str]
    category: str


@dataclass
class SystemBenchmark:
    """System benchmark results."""
    cpu_score: float
    memory_score: float
    disk_score: float
    network_score: float
    overall_score: float
    timestamp: datetime
    details: Dict[str, any]


class PerformanceAnalyzer:
    """Main performance analysis class."""
    
    def __init__(self, system_monitor: SystemMonitor) -> None:
        """Initialize the performance analyzer."""
        self.logger = logging.getLogger("system_companion.core.performance_analyzer")
        self.system_monitor = system_monitor
        
        # Performance thresholds
        self.thresholds = {
            'cpu_usage': 90.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'swap_usage': 50.0,
            'temperature': 80.0,
            'system_load': 2.0,
            'disk_io_wait': 10.0,
            'network_latency': 100.0
        }
        
        # Historical data for trend analysis
        self.historical_data = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'network': []
        }
        
        # Benchmark results cache
        self.benchmark_cache = None
        self.last_benchmark = None
        
        self.logger.info("Performance analyzer initialized")
    
    def analyze_system_performance(self) -> List[PerformanceIssue]:
        """Analyze current system performance and identify issues."""
        try:
            issues = []
            
            # Analyze CPU performance
            cpu_issues = self._analyze_cpu_performance()
            issues.extend(cpu_issues)
            
            # Analyze memory performance
            memory_issues = self._analyze_memory_performance()
            issues.extend(memory_issues)
            
            # Analyze disk performance
            disk_issues = self._analyze_disk_performance()
            issues.extend(disk_issues)
            
            # Analyze network performance
            network_issues = self._analyze_network_performance()
            issues.extend(network_issues)
            
            # Analyze process performance
            process_issues = self._analyze_process_performance()
            issues.extend(process_issues)
            
            # Analyze system load
            load_issues = self._analyze_system_load()
            issues.extend(load_issues)
            
            # Store historical data
            self._store_historical_data()
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Failed to analyze system performance: {e}")
            raise PerformanceAnalysisError(f"Failed to analyze system performance: {e}")
    
    def _analyze_cpu_performance(self) -> List[PerformanceIssue]:
        """Analyze CPU performance and identify issues."""
        issues = []
        
        try:
            cpu_info = self.system_monitor.get_cpu_info()
            
            # Check CPU usage
            if cpu_info.usage_percent > self.thresholds['cpu_usage']:
                severity = self._determine_severity(cpu_info.usage_percent, self.thresholds['cpu_usage'])
                
                issue = PerformanceIssue(
                    issue_type=IssueType.CPU_HIGH_USAGE,
                    severity=severity,
                    title="High CPU Usage",
                    description=f"CPU usage is at {cpu_info.usage_percent:.1f}%, which may impact system performance.",
                    recommendation="Consider closing unnecessary applications or checking for resource-intensive processes.",
                    current_value=f"{cpu_info.usage_percent:.1f}%",
                    threshold_value=f"{self.thresholds['cpu_usage']}%",
                    timestamp=datetime.now(),
                    affected_component="CPU"
                )
                issues.append(issue)
            
            # Check CPU temperature
            if cpu_info.temperature_celsius and cpu_info.temperature_celsius > self.thresholds['temperature']:
                severity = self._determine_severity(cpu_info.temperature_celsius, self.thresholds['temperature'])
                
                issue = PerformanceIssue(
                    issue_type=IssueType.TEMPERATURE_HIGH,
                    severity=severity,
                    title="High CPU Temperature",
                    description=f"CPU temperature is {cpu_info.temperature_celsius:.1f}°C, which may cause thermal throttling.",
                    recommendation="Check cooling system, clean dust, and ensure proper ventilation.",
                    current_value=f"{cpu_info.temperature_celsius:.1f}°C",
                    threshold_value=f"{self.thresholds['temperature']}°C",
                    timestamp=datetime.now(),
                    affected_component="CPU"
                )
                issues.append(issue)
            
            # Check system load
            load_avg_1min = cpu_info.load_average[0]
            cpu_cores = cpu_info.core_count
            
            if load_avg_1min > (cpu_cores * self.thresholds['system_load']):
                severity = self._determine_severity(load_avg_1min, cpu_cores * self.thresholds['system_load'])
                
                issue = PerformanceIssue(
                    issue_type=IssueType.SYSTEM_LOAD_HIGH,
                    severity=severity,
                    title="High System Load",
                    description=f"System load average is {load_avg_1min:.2f}, indicating high system demand.",
                    recommendation="Check for runaway processes or consider system restart if persistent.",
                    current_value=f"{load_avg_1min:.2f}",
                    threshold_value=f"{cpu_cores * self.thresholds['system_load']:.2f}",
                    timestamp=datetime.now(),
                    affected_component="System"
                )
                issues.append(issue)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze CPU performance: {e}")
        
        return issues
    
    def _analyze_memory_performance(self) -> List[PerformanceIssue]:
        """Analyze memory performance and identify issues."""
        issues = []
        
        try:
            memory_info = self.system_monitor.get_memory_info()
            
            # Check memory usage
            if memory_info.usage_percent > self.thresholds['memory_usage']:
                severity = self._determine_severity(memory_info.usage_percent, self.thresholds['memory_usage'])
                
                issue = PerformanceIssue(
                    issue_type=IssueType.MEMORY_HIGH_USAGE,
                    severity=severity,
                    title="High Memory Usage",
                    description=f"Memory usage is at {memory_info.usage_percent:.1f}%, which may cause swapping.",
                    recommendation="Close unnecessary applications or consider adding more RAM.",
                    current_value=f"{memory_info.usage_percent:.1f}%",
                    threshold_value=f"{self.thresholds['memory_usage']}%",
                    timestamp=datetime.now(),
                    affected_component="Memory"
                )
                issues.append(issue)
            
            # Check swap usage
            if memory_info.swap_usage_percent > self.thresholds['swap_usage']:
                severity = self._determine_severity(memory_info.swap_usage_percent, self.thresholds['swap_usage'])
                
                issue = PerformanceIssue(
                    issue_type=IssueType.SWAP_HIGH_USAGE,
                    severity=severity,
                    title="High Swap Usage",
                    description=f"Swap usage is at {memory_info.swap_usage_percent:.1f}%, indicating memory pressure.",
                    recommendation="Consider adding more RAM or optimizing memory usage.",
                    current_value=f"{memory_info.swap_usage_percent:.1f}%",
                    threshold_value=f"{self.thresholds['swap_usage']}%",
                    timestamp=datetime.now(),
                    affected_component="Memory"
                )
                issues.append(issue)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze memory performance: {e}")
        
        return issues
    
    def _analyze_disk_performance(self) -> List[PerformanceIssue]:
        """Analyze disk performance and identify issues."""
        issues = []
        
        try:
            disk_info_list = self.system_monitor.get_disk_info()
            
            for disk_info in disk_info_list:
                # Check disk usage
                if disk_info.usage_percent > self.thresholds['disk_usage']:
                    severity = self._determine_severity(disk_info.usage_percent, self.thresholds['disk_usage'])
                    
                    issue = PerformanceIssue(
                        issue_type=IssueType.DISK_HIGH_USAGE,
                        severity=severity,
                        title=f"High Disk Usage on {disk_info.mountpoint}",
                        description=f"Disk usage is at {disk_info.usage_percent:.1f}%, which may impact performance.",
                        recommendation="Clean up unnecessary files or consider expanding storage.",
                        current_value=f"{disk_info.usage_percent:.1f}%",
                        threshold_value=f"{self.thresholds['disk_usage']}%",
                        timestamp=datetime.now(),
                        affected_component=f"Disk ({disk_info.mountpoint})"
                    )
                    issues.append(issue)
                
                # Check disk I/O performance
                total_io = disk_info.read_bytes_per_sec + disk_info.write_bytes_per_sec
                if total_io > 100 * 1024 * 1024:  # 100 MB/s threshold
                    issue = PerformanceIssue(
                        issue_type=IssueType.DISK_SLOW_IO,
                        severity=Severity.MEDIUM,
                        title=f"High Disk I/O on {disk_info.mountpoint}",
                        description=f"Disk I/O is {total_io / (1024*1024):.1f} MB/s, which may indicate heavy disk activity.",
                        recommendation="Check for disk-intensive processes or consider SSD upgrade.",
                        current_value=f"{total_io / (1024*1024):.1f} MB/s",
                        threshold_value="100 MB/s",
                        timestamp=datetime.now(),
                        affected_component=f"Disk ({disk_info.mountpoint})"
                    )
                    issues.append(issue)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze disk performance: {e}")
        
        return issues
    
    def _analyze_network_performance(self) -> List[PerformanceIssue]:
        """Analyze network performance and identify issues."""
        issues = []
        
        try:
            network_info_list = self.system_monitor.get_network_info()
            
            for network_info in network_info_list:
                if network_info.speed_mbps is not None and network_info.speed_mbps > 100:
                    issue = PerformanceIssue(
                        issue_type=IssueType.NETWORK_SLOW,
                        severity=Severity.LOW,
                        title=f"High Network Activity on {network_info.interface}",
                        description=f"Network speed is {network_info.speed_mbps:.1f} Mbps, indicating high network usage.",
                        recommendation="Check for network-intensive applications or downloads.",
                        current_value=f"{network_info.speed_mbps:.1f} Mbps",
                        threshold_value="100 Mbps",
                        timestamp=datetime.now(),
                        affected_component=f"Network ({network_info.interface})"
                    )
                    issues.append(issue)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze network performance: {e}")
        
        return issues
    
    def _analyze_process_performance(self) -> List[PerformanceIssue]:
        """Analyze process performance and identify resource hogs."""
        issues = []
        
        try:
            processes = self.system_monitor.get_top_processes(limit=10)
            
            for process in processes:
                # Check for CPU hogs (only report if > 90% CPU)
                if process.cpu_percent > 90:
                    issue = PerformanceIssue(
                        issue_type=IssueType.PROCESS_HOG,
                        severity=Severity.HIGH,
                        title=f"High CPU Process: {process.name}",
                        description=f"Process {process.name} (PID: {process.pid}) is using {process.cpu_percent:.1f}% CPU.",
                        recommendation="Consider terminating the process if it's not needed.",
                        current_value=f"{process.cpu_percent:.1f}%",
                        threshold_value="90%",
                        timestamp=datetime.now(),
                        affected_component=f"Process ({process.name})"
                    )
                    issues.append(issue)
                
                # Check for memory hogs
                if process.memory_percent > 10:
                    issue = PerformanceIssue(
                        issue_type=IssueType.PROCESS_HOG,
                        severity=Severity.MEDIUM,
                        title=f"High Memory Process: {process.name}",
                        description=f"Process {process.name} (PID: {process.pid}) is using {process.memory_mb:.1f} MB RAM.",
                        recommendation="Consider closing the application if it's not needed.",
                        current_value=f"{process.memory_mb:.1f} MB",
                        threshold_value="10% of total RAM",
                        timestamp=datetime.now(),
                        affected_component=f"Process ({process.name})"
                    )
                    issues.append(issue)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze process performance: {e}")
        
        return issues
    
    def _analyze_system_load(self) -> List[PerformanceIssue]:
        """Analyze system load and identify issues."""
        issues = []
        
        try:
            # This is already covered in CPU analysis, but we can add more specific load analysis here
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to analyze system load: {e}")
        
        return issues
    
    def get_performance_recommendations(self) -> List[PerformanceRecommendation]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        try:
            # Get current system state
            cpu_info = self.system_monitor.get_cpu_info()
            memory_info = self.system_monitor.get_memory_info()
            disk_info_list = self.system_monitor.get_disk_info()
            
            # CPU recommendations
            if cpu_info.usage_percent > 70:
                recommendations.append(PerformanceRecommendation(
                    title="Optimize CPU Usage",
                    description="High CPU usage detected. Consider optimizing system performance.",
                    impact="High",
                    difficulty="Medium",
                    estimated_time="5-10 minutes",
                    commands=[
                        "htop  # Monitor processes",
                        "kill -9 <PID>  # Kill problematic processes",
                        "systemctl disable <service>  # Disable unnecessary services"
                    ],
                    category="CPU"
                ))
            
            # Memory recommendations
            if memory_info.usage_percent > 80:
                recommendations.append(PerformanceRecommendation(
                    title="Optimize Memory Usage",
                    description="High memory usage detected. Consider memory optimization.",
                    impact="High",
                    difficulty="Medium",
                    estimated_time="5-15 minutes",
                    commands=[
                        "free -h  # Check memory usage",
                        "sudo sysctl vm.swappiness=10  # Reduce swap usage",
                        "sudo systemctl restart <service>  # Restart memory-heavy services"
                    ],
                    category="Memory"
                ))
            
            # Disk recommendations
            for disk_info in disk_info_list:
                if disk_info.usage_percent > 85:
                    recommendations.append(PerformanceRecommendation(
                        title=f"Clean Up Disk Space on {disk_info.mountpoint}",
                        description=f"Disk usage is {disk_info.usage_percent:.1f}%. Clean up unnecessary files.",
                        impact="Medium",
                        difficulty="Low",
                        estimated_time="10-30 minutes",
                        commands=[
                            "sudo apt autoremove  # Remove unused packages",
                            "sudo apt autoclean  # Clean package cache",
                            "du -sh /*  # Find large directories",
                            "sudo journalctl --vacuum-time=7d  # Clean old logs"
                        ],
                        category="Disk"
                    ))
                    break
            
            # General system recommendations
            recommendations.append(PerformanceRecommendation(
                title="Update System Packages",
                description="Keep system packages updated for optimal performance and security.",
                impact="Medium",
                difficulty="Low",
                estimated_time="10-20 minutes",
                commands=[
                    "sudo apt update",
                    "sudo apt upgrade",
                    "sudo apt autoremove"
                ],
                category="System"
            ))
            
            # Performance monitoring recommendations (only if systemd-analyze is not available)
            if not self._is_systemd_analyze_available():
                recommendations.append(PerformanceRecommendation(
                    title="Enable Performance Monitoring",
                    description="Set up continuous performance monitoring for better insights.",
                    impact="Low",
                    difficulty="Medium",
                    estimated_time="15-30 minutes",
                    commands=[
                        "sudo systemctl enable systemd-analyze",
                        "sudo systemctl start systemd-analyze",
                        "journalctl -f  # Monitor system logs"
                    ],
                    category="Monitoring"
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to get performance recommendations: {e}")
        
        return recommendations
    
    def run_system_benchmark(self, progress_callback=None) -> SystemBenchmark:
        """Run a comprehensive system benchmark with progress feedback."""
        try:
            self.logger.info("Starting system benchmark...")
            
            if progress_callback:
                progress_callback("Starting CPU benchmark...", 0)
            
            # CPU benchmark (more intensive)
            cpu_score = self._benchmark_cpu(progress_callback)
            
            if progress_callback:
                progress_callback("Starting Memory benchmark...", 25)
            
            # Memory benchmark (more intensive)
            memory_score = self._benchmark_memory(progress_callback)
            
            if progress_callback:
                progress_callback("Starting Disk benchmark...", 50)
            
            # Disk benchmark (more intensive)
            disk_score = self._benchmark_disk(progress_callback)
            
            if progress_callback:
                progress_callback("Starting Network benchmark...", 75)
            
            # Network benchmark (more intensive)
            network_score = self._benchmark_network(progress_callback)
            
            if progress_callback:
                progress_callback("Calculating final scores...", 90)
            
            # Calculate overall score
            overall_score = (cpu_score + memory_score + disk_score + network_score) / 4
            
            benchmark = SystemBenchmark(
                cpu_score=cpu_score,
                memory_score=memory_score,
                disk_score=disk_score,
                network_score=network_score,
                overall_score=overall_score,
                timestamp=datetime.now(),
                details={
                    'cpu_cores': psutil.cpu_count(),
                    'memory_total': psutil.virtual_memory().total,
                    'disk_count': len(psutil.disk_partitions()),
                    'network_interfaces': len(psutil.net_if_addrs())
                }
            )
            
            self.benchmark_cache = benchmark
            self.last_benchmark = datetime.now()
            
            if progress_callback:
                progress_callback("Benchmark completed!", 100)
            
            self.logger.info(f"Benchmark completed. Overall score: {overall_score:.1f}")
            return benchmark
            
        except Exception as e:
            self.logger.error(f"Failed to run system benchmark: {e}")
            raise PerformanceAnalysisError(f"Failed to run system benchmark: {e}")
    
    def _benchmark_cpu(self, progress_callback=None) -> float:
        """Benchmark CPU performance."""
        try:
            start_time = time.time()
            
            # More intensive CPU benchmark with multiple test types
            results = []
            
            # Test 1: Integer arithmetic (20% of test)
            if progress_callback:
                progress_callback("CPU: Integer arithmetic test...", 5)
            
            result1 = 0
            for i in range(5000000):
                result1 += i * i
                if i % 1000000 == 0 and progress_callback:
                    progress_callback(f"CPU: Integer test {i//1000000}/5", 5 + (i//1000000) * 2)
            results.append(result1)
            
            # Test 2: Floating point operations (30% of test)
            if progress_callback:
                progress_callback("CPU: Floating point test...", 15)
            
            result2 = 0.0
            for i in range(3000000):
                result2 += (i * 1.5) / (i + 1)
                if i % 1000000 == 0 and progress_callback:
                    progress_callback(f"CPU: Float test {i//1000000}/3", 15 + (i//1000000) * 3)
            results.append(result2)
            
            # Test 3: String operations (25% of test)
            if progress_callback:
                progress_callback("CPU: String operations test...", 24)
            
            result3 = ""
            for i in range(100000):
                result3 += str(i) + "test"
                if i % 25000 == 0 and progress_callback:
                    progress_callback(f"CPU: String test {i//25000}/4", 24 + (i//25000) * 1)
            results.append(len(result3))
            
            # Test 4: List operations (25% of test)
            if progress_callback:
                progress_callback("CPU: List operations test...", 28)
            
            result4 = []
            for i in range(200000):
                result4.append(i * 2)
                if i % 50000 == 0 and progress_callback:
                    progress_callback(f"CPU: List test {i//50000}/4", 28 + (i//50000) * 1)
            results.append(len(result4))
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Score based on duration (lower is better)
            # Normalize to 0-100 scale with more realistic scoring
            score = max(0, 100 - (duration * 5))
            
            return min(100, score)
            
        except Exception as e:
            self.logger.error(f"Failed to benchmark CPU: {e}")
            return 50.0
    
    def _benchmark_memory(self, progress_callback=None) -> float:
        """Benchmark memory performance."""
        try:
            start_time = time.time()
            
            # More intensive memory benchmark
            memory_tests = []
            
            # Test 1: Large list allocation (30% of test)
            if progress_callback:
                progress_callback("Memory: Large list allocation...", 30)
            
            large_list = []
            for i in range(500000):
                large_list.append([i] * 50)
                if i % 50000 == 0 and progress_callback:
                    progress_callback(f"Memory: List allocation {i//50000}/10", 30 + (i//50000) * 2)
            memory_tests.append(len(large_list))
            
            # Test 2: Dictionary operations (25% of test)
            if progress_callback:
                progress_callback("Memory: Dictionary operations...", 40)
            
            large_dict = {}
            for i in range(200000):
                large_dict[f"key_{i}"] = f"value_{i}" * 10
                if i % 25000 == 0 and progress_callback:
                    progress_callback(f"Memory: Dict operations {i//25000}/8", 40 + (i//25000) * 2)
            memory_tests.append(len(large_dict))
            
            # Test 3: String concatenation (25% of test)
            if progress_callback:
                progress_callback("Memory: String operations...", 50)
            
            large_string = ""
            for i in range(100000):
                large_string += f"test_string_{i}_"
                if i % 12500 == 0 and progress_callback:
                    progress_callback(f"Memory: String ops {i//12500}/8", 50 + (i//12500) * 2)
            memory_tests.append(len(large_string))
            
            # Test 4: Memory cleanup (20% of test)
            if progress_callback:
                progress_callback("Memory: Cleanup operations...", 60)
            
            # Clear all test data
            del large_list
            del large_dict
            del large_string
            
            # Force garbage collection
            import gc
            gc.collect()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Score based on duration (lower is better)
            score = max(0, 100 - (duration * 20))
            
            return min(100, score)
            
        except Exception as e:
            self.logger.error(f"Failed to benchmark memory: {e}")
            return 50.0
    
    def _benchmark_disk(self, progress_callback=None) -> float:
        """Benchmark disk performance."""
        try:
            start_time = time.time()
            
            # Create a temporary file for testing
            test_file = Path("/tmp/system_companion_benchmark.tmp")
            
            # Test 1: Sequential write (40% of test)
            if progress_callback:
                progress_callback("Disk: Sequential write test...", 55)
            
            with open(test_file, 'w') as f:
                for i in range(50000):
                    f.write(f"Benchmark line {i} with some additional data to make it longer\n")
                    if i % 5000 == 0 and progress_callback:
                        progress_callback(f"Disk: Write test {i//5000}/10", 55 + (i//5000) * 3)
            
            # Test 2: Sequential read (30% of test)
            if progress_callback:
                progress_callback("Disk: Sequential read test...", 67)
            
            with open(test_file, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                if progress_callback:
                    progress_callback(f"Disk: Read {len(lines)} lines", 70)
            
            # Test 3: Random access (20% of test)
            if progress_callback:
                progress_callback("Disk: Random access test...", 77)
            
            with open(test_file, 'r') as f:
                lines = f.readlines()
                # Read random lines
                import random
                for i in range(1000):
                    random_line = random.choice(lines)
                    if i % 100 == 0 and progress_callback:
                        progress_callback(f"Disk: Random access {i//100}/10", 77 + (i//100) * 2)
            
            # Test 4: Cleanup (10% of test)
            if progress_callback:
                progress_callback("Disk: Cleanup...", 87)
            
            # Clean up
            test_file.unlink()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Score based on duration (lower is better)
            score = max(0, 100 - (duration * 50))
            
            return min(100, score)
            
        except Exception as e:
            self.logger.error(f"Failed to benchmark disk: {e}")
            return 50.0
    
    def _benchmark_network(self, progress_callback=None) -> float:
        """Benchmark network performance."""
        try:
            start_time = time.time()
            
            # More comprehensive network benchmark
            network_tests = []
            
            # Test 1: Localhost ping (30% of test)
            if progress_callback:
                progress_callback("Network: Localhost ping test...", 80)
            
            result = subprocess.run(
                ['ping', '-c', '5', '127.0.0.1'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                # Parse ping results for average time
                import re
                match = re.search(r'time=(\d+\.?\d*)', result.stdout)
                if match:
                    ping_time = float(match.group(1))
                    network_tests.append(ping_time)
                else:
                    network_tests.append(1.0)  # Default if can't parse
            else:
                network_tests.append(10.0)  # High value if ping fails
            
            if progress_callback:
                progress_callback("Network: DNS resolution test...", 85)
            
            # Test 2: DNS resolution (40% of test)
            try:
                import socket
                dns_start = time.time()
                socket.gethostbyname('google.com')
                dns_time = time.time() - dns_start
                network_tests.append(dns_time)
            except Exception:
                network_tests.append(5.0)  # High value if DNS fails
            
            if progress_callback:
                progress_callback("Network: Connection test...", 90)
            
            # Test 3: HTTP connection (30% of test)
            try:
                import urllib.request
                http_start = time.time()
                with urllib.request.urlopen('http://httpbin.org/delay/1', timeout=5) as response:
                    http_time = time.time() - http_start
                    network_tests.append(http_time)
            except Exception:
                network_tests.append(10.0)  # High value if HTTP fails
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Calculate average network performance
            avg_network_time = sum(network_tests) / len(network_tests)
            
            # Score based on network performance (lower times are better)
            score = max(0, 100 - (avg_network_time * 10))
            
            return min(100, score)
            
        except Exception as e:
            self.logger.error(f"Failed to benchmark network: {e}")
            return 50.0
    
    def _determine_severity(self, current_value: float, threshold: float) -> Severity:
        """Determine severity based on how much the current value exceeds the threshold."""
        ratio = current_value / threshold
        
        if ratio >= 2.0:
            return Severity.CRITICAL
        elif ratio >= 1.5:
            return Severity.HIGH
        elif ratio >= 1.2:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _store_historical_data(self) -> None:
        """Store current metrics in historical data."""
        try:
            timestamp = datetime.now()
            
            # Get current metrics
            cpu_info = self.system_monitor.get_cpu_info()
            memory_info = self.system_monitor.get_memory_info()
            
            # Store data
            self.historical_data['cpu'].append({
                'timestamp': timestamp,
                'usage': cpu_info.usage_percent,
                'temperature': cpu_info.temperature_celsius
            })
            
            self.historical_data['memory'].append({
                'timestamp': timestamp,
                'usage': memory_info.usage_percent,
                'swap_usage': memory_info.swap_usage_percent
            })
            
            # Keep only last 24 hours of data (86400 seconds)
            cutoff = timestamp - timedelta(hours=24)
            
            for key in self.historical_data:
                self.historical_data[key] = [
                    data for data in self.historical_data[key]
                    if data['timestamp'] > cutoff
                ]
            
        except Exception as e:
            self.logger.error(f"Failed to store historical data: {e}")
    
    def get_performance_trends(self) -> Dict[str, List[Dict]]:
        """Get performance trends over time."""
        return self.historical_data
    
    def get_last_benchmark(self) -> Optional[SystemBenchmark]:
        """Get the last benchmark results."""
        return self.benchmark_cache
    
    def _is_systemd_analyze_available(self) -> bool:
        """Check if systemd-analyze is available and working."""
        try:
            # Check if systemd-analyze executable exists
            if shutil.which('systemd-analyze') is None:
                return False
            
            # Test if systemd-analyze actually works
            result = subprocess.run(
                ['systemd-analyze', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False 