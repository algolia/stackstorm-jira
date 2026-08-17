from jira.exceptions import JIRAError
from lib.base import BaseJiraAction

__all__ = [
    'ActionManager'
]


class ActionManager(BaseJiraAction):

    def run(self, action, **kwargs):
        try:
            if action == 'transition_issue_by_name':
                action = 'transition_issue'
                kwargs['transition'] = self.transition_name_to_id(**kwargs)
                del kwargs['transition_name']
            elif action == 'transition_issue_by_status':
                status = kwargs.pop('status')
                issue = self._client.issue(kwargs['issue'], fields='status')
                if issue.fields.status.name == status:
                    return (True, None)
                transitions = [
                    transition for transition in self._client.transitions(kwargs['issue'])
                    if transition.get('to', {}).get('name') == status
                ]
                if len(transitions) != 1:
                    return (
                        False,
                        f'Expected one transition to status "{status}", found {len(transitions)}',
                    )
                action = 'transition_issue'
                kwargs['transition'] = transitions[0]['id']
            return (True, getattr(self._client, action)(**kwargs))
        except JIRAError as error:
            return (False, str(error))
        except AttributeError:
            return (False, 'Action "%s" is not implemented' % action)

    def transition_name_to_id(self, issue, transition_name):
        transitions = self._client.transitions(issue)
        res = list(filter(lambda x: x.get("name") == transition_name,
                          transitions))
        if bool(res):
            return res[0].get("id")
        return None
