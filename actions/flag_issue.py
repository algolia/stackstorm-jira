from lib.base import BaseJiraAction


class FlagIssue(BaseJiraAction):
    def run(self, issue_key: str) -> dict:
        issue = self._client.issue(issue_key)
        flag_field = "customfield_10038"
        flags = issue.raw["fields"].get(flag_field) or []

        if any(flag.get("value") == "Impediment" for flag in flags):
            return {"issue_key": issue_key, "flag_added": False}

        issue.update(fields={flag_field: [{"value": "Impediment"}]})
        return {"issue_key": issue_key, "flag_added": True}
