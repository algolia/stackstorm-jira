import mock
import pytest

from is_flagged import IsFlagged


FLAGGED_FIELD = {
    "id": "customfield_10038",
    "name": "Flagged",
    "schema": {"type": "array", "items": "option"},
}


@pytest.mark.parametrize(
    "flags,is_flagged",
    [
        ([{"id": "10019", "value": "Impediment"}], True),
        (None, False),
    ],
)
def test_run_flag_value_on_result(
    flags: list[dict] | None, is_flagged: bool
) -> None:
    jira = mock.Mock()
    jira.fields.return_value = [FLAGGED_FIELD]
    jira.issue.return_value.raw = {"fields": {"customfield_10038": flags}}
    action = IsFlagged.__new__(IsFlagged)
    action._client = jira

    result = action.run("IAAS-123")

    jira.issue.assert_called_once_with("IAAS-123", fields="customfield_10038")
    assert result == {"issue_key": "IAAS-123", "is_flagged": is_flagged}


def test_run_missing_flagged_field_on_resolution_error() -> None:
    jira = mock.Mock()
    jira.fields.return_value = []
    action = IsFlagged.__new__(IsFlagged)
    action._client = jira

    with pytest.raises(ValueError):
        action.run("IAAS-123")

    jira.issue.assert_not_called()
