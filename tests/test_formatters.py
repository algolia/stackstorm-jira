from types import SimpleNamespace
from unittest import TestCase, mock

from lib.formatters import to_issue_dict, to_links_dict


class FormattersTestCase(TestCase):
    def test_to_issue_dict_with_metadata_on_additive_output(self):
        fields = SimpleNamespace(
            assignee=SimpleNamespace(displayName="Assignee"),
            created="2026-07-29T10:00:00.000+0000",
            description="Description",
            issuetype=SimpleNamespace(name="Machine Wipe"),
            labels=["wipe"],
            priority=SimpleNamespace(name="High"),
            reporter=SimpleNamespace(displayName="Reporter"),
            resolution=SimpleNamespace(name="Done"),
            resolutiondate="2026-07-30T10:00:00.000+0000",
            status=SimpleNamespace(
                name="Completed",
                statusCategory=SimpleNamespace(name="Done"),
            ),
            summary="Wipe machine",
            updated="2026-07-30T10:00:00.000+0000",
        )
        issue = SimpleNamespace(
            fields=fields,
            id="10001",
            key="IAAS-1",
            permalink=mock.Mock(
                return_value="https://algolia.atlassian.net/browse/IAAS-1 - Wipe machine"
            ),
        )

        result = to_issue_dict(issue)

        self.assertEqual(
            result,
            {
                "id": "10001",
                "key": "IAAS-1",
                "url": "https://algolia.atlassian.net/browse/IAAS-1",
                "summary": "Wipe machine",
                "description": "Description",
                "status": "Completed",
                "issue_type": "Machine Wipe",
                "status_category": "Done",
                "priority": "High",
                "resolution": "Done",
                "labels": ["wipe"],
                "reporter": "Reporter",
                "assignee": "Assignee",
                "created_at": "2026-07-29T10:00:00.000+0000",
                "updated_at": "2026-07-30T10:00:00.000+0000",
                "resolved_at": "2026-07-30T10:00:00.000+0000",
            },
        )

    def test_to_issue_dict_without_optional_metadata_on_null_output(self):
        fields = SimpleNamespace(
            assignee=None,
            created="2026-07-29T10:00:00.000+0000",
            description=None,
            labels=[],
            reporter=None,
            resolution=None,
            resolutiondate=None,
            status=SimpleNamespace(name="Open"),
            summary="Partial issue",
            updated="2026-07-30T10:00:00.000+0000",
        )
        issue = SimpleNamespace(
            fields=fields,
            id="10002",
            key="IAAS-2",
            permalink=mock.Mock(
                return_value="https://algolia.atlassian.net/browse/IAAS-2 - Partial issue"
            ),
        )

        result = to_issue_dict(issue)

        self.assertIsNone(result["issue_type"])
        self.assertIsNone(result["status_category"])
        self.assertEqual(result["status"], "Open")
        self.assertEqual(result["summary"], "Partial issue")

    def test_to_links_dict_with_outward_issue_type_on_preserved_output(self):
        link = SimpleNamespace(
            raw={
                "id": "20001",
                "outwardIssue": {
                    "key": "IAAS-3",
                    "fields": {
                        "issuetype": {"name": "Machine Wipe"},
                        "status": {"name": "To Do"},
                        "summary": "Wipe machine",
                    },
                },
                "type": {"inward": "is caused by", "outward": "causes"},
            }
        )

        result = to_links_dict(link)

        self.assertEqual(
            result,
            {
                "id": "20001",
                "key": "IAAS-3",
                "summary": "Wipe machine",
                "status": "To Do",
                "type": "causes",
                "issue_type": "Machine Wipe",
            },
        )

    def test_to_links_dict_with_inward_issue_type_on_preserved_output(self):
        link = SimpleNamespace(
            raw={
                "id": "20002",
                "inwardIssue": {
                    "key": "IAAS-4",
                    "fields": {
                        "issuetype": {"name": "Machine Wipe"},
                        "status": {"name": "Done"},
                        "summary": "Completed wipe",
                    },
                },
                "type": {"inward": "is caused by", "outward": "causes"},
            }
        )

        result = to_links_dict(link)

        self.assertEqual(
            result,
            {
                "id": "20002",
                "key": "IAAS-4",
                "summary": "Completed wipe",
                "status": "Done",
                "type": "is caused by",
                "issue_type": "Machine Wipe",
            },
        )

    def test_to_links_dict_without_optional_issue_type_on_null_output(self):
        link = SimpleNamespace(
            raw={
                "id": "20003",
                "outwardIssue": {
                    "key": "IAAS-5",
                    "fields": {
                        "status": {"name": "To Do"},
                        "summary": "Partial linked issue",
                    },
                },
                "type": {"inward": "is caused by", "outward": "causes"},
            }
        )

        result = to_links_dict(link)

        self.assertIsNone(result["issue_type"])
        self.assertEqual(result["type"], "causes")
