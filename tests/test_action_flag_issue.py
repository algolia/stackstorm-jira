import mock
import pytest

from flag_issue import FlagIssue
from lib.flagged import resolve_flagged_field_id


CONFIG = {
    "url": "https://company.atlassian.net",
    "auth_method": "basic",
    "username": "user",
    "password": "passwd",
    "verify": True,
}
FLAGGED_FIELD = {
    "id": "customfield_10038",
    "name": "Flagged",
    "schema": {"type": "array", "items": "option"},
}


def test_resolve_flagged_field_id_matching_field_on_id_returned() -> None:
    jira = mock.Mock()
    jira.fields.return_value = [
        {
            "id": "customfield_10001",
            "name": "Flagged",
            "schema": {"type": "string"},
        },
        FLAGGED_FIELD,
    ]

    assert resolve_flagged_field_id(jira) == "customfield_10038"


@pytest.mark.parametrize(
    "fields",
    [
        [],
        [
            FLAGGED_FIELD,
            {**FLAGGED_FIELD, "id": "customfield_10039"},
        ],
    ],
)
def test_resolve_flagged_field_id_invalid_count_on_error(fields: list) -> None:
    jira = mock.Mock()
    jira.fields.return_value = fields

    with pytest.raises(ValueError) as error:
        resolve_flagged_field_id(jira)

    assert str(error.value) == (
        'Expected exactly one Jira field named "Flagged" '
        f"with schema array of option, found {len(fields)}"
    )


def test_run_unflagged_issue_on_flag_added() -> None:
    with mock.patch("lib.base.JIRA") as jira_class:
        jira = jira_class.return_value
        jira.fields.return_value = [FLAGGED_FIELD]
        issue = mock.Mock(raw={"fields": {"customfield_10038": None}})
        jira.issue.return_value = issue
        action = FlagIssue(CONFIG)

        result = action.run("IAAS-123")

    issue.update.assert_called_once_with(
        fields={"customfield_10038": [{"value": "Impediment"}]}
    )
    jira.assign_issue.assert_not_called()
    jira.issue.assert_called_once_with("IAAS-123", fields="customfield_10038")
    assert result == {"issue_key": "IAAS-123", "flag_added": True}


def test_run_flagged_issue_on_already_present() -> None:
    with mock.patch("lib.base.JIRA") as jira_class:
        jira = jira_class.return_value
        jira.fields.return_value = [FLAGGED_FIELD]
        issue = mock.Mock(
            raw={
                "fields": {
                    "customfield_10038": [
                        {"id": "10019", "value": "Impediment"},
                    ]
                }
            }
        )
        jira.issue.return_value = issue
        action = FlagIssue(CONFIG)

        result = action.run("IAAS-123")

    issue.update.assert_not_called()
    jira.assign_issue.assert_not_called()
    assert result == {"issue_key": "IAAS-123", "flag_added": False}


def test_run_unflagged_issue_matching_assignee_on_flagged_then_unassigned(
) -> None:
    with mock.patch("lib.base.JIRA") as jira_class:
        jira = jira_class.return_value
        jira.fields.return_value = [FLAGGED_FIELD]
        issue = mock.Mock(
            raw={
                "fields": {
                    "customfield_10038": None,
                    "assignee": {"displayName": "admin+jira"},
                }
            }
        )
        jira.issue.return_value = issue
        action = FlagIssue(CONFIG)

        result = action.run("IAAS-123", unassign_if_assignee="admin+jira")

    issue.update.assert_called_once_with(
        fields={"customfield_10038": [{"value": "Impediment"}]}
    )
    jira.assign_issue.assert_called_once_with("IAAS-123", None)
    jira.issue.assert_called_once_with(
        "IAAS-123", fields="customfield_10038,assignee"
    )
    assert result == {"issue_key": "IAAS-123", "flag_added": True}


def test_run_unflagged_issue_flag_failure_on_assignee_left_unchanged(
) -> None:
    with mock.patch("lib.base.JIRA") as jira_class:
        jira = jira_class.return_value
        jira.fields.return_value = [FLAGGED_FIELD]
        issue = mock.Mock(
            raw={
                "fields": {
                    "customfield_10038": None,
                    "assignee": {"displayName": "admin+jira"},
                }
            }
        )
        issue.update.side_effect = RuntimeError("Jira update failed")
        jira.issue.return_value = issue
        action = FlagIssue(CONFIG)

        with pytest.raises(RuntimeError, match="Jira update failed"):
            action.run("IAAS-123", unassign_if_assignee="admin+jira")

    jira.assign_issue.assert_not_called()


def test_run_flagged_issue_matching_assignee_on_unassigned() -> None:
    with mock.patch("lib.base.JIRA") as jira_class:
        jira = jira_class.return_value
        jira.fields.return_value = [FLAGGED_FIELD]
        issue = mock.Mock(
            raw={
                "fields": {
                    "customfield_10038": [
                        {"id": "10019", "value": "Impediment"}
                    ],
                    "assignee": {"displayName": "admin+jira"},
                }
            }
        )
        jira.issue.return_value = issue
        action = FlagIssue(CONFIG)

        result = action.run("IAAS-123", unassign_if_assignee="admin+jira")

    issue.update.assert_not_called()
    jira.assign_issue.assert_called_once_with("IAAS-123", None)
    assert result == {"issue_key": "IAAS-123", "flag_added": False}


@pytest.mark.parametrize("assignee", [None, {"displayName": "operator"}])
def test_run_unflagged_issue_other_assignee_on_flagged_only(
    assignee: dict | None,
) -> None:
    with mock.patch("lib.base.JIRA") as jira_class:
        jira = jira_class.return_value
        jira.fields.return_value = [FLAGGED_FIELD]
        issue = mock.Mock(
            raw={
                "fields": {
                    "customfield_10038": None,
                    "assignee": assignee,
                }
            }
        )
        jira.issue.return_value = issue
        action = FlagIssue(CONFIG)

        result = action.run("IAAS-123", unassign_if_assignee="admin+jira")

    issue.update.assert_called_once_with(
        fields={"customfield_10038": [{"value": "Impediment"}]}
    )
    jira.assign_issue.assert_not_called()
    assert result == {"issue_key": "IAAS-123", "flag_added": True}
