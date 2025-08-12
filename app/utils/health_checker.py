# app/utils/health_checker.py
import psutil
import time
import threading
import logging
import os
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthChecker:
    """System health monitoring utility"""
    
    def __init__(self):
        self.start_time = time.time()
        self.monitoring = False
        self.monitor_thread = None
        self.health_data = {}
        self.lock = threading.Lock()
    
    def start_monitoring(self):
        """Start background health monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop background health monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Health monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            with self.lock:
                self.health_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "uptime": time.time() - self.start_time,
                    "cpu": {
                        "percent": cpu_percent,
                        "count": psutil.cpu_count()
                    },
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "process_rss": process_memory.rss,
                        "process_vms": process_memory.vms
                    },
                    "disk": {
                        "total": disk.total,
                        "free": disk.free,
                        "percent": disk.percent
                    },
                    "system": {
                        "boot_time": psutil.boot_time(),
                        "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
                    }
                }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        with self.lock:
            return self.health_data.copy()
    
    def is_healthy(self) -> bool:
        """Check if system is healthy based on thresholds"""
        try:
            with self.lock:
                if not self.health_data:
                    return False
                
                # Check memory usage
                memory_percent = self.health_data.get("memory", {}).get("percent", 0)
                if memory_percent > 90:
                    return False
                
                # Check disk usage
                disk_percent = self.health_data.get("disk", {}).get("percent", 0)
                if disk_percent > 95:
                    return False
                
                # Check CPU usage
                cpu_percent = self.health_data.get("cpu", {}).get("percent", 0)
                if cpu_percent > 95:
                    return False
                
                return True
        except Exception:
            return False