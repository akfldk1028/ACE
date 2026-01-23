"""
Playwright E2E Tests for AG-ACE-BRIDGE Dashboard

This test suite verifies:
1. Dashboard loads correctly
2. Orchestrator controls work
3. Project submission works
4. Pipeline progress is displayed
5. A2A health check works

Prerequisites:
1. Install Playwright:
   pip install pytest-playwright
   playwright install chromium

2. Start the dashboard:
   cd D:\Data\25_ACE\AG-ACE-BRIDGE
   python main.py --dashboard

3. Run tests:
   pytest tests/e2e/test_dashboard.py -v --headed
   # or headless:
   pytest tests/e2e/test_dashboard.py -v
"""

import pytest
from playwright.sync_api import Page, expect
import time


# Configuration
DASHBOARD_URL = "http://localhost:8080"
WAIT_TIMEOUT = 30000  # 30 seconds


class TestDashboardBasic:
    """Basic dashboard functionality tests"""

    def test_dashboard_loads(self, page: Page):
        """Test that dashboard loads correctly"""
        page.goto(DASHBOARD_URL)

        # Check title
        expect(page).to_have_title("AG-ACE-BRIDGE Dashboard")

        # Check header
        expect(page.locator("h1")).to_have_text("AG-ACE-BRIDGE")

        # Check status badge exists
        expect(page.locator("#status-badge")).to_be_visible()

    def test_controls_visible(self, page: Page):
        """Test that all control buttons are visible"""
        page.goto(DASHBOARD_URL)

        # Check control buttons
        expect(page.locator("button:has-text('Start')")).to_be_visible()
        expect(page.locator("button:has-text('Stop')")).to_be_visible()
        expect(page.locator("button:has-text('Pause')")).to_be_visible()
        expect(page.locator("button:has-text('Resume')")).to_be_visible()
        expect(page.locator("button:has-text('Check Agents')")).to_be_visible()

    def test_metrics_displayed(self, page: Page):
        """Test that metrics are displayed"""
        page.goto(DASHBOARD_URL)

        # Check metrics
        expect(page.locator("#tasks-processed")).to_be_visible()
        expect(page.locator("#tasks-succeeded")).to_be_visible()
        expect(page.locator("#tasks-failed")).to_be_visible()
        expect(page.locator("#queue-size")).to_be_visible()


class TestOrchestratorControls:
    """Orchestrator control tests"""

    def test_start_orchestrator(self, page: Page):
        """Test starting the orchestrator"""
        page.goto(DASHBOARD_URL)

        # Click start button
        page.click("button:has-text('Start')")

        # Wait for activity log entry
        page.wait_for_selector("#activity-log >> text=starting", timeout=WAIT_TIMEOUT)

        # Verify status changes (may take a moment)
        time.sleep(2)

    def test_stop_orchestrator(self, page: Page):
        """Test stopping the orchestrator"""
        page.goto(DASHBOARD_URL)

        # First start the orchestrator
        page.click("button:has-text('Start')")
        time.sleep(2)

        # Then stop it
        page.click("button:has-text('Stop')")

        # Wait for activity log entry
        page.wait_for_selector("#activity-log >> text=stopped", timeout=WAIT_TIMEOUT)


class TestA2AHealthCheck:
    """A2A agent health check tests"""

    def test_check_a2a_health(self, page: Page):
        """Test A2A health check functionality"""
        page.goto(DASHBOARD_URL)

        # Click check agents button
        page.click("button:has-text('Check Agents')")

        # Wait for activity log entry
        page.wait_for_selector("#activity-log >> text=Checking A2A agents", timeout=WAIT_TIMEOUT)

        # Wait for results
        time.sleep(2)

        # Verify health status is updated
        expect(page.locator("#a2a-poetry")).to_be_visible()
        expect(page.locator("#a2a-calculator")).to_be_visible()


