"""
Maintenance management functionality for System Companion.

This module provides system maintenance, cleanup, and optimization
capabilities for keeping the system running smoothly.
"""

import logging
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import os

from ..utils.exceptions import MaintenanceError


class TaskStatus(Enum):
    """Maintenance task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    """Maintenance task priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MaintenanceTask:
    """Represents a maintenance task."""
    id: str
    name: str
    description: str
    category: str
    priority: TaskPriority
    estimated_duration: str
    commands: List[str]
    status: TaskStatus
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    result: Optional[str]
    requires_sudo: bool


@dataclass
class MaintenanceResult:
    """Result of a maintenance operation."""
    task_id: str
    success: bool
    output: str
    error: Optional[str]
    duration: float
    timestamp: datetime


class MaintenanceManager:
    """Main system maintenance manager."""
    
    STATE_FILE = Path.home() / ".local" / "share" / "system-companion" / "maintenance_state.json"
    HISTORY_FILE = Path.home() / ".local" / "share" / "system-companion" / "maintenance_history.json"
    FIRMWARE_NO_SUPPORT_KEY = "firmware_no_supported_hardware"
    SMARTCTL_NOT_FOUND_KEY = "smartctl_not_found"
    NO_SMART_DEVICES_KEY = "no_smart_devices_found"
    HAS_SATA_KEY = "has_sata_devices"
    HAS_NVME_KEY = "has_nvme_devices"

    def __init__(self) -> None:
        """Initialize the maintenance manager."""
        self.logger = logging.getLogger("system_companion.core.maintenance_manager")
        
        # Maintenance tasks registry
        self.tasks = self._initialize_tasks()
        
        # Task history
        self.task_history = []
        self._load_task_history()
        
        # Configuration
        self.config = {
            'auto_cleanup_enabled': True,
            'cleanup_interval_hours': 24,
            'max_log_age_days': 7,
            'max_cache_age_days': 30,
            'temp_file_threshold_mb': 100
        }
        
        # Firmware support state
        self.firmware_no_supported_hardware = False
        self.smartctl_not_found = False
        self.no_smart_devices_found = False
        self.has_sata_devices = False
        self.has_nvme_devices = False
        # Load last_run state from file
        self._load_last_run_state()
        # Scan for storage devices on startup
        self.scan_storage_devices()
        
        self.logger.info("Maintenance manager initialized")
    
    def _initialize_tasks(self) -> Dict[str, MaintenanceTask]:
        """Initialize the maintenance tasks."""
        tasks = {}
        
        # Package management tasks
        tasks['update_packages'] = MaintenanceTask(
            id='update_packages',
            name='Update System Packages',
            description='Update all system packages to their latest versions',
            category='Package Management',
            priority=TaskPriority.MEDIUM,
            estimated_duration='5-15 minutes',
            commands=[
                'sudo apt update',
                'sudo apt upgrade -y',
                'sudo apt autoremove -y'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        
        tasks['clean_package_cache'] = MaintenanceTask(
            id='clean_package_cache',
            name='Clean Package Cache',
            description='Remove old package cache files to free up disk space',
            category='Package Management',
            priority=TaskPriority.LOW,
            estimated_duration='1-2 minutes',
            commands=[
                'sudo apt autoclean',
                'sudo apt autoremove -y'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        
        # System cleanup tasks
        tasks['clean_temp_files'] = MaintenanceTask(
            id='clean_temp_files',
            name='Clean Temporary Files',
            description='Remove temporary files and directories',
            category='System Cleanup',
            priority=TaskPriority.LOW,
            estimated_duration='1-3 minutes',
            commands=[
                'sudo rm -rf /tmp/*',
                'sudo rm -rf /var/tmp/*',
                'find /home -name "*.tmp" -delete',
                'find /home -name "*.temp" -delete'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        
        tasks['clean_logs'] = MaintenanceTask(
            id='clean_logs',
            name='Clean Old Log Files',
            description='Remove old log files to free up disk space',
            category='System Cleanup',
            priority=TaskPriority.LOW,
            estimated_duration='1-2 minutes',
            commands=[
                'sudo journalctl --vacuum-time=7d',
                'sudo find /var/log -name "*.log.*" -mtime +7 -delete',
                'sudo find /var/log -name "*.gz" -mtime +7 -delete'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        
        tasks['clean_browser_cache'] = MaintenanceTask(
            id='clean_browser_cache',
            name='Clean Browser Cache',
            description='Remove browser cache files to free up disk space',
            category='User Cleanup',
            priority=TaskPriority.LOW,
            estimated_duration='2-5 minutes',
            commands=[
                'rm -rf ~/.cache/mozilla/firefox/*/Cache*',
                'rm -rf ~/.cache/google-chrome/Default/Cache*',
                'rm -rf ~/.cache/chromium/Default/Cache*',
                'rm -rf ~/.cache/brave/Default/Cache*'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=False
        )
        
        # System optimization tasks
        tasks['optimize_swap'] = MaintenanceTask(
            id='optimize_swap',
            name='Optimize Swap Usage',
            description='Configure swap usage for better performance',
            category='System Optimization',
            priority=TaskPriority.MEDIUM,
            estimated_duration='1 minute',
            commands=[
                'sudo sysctl vm.swappiness=10',
                'echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        
        tasks['defragment_filesystem'] = MaintenanceTask(
            id='defragment_filesystem',
            name='Defragment Filesystem',
            description='Defragment ext4 filesystem for better performance',
            category='System Optimization',
            priority=TaskPriority.LOW,
            estimated_duration='10-30 minutes',
            commands=[
                'sudo e4defrag /',
                'sudo e4defrag /home'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        
        tasks['update_firmware'] = MaintenanceTask(
            id='update_firmware',
            name='Update System Firmware',
            description='Check for and install firmware updates',
            category='System Updates',
            priority=TaskPriority.HIGH,
            estimated_duration='5-20 minutes',
            commands=[
                'sudo fwupdmgr refresh --force',
                'sudo fwupdmgr update'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        
        tasks['check_disk_health'] = MaintenanceTask(
            id='check_disk_health',
            name='Check Disk Health',
            description='Check disk health and SMART status',
            category='System Health',
            priority=TaskPriority.MEDIUM,
            estimated_duration='2-5 minutes',
            commands=[
                'sudo smartctl -a /dev/sda',
                'sudo smartctl -a /dev/sdb'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        
        tasks['check_nvme_health'] = MaintenanceTask(
            id='check_nvme_health',
            name='Check NVMe Health',
            description='Check NVMe SSD health and SMART status',
            category='System Health',
            priority=TaskPriority.MEDIUM,
            estimated_duration='1-2 minutes',
            commands=[
                # Placeholder, actual command is dynamic
                'nvme smart-log /dev/nvme0n1'
            ],
            status=TaskStatus.PENDING,
            last_run=None,
            next_run=None,
            result=None,
            requires_sudo=True
        )
        return tasks
    
    def _load_last_run_state(self) -> None:
        """Load last_run values for tasks from JSON file."""
        try:
            if self.STATE_FILE.exists():
                with open(self.STATE_FILE, "r") as f:
                    state = json.load(f)
                for task_id, last_run_str in state.get("last_run", {}).items():
                    if task_id in self.tasks and last_run_str:
                        try:
                            self.tasks[task_id].last_run = datetime.fromisoformat(last_run_str)
                        except Exception:
                            self.tasks[task_id].last_run = None
                self.firmware_no_supported_hardware = state.get(self.FIRMWARE_NO_SUPPORT_KEY, False)
                self.smartctl_not_found = state.get(self.SMARTCTL_NOT_FOUND_KEY, False)
                self.no_smart_devices_found = state.get(self.NO_SMART_DEVICES_KEY, False)
                self.has_sata_devices = state.get(self.HAS_SATA_KEY, False)
                self.has_nvme_devices = state.get(self.HAS_NVME_KEY, False)
        except Exception as e:
            self.logger.error(f"Failed to load last_run state: {e}")

    def _save_last_run_state(self) -> None:
        """Save last_run values for tasks to JSON file."""
        try:
            state = {"last_run": {}}
            for task_id, task in self.tasks.items():
                if task.last_run:
                    state["last_run"][task_id] = task.last_run.isoformat()
                else:
                    state["last_run"][task_id] = None
            state[self.FIRMWARE_NO_SUPPORT_KEY] = self.firmware_no_supported_hardware
            state[self.SMARTCTL_NOT_FOUND_KEY] = self.smartctl_not_found
            state[self.NO_SMART_DEVICES_KEY] = self.no_smart_devices_found
            state[self.HAS_SATA_KEY] = self.has_sata_devices
            state[self.HAS_NVME_KEY] = self.has_nvme_devices
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.STATE_FILE, "w") as f:
                json.dump(state, f)
        except Exception as e:
            self.logger.error(f"Failed to save last_run state: {e}")
    
    def _load_task_history(self) -> None:
        """Load task history from JSON file."""
        try:
            if self.HISTORY_FILE.exists():
                with open(self.HISTORY_FILE, "r") as f:
                    data = json.load(f)
                self.task_history = [
                    MaintenanceResult(
                        task_id=entry["task_id"],
                        success=entry["success"],
                        output=entry.get("output", ""),
                        error=entry.get("error"),
                        duration=entry.get("duration", 0.0),
                        timestamp=datetime.fromisoformat(entry["timestamp"])
                    )
                    for entry in data.get("history", [])
                ]
        except Exception as e:
            self.logger.error(f"Failed to load task history: {e}")

    def _save_task_history(self) -> None:
        """Save task history to JSON file (limit to last 100 entries)."""
        try:
            entries = []
            for result in self.task_history[-100:]:
                entries.append({
                    "task_id": result.task_id,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "duration": result.duration,
                    "timestamp": result.timestamp.isoformat()
                })
            self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.HISTORY_FILE, "w") as f:
                json.dump({"history": entries}, f)
        except Exception as e:
            self.logger.error(f"Failed to save task history: {e}")

    def clear_task_history(self) -> None:
        """Clear task history in memory and on disk."""
        self.task_history = []
        try:
            if self.HISTORY_FILE.exists():
                self.HISTORY_FILE.unlink()
        except Exception as e:
            self.logger.error(f"Failed to clear task history file: {e}")
    
    def get_all_tasks(self) -> List[MaintenanceTask]:
        """Get all maintenance tasks."""
        return list(self.tasks.values())
    
    def get_tasks_by_category(self, category: str) -> List[MaintenanceTask]:
        """Get tasks filtered by category."""
        return [task for task in self.tasks.values() if task.category == category]
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[MaintenanceTask]:
        """Get tasks filtered by priority."""
        return [task for task in self.tasks.values() if task.priority == priority]
    
    def get_pending_tasks(self) -> List[MaintenanceTask]:
        """Get all pending tasks."""
        return [task for task in self.tasks.values() if task.status == TaskStatus.PENDING]
    
    def run_task(self, task_id: str) -> MaintenanceResult:
        """Run a specific maintenance task."""
        try:
            if task_id not in self.tasks:
                raise MaintenanceError(f"Task '{task_id}' not found")
            
            task = self.tasks[task_id]
            self.logger.info(f"Starting maintenance task: {task.name}")
            
            # Update task status
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.now()
            self._save_last_run_state()
            
            start_time = datetime.now()
            success = True
            output = ""
            error = None
            
            # If task requires sudo, create a batch script to run all commands in one session
            if task.requires_sudo and len(task.commands) > 1 and task_id not in ['check_disk_health', 'check_nvme_health']:
                success, output, error = self._run_commands_batch(task.commands)
            elif task_id == 'check_disk_health':
                # Dynamically scan for SATA devices
                try:
                    scan_result = subprocess.run(
                        'smartctl --scan',
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    scan_output = scan_result.stdout.strip()
                    devices = []
                    for line in scan_output.splitlines():
                        parts = line.split()
                        if parts and parts[0].startswith('/dev/sd'):
                            devices.append(parts[0])
                    self.has_sata_devices = bool(devices)
                    if not devices:
                        self.no_smart_devices_found = True
                        self._save_last_run_state()
                        raise MaintenanceError("No supported disks found for SMART health check.")
                    self.no_smart_devices_found = False
                    self._save_last_run_state()
                    # Run smartctl on each device
                    for dev in devices:
                        cmd = f'pkexec smartctl -a {dev}'
                        self.logger.debug(f"Checking SMART health: {cmd}")
                        result = subprocess.run(
                            cmd,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        output += f"Device: {dev}\n{result.stdout}\n"
                        if result.returncode != 0:
                            success = False
                            error = result.stderr
                except Exception as e:
                    success = False
                    error = str(e)
            elif task_id == 'check_nvme_health':
                # Dynamically scan for NVMe devices (robust table parsing)
                try:
                    list_result = subprocess.run(
                        'nvme list',
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    list_output = list_result.stdout.strip()
                    devices = []
                    for line in list_output.splitlines():
                        line = line.strip()
                        if not line or line.startswith('Node') or line.startswith('-'):
                            continue  # skip header and separator
                        parts = line.split()
                        if parts and parts[0].startswith('/dev/nvme'):
                            devices.append(parts[0])
                    self.has_nvme_devices = bool(devices)
                    if not devices:
                        self._save_last_run_state()
                        raise MaintenanceError("No NVMe devices found for health check.")
                    self._save_last_run_state()
                    # Run nvme smart-log on each device
                    for dev in devices:
                        cmd = f'pkexec nvme smart-log {dev}'
                        self.logger.debug(f"Checking NVMe health: {cmd}")
                        result = subprocess.run(
                            cmd,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        output += f"Device: {dev}\n{result.stdout}\n"
                        if result.returncode != 0:
                            success = False
                            error = result.stderr
                except Exception as e:
                    success = False
                    error = str(e)
            else:
                # Execute commands individually
                for command in task.commands:
                    try:
                        self.logger.debug(f"Executing command: {command}")
                        
                        # Check if command requires sudo and use pkexec for GUI applications
                        if task.requires_sudo:
                            if command.startswith('sudo '):
                                # Replace sudo with pkexec for GUI applications
                                command = command.replace('sudo ', 'pkexec ', 1)
                                self.logger.info(f"Using pkexec for GUI command: {command}")
                            elif not command.startswith('pkexec '):
                                command = f"pkexec {command}"
                                self.logger.info(f"Using pkexec for command: {command}")
                        
                        # Execute command
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minute timeout
                        )
                        
                        if result.returncode != 0:
                            success = False
                            error = f"Command failed: {result.stderr}"
                            output += f"Command: {command}\nError: {result.stderr}\n"
                        else:
                            output += f"Command: {command}\nOutput: {result.stdout}\n"
                        
                    except subprocess.TimeoutExpired:
                        success = False
                        error = f"Command timed out: {command}"
                        output += f"Command: {command}\nError: Timeout\n"
                    except Exception as e:
                        success = False
                        error = f"Command failed: {str(e)}"
                        output += f"Command: {command}\nError: {str(e)}\n"
            
            # Special handling for firmware update task
            if task_id == 'update_firmware':
                if '0 local devices supported' in output:
                    self.firmware_no_supported_hardware = True
                else:
                    self.firmware_no_supported_hardware = False
                self._save_last_run_state()
            # Special handling for check_disk_health task
            if task_id == 'check_disk_health':
                if (error and "Command 'smartctl' not found" in error) or (output and "Command 'smartctl' not found" in output):
                    self.smartctl_not_found = True
                else:
                    self.smartctl_not_found = False
                self._save_last_run_state()
            
            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Update task status
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.result = "Success" if success else f"Failed: {error}"
            
            # Create result
            result = MaintenanceResult(
                task_id=task_id,
                success=success,
                output=output,
                error=error,
                duration=duration,
                timestamp=datetime.now()
            )
            
            # Store in history
            self.task_history.append(result)
            self._save_task_history()
            
            self.logger.info(f"Task '{task.name}' completed with status: {'Success' if success else 'Failed'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to run task '{task_id}': {e}")
            raise MaintenanceError(f"Failed to run task '{task_id}': {e}")
    
    def _run_commands_batch(self, commands: List[str]) -> Tuple[bool, str, Optional[str]]:
        """Run multiple commands in a single elevated session to avoid multiple password prompts."""
        try:
            import tempfile
            import os
            
            # Create a temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
                script_path = script_file.name
                
                # Write shebang and commands
                script_file.write("#!/bin/bash\n")
                script_file.write("set -e\n")  # Exit on any error
                script_file.write("echo 'Starting maintenance commands...'\n")
                
                for i, command in enumerate(commands):
                    # Remove sudo prefix if present
                    clean_command = command.replace('sudo ', '')
                    script_file.write(f"echo 'Executing command {i+1}: {clean_command}'\n")
                    script_file.write(f"{clean_command}\n")
                    script_file.write(f"echo 'Command {i+1} completed'\n")
                
                script_file.write("echo 'All commands completed successfully'\n")
            
            # Make the script executable
            os.chmod(script_path, 0o755)
            
            # Run the script with pkexec (single password prompt)
            self.logger.info(f"Running batch script with pkexec: {script_path}")
            result = subprocess.run(
                ['pkexec', script_path],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for batch operations
            )
            
            # Clean up the temporary script
            try:
                os.unlink(script_path)
            except:
                pass
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr if not success else None
            
            return success, output, error
            
        except Exception as e:
            self.logger.error(f"Failed to run commands batch: {e}")
            return False, "", str(e)
    
    def run_automated_cleanup(self) -> List[MaintenanceResult]:
        """Run automated cleanup tasks."""
        try:
            self.logger.info("Starting automated cleanup")
            
            results = []
            
            # Get low priority cleanup tasks
            cleanup_tasks = [
                task for task in self.tasks.values()
                if task.category in ['System Cleanup', 'User Cleanup', 'Package Management']
                and task.priority in [TaskPriority.LOW, TaskPriority.MEDIUM]
            ]
            
            # Group tasks by whether they require sudo
            sudo_tasks = [task for task in cleanup_tasks if task.requires_sudo]
            non_sudo_tasks = [task for task in cleanup_tasks if not task.requires_sudo]
            
            # Run all sudo tasks in a single batch to avoid multiple password prompts
            if sudo_tasks:
                try:
                    all_sudo_commands = []
                    for task in sudo_tasks:
                        all_sudo_commands.extend(task.commands)
                    
                    self.logger.info(f"Running {len(sudo_tasks)} sudo tasks in single batch")
                    success, output, error = self._run_commands_batch(all_sudo_commands)
                    
                    # Create results for each sudo task
                    for task in sudo_tasks:
                        result = MaintenanceResult(
                            task_id=task.id,
                            success=success,
                            output=output,
                            error=error,
                            duration=0.0,  # Duration not tracked for batch operations
                            timestamp=datetime.now()
                        )
                        results.append(result)
                        
                        # Update task status
                        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
                        task.result = "Success" if success else f"Failed: {error}"
                        
                        if not success:
                            self.logger.warning(f"Automated cleanup task '{task.name}' failed: {error}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to run sudo tasks batch: {e}")
                    # Mark all sudo tasks as failed
                    for task in sudo_tasks:
                        result = MaintenanceResult(
                            task_id=task.id,
                            success=False,
                            output="",
                            error=str(e),
                            duration=0.0,
                            timestamp=datetime.now()
                        )
                        results.append(result)
                        task.status = TaskStatus.FAILED
                        task.result = f"Failed: {e}"
            
            # Run non-sudo tasks individually (no password prompts needed)
            for task in non_sudo_tasks:
                try:
                    result = self.run_task(task.id)
                    results.append(result)
                    
                    # If task failed, log but continue with others
                    if not result.success:
                        self.logger.warning(f"Automated cleanup task '{task.name}' failed: {result.error}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to run automated cleanup task '{task.name}': {e}")
                    continue
            
            self.logger.info(f"Automated cleanup completed. {len(results)} tasks executed.")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to run automated cleanup: {e}")
            raise MaintenanceError(f"Failed to run automated cleanup: {e}")
    
    def get_system_cleanup_info(self) -> Dict[str, any]:
        """Get information about system cleanup opportunities."""
        try:
            cleanup_info = {
                'package_cache_size': 0,
                'temp_files_size': 0,
                'log_files_size': 0,
                'browser_cache_size': 0,
                'old_packages_count': 0,
                'total_cleanup_size': 0
            }
            
            # Check package cache size
            try:
                result = subprocess.run(
                    ['du', '-sh', '/var/cache/apt/archives'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    size_str = result.stdout.split()[0]
                    cleanup_info['package_cache_size'] = self._parse_size(size_str)
            except Exception as e:
                self.logger.debug(f"Could not check package cache size: {e}")
            
            # Check temp files size
            try:
                result = subprocess.run(
                    ['du', '-sh', '/tmp'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    size_str = result.stdout.split()[0]
                    cleanup_info['temp_files_size'] = self._parse_size(size_str)
            except Exception as e:
                self.logger.debug(f"Could not check temp files size: {e}")
            
            # Check log files size
            try:
                result = subprocess.run(
                    ['du', '-sh', '/var/log'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    size_str = result.stdout.split()[0]
                    cleanup_info['log_files_size'] = self._parse_size(size_str)
            except Exception as e:
                self.logger.debug(f"Could not check log files size: {e}")
            
            # Check browser cache size
            try:
                browser_cache_dirs = [
                    os.path.expanduser('~/.cache/mozilla/firefox'),
                    os.path.expanduser('~/.cache/google-chrome'),
                    os.path.expanduser('~/.cache/chromium'),
                    os.path.expanduser('~/.cache/brave')
                ]
                
                total_browser_cache = 0
                for cache_dir in browser_cache_dirs:
                    if os.path.exists(cache_dir):
                        result = subprocess.run(
                            ['du', '-sh', cache_dir],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            size_str = result.stdout.split()[0]
                            total_browser_cache += self._parse_size(size_str)
                
                cleanup_info['browser_cache_size'] = total_browser_cache
            except Exception as e:
                self.logger.debug(f"Could not check browser cache size: {e}")
            
            # Calculate total cleanup size
            cleanup_info['total_cleanup_size'] = (
                cleanup_info['package_cache_size'] +
                cleanup_info['temp_files_size'] +
                cleanup_info['log_files_size'] +
                cleanup_info['browser_cache_size']
            )
            
            return cleanup_info
            
        except Exception as e:
            self.logger.error(f"Failed to get system cleanup info: {e}")
            return {}
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '1.2G', '500M') to bytes."""
        try:
            size_str = size_str.strip()
            
            if size_str.endswith('G'):
                return int(float(size_str[:-1]) * 1024 * 1024 * 1024)
            elif size_str.endswith('M'):
                return int(float(size_str[:-1]) * 1024 * 1024)
            elif size_str.endswith('K'):
                return int(float(size_str[:-1]) * 1024)
            else:
                return int(size_str)
        except Exception:
            return 0
    
    def get_task_history(self, limit: int = 50) -> List[MaintenanceResult]:
        """Get recent task history."""
        return self.task_history[-limit:] if self.task_history else []
    
    def get_task_statistics(self) -> Dict[str, any]:
        """Get maintenance task statistics."""
        try:
            total_tasks = len(self.tasks)
            completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
            failed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
            pending_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
            
            # Calculate success rate
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Get recent activity
            recent_results = self.get_task_history(10)
            recent_success_rate = (
                len([r for r in recent_results if r.success]) / len(recent_results) * 100
            ) if recent_results else 0
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'pending_tasks': pending_tasks,
                'success_rate': success_rate,
                'recent_success_rate': recent_success_rate,
                'last_maintenance': self._get_last_maintenance_time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get task statistics: {e}")
            return {}
    
    def _get_last_maintenance_time(self) -> Optional[datetime]:
        """Get the last maintenance time."""
        try:
            if not self.task_history:
                return None
            
            # Get the most recent completed task
            completed_tasks = [r for r in self.task_history if r.success]
            if not completed_tasks:
                return None
            
            return max(completed_tasks, key=lambda r: r.timestamp).timestamp
            
        except Exception as e:
            self.logger.error(f"Failed to get last maintenance time: {e}")
            return None
    
    def schedule_task(self, task_id: str, run_at: datetime) -> None:
        """Schedule a task to run at a specific time."""
        try:
            if task_id not in self.tasks:
                raise MaintenanceError(f"Task '{task_id}' not found")
            
            task = self.tasks[task_id]
            task.next_run = run_at
            task.status = TaskStatus.PENDING
            
            self.logger.info(f"Scheduled task '{task.name}' to run at {run_at}")
            
        except Exception as e:
            self.logger.error(f"Failed to schedule task '{task_id}': {e}")
            raise MaintenanceError(f"Failed to schedule task '{task_id}': {e}")
    
    def cancel_scheduled_task(self, task_id: str) -> None:
        """Cancel a scheduled task."""
        try:
            if task_id not in self.tasks:
                raise MaintenanceError(f"Task '{task_id}' not found")
            
            task = self.tasks[task_id]
            task.next_run = None
            
            self.logger.info(f"Cancelled scheduled task '{task.name}'")
            
        except Exception as e:
            self.logger.error(f"Failed to cancel scheduled task '{task_id}': {e}")
            raise MaintenanceError(f"Failed to cancel scheduled task '{task_id}': {e}") 

    def has_no_supported_firmware_devices(self) -> bool:
        """Return True if no supported hardware for firmware updates was detected."""
        return self.firmware_no_supported_hardware 

    def is_smartctl_not_found(self) -> bool:
        """Return True if smartctl is not installed (detected from last run)."""
        return self.smartctl_not_found 

    def no_smart_devices(self) -> bool:
        """Return True if no SMART devices were found in last check."""
        return self.no_smart_devices_found 

    def has_sata(self) -> bool:
        """Return True if at least one SATA device was found."""
        return self.has_sata_devices

    def has_nvme(self) -> bool:
        """Return True if at least one NVMe device was found."""
        return self.has_nvme_devices 

    def scan_storage_devices(self) -> None:
        """Scan for SATA and NVMe devices and update state."""
        # Scan for SATA devices
        try:
            scan_result = subprocess.run(
                'smartctl --scan',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            scan_output = scan_result.stdout.strip()
            sata_devices = []
            for line in scan_output.splitlines():
                parts = line.split()
                if parts and parts[0].startswith('/dev/sd'):
                    sata_devices.append(parts[0])
            self.has_sata_devices = bool(sata_devices)
        except Exception as e:
            self.logger.error(f"Failed to scan SATA devices: {e}")
            self.has_sata_devices = False
        # Scan for NVMe devices
        try:
            list_result = subprocess.run(
                'nvme list',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            list_output = list_result.stdout.strip()
            nvme_devices = []
            for line in list_output.splitlines():
                line = line.strip()
                if not line or line.startswith('Node') or line.startswith('-'):
                    continue
                parts = line.split()
                if parts and parts[0].startswith('/dev/nvme'):
                    nvme_devices.append(parts[0])
            self.has_nvme_devices = bool(nvme_devices)
        except Exception as e:
            self.logger.error(f"Failed to scan NVMe devices: {e}")
            self.has_nvme_devices = False
        self._save_last_run_state() 