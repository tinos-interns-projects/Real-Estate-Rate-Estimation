"""
Performance Monitoring and Optimization
"""

import time
import psutil
import threading
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json

class PerformanceMonitor:
    """Monitor application performance and system resources"""
    
    def __init__(self):
        self.request_times = defaultdict(deque)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0
        })
        self.system_metrics = deque(maxlen=100)  # Keep last 100 measurements
        self.alerts = []
        self.monitoring_active = True
        
        # Start background monitoring
        self.start_system_monitoring()
    
    def start_system_monitoring(self):
        """Start background system monitoring"""
        def monitor_system():
            while self.monitoring_active:
                try:
                    # Collect system metrics
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    # Network stats (if available)
                    try:
                        network = psutil.net_io_counters()
                        network_stats = {
                            'bytes_sent': network.bytes_sent,
                            'bytes_recv': network.bytes_recv
                        }
                    except:
                        network_stats = {'bytes_sent': 0, 'bytes_recv': 0}
                    
                    metrics = {
                        'timestamp': datetime.now().isoformat(),
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_used': memory.used,
                        'memory_available': memory.available,
                        'disk_percent': disk.percent,
                        'disk_used': disk.used,
                        'disk_free': disk.free,
                        'network': network_stats
                    }
                    
                    self.system_metrics.append(metrics)
                    
                    # Check for alerts
                    self.check_performance_alerts(metrics)
                    
                except Exception as e:
                    print(f"Error in system monitoring: {e}")
                
                time.sleep(30)  # Monitor every 30 seconds
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def track_request(self, endpoint, duration, success=True):
        """Track request performance"""
        stats = self.endpoint_stats[endpoint]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        
        if not success:
            stats['errors'] += 1
        
        # Keep recent request times for trend analysis
        self.request_times[endpoint].append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'success': success
        })
        
        # Keep only last 100 requests per endpoint
        if len(self.request_times[endpoint]) > 100:
            self.request_times[endpoint].popleft()
    
    def check_performance_alerts(self, metrics):
        """Check for performance issues and create alerts"""
        alerts = []
        
        # CPU usage alert
        if metrics['cpu_percent'] > 80:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning' if metrics['cpu_percent'] < 90 else 'critical',
                'message': f"High CPU usage: {metrics['cpu_percent']:.1f}%",
                'timestamp': metrics['timestamp']
            })
        
        # Memory usage alert
        if metrics['memory_percent'] > 85:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning' if metrics['memory_percent'] < 95 else 'critical',
                'message': f"High memory usage: {metrics['memory_percent']:.1f}%",
                'timestamp': metrics['timestamp']
            })
        
        # Disk usage alert
        if metrics['disk_percent'] > 90:
            alerts.append({
                'type': 'disk_high',
                'severity': 'warning' if metrics['disk_percent'] < 95 else 'critical',
                'message': f"High disk usage: {metrics['disk_percent']:.1f}%",
                'timestamp': metrics['timestamp']
            })
        
        # Add alerts to the list
        for alert in alerts:
            self.alerts.append(alert)
            print(f"PERFORMANCE ALERT: {alert['message']}")
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
    
    def get_endpoint_performance(self, endpoint=None):
        """Get performance statistics for endpoints"""
        if endpoint:
            return self.endpoint_stats.get(endpoint, {})
        return dict(self.endpoint_stats)
    
    def get_slow_endpoints(self, threshold_ms=1000):
        """Get endpoints that are performing slowly"""
        slow_endpoints = []
        for endpoint, stats in self.endpoint_stats.items():
            if stats['avg_time'] > threshold_ms:
                slow_endpoints.append({
                    'endpoint': endpoint,
                    'avg_time': stats['avg_time'],
                    'max_time': stats['max_time'],
                    'count': stats['count'],
                    'error_rate': (stats['errors'] / stats['count']) * 100 if stats['count'] > 0 else 0
                })
        
        return sorted(slow_endpoints, key=lambda x: x['avg_time'], reverse=True)
    
    def get_system_health(self):
        """Get current system health status"""
        if not self.system_metrics:
            return {'status': 'unknown', 'message': 'No metrics available'}
        
        latest = self.system_metrics[-1]
        
        # Determine overall health
        issues = []
        if latest['cpu_percent'] > 80:
            issues.append(f"High CPU: {latest['cpu_percent']:.1f}%")
        if latest['memory_percent'] > 85:
            issues.append(f"High Memory: {latest['memory_percent']:.1f}%")
        if latest['disk_percent'] > 90:
            issues.append(f"High Disk: {latest['disk_percent']:.1f}%")
        
        if not issues:
            status = 'healthy'
            message = 'All systems operating normally'
        elif len(issues) == 1:
            status = 'warning'
            message = issues[0]
        else:
            status = 'critical'
            message = f"Multiple issues: {', '.join(issues)}"
        
        return {
            'status': status,
            'message': message,
            'metrics': latest,
            'alerts': len(self.alerts)
        }
    
    def get_performance_trends(self, hours=24):
        """Get performance trends over time"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent metrics
        recent_metrics = [
            m for m in self.system_metrics
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate trends
        cpu_values = [m['cpu_percent'] for m in recent_metrics]
        memory_values = [m['memory_percent'] for m in recent_metrics]
        
        return {
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values),
                'current': cpu_values[-1] if cpu_values else 0
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values),
                'min': min(memory_values),
                'max': max(memory_values),
                'current': memory_values[-1] if memory_values else 0
            },
            'data_points': len(recent_metrics)
        }
    
    def export_performance_data(self):
        """Export performance data for analysis"""
        return {
            'endpoint_stats': dict(self.endpoint_stats),
            'system_metrics': list(self.system_metrics),
            'alerts': self.alerts,
            'exported_at': datetime.now().isoformat()
        }
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance(endpoint_name=None):
    """Decorator to monitor endpoint performance"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                endpoint = endpoint_name or f.__name__
                performance_monitor.track_request(endpoint, duration, success)
        
        return decorated_function
    return decorator

def get_performance_summary():
    """Get a summary of application performance"""
    return {
        'system_health': performance_monitor.get_system_health(),
        'slow_endpoints': performance_monitor.get_slow_endpoints(),
        'performance_trends': performance_monitor.get_performance_trends(),
        'total_endpoints': len(performance_monitor.endpoint_stats),
        'total_requests': sum(stats['count'] for stats in performance_monitor.endpoint_stats.values()),
        'avg_response_time': sum(stats['avg_time'] for stats in performance_monitor.endpoint_stats.values()) / len(performance_monitor.endpoint_stats) if performance_monitor.endpoint_stats else 0
    }
