"""
Unit tests for observability module (Slice 06)

Tests for:
- MetricsCollector: counter, gauge, histogram metrics
- AlertManager: alert registration and evaluation
- StructuredLogger: JSON logging with context
"""

import json
import pytest
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from src.core.observability import (
    MetricsCollector,
    AlertManager,
    StructuredLogger,
    get_logger,
    get_metrics_collector,
    get_alert_manager,
)


class TestMetricsCollector:
    """Test metrics collection functionality"""

    def test_increment_counter_basic(self, tmp_path):
        """Counter increments correctly"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.increment_counter("test_counter", 1)
        metric = collector.get_metric("test_counter")

        assert metric["type"] == "counter"
        assert metric["value"] == 1

    def test_increment_counter_multiple_times(self, tmp_path):
        """Counter increments multiple times"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.increment_counter("test_counter", 5)
        collector.increment_counter("test_counter", 3)

        metric = collector.get_metric("test_counter")
        assert metric["value"] == 8

    def test_increment_counter_with_labels(self, tmp_path):
        """Counter with labels works correctly"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.increment_counter("http_requests", 1, labels={"method": "GET", "status": "200"})
        collector.increment_counter("http_requests", 1, labels={"method": "POST", "status": "201"})

        metric_get = collector.get_metric("http_requests", labels={"method": "GET", "status": "200"})
        metric_post = collector.get_metric("http_requests", labels={"method": "POST", "status": "201"})

        assert metric_get["value"] == 1
        assert metric_post["value"] == 1

    def test_set_gauge_basic(self, tmp_path):
        """Gauge sets to correct value"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.set_gauge("temperature", 23.5)
        metric = collector.get_metric("temperature")

        assert metric["type"] == "gauge"
        assert metric["value"] == 23.5

    def test_set_gauge_updates_value(self, tmp_path):
        """Gauge value updates correctly"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.set_gauge("temperature", 20.0)
        collector.set_gauge("temperature", 25.0)

        metric = collector.get_metric("temperature")
        assert metric["value"] == 25.0

    def test_observe_histogram_basic(self, tmp_path):
        """Histogram records observations"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.observe_histogram("request_duration", 0.123)
        collector.observe_histogram("request_duration", 0.456)
        collector.observe_histogram("request_duration", 0.789)

        metric = collector.get_metric("request_duration")

        assert metric["type"] == "histogram"
        assert len(metric["observations"]) == 3
        assert metric["count"] == 3
        assert "sum" in metric
        assert "avg" in metric

    def test_histogram_statistics(self, tmp_path):
        """Histogram calculates correct statistics"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for val in values:
            collector.observe_histogram("test_histogram", val)

        metric = collector.get_metric("test_histogram")

        assert metric["count"] == 5
        assert metric["sum"] == 15.0
        assert metric["avg"] == 3.0
        assert metric["min"] == 1.0
        assert metric["max"] == 5.0

    def test_get_metric_nonexistent(self, tmp_path):
        """Getting nonexistent metric returns None"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        metric = collector.get_metric("nonexistent_metric")
        assert metric is None

    def test_get_all_metrics(self, tmp_path):
        """All metrics returned in correct format"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.increment_counter("counter1", 10)
        collector.set_gauge("gauge1", 42.0)
        collector.observe_histogram("histogram1", 1.5)

        all_metrics = collector.get_all_metrics()

        assert "counter1" in all_metrics
        assert "gauge1" in all_metrics
        assert "histogram1" in all_metrics
        assert all_metrics["counter1"]["value"] == 10
        assert all_metrics["gauge1"]["value"] == 42.0

    def test_export_prometheus_format(self, tmp_path):
        """Prometheus export format is valid"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.increment_counter("test_counter", 5)
        collector.set_gauge("test_gauge", 123.45)

        prometheus_output = collector.export_prometheus()

        assert "# TYPE test_counter counter" in prometheus_output
        assert "test_counter 5" in prometheus_output
        assert "# TYPE test_gauge gauge" in prometheus_output
        assert "test_gauge 123.45" in prometheus_output

    def test_export_prometheus_with_labels(self, tmp_path):
        """Prometheus export includes labels"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.increment_counter("http_requests", 10, labels={"method": "GET", "status": "200"})

        prometheus_output = collector.export_prometheus()

        assert 'http_requests{method="GET",status="200"} 10' in prometheus_output

    def test_save_and_load_from_disk(self, tmp_path):
        """Metrics persist and load correctly"""
        storage_path = tmp_path / "metrics.json"

        # Create collector and add metrics
        collector1 = MetricsCollector(storage_path=str(storage_path))
        collector1.increment_counter("saved_counter", 42)
        collector1.set_gauge("saved_gauge", 3.14)
        collector1.save_to_disk()

        # Create new collector and load
        collector2 = MetricsCollector(storage_path=str(storage_path))
        collector2.load_from_disk()

        assert collector2.get_metric("saved_counter")["value"] == 42
        assert collector2.get_metric("saved_gauge")["value"] == 3.14

    def test_persistence_nonexistent_file(self, tmp_path):
        """Loading from nonexistent file doesn't crash"""
        storage_path = tmp_path / "nonexistent.json"
        collector = MetricsCollector(storage_path=str(storage_path))

        # Should not raise exception
        collector.load_from_disk()

        # Should have empty metrics
        all_metrics = collector.get_all_metrics()
        assert len(all_metrics) == 0

    def test_concurrent_counter_updates(self, tmp_path):
        """Thread-safe counter updates"""
        import threading

        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        def increment():
            for _ in range(100):
                collector.increment_counter("concurrent_counter", 1)

        threads = [threading.Thread(target=increment) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        metric = collector.get_metric("concurrent_counter")
        assert metric["value"] == 1000

    def test_metric_timestamp(self, tmp_path):
        """Metrics include timestamp"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        before = time.time()
        collector.increment_counter("test_counter", 1)
        after = time.time()

        metric = collector.get_metric("test_counter")
        assert "timestamp" in metric
        assert before <= metric["timestamp"] <= after


class TestAlertManager:
    """Test alert evaluation and management"""

    def test_register_alert(self, tmp_path):
        """Alert registration works"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        alert_manager.register_alert(
            name="test_alert",
            condition=lambda: True,
            severity="warning",
            message="Test alert message"
        )

        # Alert should be registered
        alerts = alert_manager.evaluate_alerts()
        assert len(alerts) > 0
        assert alerts[0]["name"] == "test_alert"

    def test_evaluate_alerts_triggered(self, tmp_path):
        """Alert triggers when condition is true"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        alert_manager.register_alert(
            name="high_value_alert",
            condition=lambda: True,  # Always true
            severity="critical",
            message="Value is too high"
        )

        alerts = alert_manager.evaluate_alerts()

        assert len(alerts) == 1
        assert alerts[0]["name"] == "high_value_alert"
        assert alerts[0]["severity"] == "critical"
        assert alerts[0]["resolved"] is False

    def test_evaluate_alerts_not_triggered(self, tmp_path):
        """Alert doesn't trigger when condition is false"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        alert_manager.register_alert(
            name="low_value_alert",
            condition=lambda: False,  # Always false
            severity="warning",
            message="Value is too low"
        )

        alerts = alert_manager.evaluate_alerts()

        # Should be empty or alert should be resolved
        active_alerts = [a for a in alerts if not a["resolved"]]
        assert len(active_alerts) == 0

    def test_get_active_alerts(self, tmp_path):
        """Active alerts returned correctly"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        alert_manager.register_alert(
            name="active_alert",
            condition=lambda: True,
            severity="warning",
            message="This is active"
        )

        alert_manager.register_alert(
            name="inactive_alert",
            condition=lambda: False,
            severity="warning",
            message="This is inactive"
        )

        alert_manager.evaluate_alerts()
        active = alert_manager.get_active_alerts()

        assert len(active) == 1
        assert active[0]["name"] == "active_alert"

    def test_acknowledge_alert(self, tmp_path):
        """Alert acknowledgment works"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        alert_manager.register_alert(
            name="ack_alert",
            condition=lambda: True,
            severity="warning",
            message="Acknowledge me"
        )

        alert_manager.evaluate_alerts()
        alert_manager.acknowledge_alert("ack_alert")

        # Alert should be marked as acknowledged
        active = alert_manager.get_active_alerts()
        ack_alert = [a for a in active if a["name"] == "ack_alert"]

        if ack_alert:
            assert ack_alert[0].get("acknowledged") is True

    def test_alert_severity_levels(self, tmp_path):
        """Alert severity levels work correctly"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        alert_manager.register_alert(
            name="critical_alert",
            condition=lambda: True,
            severity="critical",
            message="Critical"
        )

        alert_manager.register_alert(
            name="warning_alert",
            condition=lambda: True,
            severity="warning",
            message="Warning"
        )

        alerts = alert_manager.evaluate_alerts()

        critical = [a for a in alerts if a["name"] == "critical_alert"]
        warning = [a for a in alerts if a["name"] == "warning_alert"]

        assert critical[0]["severity"] == "critical"
        assert warning[0]["severity"] == "warning"

    def test_alert_resolution(self, tmp_path):
        """Alerts auto-resolve when condition clears"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        trigger = {"value": True}

        alert_manager.register_alert(
            name="toggle_alert",
            condition=lambda: trigger["value"],
            severity="warning",
            message="Toggle alert"
        )

        # First evaluation - should trigger
        alert_manager.evaluate_alerts()
        active1 = alert_manager.get_active_alerts()
        assert len(active1) == 1

        # Change condition
        trigger["value"] = False

        # Second evaluation - should resolve
        alert_manager.evaluate_alerts()
        active2 = alert_manager.get_active_alerts()
        assert len(active2) == 0

    def test_alert_condition_with_metrics(self, tmp_path):
        """Alerts can evaluate based on metrics"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        collector.increment_counter("error_count", 0)

        alert_manager.register_alert(
            name="high_error_rate",
            condition=lambda: collector.get_metric("error_count")["value"] > 5,
            severity="critical",
            message="Error rate too high"
        )

        # Initially no alert
        alert_manager.evaluate_alerts()
        assert len(alert_manager.get_active_alerts()) == 0

        # Increase errors
        collector.increment_counter("error_count", 10)

        # Now alert should trigger
        alert_manager.evaluate_alerts()
        assert len(alert_manager.get_active_alerts()) == 1


class TestStructuredLogger:
    """Test structured logging functionality"""

    def test_log_with_context(self, tmp_path):
        """Logging with context works"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger", log_dir=str(log_dir))

        logger.info("Test message", context={"key": "value"})

        # Check log file was created
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0

        # Check log content
        with open(log_files[0]) as f:
            log_line = f.readline()
            log_data = json.loads(log_line)

            assert log_data["message"] == "Test message"
            assert log_data["context"]["key"] == "value"

    def test_log_levels(self, tmp_path):
        """All log levels work correctly"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger_levels", log_dir=str(log_dir), log_level="DEBUG")

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # Flush the log handlers to ensure logs are written
        for handler in logger.logger.handlers:
            handler.flush()

        # Check all messages were logged
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0, f"No log files found in {log_dir}"

        with open(log_files[0]) as f:
            lines = f.readlines()
            assert len(lines) == 5

            levels = [json.loads(line)["level"] for line in lines]
            assert "DEBUG" in levels
            assert "INFO" in levels
            assert "WARNING" in levels
            assert "ERROR" in levels
            assert "CRITICAL" in levels

    def test_persistent_context(self, tmp_path):
        """Context persistence works"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger_context", log_dir=str(log_dir))

        logger.set_context(request_id="abc123", user_id="user456")
        logger.info("First message")
        logger.info("Second message")

        # Flush the log handlers
        for handler in logger.logger.handlers:
            handler.flush()

        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0, f"No log files found in {log_dir}"

        with open(log_files[0]) as f:
            lines = f.readlines()

            log1 = json.loads(lines[0])
            log2 = json.loads(lines[1])

            assert log1["context"]["request_id"] == "abc123"
            assert log2["context"]["request_id"] == "abc123"

    def test_clear_context(self, tmp_path):
        """Context clearing works"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger_clear", log_dir=str(log_dir))

        logger.set_context(key="value")
        logger.info("With context")

        logger.clear_context()
        logger.info("Without context")

        # Flush the log handlers
        for handler in logger.logger.handlers:
            handler.flush()

        log_files = list(log_dir.glob("*.log"))
        with open(log_files[0]) as f:
            lines = f.readlines()

            log1 = json.loads(lines[0])
            log2 = json.loads(lines[1])

            assert "key" in log1["context"]
            assert "key" not in log2["context"]

    def test_json_format(self, tmp_path):
        """Log output is valid JSON"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger_json", log_dir=str(log_dir))

        logger.info(
            "Test message",
            context={"week_key": "2025.W45", "job_type": "preview"},
            error_code="TEST_ERROR",
            error_message="Test error",
            trace_id="trace123"
        )

        # Flush the log handlers
        for handler in logger.logger.handlers:
            handler.flush()

        log_files = list(log_dir.glob("*.log"))
        with open(log_files[0]) as f:
            log_line = f.readline()
            log_data = json.loads(log_line)  # Should not raise

            assert log_data["message"] == "Test message"
            assert log_data["level"] == "INFO"
            assert log_data["logger"] == "test_logger_json"
            assert log_data["context"]["week_key"] == "2025.W45"
            assert log_data["error_code"] == "TEST_ERROR"
            assert log_data["trace_id"] == "trace123"

    def test_trace_id_propagation(self, tmp_path):
        """Trace ID propagation works"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger_trace", log_dir=str(log_dir))

        logger.info("Message 1", trace_id="trace-abc-123")
        logger.info("Message 2", trace_id="trace-abc-123")

        # Flush the log handlers
        for handler in logger.logger.handlers:
            handler.flush()

        log_files = list(log_dir.glob("*.log"))
        with open(log_files[0]) as f:
            lines = f.readlines()

            log1 = json.loads(lines[0])
            log2 = json.loads(lines[1])

            assert log1["trace_id"] == "trace-abc-123"
            assert log2["trace_id"] == "trace-abc-123"

    def test_error_logging(self, tmp_path):
        """Error logging includes error details"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger_error", log_dir=str(log_dir))

        logger.error(
            "Operation failed",
            error_code="FETCH_ERROR",
            error_message="Connection timeout",
            context={"source": "techcrunch.com"}
        )

        # Flush the log handlers
        for handler in logger.logger.handlers:
            handler.flush()

        log_files = list(log_dir.glob("*.log"))
        with open(log_files[0]) as f:
            log_data = json.loads(f.readline())

            assert log_data["level"] == "ERROR"
            assert log_data["error_code"] == "FETCH_ERROR"
            assert log_data["error_message"] == "Connection timeout"

    def test_log_filtering_by_level(self, tmp_path):
        """Log level filtering works"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger_filter", log_dir=str(log_dir), log_level="WARNING")

        logger.debug("Debug message")  # Should not be logged
        logger.info("Info message")    # Should not be logged
        logger.warning("Warning message")  # Should be logged
        logger.error("Error message")      # Should be logged

        # Flush the log handlers
        for handler in logger.logger.handlers:
            handler.flush()

        log_files = list(log_dir.glob("*.log"))
        with open(log_files[0]) as f:
            lines = f.readlines()
            assert len(lines) == 2  # Only warning and error


class TestSingletonGetters:
    """Test singleton pattern for observability instances"""

    def test_get_logger_singleton(self):
        """get_logger returns singleton instances"""
        logger1 = get_logger("test.module")
        logger2 = get_logger("test.module")

        assert logger1 is logger2

    def test_get_metrics_collector_singleton(self):
        """get_metrics_collector returns singleton instance"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2

    def test_get_alert_manager_singleton(self):
        """get_alert_manager returns singleton instance"""
        manager1 = get_alert_manager()
        manager2 = get_alert_manager()

        assert manager1 is manager2