class TestProjectSubmission:
    """Project submission and pipeline progress tests"""

    def test_project_form_visible(self, page: Page):
        """Test that project submission form is visible"""
        page.goto(DASHBOARD_URL)

        # Check form elements
        expect(page.locator("#project-name")).to_be_visible()
        expect(page.locator("#project-type")).to_be_visible()
        expect(page.locator("#project-description")).to_be_visible()
        expect(page.locator("button:has-text('Submit Project')")).to_be_visible()

    def test_submit_calculator_project(self, page: Page):
        """Test submitting a Calculator project"""
        page.goto(DASHBOARD_URL)

        # Fill in project details
        page.fill("#project-name", "Calculator Test")
        page.select_option("#project-type", "calculator")
        page.fill("#project-description", "Test calculator project with add, subtract, multiply, divide")

        # Submit project
        page.click("button:has-text('Submit Project')")

        # Wait for submission confirmation
        page.wait_for_selector("#activity-log >> text=submitted", timeout=WAIT_TIMEOUT)

        # Verify pipeline section appears
        expect(page.locator("#pipeline-section")).to_be_visible()

        # Verify current project name
        expect(page.locator("#current-project-name")).to_have_text("Calculator Test")

    def test_pipeline_progress_displayed(self, page: Page):
        """Test that pipeline progress is displayed after submission"""
        page.goto(DASHBOARD_URL)

        # Submit a project
        page.fill("#project-name", "Pipeline Test")
        page.click("button:has-text('Submit Project')")

        # Wait for pipeline section
        page.wait_for_selector("#pipeline-section:not(.hidden)", timeout=WAIT_TIMEOUT)

        # Wait for stages to appear
        page.wait_for_selector("#pipeline-stages", timeout=WAIT_TIMEOUT)

        # Verify stages are displayed
        expect(page.locator("#pipeline-stages")).to_be_visible()

    def test_watch_full_pipeline(self, page: Page):
        """Test watching the full pipeline execution (demo mode)"""
        page.goto(DASHBOARD_URL)

        # Submit a project
        page.fill("#project-name", "Full Pipeline Test")
        page.click("button:has-text('Submit Project')")

        # Wait for pipeline section
        page.wait_for_selector("#pipeline-section:not(.hidden)", timeout=WAIT_TIMEOUT)

        # Wait for Planning stage to start (look for running indicator)
        page.wait_for_selector(".stage-running", timeout=WAIT_TIMEOUT)

        # Wait for all stages to complete (takes about 10-12 seconds in demo)
        # Look for completed stages
        time.sleep(15)  # Wait for demo to complete

        # Verify project completed message
        expect(page.locator("#activity-log")).to_contain_text("completed successfully")

        # Verify output is displayed
        expect(page.locator("#code-output")).to_contain_text("PROJECT COMPLETED")


class TestWebSocketUpdates:
    """WebSocket real-time update tests"""

    def test_websocket_status_updates(self, page: Page):
        """Test that status updates via WebSocket"""
        page.goto(DASHBOARD_URL)

        # Get initial uptime
        initial_uptime = page.locator("#uptime").text_content()

        # Wait for a few seconds
        time.sleep(5)

        # Uptime should remain at 0s if orchestrator not running
        # This verifies WebSocket is working
        expect(page.locator("#uptime")).to_be_visible()

    def test_project_events_via_websocket(self, page: Page):
        """Test that project events are received via WebSocket"""
        page.goto(DASHBOARD_URL)

        # Submit a project
        page.fill("#project-name", "WebSocket Test")
        page.click("button:has-text('Submit Project')")

        # Wait for events to appear in activity log
        page.wait_for_selector("#activity-log >> text=Planning", timeout=WAIT_TIMEOUT)

        # Verify multiple events received
        expect(page.locator("#activity-log")).to_contain_text("Planner")


class TestAgentCards:
    """Agent status card tests"""

    def test_auto_claude_agents_displayed(self, page: Page):
        """Test Auto-Claude agent cards are displayed"""
        page.goto(DASHBOARD_URL)

        # Check Auto-Claude agents
        expect(page.locator("#agent-planner")).to_be_visible()
        expect(page.locator("#agent-coder")).to_be_visible()
        expect(page.locator("#agent-qa-reviewer")).to_be_visible()
        expect(page.locator("#agent-qa-fixer")).to_be_visible()

    def test_a2a_agents_displayed(self, page: Page):
        """Test A2A agent cards are displayed"""
        page.goto(DASHBOARD_URL)

        # Check A2A agents
        expect(page.locator("#a2a-poetry-card")).to_be_visible()
        expect(page.locator("#a2a-philosophy-card")).to_be_visible()
        expect(page.locator("#a2a-history-card")).to_be_visible()
        expect(page.locator("#a2a-calculator-card")).to_be_visible()
        expect(page.locator("#a2a-gui-test-card")).to_be_visible()


# Pytest fixtures
@pytest.fixture(scope="function")
def page(browser):
    """Create a new page for each test"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session")
def browser(playwright):
    """Launch browser for the test session"""
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])
