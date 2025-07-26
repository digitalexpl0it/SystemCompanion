"""
Database management for System Companion.

This module handles SQLite database operations for storing system metrics,
configuration, and historical data.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from ..utils.exceptions import DatabaseError


class Database:
    """SQLite database manager for System Companion."""
    
    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize database manager.
        
        Args:
            db_path: Path to database file (default: ~/.local/share/system-companion/data.db)
        """
        self.logger = logging.getLogger("system_companion.data.database")
        
        if db_path is None:
            data_dir = Path.home() / ".local" / "share" / "system-companion"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "data.db"
        
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        
        self.logger.info(f"Database initialized: {self.db_path}")
    
    def initialize(self) -> None:
        """Initialize database tables and schema."""
        try:
            with self._get_connection() as conn:
                self._create_tables(conn)
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create database tables."""
        # System metrics table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                network_rx REAL,
                network_tx REAL,
                temperature REAL,
                battery_level REAL
            )
        """)
        
        # Performance history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT
            )
        """)
        
        # Maintenance logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                duration REAL
            )
        """)
        
        # Alerts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_history(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        
        conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context management."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def store_system_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Store system metrics in the database.
        
        Args:
            metrics: Dictionary of metric values
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO system_metrics 
                    (cpu_usage, memory_usage, disk_usage, network_rx, network_tx, temperature, battery_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.get('cpu_usage'),
                    metrics.get('memory_usage'),
                    metrics.get('disk_usage'),
                    metrics.get('network_rx'),
                    metrics.get('network_tx'),
                    metrics.get('temperature'),
                    metrics.get('battery_level')
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store system metrics: {e}")
            raise DatabaseError(f"Failed to store system metrics: {e}")
    
    def get_recent_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent system metrics.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of metric records
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM system_metrics 
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get recent metrics: {e}")
            raise DatabaseError(f"Failed to get recent metrics: {e}")
    
    def store_alert(self, alert_type: str, severity: str, message: str) -> None:
        """
        Store an alert in the database.
        
        Args:
            alert_type: Type of alert
            severity: Alert severity (info, warning, error, critical)
            message: Alert message
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO alerts (alert_type, severity, message)
                    VALUES (?, ?, ?)
                """, (alert_type, severity, message))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to store alert: {e}")
            raise DatabaseError(f"Failed to store alert: {e}")
    
    def get_unacknowledged_alerts(self) -> List[Dict[str, Any]]:
        """
        Get unacknowledged alerts.
        
        Returns:
            List of unacknowledged alerts
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM alerts 
                    WHERE acknowledged = FALSE
                    ORDER BY timestamp DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get unacknowledged alerts: {e}")
            raise DatabaseError(f"Failed to get unacknowledged alerts: {e}")
    
    def acknowledge_alert(self, alert_id: int) -> None:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of the alert to acknowledge
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE alerts 
                    SET acknowledged = TRUE 
                    WHERE id = ?
                """, (alert_id,))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert: {e}")
            raise DatabaseError(f"Failed to acknowledge alert: {e}")
    
    def cleanup_old_data(self, days: int = 30) -> None:
        """
        Clean up old data from the database.
        
        Args:
            days: Number of days to keep
        """
        try:
            with self._get_connection() as conn:
                # Clean up old metrics
                conn.execute("""
                    DELETE FROM system_metrics 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))
                
                # Clean up old performance history
                conn.execute("""
                    DELETE FROM performance_history 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))
                
                # Clean up old maintenance logs
                conn.execute("""
                    DELETE FROM maintenance_logs 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))
                
                # Clean up acknowledged alerts older than 7 days
                conn.execute("""
                    DELETE FROM alerts 
                    WHERE acknowledged = TRUE 
                    AND timestamp < datetime('now', '-7 days')
                """)
                
                conn.commit()
                self.logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            raise DatabaseError(f"Failed to cleanup old data: {e}")
    
    def get_database_size(self) -> int:
        """
        Get database file size in bytes.
        
        Returns:
            Database file size in bytes
        """
        return self.db_path.stat().st_size if self.db_path.exists() else 0 