class TestIntegration:
    """Test observability integration"""

    def test_metrics_and_alerts_integration(self, tmp_path):
        """Alerts can trigger based on metrics"""
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        # Register alert that triggers when counter > 10
        alert_manager.register_alert(
            name="high_count_alert",
            condition=lambda: (
                collector.get_metric("event_count") and
                collector.get_metric("event_count")["value"] > 10
            ),
            severity="warning",
            message="Event count exceeded threshold"
        )

        # Initially no alert
        collector.increment_counter("event_count", 5)
        alert_manager.evaluate_alerts()
        assert len(alert_manager.get_active_alerts()) == 0

        # Trigger alert
        collector.increment_counter("event_count", 10)
        alert_manager.evaluate_alerts()
        assert len(alert_manager.get_active_alerts()) == 1

    def test_logger_with_metrics(self, tmp_path):
        """Logger can log metrics values"""
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="test_logger_metrics", log_dir=str(log_dir))
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))

        collector.increment_counter("requests_total", 100)
        metric = collector.get_metric("requests_total")

        logger.info(
            "Metrics report",
            context={"metric_name": "requests_total", "metric_value": metric["value"]}
        )

        # Flush the log handlers
        for handler in logger.logger.handlers:
            handler.flush()

        log_files = list(log_dir.glob("*.log"))
        with open(log_files[0]) as f:
            log_data = json.loads(f.readline())
            assert log_data["context"]["metric_value"] == 100

    def test_end_to_end_observability(self, tmp_path):
        """Full observability pipeline works"""
        # Setup all components
        log_dir = tmp_path / "logs"
        logger = StructuredLogger(name="app", log_dir=str(log_dir))
        collector = MetricsCollector(storage_path=str(tmp_path / "metrics.json"))
        alert_manager = AlertManager(collector)

        # Register alert
        alert_manager.register_alert(
            name="test_alert",
            condition=lambda: (
                collector.get_metric("errors") and
                collector.get_metric("errors")["value"] > 5
            ),
            severity="critical",
            message="Too many errors"
        )

        # Simulate operation
        logger.info("Starting operation", context={"operation": "test"})
        collector.increment_counter("operations", 1)

        # Simulate error
        logger.error("Operation failed", error_code="TEST_ERROR")
        collector.increment_counter("errors", 10)

        # Flush the log handlers
        for handler in logger.logger.handlers:
            handler.flush()

        # Evaluate alerts
        alert_manager.evaluate_alerts()
        alerts = alert_manager.get_active_alerts()

        # Verify everything works
        assert len(alerts) == 1
        assert alerts[0]["name"] == "test_alert"
        assert collector.get_metric("operations")["value"] == 1
        assert collector.get_metric("errors")["value"] == 10

        # Verify logs
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0
