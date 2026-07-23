import requests

from app.core.jira_config import (
    JIRA_URL,
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    JIRA_PROJECT_KEY,
)


class JiraClient:
    def __init__(self):
        self.base_url = JIRA_URL.rstrip("/")
        self.project_key = JIRA_PROJECT_KEY

        self.auth = (
            JIRA_EMAIL,
            JIRA_API_TOKEN,
        )

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _adf(self, text: str):
        """
        Convert plain text into Atlassian Document Format (ADF).
        Jira Cloud REST API v3 requires this format for rich-text fields
        such as description.
        """
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": text or "",
                        }
                    ],
                }
            ],
        }

    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str,
        parent_key: str | None = None,
    ):
        payload = {
            "fields": {
                "project": {
                    "key": self.project_key,
                },
                "summary": summary,
                "description": self._adf(description),
                "issuetype": {
                    "name": issue_type,
                },
            }
        }

        # Team-managed projects support parent
        if parent_key:
            payload["fields"]["parent"] = {
                "key": parent_key,
            }

        response = requests.post(
            f"{self.base_url}/rest/api/3/issue",
            auth=self.auth,
            headers=self.headers,
            json=payload,
        )

        if response.status_code >= 400:
            raise Exception(
                f"Jira Error ({response.status_code}): {response.text}"
            )

        return response.json()

    def get_issue(self, issue_key: str):
        response = requests.get(
            f"{self.base_url}/rest/api/3/issue/{issue_key}",
            auth=self.auth,
            headers=self.headers,
        )

        if response.status_code >= 400:
            raise Exception(
                f"Jira Error ({response.status_code}): {response.text}"
            )

        return response.json()

    def search_issues(self, jql: str):
        response = requests.post(
            f"{self.base_url}/rest/api/3/search",
            auth=self.auth,
            headers=self.headers,
            json={
                "jql": jql,
                "maxResults": 100,
            },
        )

        if response.status_code >= 400:
            raise Exception(
                f"Jira Error ({response.status_code}): {response.text}"
            )

        return response.json()