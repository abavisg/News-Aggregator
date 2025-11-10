"""
Behave environment configuration and hooks for BDD tests.

This module sets up the test environment, manages fixtures,
and provides hooks for before/after scenarios and features.
"""

import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def before_all(context):
    """
    Hook that runs once before all features.

    Setup:
    - Configure logging
    - Initialize test database
    - Setup shared test fixtures
    """
    # Configure logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    context.logger = logging.getLogger('behave')
    context.logger.info("Starting BDD test suite")

    # Store test configuration
    context.test_config = {
        'timeout': 30,
        'max_retries': 3,
        'mock_external_apis': True
    }


def before_feature(context, feature):
    """
    Hook that runs before each feature.

    Args:
        context: Behave context object
        feature: Feature being executed
    """
    context.logger.info(f"Starting feature: {feature.name}")
    context.feature_name = feature.name

    # Feature-specific setup
    if 'slice01' in feature.tags:
        context.logger.info("Setting up Fetcher test environment")
    elif 'slice02' in feature.tags:
        context.logger.info("Setting up Summarizer test environment")
    elif 'slice03' in feature.tags:
        context.logger.info("Setting up Composer test environment")
    elif 'golden' in feature.tags:
        context.logger.info("Setting up E2E Golden Path test environment")


def before_scenario(context, scenario):
    """
    Hook that runs before each scenario.

    Args:
        context: Behave context object
        scenario: Scenario being executed
    """
    context.logger.info(f"Starting scenario: {scenario.name}")

    # Reset scenario-specific state
    context.articles = []
    context.summaries = []
    context.post = None
    context.errors = []
    context.warnings = []

    # Track scenario execution time
    import time
    context.start_time = time.time()


def after_scenario(context, scenario):
    """
    Hook that runs after each scenario.

    Args:
        context: Behave context object
        scenario: Scenario that was executed
    """
    import time
    elapsed = time.time() - context.start_time

    status = "PASSED" if scenario.status == "passed" else "FAILED"
    context.logger.info(
        f"Scenario '{scenario.name}' {status} in {elapsed:.2f}s"
    )

    # Log any errors that occurred
    if context.errors:
        context.logger.error(f"Errors during scenario: {context.errors}")

    # Cleanup scenario resources
    context.articles = []
    context.summaries = []
    context.post = None


def after_feature(context, feature):
    """
    Hook that runs after each feature.

    Args:
        context: Behave context object
        feature: Feature that was executed
    """
    context.logger.info(f"Completed feature: {feature.name}")

    # Feature-specific cleanup
    if 'slice01' in feature.tags:
        context.logger.info("Cleaning up Fetcher test environment")
    elif 'slice02' in feature.tags:
        context.logger.info("Cleaning up Summarizer test environment")
    elif 'slice03' in feature.tags:
        context.logger.info("Cleaning up Composer test environment")


def after_all(context):
    """
    Hook that runs once after all features.

    Cleanup:
    - Close database connections
    - Generate test reports
    - Cleanup temporary files
    """
    context.logger.info("BDD test suite completed")

    # Log summary statistics if available
    if hasattr(context, '_runner'):
        context.logger.info("Test execution complete")
