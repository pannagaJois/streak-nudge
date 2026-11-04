"""Automated IAM Least-Privilege Audit Test Suite.

Cloud Computing Concepts Tested:
1. Principle of Least Privilege (PoLP):
   Verifies that no IAM policy grants administrative or excessive permissions.
2. Zero Wildcard Verification:
   Ensures no Action uses wildcards (e.g., 'dynamodb:*' or 'sns:*') and no sensitive
   Resource ARN is set to '*' (which would violate environment boundaries).
3. Role Isolation:
   Confirms that every microservice Lambda has its own distinct execution role.
"""

import yaml
import pytest


class CFLoader(yaml.SafeLoader):
    pass


for tag in ["!Sub", "!Ref", "!GetAtt", "!Condition", "!FindInMap", "!Join", "!Select", "!Split"]:
    CFLoader.add_constructor(tag, lambda loader, node: node.value)


@pytest.fixture
def sam_template():
    """Load and parse template.yaml."""
    with open("template.yaml") as f:
        return yaml.load(f, Loader=CFLoader)


def test_dedicated_roles_per_lambda(sam_template):
    """Confirm every Lambda has an independent dedicated execution role."""
    resources = sam_template["Resources"]
    log_solve = resources["LogSolveFunction"]["Properties"]
    get_streak = resources["GetStreakFunction"]["Properties"]
    nudge = resources["NudgeFunction"]["Properties"]

    roles = [log_solve["Role"], get_streak["Role"], nudge["Role"]]
    # All 3 roles must be distinct
    assert len(set(roles)) == 3
    assert "LogSolveRole" in roles[0]
    assert "GetStreakRole" in roles[1]
    assert "NudgeRole" in roles[2]


def test_no_wildcard_actions(sam_template):
    """Confirm no policy statement uses wildcard actions (e.g., 'dynamodb:*')."""
    resources = sam_template["Resources"]
    iam_roles = [r for r in resources.values() if r.get("Type") == "AWS::IAM::Role"]

    assert len(iam_roles) == 3

    for role in iam_roles:
        for policy in role["Properties"]["Policies"]:
            statements = policy["PolicyDocument"]["Statement"]
            for stmt in statements:
                actions = stmt["Action"]
                if isinstance(actions, str):
                    actions = [actions]
                for act in actions:
                    assert "*" not in act, f"Wildcard action found in {role['Properties']['RoleName']}: {act}"


def test_no_wildcard_resources_on_data_stores(sam_template):
    """Confirm no DynamoDB or SNS permissions are granted on wildcard Resource '*'."""
    resources = sam_template["Resources"]
    iam_roles = [r for r in resources.values() if r.get("Type") == "AWS::IAM::Role"]

    for role in iam_roles:
        for policy in role["Properties"]["Policies"]:
            statements = policy["PolicyDocument"]["Statement"]
            for stmt in statements:
                actions = stmt["Action"]
                if isinstance(actions, str):
                    actions = [actions]
                resource = stmt["Resource"]

                # Check if statement targets DynamoDB or SNS
                is_data_store = any(a.startswith("dynamodb:") or a.startswith("sns:") for a in actions)
                if is_data_store:
                    assert resource != "*", (
                        f"Excessive wildcard resource found in {role['Properties']['RoleName']} "
                        f"for actions {actions}"
                    )
                    assert ("StreakTable" in resource) or ("StreakNudgeTopic" in resource), (
                        f"Resource not properly scoped: {resource}"
                    )


def test_log_solve_permissions_exact(sam_template):
    """Confirm LogSolve role has only GetItem and PutItem on DynamoDB."""
    role = sam_template["Resources"]["LogSolveRole"]["Properties"]
    dynamo_policy = next(p for p in role["Policies"] if p["PolicyName"] == "LogSolveDynamoAccess")
    stmt = dynamo_policy["PolicyDocument"]["Statement"][0]
    allowed_actions = set(stmt["Action"])

    assert allowed_actions == {"dynamodb:GetItem", "dynamodb:PutItem"}
    assert "dynamodb:Scan" not in allowed_actions
    assert "dynamodb:DeleteItem" not in allowed_actions


def test_get_streak_permissions_exact(sam_template):
    """Confirm GetStreak role is strictly read-only (Query and GetItem)."""
    role = sam_template["Resources"]["GetStreakRole"]["Properties"]
    dynamo_policy = next(p for p in role["Policies"] if p["PolicyName"] == "GetStreakDynamoAccess")
    stmt = dynamo_policy["PolicyDocument"]["Statement"][0]
    allowed_actions = set(stmt["Action"])

    assert allowed_actions == {"dynamodb:Query", "dynamodb:GetItem"}
    assert "dynamodb:PutItem" not in allowed_actions
    assert "dynamodb:Scan" not in allowed_actions
    assert "dynamodb:DeleteItem" not in allowed_actions


def test_nudge_permissions_exact(sam_template):
    """Confirm Nudge role has exact permissions for Scan/GetItem/Query and SNS Publish."""
    role = sam_template["Resources"]["NudgeRole"]["Properties"]
    dynamo_policy = next(p for p in role["Policies"] if p["PolicyName"] == "NudgeDynamoAccess")
    dynamo_stmt = dynamo_policy["PolicyDocument"]["Statement"][0]
    assert set(dynamo_stmt["Action"]) == {"dynamodb:Scan", "dynamodb:GetItem", "dynamodb:Query"}

    sns_policy = next(p for p in role["Policies"] if p["PolicyName"] == "NudgeSnsPublishAccess")
    sns_stmt = sns_policy["PolicyDocument"]["Statement"][0]
    assert set(sns_stmt["Action"]) if isinstance(sns_stmt["Action"], list) else {sns_stmt["Action"]} == {"sns:Publish"}
