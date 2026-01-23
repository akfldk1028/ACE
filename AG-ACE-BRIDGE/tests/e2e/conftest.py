"""
Playwright E2E Test Configuration

This conftest.py provides fixtures for Playwright E2E tests.
"""

import pytest
from playwright.sync_api import Playwright, Browser, BrowserContext, Page


@pytest.fixture(scope="session")
def playwright_instance(playwright: Playwright) -> Playwright:
    """Provide playwright instance"""
    return playwright


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Browser:
    """Launch browser for the test session"""
    browser = playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> BrowserContext:
    """Create a new browser context for each test"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    """Create a new page for each test"""
    page = context.new_page()
    page.set_default_timeout(30000)  # 30 seconds
    yield page
    page.close()


# Configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "dashboard: marks tests for dashboard"
    )
    config.addinivalue_line(
        "markers", "pipeline: marks tests for pipeline"
    )
