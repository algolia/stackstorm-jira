import mock

from jira.exceptions import JIRAError
from run import ActionManager
from tests.lib.actions import JIRABaseActionTestCase


class RunTestCase(JIRABaseActionTestCase):
    __test__ = True
    action_cls = ActionManager

    @mock.patch('lib.base.JIRA')
    def test_run_without_exception(self, mock_jira):
        action = self.get_action_instance(self.full_auth_passwd_config)

        action._client.method.return_value = 'result'

        (is_success, value) = action.run(action='method')
        self.assertTrue(is_success)
        self.assertEqual(value, 'result')

    @mock.patch('lib.base.JIRA')
    def test_run_with_invalid_action(self, mock_jira):
        action = self.get_action_instance(self.full_auth_passwd_config)

        def side_effect(*args, **kwargs):
            raise AttributeError()

        action._client.not_implemented_method.side_effect = side_effect

        (is_success, value) = action.run(action='not_implemented_method')
        self.assertFalse(is_success)
        self.assertEqual(value, 'Action "not_implemented_method" is not implemented')

    @mock.patch('lib.base.JIRA')
    def test_run_with_jira_exception(self, mock_jira):
        action = self.get_action_instance(self.full_auth_passwd_config)

        def side_effect(*args, **kwargs):
            raise JIRAError('error message')

        action._client.method.side_effect = side_effect

        (is_success, value) = action.run(action='method')
        self.assertFalse(is_success)
        self.assertEqual(value, "JiraError HTTP None\n\ttext: error message\n\t")

    @mock.patch('lib.base.JIRA')
    def test_transition_name_to_id(self, mock_jira):
        action = self.get_action_instance(self.full_auth_passwd_config)

        def side_effect(*args, **kwargs):
            return [{'id': '11', 'name': 'Start'},
                    {'id': '21', 'name': 'Doing'},
                    {'id': '31', 'name': 'Close'}]

        action._client.transitions.side_effect = side_effect

        kwargs = {'issue': 'ISSUE-XX', 'transition_name': 'Doing'}
        transition_id = action.transition_name_to_id(**kwargs)
        self.assertEqual(transition_id, '21')

        kwargs = {'issue': 'ISSUE-XX', 'transition_name': 'Done'}
        transition_id = action.transition_name_to_id(**kwargs)
        self.assertEqual(transition_id, None)


def test_transition_issue_by_status_single_match_on_transition_executed() -> None:
    action = ActionManager.__new__(ActionManager)
    action._client = mock.Mock()
    action._client.issue.return_value.fields.status.name = 'To Do'
    action._client.transitions.return_value = [
        {'id': '11', 'name': 'Start Progress', 'to': {'name': 'In Progress'}},
        {'id': '21', 'name': 'Close', 'to': {'name': 'Done'}},
    ]

    result = action.run(
        action='transition_issue_by_status',
        issue='IAAS-3035',
        status='In Progress',
    )

    assert result == (True, action._client.transition_issue.return_value)
    action._client.transition_issue.assert_called_once_with(
        issue='IAAS-3035',
        transition='11',
    )


def test_transition_issue_by_status_target_status_on_noop_success() -> None:
    action = ActionManager.__new__(ActionManager)
    action._client = mock.Mock()
    action._client.issue.return_value.fields.status.name = 'Done'

    result = action.run(
        action='transition_issue_by_status',
        issue='IAAS-3035',
        status='Done',
    )

    assert result == (True, None)
    action._client.issue.assert_called_once_with('IAAS-3035', fields='status')
    action._client.transitions.assert_not_called()
    action._client.transition_issue.assert_not_called()


def test_transition_issue_by_status_no_match_on_explicit_failure() -> None:
    action = ActionManager.__new__(ActionManager)
    action._client = mock.Mock()
    action._client.issue.return_value.fields.status.name = 'To Do'
    action._client.transitions.return_value = []

    result = action.run(
        action='transition_issue_by_status',
        issue='IAAS-3035',
        status='Done',
    )

    assert result == (False, 'Expected one transition to status "Done", found 0')
    action._client.transition_issue.assert_not_called()


def test_transition_issue_by_status_exact_name_on_transition_executed() -> None:
    action = ActionManager.__new__(ActionManager)
    action._client = mock.Mock()
    action._client.issue.return_value.fields.status.name = 'To Do'
    action._client.transitions.return_value = [
        {'id': '11', 'name': 'Done', 'to': {'name': 'Done'}},
        {'id': '21', 'name': 'Complete', 'to': {'name': 'Done'}},
    ]

    result = action.run(
        action='transition_issue_by_status',
        issue='IAAS-3035',
        status='Done',
    )

    assert result == (True, action._client.transition_issue.return_value)
    action._client.transition_issue.assert_called_once_with(
        issue='IAAS-3035',
        transition='11',
    )


def test_transition_issue_by_status_multiple_matches_on_explicit_failure() -> None:
    action = ActionManager.__new__(ActionManager)
    action._client = mock.Mock()
    action._client.issue.return_value.fields.status.name = 'To Do'
    action._client.transitions.return_value = [
        {'id': '11', 'name': 'Resolve', 'to': {'name': 'Done'}},
        {'id': '21', 'name': 'Close', 'to': {'name': 'Done'}},
    ]

    result = action.run(
        action='transition_issue_by_status',
        issue='IAAS-3035',
        status='Done',
    )

    assert result == (False, 'Expected one transition to status "Done", found 2')
    action._client.transition_issue.assert_not_called()
