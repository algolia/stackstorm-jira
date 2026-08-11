import mock

from flag_issue import FlagIssue


CONFIG = {
    "url": "https://company.atlassian.net",
    "auth_method": "basic",
    "username": "user",
    "password": "passwd",
    "verify": True,
}


def test_run_unflagged_issue_on_flag_added():
    with mock.patch("lib.base.JIRA") as jira_class:
        jira = jira_class.return_value
        issue = mock.Mock(raw={"fields": {"customfield_10038": None}})
        jira.issue.return_value = issue
        action = FlagIssue(CONFIG)

        result = action.run("IAAS-123")

    issue.update.assert_called_once_with(
        fields={"customfield_10038": [{"value": "Impediment"}]}
    )
    assert result == {"issue_key": "IAAS-123", "flag_added": True}


def test_run_flagged_issue_on_already_present():
    with mock.patch("lib.base.JIRA") as jira_class:
        jira = jira_class.return_value
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
    assert result == {"issue_key": "IAAS-123", "flag_added": False}
