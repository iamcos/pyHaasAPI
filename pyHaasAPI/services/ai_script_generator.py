"""
AI Script Generator Service

Uses AI (Gemini) to generate, modify, and fix HaasScript code.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from .haasscript_knowledge_service import HaasScriptKnowledgeService
from .script_error_repository import ScriptErrorRepository
from ..core.logging import get_logger
from ..exceptions.script import ScriptError


@dataclass
class AIConfig:
    """Configuration for AI script generation."""
    model_name: str = "gemini-2.0-flash-exp"
    api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    max_fix_iterations: int = 3
    
    @classmethod
    def from_env(cls) -> 'AIConfig':
        """Load configuration from environment variables."""
        return cls(
            model_name=os.getenv("AI_MODEL", "gemini-2.0-flash-exp"),
            api_key=os.getenv("GEMINI_API_KEY", ""),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
            max_fix_iterations=int(os.getenv("AI_MAX_FIX_ITERATIONS", "3"))
        )


class AIScriptGenerator:
    """
    AI-powered HaasScript generator using Gemini.
    """
    
    def __init__(
        self,
        knowledge_service: HaasScriptKnowledgeService,
        config: Optional[AIConfig] = None,
        error_repository: Optional[ScriptErrorRepository] = None
    ):
        """
        Initialize the AI script generator.
        
        Args:
            knowledge_service: HaasScript knowledge service
            config: AI configuration (defaults to env-based config)
            
        Raises:
            ScriptError: If Gemini API is not available or not configured
        """
        if not GENAI_AVAILABLE:
            raise ScriptError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        
        self.knowledge_service = knowledge_service
        self.config = config or AIConfig.from_env()
        self.error_repository = error_repository
        self.logger = get_logger("ai_script_generator")
        
        if not self.config.api_key:
            raise ScriptError(
                "GEMINI_API_KEY not configured. "
                "Set environment variable GEMINI_API_KEY."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.config.api_key)
        self.model = genai.GenerativeModel(self.config.model_name)
        
        self.logger.info(f"Initialized AI generator with model: {self.config.model_name}")
    
    async def generate_from_idea(
        self,
        idea: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate HaasScript code from natural language idea.
        
        Args:
            idea: Natural language description of desired script
            context: Additional context (market, timeframe, etc.)
            
        Returns:
            Generated HaasScript source code
            
        Raises:
            ScriptError: If generation fails
        """
        try:
            self.logger.info(f"Generating script from idea: {idea[:100]}...")
            
            # Build prompt
            prompt = self._build_generation_prompt(idea, context)
            
            # Generate with Gemini
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
            )
            
            # Extract code from response
            code = self._extract_code(response.text)
            
            self.logger.info(f"Generated {len(code)} characters of code")
            return code
            
        except Exception as e:
            self.logger.error(f"Failed to generate script: {e}")
            raise ScriptError(f"AI generation failed: {e}") from e
    
    async def modify_script(
        self,
        current_code: str,
        modification: str
    ) -> str:
        """
        Modify existing HaasScript code based on natural language instruction.
        
        Args:
            current_code: Current script source code
            modification: Natural language modification instruction
            
        Returns:
            Modified HaasScript source code
            
        Raises:
            ScriptError: If modification fails
        """
        try:
            self.logger.info(f"Modifying script: {modification[:100]}...")
            
            prompt = self._build_modification_prompt(current_code, modification)
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
            )
            
            code = self._extract_code(response.text)
            
            self.logger.info("Script modification complete")
            return code
            
        except Exception as e:
            self.logger.error(f"Failed to modify script: {e}")
            raise ScriptError(f"AI modification failed: {e}") from e
    
    async def fix_errors(
        self,
        script_code: str,
        errors: List[str]
    ) -> str:
        """
        Automatically fix compilation/runtime errors in HaasScript.
        
        Args:
            script_code: Script source code with errors
            errors: List of error messages
            
        Returns:
            Fixed HaasScript source code
            
        Raises:
            ScriptError: If error fixing fails
        """
        try:
            self.logger.info(f"Fixing {len(errors)} errors in script")
            
            error_knowledge = self.error_repository.get_knowledge_context() if self.error_repository else ""
            prompt = self._build_error_fix_prompt(script_code, errors, error_knowledge)
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.max_tokens,
                    temperature=0.3  # Lower temperature for fixes
                )
            )
            
            code = self._extract_code(response.text)
            
            self.logger.info("Error fixing complete")
            return code
            
        except Exception as e:
            self.logger.error(f"Failed to fix errors: {e}")
            raise ScriptError(f"AI error fixing failed: {e}") from e
    
    async def explain_script(self, script_code: str) -> str:
        """
        Generate human-readable explanation of HaasScript code.
        
        Args:
            script_code: Script source code to explain
            
        Returns:
            Natural language explanation
        """
        try:
            prompt = f"""Explain the following HaasScript code in simple terms:

```haasscript
{script_code}
```

Provide a clear, concise explanation of what this script does."""
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to explain script: {e}")
            return f"Error generating explanation: {e}"
    
    def _build_generation_prompt(
        self,
        idea: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for script generation."""
        # Get HaasScript knowledge
        haasscript_context = self.knowledge_service.get_ai_context()
        
        context_str = ""
        if context:
            context_str = f"\n**Additional Context**:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
        
        prompt = f"""You are an expert HaasScript developer. Generate valid, working HaasScript code based on the user's idea.

{haasscript_context}

**User Idea**:
{idea}
{context_str}

**Instructions**:
1. Generate ONLY the HaasScript code, no explanations
2. Ensure the code is syntactically correct
3. Include necessary variable declarations
4. Add brief inline comments for clarity
5. Follow HaasScript best practices

Generate the code now:"""
        
        return prompt
    
    def _build_modification_prompt(
        self,
        current_code: str,
        modification: str
    ) -> str:
        """Build prompt for script modification."""
        prompt = f"""You are an expert HaasScript developer. Modify the following HaasScript code according to the user's instruction.

**Current Code**:
```haasscript
{current_code}
```

**Modification Request**:
{modification}

**Instructions**:
1. Apply the requested modification
2. Preserve existing functionality unless explicitly changed
3. Ensure the modified code is syntactically correct
4. Return ONLY the complete modified code, no explanations

Generate the modified code now:"""
        
        return prompt
    
    def _build_error_fix_prompt(
        self,
        script_code: str,
        errors: List[str],
        error_knowledge: str = ""
    ) -> str:
        """Build prompt for error fixing."""
        errors_str = "\n".join(f"- {err}" for err in errors)
        
        knowledge_section = ""
        if error_knowledge:
            knowledge_section = f"\n**Previous Error Memory**:\n{error_knowledge}\n"
            
        prompt = f"""You are an expert HaasScript developer. Fix the following errors in the HaasScript code.
{knowledge_section}
**Code with Errors**:
```haasscript
{script_code}
```

**Errors**:
{errors_str}

**Instructions**:
1. Identify and fix all errors
2. Ensure the fixed code is syntactically correct
3. Preserve the original logic and intent
4. Return ONLY the complete fixed code, no explanations

Generate the fixed code now:"""
        
        return prompt
    
    def _extract_code(self, response_text: str) -> str:
        """
        Extract code from AI response, removing markdown formatting.
        
        Args:
            response_text: Raw AI response text
            
        Returns:
            Clean code without markdown
        """
        # Remove markdown code blocks
        text = response_text.strip()
        
        # Check for code blocks
        if "```" in text:
            # Extract content between code fences
            parts = text.split("```")
            if len(parts) >= 3:
                code = parts[1]
                # Remove language identifier if present
                if code.startswith("haasscript\n"):
                    code = code[11:]
                elif code.startswith("haasscript "):
                    code = code[11:]
                elif "\n" in code and code.split("\n")[0].strip() in ["haasscript", "hs"]:
                    code = "\n".join(code.split("\n")[1:])
                return code.strip()
        
        return text
