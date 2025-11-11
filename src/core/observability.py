"""
Observability module for News Aggregator (Slice 06)

Provides:
- MetricsCollector: Track counters, gauges, and histograms
- AlertManager: Evaluate alert conditions and track active alerts
- StructuredLogger: JSON-formatted structured logging
"""

import json
import logging
import logging.handlers
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class MetricsCollector:
    """
    Collects and persists application metrics.
    Supports counters, gauges, and histograms.
    """

    def __init__(self, storage_path: str = "./data/metrics.json"):
        """Initialize metrics collector with persistence"""
        self.storage_path = storage_path
        self.metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()

        # Ensure storage directory exists
        Path(storage_path).parent.mkdir(parents=True, exist_ok=True)

        # Load existing metrics if available
        self.load_from_disk()

    def _make_metric_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key for a metric with labels"""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name

    def increment_counter(
        self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric"""
        with self._lock:
            key = self._make_metric_key(name, labels)

            if key not in self.metrics:
                self.metrics[key] = {
                    "type": "counter",
                    "value": 0,
                    "labels": labels or {},
                    "timestamp": time.time(),
                }

            self.metrics[key]["value"] += value
            self.metrics[key]["timestamp"] = time.time()

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric to a specific value"""
        with self._lock:
            key = self._make_metric_key(name, labels)

            self.metrics[key] = {
                "type": "gauge",
                "value": value,
                "labels": labels or {},
                "timestamp": time.time(),
            }

    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Add an observation to a histogram"""
        with self._lock:
            key = self._make_metric_key(name, labels)

            if key not in self.metrics:
                self.metrics[key] = {
                    "type": "histogram",
                    "observations": [],
                    "labels": labels or {},
                    "timestamp": time.time(),
                }

            self.metrics[key]["observations"].append(value)
            self.metrics[key]["timestamp"] = time.time()

            # Calculate statistics
            observations = self.metrics[key]["observations"]
            self.metrics[key]["count"] = len(observations)
            self.metrics[key]["sum"] = sum(observations)
            self.metrics[key]["avg"] = sum(observations) / len(observations)
            self.metrics[key]["min"] = min(observations)
            self.metrics[key]["max"] = max(observations)

    def get_metric(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get current value of a metric"""
        with self._lock:
            key = self._make_metric_key(name, labels)
            return self.metrics.get(key)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self._lock:
            return dict(self.metrics)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus exposition format"""
        with self._lock:
            lines = []

            for key, metric in self.metrics.items():
                metric_type = metric["type"]
                labels = metric.get("labels", {})

                # Add TYPE comment
                base_name = key.split("{")[0]
                lines.append(f"# TYPE {base_name} {metric_type}")

                # Format metric line
                if labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                    metric_line = f'{base_name}{{{label_str}}}'
                else:
                    metric_line = base_name

                # Add value
                if metric_type == "counter" or metric_type == "gauge":
                    lines.append(f"{metric_line} {metric['value']}")
                elif metric_type == "histogram":
                    lines.append(f"{metric_line}_count {metric['count']}")
                    lines.append(f"{metric_line}_sum {metric['sum']}")

            return "\n".join(lines)

    def save_to_disk(self) -> None:
        """Persist metrics to disk"""
        with self._lock:
            try:
                with open(self.storage_path, "w") as f:
                    json.dump(self.metrics, f, indent=2)
            except Exception as e:
                # Log error but don't crash
                print(f"Error saving metrics: {e}")

    def load_from_disk(self) -> None:
        """Load metrics from disk"""
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r") as f:
                self.metrics = json.load(f)
        except Exception as e:
            # Log error but don't crash
            print(f"Error loading metrics: {e}")
            self.metrics = {}


class AlertManager:
    """
    Evaluates alert conditions and triggers notifications.
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize alert manager with metrics collector"""
        self.metrics_collector = metrics_collector
        self.alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_states: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def register_alert(
        self,
        name: str,
        condition: Callable[[], bool],
        severity: str = "warning",
        message: str = "",
    ) -> None:
        """Register a new alert condition"""
        with self._lock:
            self.alerts[name] = {
                "condition": condition,
                "severity": severity,
                "message": message,
            }

    def evaluate_alerts(self) -> List[Dict[str, Any]]:
        """
        Evaluate all registered alerts and return active ones.

        Returns:
            List of alert dictionaries with name, severity, message, triggered_at, resolved
        """
        with self._lock:
            results = []

            for name, alert_config in self.alerts.items():
                try:
                    # Evaluate condition
                    is_triggered = alert_config["condition"]()

                    # Get or create alert state
                    if name not in self.alert_states:
                        self.alert_states[name] = {
                            "triggered": False,
                            "triggered_at": None,
                            "acknowledged": False,
                        }

                    state = self.alert_states[name]

                    # Update state
                    if is_triggered and not state["triggered"]:
                        # Alert is newly triggered
                        state["triggered"] = True
                        state["triggered_at"] = datetime.now().isoformat()
                        state["acknowledged"] = False

                    elif not is_triggered and state["triggered"]:
                        # Alert is resolved
                        state["triggered"] = False
                        state["triggered_at"] = None
                        state["acknowledged"] = False

                    # Build alert result
                    results.append(
                        {
                            "name": name,
                            "severity": alert_config["severity"],
                            "message": alert_config["message"],
                            "triggered_at": state["triggered_at"],
                            "resolved": not state["triggered"],
                            "acknowledged": state.get("acknowledged", False),
                        }
                    )

                except Exception as e:
                    # Don't let alert evaluation crash the system
                    print(f"Error evaluating alert {name}: {e}")

            return results

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active (not resolved) alerts"""
        all_alerts = self.evaluate_alerts()
        return [alert for alert in all_alerts if not alert["resolved"]]

    def acknowledge_alert(self, name: str) -> None:
        """Acknowledge an alert (mark as seen)"""
        with self._lock:
            if name in self.alert_states:
                self.alert_states[name]["acknowledged"] = True


class StructuredLogger:
    """
    Provides structured JSON logging with context propagation.
    """

    def __init__(
        self,
        name: str,
        log_dir: str = "./logs",
        log_level: str = "INFO",
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 5,
    ):
        """Initialize structured logger with rotation"""
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.context: Dict[str, Any] = {}
        self._lock = threading.Lock()

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Create rotating file handler
            log_file = self.log_dir / f"{name}.log"
            handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )

            # Use minimal formatter (we'll format as JSON ourselves)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """Log a structured message"""
        with self._lock:
            # Build log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": level.upper(),
                "logger": self.name,
                "message": message,
                "context": {**self.context, **(context or {})},
                "error_code": error_code,
                "error_message": error_message,
                "trace_id": trace_id,
            }

            # Convert to JSON
            log_line = json.dumps(log_entry)

            # Log at appropriate level
            log_level = getattr(logging, level.upper())
            self.logger.log(log_level, log_line)

    def debug(self, message: str, **kwargs) -> None:
        """Log DEBUG level message"""
        self.log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log INFO level message"""
        self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log WARNING level message"""
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log ERROR level message"""
        self.log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log CRITICAL level message"""
        self.log("CRITICAL", message, **kwargs)

    def set_context(self, **kwargs) -> None:
        """Set persistent context for subsequent logs"""
        with self._lock:
            self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear persistent context"""
        with self._lock:
            self.context = {}


# Singleton instances
_logger_instances: Dict[str, StructuredLogger] = {}
_metrics_collector: Optional[MetricsCollector] = None
_alert_manager: Optional[AlertManager] = None
_lock = threading.Lock()


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger instance"""
    with _lock:
        if name not in _logger_instances:
            _logger_instances[name] = StructuredLogger(name)
        return _logger_instances[name]


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    with _lock:
        if _metrics_collector is None:
            _metrics_collector = MetricsCollector()
        return _metrics_collector


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance"""
    global _alert_manager
    with _lock:
        if _alert_manager is None:
            collector = get_metrics_collector()
            _alert_manager = AlertManager(collector)
        return _alert_manager
