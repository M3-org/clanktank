#!/usr/bin/env python3
"""
Syncs the backend submission_schema.json to the frontend and generates TypeScript types.
"""

import json
import os
import shutil

# Update BACKEND_SCHEMA path to reflect new location in backend/
BACKEND_SCHEMA = os.path.abspath(os.path.join(os.path.dirname(__file__), "submission_schema.json"))
FRONTEND_SCHEMA = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../frontend/public/submission_schema.json",
    )
)
FRONTEND_TYPES = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../frontend/src/types/submissionSchema.ts",
    )
)


def ensure_parent_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def sync_schema():
    ensure_parent_dir(FRONTEND_SCHEMA)
    print(f"Copying {BACKEND_SCHEMA} to {FRONTEND_SCHEMA}")
    shutil.copyfile(BACKEND_SCHEMA, FRONTEND_SCHEMA)
    print("Schema copied.")


def generate_types():
    ensure_parent_dir(FRONTEND_TYPES)
    with open(BACKEND_SCHEMA) as f:
        schema = json.load(f)
    v2_fields = schema["schemas"]["v2"]
    ts_fields = []
    for field in v2_fields:
        name = field["name"]
        required = field.get("required", False)
        t = "string"  # All fields are text in DB, can be refined if needed
        ts_fields.append(f"  {name}{'' if required else '?'}: {t};")
    ts = "export interface SubmissionSchemaV2 {\n" + "\n".join(ts_fields) + "\n}\n"
    with open(FRONTEND_TYPES, "w") as f:
        f.write(ts)
    print(f"TypeScript types written to {FRONTEND_TYPES}")


def main():
    sync_schema()
    generate_types()
    print("Frontend schema and types are now up to date.")


if __name__ == "__main__":
    main()
