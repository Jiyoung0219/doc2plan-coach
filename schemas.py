ASSIGNMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "assignment_title": {"type": "string"},
        "goal": {"type": "string"},
        "requirements": {"type": "array", "items": {"type": "string"}},
        "deliverables": {"type": "array", "items": {"type": "string"}},
        "rubric": {"type": "array", "items": {"type": "string"}},
        "deadline": {"type": "string"},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "tools_required": {"type": "array", "items": {"type": "string"}},
    },
}

PROJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "project_title": {"type": "string"},
        "project_goal": {"type": "string"},
        "milestones": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "due": {"type": "string"},
                    "deliverables": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "roles_suggested": {"type": "array", "items": {"type": "string"}},
        "evaluation_criteria": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
    },
}
