from lib.base import BaseJiraAction
from lib.flagged import resolve_flagged_field_id


class IsFlagged(BaseJiraAction):
    def run(self, issue_key: str) -> bool:
        flag_field = resolve_flagged_field_id(self._client)
        issue = self._client.issue(issue_key, fields=flag_field)
        fields = issue.raw["fields"]
        if flag_field not in fields:
            raise ValueError(
                f'Issue "{issue_key}" does not expose Jira field "{flag_field}"'
            )
        flags = fields[flag_field] or []

        return any(flag.get("value") == "Impediment" for flag in flags)
