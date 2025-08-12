# app/middleware/metrics.py
import time
import threading
from typing import Dict, Any, List
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect and store API performance metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.start_time = time.time()
        self.lock = threading.Lock()
        
        # Metrics storage
        self.request_history = deque()
        self.total_requests = 0
        self.total_errors = 0
        self.response_times = deque()
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "errors": 0
        })
        self.model_usage = defaultdict(int)
        self.status_codes = defaultdict(int)
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def record_request(self, endpoint: str, method: str, status_code: int, 
                      processing_time: float, model_name: str = None):
        """Record a completed request"""
        with self.lock:
            timestamp = datetime.utcnow()
            
            # Store request record
            request_record = {
                "timestamp": timestamp,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "processing_time": processing_time,
                "model_name": model_name
            }
            self.request_history.append(request_record)
            
            # Update counters
            self.total_requests += 1
            if status_code >= 400:
                self.total_errors += 1
                self.endpoint_stats[endpoint]["errors"] += 1
            
            # Update endpoint stats
            self.endpoint_stats[endpoint]["count"] += 1
            self.endpoint_stats[endpoint]["total_time"] += processing_time
            
            # Update model usage
            if model_name:
                self.model_usage[model_name] += 1
            
            # Update status codes
            self.status_codes[status_code] += 1
            
            # Store response time
            self.response_times.append(processing_time)
            if len(self.response_times) > 1000:  # Keep last 1000 response times
                self.response_times.popleft()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        with self.lock:
            # Calculate average response time
            avg_response_time = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0
            )
            
            # Calculate error rate
            error_rate = (
                (self.total_errors / self.total_requests * 100)
                if self.total_requests > 0 else 0
            )
            
            # Get recent request rate (last hour)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            recent_requests = [
                r for r in self.request_history
                if r["timestamp"] > cutoff_time
            ]
            requests_per_hour = len(recent_requests)
            
            # Endpoint performance
            endpoint_performance = {}
            for endpoint, stats in self.endpoint_stats.items():
                avg_time = (
                    stats["total_time"] / stats["count"]
                    if stats["count"] > 0 else 0
                )
                error_rate_endpoint = (
                    stats["errors"] / stats["count"] * 100
                    if stats["count"] > 0 else 0
                )
                endpoint_performance[endpoint] = {
                    "total_requests": stats["count"],
                    "average_response_time": avg_time,
                    "error_rate": error_rate_endpoint,
                    "total_errors": stats["errors"]
                }
            
            return {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate": error_rate,
                "average_response_time": avg_response_time,
                "requests_per_hour": requests_per_hour,
                "uptime": time.time() - self.start_time,
                "model_usage": dict(self.model_usage),
                "status_codes": dict(self.status_codes),
                "endpoint_performance": endpoint_performance,
                "response_time_percentiles": self._calculate_percentiles(),
                "recent_activity": self._get_recent_activity()
            }
    
    def _calculate_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles"""
        if not self.response_times:
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
        
        sorted_times = sorted(self.response_times)
        n = len(sorted_times)
        
        return {
            "p50": sorted_times[int(n * 0.5)],
            "p90": sorted_times[int(n * 0.9)],
            "p95": sorted_times[int(n * 0.95)],
            "p99": sorted_times[int(n * 0.99)]
        }
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity summary"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        recent_requests = [
            {
                "timestamp": r["timestamp"].isoformat(),
                "endpoint": r["endpoint"],
                "status_code": r["status_code"],
                "processing_time": r["processing_time"],
                "model_name": r["model_name"]
            }
            for r in self.request_history
            if r["timestamp"] > cutoff_time
        ]
        return recent_requests[-10:]  # Last 10 requests
    
    def _cleanup_loop(self):
        """Background cleanup of old metrics"""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                self._cleanup_old_data()
            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
    
    def _cleanup_old_data(self):
        """Remove old data beyond retention period"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
            
            # Clean request history
            while (self.request_history and 
                   self.request_history[0]["timestamp"] < cutoff_time):
                self.request_history.popleft()
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        with self.lock:
            self.request_history.clear()
            self.total_requests = 0
            self.total_errors = 0
            self.response_times.clear()
            self.endpoint_stats.clear()
            self.model_usage.clear()
            self.status_codes.clear()
            self.start_time = time.time()
            logger.info("Metrics reset completed")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status based on metrics"""
        with self.lock:
            # Check error rate in last hour
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            recent_requests = [
                r for r in self.request_history
                if r["timestamp"] > cutoff_time
            ]
            recent_errors = [
                r for r in recent_requests
                if r["status_code"] >= 400
            ]
            
            recent_error_rate = (
                len(recent_errors) / len(recent_requests) * 100
                if recent_requests else 0
            )
            
            # Check average response time
            avg_response_time = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0
            )
            
            # Determine health status
            is_healthy = (
                recent_error_rate < 10 and  # Less than 10% error rate
                avg_response_time < 30      # Less than 30s average response time
            )
            
            return {
                "is_healthy": is_healthy,
                "recent_error_rate": recent_error_rate,
                "average_response_time": avg_response_time,
                "total_requests": len(recent_requests),
                "uptime_hours": (time.time() - self.start_time) / 3600
            }