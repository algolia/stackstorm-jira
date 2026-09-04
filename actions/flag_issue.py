from lib.base import BaseJiraAction
from lib.flagged import resolve_flagged_field_id


class FlagIssue(BaseJiraAction):
    def run(
        self, issue_key: str, unassign_if_assignee: str | None = None
    ) -> dict:
        flag_field = resolve_flagged_field_id(self._client)
        fields = (
            f"{flag_field},assignee"
            if unassign_if_assignee is not None
            else flag_field
        )
        issue = self._client.issue(issue_key, fields=fields)
        issue_fields = issue.raw["fields"]
        flags = issue_fields.get(flag_field) or []
        flag_added = not any(
            flag.get("value") == "Impediment" for flag in flags
        )

        if flag_added:
            issue.update(fields={flag_field: [{"value": "Impediment"}]})

        assignee = issue_fields.get("assignee") or {}
        if unassign_if_assignee is not None:
            if assignee.get("displayName") == unassign_if_assignee:
                self._client.assign_issue(issue_key, None)

        return {"issue_key": issue_key, "flag_added": flag_added}
