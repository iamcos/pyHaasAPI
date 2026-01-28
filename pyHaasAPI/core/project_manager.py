import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from ..models.project import ProjectConfig, LabProjectConfig, BacktestStep
from ..core.logging import get_logger

class ProjectManager:
    """Manages persistence of user-defined backtesting projects."""
    
    def __init__(self, projects_file: str = "projects.json"):
        self.projects_file = Path(projects_file)
        self.logger = get_logger("project_manager")
        self.projects: Dict[str, ProjectConfig] = {}
        self.load_projects()

    def load_projects(self) -> None:
        """Load projects from projects.json file."""
        if not self.projects_file.exists():
            self.logger.info(f"No projects file found at {self.projects_file}")
            return

        try:
            with open(self.projects_file, "r") as f:
                data = json.load(f)
            
            for name, p_data in data.items():
                def parse_date(date_str: Any) -> datetime:
                    if isinstance(date_str, datetime):
                        return date_str
                    if not date_str or not isinstance(date_str, str):
                        return datetime.now()
                    try:
                        return datetime.fromisoformat(date_str)
                    except ValueError:
                        return datetime.now()

                labs = []
                for l in p_data.get("labs", []):
                    # Parse dates inside lab config
                    if "added_at" in l and isinstance(l["added_at"], str):
                        l["added_at"] = parse_date(l["added_at"])
                    labs.append(LabProjectConfig(**l))

                steps = [BacktestStep(**s) for s in p_data.get("steps", [])]
                
                self.projects[name] = ProjectConfig(
                    name=p_data.get("name", name),
                    description=p_data.get("description", ""),
                    labs=labs,
                    steps=steps,
                    created_at=parse_date(p_data.get("created_at")),
                    updated_at=parse_date(p_data.get("updated_at"))
                )
            self.logger.info(f"Loaded {len(self.projects)} projects")
        except Exception as e:
            self.logger.error(f"Failed to load projects: {e}")

    def save_projects(self) -> None:
        """Save projects to projects.json file."""
        try:
            data = {}
            for name, p in self.projects.items():
                data[name] = {
                    "name": p.name,
                    "description": p.description,
                    "labs": [vars(l) for l in p.labs],
                    "steps": [vars(s) for s in p.steps],
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat()
                }
                # Fix datetime in labs if any (vars might not handle it perfectly)
                for i, lab in enumerate(p.labs):
                    if isinstance(lab.added_at, datetime):
                        data[name]["labs"][i]["added_at"] = lab.added_at.isoformat()
                    else:
                        data[name]["labs"][i]["added_at"] = str(lab.added_at)

            with open(self.projects_file, "w") as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Saved {len(self.projects)} projects")
        except Exception as e:
            self.logger.error(f"Failed to save projects: {e}")

    def create_project(self, name: str, description: str = "") -> ProjectConfig:
        """Create a new project."""
        if name in self.projects:
            raise ValueError(f"Project '{name}' already exists")
        
        project = ProjectConfig(name=name, description=description)
        self.projects[name] = project
        self.save_projects()
        return project

    def get_project(self, name: str) -> Optional[ProjectConfig]:
        """Get a project by name."""
        return self.projects.get(name)

    def delete_project(self, name: str) -> bool:
        """Delete a project."""
        if name in self.projects:
            del self.projects[name]
            self.save_projects()
            return True
        return False

    def add_lab_to_project(self, project_name: str, lab_config: LabProjectConfig) -> bool:
        """Add a lab to an existing project."""
        project = self.get_project(project_name)
        if not project:
            return False
        
        # Allow duplicates for multi-stage optimization steps
            
        project.labs.append(lab_config)
        project.updated_at = datetime.now()
        self.save_projects()
        return True
