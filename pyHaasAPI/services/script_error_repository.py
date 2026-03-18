"""
Script Error Repository for pyHaasAPI v2

Persists HaasScript errors and their AI-generated solutions to allow
the system to learn from past mistakes and improve future generations.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

@dataclass
class ErrorSolution:
    """A record of a script error and its corresponding fix."""
    error_message: str
    offending_code: str
    fixed_code: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success_count: int = 1

class ScriptErrorRepository:
    """
    Manages a local knowledge base of HaasScript errors and solutions.
    """
    
    def __init__(self, persistence_file: Path):
        self.persistence_file = persistence_file
        self.solutions: List[ErrorSolution] = []
        self._load()

    def _load(self):
        """Load solutions from disk."""
        if self.persistence_file.exists():
            try:
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    self.solutions = [ErrorSolution(**item) for item in data]
            except Exception as e:
                print(f"Failed to load error repository: {e}")

    def save(self):
        """Save solutions to disk."""
        try:
            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_file, 'w') as f:
                json.dump([asdict(s) for s in self.solutions], f, indent=2)
        except Exception as e:
            print(f"Failed to save error repository: {e}")

    def add_solution(self, error_message: str, offending_code: str, fixed_code: str, context: Optional[Dict[str, Any]] = None):
        """Add or update a solution in the repository."""
        # Simple deduplication based on error message (can be improved with fuzzy matching)
        for s in self.solutions:
            if s.error_message == error_message:
                s.success_count += 1
                s.offending_code = offending_code
                s.fixed_code = fixed_code
                s.timestamp = datetime.now().isoformat()
                self.save()
                return
        
        new_solution = ErrorSolution(
            error_message=error_message,
            offending_code=offending_code,
            fixed_code=fixed_code,
            context=context or {}
        )
        self.solutions.append(new_solution)
        self.save()

    def get_relevant_solutions(self, current_error: str, limit: int = 3) -> List[ErrorSolution]:
        """
        Find solutions relevant to a current error.
        Currently uses simple keyword matching.
        """
        relevant = []
        keywords = set(current_error.lower().split())
        
        # Avoid common words
        stopwords = {"the", "a", "an", "is", "at", "in", "of", "to", "and", "or"}
        keywords = {k for k in keywords if len(k) > 2 and k not in stopwords}
        
        for s in self.solutions:
            s_keywords = set(s.error_message.lower().split())
            if keywords.intersection(s_keywords):
                relevant.append(s)
        
        # Sort by relevance (number of matching keywords) and success count
        relevant.sort(key=lambda x: (len(keywords.intersection(set(x.error_message.lower().split()))), x.success_count), reverse=True)
        
        return relevant[:limit]
        
    def get_knowledge_context(self) -> str:
        """Format the repository content for an AI prompt."""
        if not self.solutions:
            return "No prior error memory available."
            
        context = "Past HaasScript Errors and Verified Fixes:\n"
        for i, s in enumerate(self.solutions[:10]): # Limit to top 10 for context window
            context += f"--- Example {i+1} ---\n"
            context += f"Error: {s.error_message}\n"
            context += f"Fix: {s.fixed_code[:200]}...\n" # Brief snippet
        return context
