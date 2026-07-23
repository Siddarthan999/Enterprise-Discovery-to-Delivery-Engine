ARTIFACT_PROMPTS = {
    "jira_backlog": """
You are a Senior Agile Delivery Manager.

Using the approved Statement of Work below, generate a COMPLETE Jira backlog.

Return ONLY valid JSON.

Schema:

{
  "epics":[
    {
      "summary":"",
      "description":"",
      "features":[
        {
          "summary":"",
          "description":"",
          "stories":[
            {
              "summary":"",
              "description":"",
              "acceptance_criteria":[
                ""
              ],
              "priority":"High",
              "story_points":5
            }
          ]
        }
      ]
    }
  ]
}

Rules

- Produce every major Epic.
- Every Epic must contain Features.
- Every Feature must contain User Stories.
- Stories must have acceptance criteria.
- Do not explain anything.
- Return JSON only.

Approved SOW

--------------------
{SOW}
--------------------
""",

    "raid_register": """
You are a Senior Project Manager.

Generate a RAID Register.

Return ONLY JSON.

{
  "risks":[
    {
      "id":"R1",
      "description":"",
      "impact":"",
      "probability":"High",
      "mitigation":"",
      "owner":"Project Manager"
    }
  ],
  "assumptions":[
    {
      "id":"A1",
      "description":"",
      "owner":"Client"
    }
  ],
  "issues":[
    {
      "id":"I1",
      "description":"",
      "owner":""
    }
  ],
  "dependencies":[
    {
      "id":"D1",
      "description":"",
      "owner":""
    }
  ]
}

Return JSON only.

Approved SOW

--------------------
{SOW}
--------------------
""",

    "project_plan": """
You are an Enterprise Delivery Lead.

Generate a project implementation plan.

Return ONLY JSON.

{
  "phases":[
    {
      "name":"",
      "duration":"",
      "deliverables":[]
    }
  ]
}

Approved SOW

--------------------
{SOW}
--------------------
""",

    "sprint_plan": """
Generate a sprint plan.

Return ONLY JSON.

{
  "sprints":[
    {
      "name":"",
      "goal":"",
      "duration":"2 Weeks",
      "stories":[]
    }
  ]
}

Approved SOW

--------------------
{SOW}
--------------------
""",

    "resource_plan": """
Generate a resource allocation plan.

Return ONLY JSON.

{
  "resources":[
    {
      "role":"",
      "allocation":"100%",
      "duration":"",
      "responsibilities":[]
    }
  ]
}

Approved SOW

--------------------
{SOW}
--------------------
""",

    "stakeholder_matrix": """
Generate a stakeholder matrix.

Return ONLY JSON.

{
  "stakeholders":[
    {
      "name":"",
      "role":"",
      "interest":"High",
      "influence":"High",
      "communication":"Weekly"
    }
  ]
}

Approved SOW

--------------------
{SOW}
--------------------
""",

    "raci_matrix": """
Generate a RACI matrix.

Return ONLY JSON.

{
  "activities":[
    {
      "activity":"",
      "architect":"R",
      "client":"A",
      "practice_lead":"C",
      "delivery_manager":"R",
      "qa":"I"
    }
  ]
}

Approved SOW

--------------------
{SOW}
--------------------
""",

    "development_order": """
Generate the implementation sequence.

Return ONLY JSON.

{
  "steps":[
    {
      "order":1,
      "title":"",
      "reason":""
    }
  ]
}

Approved SOW

--------------------
{SOW}
--------------------
"""
}


def build_delivery_prompt(
    artifact_type: str,
    sow_markdown: str,
) -> str:

    if artifact_type not in ARTIFACT_PROMPTS:
        raise ValueError(f"Unknown artifact type: {artifact_type}")

    return ARTIFACT_PROMPTS[artifact_type].replace(
        "{SOW}",
        sow_markdown,
    )