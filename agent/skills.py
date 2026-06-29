"""Skills progressive disclosure system for the recruitment agent."""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


@dataclass
class SkillDefinition:
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    trigger: str = ""
    content: str = ""


def _parse_frontmatter(text: str) -> tuple[dict[str, str | list[str]], str]:
    """Extract YAML-like frontmatter and body from a markdown skill file."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text

    meta: dict[str, str | list[str]] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = value

    return meta, match.group(2).strip()


def load_all_skills(skills_dir: Path | None = None) -> list[SkillDefinition]:
    """Load all .md skill files from the skills directory."""
    directory = skills_dir or SKILLS_DIR
    if not directory.exists():
        logger.warning("Skills directory not found: %s", directory)
        return []

    skills: list[SkillDefinition] = []
    for path in sorted(directory.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(raw)
        tools_value = meta.get("tools", [])
        tools = tools_value if isinstance(tools_value, list) else [tools_value]

        skill = SkillDefinition(
            name=str(meta.get("name", path.stem)),
            description=str(meta.get("description", "")),
            tools=tools,
            trigger=str(meta.get("trigger", "")),
            content=body,
        )
        skills.append(skill)
        logger.info("Loaded skill: %s (tools=%s)", skill.name, skill.tools)

    logger.info("Total skills loaded: %d", len(skills))
    return skills


def match_skills(
    task_description: str,
    available_skills: list[SkillDefinition],
) -> list[SkillDefinition]:
    """Match skills whose trigger keywords appear in the task description."""
    task_lower = task_description.lower()
    matched: list[SkillDefinition] = []

    for skill in available_skills:
        trigger_lower = skill.trigger.lower()
        keywords = re.findall(r"[\u4e00-\u9fff]+|\w+", trigger_lower)
        if any(kw in task_lower for kw in keywords if len(kw) >= 2):
            matched.append(skill)

    return matched


def build_skill_context(skills: list[SkillDefinition]) -> str:
    """Format matched skills into a context string injectable into prompts."""
    if not skills:
        return ""

    sections: list[str] = ["## 已激活技能\n"]
    for skill in skills:
        sections.append(
            f"### {skill.name}\n"
            f"{skill.description}\n\n"
            f"关联工具: {', '.join(skill.tools)}\n\n"
            f"{skill.content}"
        )
    return "\n\n".join(sections)


def get_skill_tools(skills: list[SkillDefinition]) -> list[str]:
    """Collect deduplicated tool names from a list of skills."""
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        for tool_name in skill.tools:
            if tool_name not in seen:
                seen.add(tool_name)
                result.append(tool_name)
    return result
