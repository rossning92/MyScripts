import glob
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from utils.yaml import parse_yaml


@dataclass
class Skill:
    name: str
    description: str
    file_path: str
    metadata: Dict
    content: str


_skills: List[Skill] = []


def _get_skills_dirs():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dirs = [os.path.join(current_dir, "skills")]

    env_dir = os.environ.get("SKILLS_DIR")
    if env_dir and os.path.isdir(env_dir):
        dirs.append(env_dir)

    return dirs


def get_skills() -> List[Skill]:
    if _skills:
        return _skills

    for skills_dir in _get_skills_dirs():
        for file in glob.glob(os.path.join(skills_dir, "*.md")):
            skill_name = os.path.splitext(os.path.basename(file))[0]

            if any(s.name == skill_name for s in _skills):
                raise ValueError(f"Duplicated skill: {skill_name}")

            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
            if not match:
                raise ValueError(f"Skill {skill_name} missing front matter")

            metadata = parse_yaml(match.group(1))

            description = metadata.get("description", "").strip()
            if not description:
                raise ValueError(f"Skill {skill_name} description cannot be empty")

            _skills.append(
                Skill(
                    name=skill_name,
                    description=description,
                    file_path=file,
                    metadata=metadata,
                    content=content[match.end() :].strip(),
                )
            )

    return _skills


def get_skill_prompt() -> Optional[str]:
    skills = get_skills()
    if not skills:
        return None

    prompt = """# Task-Specific Instructions

You should read the following Markdown file for detailed, task-specific, step-by-step instructions when a task matches the description:

"""
    for skill in skills:
        prompt += f"`{skill.file_path}`: {skill.description}\n"
    return prompt
