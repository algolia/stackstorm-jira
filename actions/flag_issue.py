from lib.base import BaseJiraAction
from lib.flagged import resolve_flagged_field_id


class FlagIssue(BaseJiraAction):
    def run(self, issue_key: str) -> dict:
        flag_field = resolve_flagged_field_id(self._client)
        issue = self._client.issue(issue_key, fields=flag_field)
        flags = issue.raw["fields"].get(flag_field) or []

        if any(flag.get("value") == "Impediment" for flag in flags):
            return {"issue_key": issue_key, "flag_added": False}

        issue.update(fields={flag_field: [{"value": "Impediment"}]})
        return {"issue_key": issue_key, "flag_added": True}
