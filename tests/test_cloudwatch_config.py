"""Validation tests for CloudWatch Dashboard and Alarm configuration in template.yaml."""

import json
import yaml
import pytest


class CFLoader(yaml.SafeLoader):
    """YAML Loader that ignores CloudFormation custom tags for schema inspection."""
    pass


for tag in ["!Sub", "!Ref", "!GetAtt", "!Condition", "!FindInMap", "!Join", "!Select", "!Split"]:
    CFLoader.add_constructor(tag, lambda loader, node: node.value)


@pytest.fixture
def sam_template():
    """Load and parse template.yaml."""
    with open("template.yaml") as f:
        return yaml.load(f, Loader=CFLoader)


def test_cloudwatch_dashboard_exists(sam_template):
    """Verify that CloudWatch Dashboard resource is properly defined."""
    resources = sam_template["Resources"]
    assert "StreakMonitoringDashboard" in resources
    dashboard = resources["StreakMonitoringDashboard"]
    assert dashboard["Type"] == "AWS::CloudWatch::Dashboard"


def test_cloudwatch_dashboard_body_structure(sam_template):
    """Verify that CloudWatch DashboardBody contains valid widgets for all metrics."""
    dashboard = sam_template["Resources"]["StreakMonitoringDashboard"]
    raw_body = dashboard["Properties"]["DashboardBody"]

    # In template.yaml, !Sub strings might have variable placeholders like ${LogSolveFunction}
    # We replace them with dummy values to validate JSON parseability
    import re
    cleaned_body = re.sub(r"\$\{[^}]+\}", "mock-value", raw_body)

    body = json.loads(cleaned_body)
    assert "widgets" in body
    widgets = body["widgets"]
    assert len(widgets) == 4

    titles = [w["properties"]["title"] for w in widgets]
    assert any("Invocations" in t for t in titles)
    assert any("Errors" in t for t in titles)
    assert any("Duration" in t or "Latency" in t for t in titles)
    assert any("DynamoDB" in t or "Capacity" in t for t in titles)


def test_cloudwatch_alarm_configuration(sam_template):
    """Verify that CloudWatch Metric Alarm triggers on Lambda errors and targets SNS."""
    resources = sam_template["Resources"]
    assert "StreakLambdaErrorsAlarm" in resources
    alarm = resources["StreakLambdaErrorsAlarm"]
    assert alarm["Type"] == "AWS::CloudWatch::Alarm"

    props = alarm["Properties"]
    assert props["ComparisonOperator"] == "GreaterThanOrEqualToThreshold"
    assert props["Threshold"] == 1
    assert "StreakNudgeTopic" in props["AlarmActions"]

    # Metric Math verification
    metrics = props["Metrics"]
    metric_ids = [m["Id"] for m in metrics]
    assert "totalErrors" in metric_ids
    total_metric = next(m for m in metrics if m["Id"] == "totalErrors")
    assert total_metric["Expression"] == "e1 + e2 + e3"
