from typing import Any


def resolve_flagged_field_id(client: Any) -> str:
    fields = [
        field["id"]
        for field in client.fields()
        if field.get("name") == "Flagged" and
        field.get("schema", {}).get("type") == "array" and
        field.get("schema", {}).get("items") == "option"
    ]

    if len(fields) != 1:
        raise ValueError(
            'Expected exactly one Jira field named "Flagged" '
            "with schema array of option, "
            f"found {len(fields)}"
        )

    return fields[0]
