"""Optional Gemini REST client."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from buildquarry.domain.models import Plan, ProjectInput


class GeminiError(RuntimeError):
    """Raised when Gemini cannot return a valid plan."""


def create_gemini_plan(project: ProjectInput, api_key: str, model: str) -> Plan:
    prompt = f"""Act as a senior software architect and pragmatic MVP engineer.
Create a technically specific, implementation-ready MVP plan from this project brief.
Prefer concrete technologies, modules, interfaces, data structures, API boundaries,
dependencies, validation rules, and security considerations over generic product language.
Do not invent requirements not supported by the brief. Keep architecture appropriate for
the selected time budget. Mark uncertain choices as assumptions.
Return only JSON matching this shape:
{{"title":"string","mvp":"string","primary_user":"string","in_scope":["string"],"out_of_scope":["string"],"milestones":[{{"title":"string","tasks":["string"]}}],"acceptance_criteria":["string"],"architecture":["concrete component or boundary"],"data_model":["entity, field, or storage decision"],"api_design":["endpoint, interface, or event"],"technical_risks":["specific technical risk and mitigation"],"implementation_notes":["specific library, algorithm, command, or setup note"]}}
Every task must name a concrete deliverable or verification step.
Respect time budget: {project.time_budget}. Skill level: {project.skill_level}.
Project idea: {project.idea}
Target user: {project.target_user}
Tech stack: {project.tech_stack or "not specified"}
Constraints: {project.constraints or "none"}
"""
    request = Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote(model, safe='')}:generateContent?key={quote(api_key, safe='')}",
        data=json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            details = json.loads(error.read().decode("utf-8"))
            message = details.get("error", {}).get("message", "")
        except (OSError, ValueError):
            message = ""
        if error.code in (400, 401, 403):
            raise GeminiError(
                "Gemini rejected this API key or request"
                + (f": {message}" if message else ". Use Change Gemini key and try again.")
            ) from error
        raise GeminiError(
            "Gemini request failed"
            + (f": {message}" if message else ". Check network connection and try again.")
        ) from error
    except (URLError, TimeoutError) as error:
        raise GeminiError("Gemini request failed. Check network connection and try again.") from error
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        return Plan.model_validate_json(text)
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise GeminiError("Gemini returned an invalid plan. Try again or use manual mode.") from error
