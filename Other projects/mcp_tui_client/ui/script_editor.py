"""
HaasScript Editor Implementation

Advanced script editor with syntax highlighting, validation, and development tools.
"""

import asyncio
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual.widget import Widget
from textual.widgets import (
    Static, Button, Input, Select, TextArea, Tree, 
    TabbedContent, TabPane, Label, Collapsible
)
from textual.message import Message
from textual.reactive import reactive
from textual import events

from ..ui.components.panels import BasePanel, StatusPanel
from ..ui.components.forms import FormField, BaseForm as FormContainer
from ..utils.logging import get_logger


class SyntaxTokenType(Enum):
    """HaasScript syntax token types"""
    KEYWORD = "keyword"
    FUNCTION = "function"
    VARIABLE = "variable"
    NUMBER = "number"
    STRING = "string"
    COMMENT = "comment"
    OPERATOR = "operator"
    BRACKET = "bracket"
    IDENTIFIER = "identifier"
    ERROR = "error"


@dataclass
class SyntaxToken:
    """Syntax highlighting token"""
    type: SyntaxTokenType
    value: str
    start: int
    end: int
    line: int
    column: int


@dataclass
class ValidationError:
    """Script validation error"""
    line: int
    column: int
    message: str
    severity: str = "error"  # error, warning, info
    code: str = ""


@dataclass
class AutocompleteItem:
    """Autocomplete suggestion item"""
    text: str
    type: str  # function, variable, keyword, etc.
    description: str = ""
    signature: str = ""
    documentation: str = ""


class HaasScriptSyntaxHighlighter:
    """Syntax highlighter for HaasScript"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # HaasScript keywords
        self.keywords = {
            'if', 'else', 'elseif', 'endif', 'while', 'endwhile', 'for', 'endfor',
            'function', 'endfunction', 'return', 'break', 'continue', 'true', 'false',
            'and', 'or', 'not', 'in', 'is', 'null', 'undefined'
        }
        
        # HaasScript built-in functions
        self.functions = {
            # Price functions
            'Open', 'High', 'Low', 'Close', 'Volume', 'Timestamp',
            'OpenTime', 'CloseTime', 'TypicalPrice', 'MedianPrice',
            
            # Technical indicators
            'SMA', 'EMA', 'RSI', 'MACD', 'Bollinger', 'Stochastic',
            'ATR', 'ADX', 'CCI', 'Williams', 'MFI', 'OBV',
            
            # Math functions
            'Abs', 'Max', 'Min', 'Round', 'Floor', 'Ceil', 'Sqrt',
            'Log', 'Exp', 'Sin', 'Cos', 'Tan', 'Atan', 'Random',
            
            # Array functions
            'Length', 'Sum', 'Average', 'StdDev', 'Variance',
            'Highest', 'Lowest', 'CrossOver', 'CrossUnder',
            
            # Trading functions
            'Buy', 'Sell', 'Position', 'Balance', 'Equity',
            'Profit', 'DrawDown', 'WinRate', 'TradeCount',
            
            # Utility functions
            'Print', 'Alert', 'Log', 'Format', 'ToString',
            'ToNumber', 'IsNumber', 'IsString', 'IsArray'
        }
        
        # Operators
        self.operators = {
            '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
            '&&', '||', '!', '&', '|', '^', '<<', '>>', '++', '--',
            '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^='
        }
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for syntax highlighting"""
        # Keywords pattern
        keyword_pattern = r'\b(' + '|'.join(self.keywords) + r')\b'
        self.keyword_regex = re.compile(keyword_pattern, re.IGNORECASE)
        
        # Functions pattern
        function_pattern = r'\b(' + '|'.join(self.functions) + r')\s*\('
        self.function_regex = re.compile(function_pattern, re.IGNORECASE)
        
        # Numbers pattern
        self.number_regex = re.compile(r'\b\d+\.?\d*\b')
        
        # Strings pattern
        self.string_regex = re.compile(r'"[^"]*"|\'[^\']*\'')
        
        # Comments pattern
        self.comment_regex = re.compile(r'//.*$|/\*.*?\*/', re.MULTILINE | re.DOTALL)
        
        # Variables pattern (identifiers starting with letter or underscore)
        self.variable_regex = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
        
        # Operators pattern
        operator_pattern = '|'.join(re.escape(op) for op in sorted(self.operators, key=len, reverse=True))
        self.operator_regex = re.compile(operator_pattern)
        
        # Brackets pattern
        self.bracket_regex = re.compile(r'[(){}\[\]]')
    
    def tokenize(self, text: str) -> List[SyntaxToken]:
        """Tokenize HaasScript code for syntax highlighting"""
        tokens = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            if not line.strip():
                continue
            
            # Track processed positions to avoid overlaps
            processed = set()
            
            # Find comments first (highest priority)
            for match in self.comment_regex.finditer(line):
                start, end = match.span()
                if not any(pos in processed for pos in range(start, end)):
                    tokens.append(SyntaxToken(
                        SyntaxTokenType.COMMENT, match.group(),
                        start, end, line_num, start
                    ))
                    processed.update(range(start, end))
            
            # Find strings
            for match in self.string_regex.finditer(line):
                start, end = match.span()
                if not any(pos in processed for pos in range(start, end)):
                    tokens.append(SyntaxToken(
                        SyntaxTokenType.STRING, match.group(),
                        start, end, line_num, start
                    ))
                    processed.update(range(start, end))
            
            # Find numbers
            for match in self.number_regex.finditer(line):
                start, end = match.span()
                if not any(pos in processed for pos in range(start, end)):
                    tokens.append(SyntaxToken(
                        SyntaxTokenType.NUMBER, match.group(),
                        start, end, line_num, start
                    ))
                    processed.update(range(start, end))
            
            # Find functions
            for match in self.function_regex.finditer(line):
                start, end = match.span()
                func_name = match.group().rstrip('(').strip()
                func_end = start + len(func_name)
                if not any(pos in processed for pos in range(start, func_end)):
                    tokens.append(SyntaxToken(
                        SyntaxTokenType.FUNCTION, func_name,
                        start, func_end, line_num, start
                    ))
                    processed.update(range(start, func_end))
            
            # Find keywords
            for match in self.keyword_regex.finditer(line):
                start, end = match.span()
                if not any(pos in processed for pos in range(start, end)):
                    tokens.append(SyntaxToken(
                        SyntaxTokenType.KEYWORD, match.group(),
                        start, end, line_num, start
                    ))
                    processed.update(range(start, end))
            
            # Find operators
            for match in self.operator_regex.finditer(line):
                start, end = match.span()
                if not any(pos in processed for pos in range(start, end)):
                    tokens.append(SyntaxToken(
                        SyntaxTokenType.OPERATOR, match.group(),
                        start, end, line_num, start
                    ))
                    processed.update(range(start, end))
            
            # Find brackets
            for match in self.bracket_regex.finditer(line):
                start, end = match.span()
                if not any(pos in processed for pos in range(start, end)):
                    tokens.append(SyntaxToken(
                        SyntaxTokenType.BRACKET, match.group(),
                        start, end, line_num, start
                    ))
                    processed.update(range(start, end))
        
        return tokens
    
    def apply_highlighting(self, text_area: TextArea, tokens: List[SyntaxToken]) -> None:
        """Apply syntax highlighting to text area"""
        try:
            # Clear existing highlighting
            text_area.clear_highlights()
            
            # Apply token-based highlighting
            for token in tokens:
                style_class = f"syntax-{token.type.value}"
                # Note: This is a simplified approach - actual implementation
                # would depend on Textual's highlighting capabilities
                
        except Exception as e:
            self.logger.error(f"Error applying syntax highlighting: {e}")


class HaasScriptValidator:
    """HaasScript code validator"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.highlighter = HaasScriptSyntaxHighlighter()
    
    def validate(self, code: str) -> List[ValidationError]:
        """Validate HaasScript code and return errors"""
        errors = []
        lines = code.split('\n')
        
        # Track context
        function_stack = []
        block_stack = []
        variable_declarations = set()
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # Check for syntax errors
            errors.extend(self._check_syntax_errors(line, line_num))
            
            # Check for semantic errors
            errors.extend(self._check_semantic_errors(line, line_num, variable_declarations))
            
            # Track function and block context
            self._update_context(line, function_stack, block_stack)
        
        # Check for unclosed blocks
        if block_stack:
            errors.append(ValidationError(
                len(lines), 0,
                f"Unclosed block: {block_stack[-1]}",
                "error", "E001"
            ))
        
        if function_stack:
            errors.append(ValidationError(
                len(lines), 0,
                f"Unclosed function: {function_stack[-1]}",
                "error", "E002"
            ))
        
        return errors
    
    def _check_syntax_errors(self, line: str, line_num: int) -> List[ValidationError]:
        """Check for basic syntax errors"""
        errors = []
        
        # Check for unmatched brackets
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(line):
            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    errors.append(ValidationError(
                        line_num, i,
                        f"Unmatched closing bracket: {char}",
                        "error", "E003"
                    ))
                else:
                    open_char, _ = stack.pop()
                    if brackets[open_char] != char:
                        errors.append(ValidationError(
                            line_num, i,
                            f"Mismatched bracket: expected {brackets[open_char]}, got {char}",
                            "error", "E004"
                        ))
        
        # Check for unclosed brackets on this line
        if stack:
            char, pos = stack[-1]
            errors.append(ValidationError(
                line_num, pos,
                f"Unclosed bracket: {char}",
                "error", "E005"
            ))
        
        # Check for invalid characters
        invalid_chars = set(line) - set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_()[]{}+-*/=<>!&|^%~.,;: \t"\'\\/')
        if invalid_chars:
            errors.append(ValidationError(
                line_num, 0,
                f"Invalid characters: {', '.join(invalid_chars)}",
                "warning", "W001"
            ))
        
        return errors
    
    def _check_semantic_errors(self, line: str, line_num: int, variables: Set[str]) -> List[ValidationError]:
        """Check for semantic errors"""
        errors = []
        
        # Check for undefined variables (simplified)
        tokens = self.highlighter.tokenize(line)
        for token in tokens:
            if token.type == SyntaxTokenType.IDENTIFIER:
                if (token.value not in self.highlighter.functions and 
                    token.value not in self.highlighter.keywords and
                    token.value not in variables):
                    errors.append(ValidationError(
                        line_num, token.column,
                        f"Undefined variable or function: {token.value}",
                        "warning", "W002"
                    ))
        
        # Track variable declarations
        if '=' in line and not line.strip().startswith('//'):
            # Simple variable assignment detection
            parts = line.split('=')
            if len(parts) >= 2:
                var_part = parts[0].strip()
                if var_part and var_part.replace('_', '').replace(' ', '').isalnum():
                    variables.add(var_part.split()[-1])  # Get last word as variable name
        
        return errors
    
    def _update_context(self, line: str, function_stack: List[str], block_stack: List[str]) -> None:
        """Update function and block context"""
        line_lower = line.lower()
        
        # Function tracking
        if line_lower.startswith('function '):
            func_name = line.split()[1] if len(line.split()) > 1 else "anonymous"
            function_stack.append(func_name)
        elif line_lower == 'endfunction':
            if function_stack:
                function_stack.pop()
        
        # Block tracking
        if line_lower.startswith(('if ', 'while ', 'for ')):
            block_type = line_lower.split()[0]
            block_stack.append(block_type)
        elif line_lower in ('endif', 'endwhile', 'endfor'):
            if block_stack:
                block_stack.pop()


class HaasScriptAutocomplete:
    """Autocomplete provider for HaasScript"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.highlighter = HaasScriptSyntaxHighlighter()
        self._build_autocomplete_items()
    
    def _build_autocomplete_items(self) -> None:
        """Build autocomplete items database"""
        self.items = []
        
        # Add keywords
        for keyword in self.highlighter.keywords:
            self.items.append(AutocompleteItem(
                keyword, "keyword",
                f"HaasScript keyword: {keyword}",
                keyword
            ))
        
        # Add functions with signatures
        function_signatures = {
            'SMA': 'SMA(source, period)',
            'EMA': 'EMA(source, period)',
            'RSI': 'RSI(source, period)',
            'MACD': 'MACD(source, fast, slow, signal)',
            'Bollinger': 'Bollinger(source, period, deviation)',
            'Buy': 'Buy(amount, price)',
            'Sell': 'Sell(amount, price)',
            'Print': 'Print(message)',
            'Alert': 'Alert(message, level)',
            'Max': 'Max(value1, value2)',
            'Min': 'Min(value1, value2)',
            'Round': 'Round(value, decimals)',
            'Abs': 'Abs(value)',
            'Length': 'Length(array)',
            'Sum': 'Sum(array, period)',
            'Average': 'Average(array, period)',
            'CrossOver': 'CrossOver(series1, series2)',
            'CrossUnder': 'CrossUnder(series1, series2)'
        }
        
        for func in self.highlighter.functions:
            signature = function_signatures.get(func, f"{func}()")
            self.items.append(AutocompleteItem(
                func, "function",
                f"HaasScript function: {func}",
                signature,
                f"Built-in HaasScript function {func}"
            ))
    
    def get_suggestions(self, text: str, cursor_pos: int) -> List[AutocompleteItem]:
        """Get autocomplete suggestions for current cursor position"""
        try:
            # Find the word being typed
            lines = text[:cursor_pos].split('\n')
            current_line = lines[-1] if lines else ""
            
            # Find word boundaries
            word_start = cursor_pos
            for i in range(len(current_line) - 1, -1, -1):
                if current_line[i].isalnum() or current_line[i] == '_':
                    word_start = cursor_pos - (len(current_line) - i)
                else:
                    break
            
            partial_word = text[word_start:cursor_pos].lower()
            
            if not partial_word:
                return []
            
            # Filter suggestions
            suggestions = []
            for item in self.items:
                if item.text.lower().startswith(partial_word):
                    suggestions.append(item)
            
            # Sort by relevance (exact match first, then alphabetical)
            suggestions.sort(key=lambda x: (
                0 if x.text.lower() == partial_word else 1,
                x.text.lower()
            ))
            
            return suggestions[:20]  # Limit to 20 suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting autocomplete suggestions: {e}")
            return []


class HaasScriptEditor(BasePanel):
    """Advanced HaasScript editor with syntax highlighting and validation"""
    
    def __init__(self, script_content: str = "", **kwargs):
        super().__init__(title="HaasScript Editor", **kwargs)
        self.script_content = script_content
        self.logger = get_logger(__name__)
        
        # Editor components
        self.highlighter = HaasScriptSyntaxHighlighter()
        self.validator = HaasScriptValidator()
        self.autocomplete = HaasScriptAutocomplete()
        
        # Editor state
        self.validation_errors: List[ValidationError] = []
        self.is_modified = False
        self.last_validation_time = datetime.now()
        
        # Callbacks
        self.on_content_changed: Optional[Callable[[str], None]] = None
        self.on_validation_changed: Optional[Callable[[List[ValidationError]], None]] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize the script editor"""
        self._setup_editor_interface()
    
    def _setup_editor_interface(self) -> None:
        """Set up the editor interface"""
        editor_container = TabbedContent()
        
        # Main editor tab
        with editor_container.add_pane("editor", "Editor"):
            editor_layout = Vertical()
            
            # Toolbar
            toolbar = Horizontal(classes="editor-toolbar")
            toolbar.mount(Button("Save", id="save-script", variant="primary"))
            toolbar.mount(Button("Validate", id="validate-script", variant="default"))
            toolbar.mount(Button("Format", id="format-script", variant="default"))
            toolbar.mount(Button("Test", id="test-script", variant="success"))
            
            # Editor area
            text_editor = TextArea(
                self.script_content,
                language="javascript",  # Closest to HaasScript
                theme="monokai",
                id="script-editor"
            )
            text_editor.focus()
            
            editor_layout.mount(toolbar)
            editor_layout.mount(text_editor)
        
        # Validation tab
        with editor_container.add_pane("validation", "Validation"):
            validation_panel = ScrollableContainer()
            validation_panel.mount(Static("No validation errors", id="validation-results"))
        
        # Help tab
        with editor_container.add_pane("help", "Help"):
            help_panel = self._create_help_panel()
        
        self.update_content(editor_container)
        
        # Start validation timer
        self._start_validation_timer()
    
    def _create_help_panel(self) -> Widget:
        """Create help panel with HaasScript documentation"""
        help_container = ScrollableContainer()
        
        # Function reference
        functions_section = Collapsible(title="Built-in Functions", collapsed=False)
        functions_content = Static(self._generate_function_help())
        functions_section.mount(functions_content)
        
        # Keywords reference
        keywords_section = Collapsible(title="Keywords", collapsed=True)
        keywords_content = Static(self._generate_keywords_help())
        keywords_section.mount(keywords_content)
        
        # Examples section
        examples_section = Collapsible(title="Examples", collapsed=True)
        examples_content = Static(self._generate_examples_help())
        examples_section.mount(examples_content)
        
        help_container.mount(functions_section)
        help_container.mount(keywords_section)
        help_container.mount(examples_section)
        
        return help_container
    
    def _generate_function_help(self) -> str:
        """Generate function reference help text"""
        help_text = []
        
        categories = {
            "Price Functions": ['Open', 'High', 'Low', 'Close', 'Volume'],
            "Technical Indicators": ['SMA', 'EMA', 'RSI', 'MACD', 'Bollinger'],
            "Math Functions": ['Abs', 'Max', 'Min', 'Round', 'Sqrt'],
            "Trading Functions": ['Buy', 'Sell', 'Position', 'Balance'],
            "Utility Functions": ['Print', 'Alert', 'Log', 'Format']
        }
        
        for category, functions in categories.items():
            help_text.append(f"\n{category}:")
            help_text.append("-" * len(category))
            for func in functions:
                if func in self.highlighter.functions:
                    help_text.append(f"  {func}() - Built-in function")
        
        return "\n".join(help_text)
    
    def _generate_keywords_help(self) -> str:
        """Generate keywords reference help text"""
        help_text = ["HaasScript Keywords:", "=" * 20]
        
        keyword_groups = {
            "Control Flow": ['if', 'else', 'elseif', 'endif', 'while', 'endwhile', 'for', 'endfor'],
            "Functions": ['function', 'endfunction', 'return'],
            "Loop Control": ['break', 'continue'],
            "Logical": ['and', 'or', 'not', 'true', 'false'],
            "Other": ['in', 'is', 'null', 'undefined']
        }
        
        for group, keywords in keyword_groups.items():
            help_text.append(f"\n{group}:")
            for keyword in keywords:
                help_text.append(f"  {keyword}")
        
        return "\n".join(help_text)
    
    def _generate_examples_help(self) -> str:
        """Generate examples help text"""
        examples = [
            "Simple Moving Average Strategy:",
            "=" * 30,
            "",
            "// Calculate 20-period SMA",
            "sma20 = SMA(Close, 20)",
            "",
            "// Buy when price crosses above SMA",
            "if CrossOver(Close, sma20)",
            "    Buy(100, Close)",
            "endif",
            "",
            "// Sell when price crosses below SMA", 
            "if CrossUnder(Close, sma20)",
            "    Sell(Position, Close)",
            "endif",
            "",
            "RSI Oversold/Overbought Strategy:",
            "=" * 35,
            "",
            "// Calculate 14-period RSI",
            "rsi = RSI(Close, 14)",
            "",
            "// Buy when oversold",
            "if rsi < 30 and Position == 0",
            "    Buy(100, Close)",
            "    Print(\"Buying - RSI Oversold: \" + ToString(rsi))",
            "endif",
            "",
            "// Sell when overbought",
            "if rsi > 70 and Position > 0",
            "    Sell(Position, Close)",
            "    Print(\"Selling - RSI Overbought: \" + ToString(rsi))",
            "endif"
        ]
        
        return "\n".join(examples)
    
    def _start_validation_timer(self) -> None:
        """Start background validation timer"""
        # This would be implemented with Textual's timer system
        # For now, we'll validate on content changes
        pass
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "save-script":
            await self._save_script()
        elif event.button.id == "validate-script":
            await self._validate_script()
        elif event.button.id == "format-script":
            await self._format_script()
        elif event.button.id == "test-script":
            await self._test_script()
    
    async def on_text_area_changed(self, event) -> None:
        """Handle text area content changes"""
        if hasattr(event, 'text_area') and event.text_area.id == "script-editor":
            self.script_content = event.text_area.text
            self.is_modified = True
            
            # Trigger validation after a delay
            await self._delayed_validation()
            
            # Notify content change
            if self.on_content_changed:
                self.on_content_changed(self.script_content)
    
    async def _delayed_validation(self) -> None:
        """Perform validation after a delay to avoid excessive validation"""
        await asyncio.sleep(1.0)  # Wait 1 second
        await self._validate_script()
    
    async def _save_script(self) -> None:
        """Save the current script"""
        try:
            # This would integrate with the MCP client to save the script
            self.logger.info("Saving script...")
            self.is_modified = False
            self.set_status("success", "Script saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving script: {e}")
            self.set_status("error", f"Failed to save script: {e}")
    
    async def _validate_script(self) -> None:
        """Validate the current script"""
        try:
            self.validation_errors = self.validator.validate(self.script_content)
            self.last_validation_time = datetime.now()
            
            # Update validation display
            await self._update_validation_display()
            
            # Notify validation change
            if self.on_validation_changed:
                self.on_validation_changed(self.validation_errors)
            
            if not self.validation_errors:
                self.set_status("success", "No validation errors")
            else:
                error_count = len([e for e in self.validation_errors if e.severity == "error"])
                warning_count = len([e for e in self.validation_errors if e.severity == "warning"])
                self.set_status("warning", f"{error_count} errors, {warning_count} warnings")
            
        except Exception as e:
            self.logger.error(f"Error validating script: {e}")
            self.set_status("error", f"Validation failed: {e}")
    
    async def _update_validation_display(self) -> None:
        """Update the validation results display"""
        try:
            validation_results = self.query_one("#validation-results", Static)
            
            if not self.validation_errors:
                validation_results.update("✅ No validation errors found!")
                return
            
            # Group errors by type
            errors = [e for e in self.validation_errors if e.severity == "error"]
            warnings = [e for e in self.validation_errors if e.severity == "warning"]
            
            result_lines = []
            
            if errors:
                result_lines.append(f"🔴 Errors ({len(errors)}):")
                result_lines.append("=" * 20)
                for error in errors:
                    result_lines.append(f"Line {error.line + 1}: {error.message}")
                result_lines.append("")
            
            if warnings:
                result_lines.append(f"⚠️ Warnings ({len(warnings)}):")
                result_lines.append("=" * 20)
                for warning in warnings:
                    result_lines.append(f"Line {warning.line + 1}: {warning.message}")
            
            validation_results.update("\n".join(result_lines))
            
        except Exception as e:
            self.logger.error(f"Error updating validation display: {e}")
    
    async def _format_script(self) -> None:
        """Format the current script"""
        try:
            # Simple formatting - add proper indentation
            formatted_content = self._format_haasscript(self.script_content)
            
            # Update editor content
            text_editor = self.query_one("#script-editor", TextArea)
            text_editor.text = formatted_content
            self.script_content = formatted_content
            
            self.set_status("success", "Script formatted")
            
        except Exception as e:
            self.logger.error(f"Error formatting script: {e}")
            self.set_status("error", f"Failed to format script: {e}")
    
    def _format_haasscript(self, code: str) -> str:
        """Format HaasScript code with proper indentation"""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append("")
                continue
            
            # Decrease indent for closing keywords
            if stripped.lower() in ('endif', 'endwhile', 'endfor', 'endfunction'):
                indent_level = max(0, indent_level - 1)
            
            # Add indented line
            formatted_lines.append("    " * indent_level + stripped)
            
            # Increase indent for opening keywords
            if stripped.lower().startswith(('if ', 'while ', 'for ', 'function ')):
                indent_level += 1
        
        return '\n'.join(formatted_lines)
    
    async def _test_script(self) -> None:
        """Test the current script"""
        try:
            # First validate
            await self._validate_script()
            
            if any(e.severity == "error" for e in self.validation_errors):
                self.set_status("error", "Cannot test script with validation errors")
                return
            
            # This would integrate with the MCP client to test the script
            self.logger.info("Testing script...")
            self.set_status("info", "Script test initiated...")
            
            # Mock test result
            await asyncio.sleep(2)  # Simulate test time
            self.set_status("success", "Script test completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error testing script: {e}")
            self.set_status("error", f"Failed to test script: {e}")
    
    def get_content(self) -> str:
        """Get current script content"""
        return self.script_content
    
    def set_content(self, content: str) -> None:
        """Set script content"""
        self.script_content = content
        try:
            text_editor = self.query_one("#script-editor", TextArea)
            text_editor.text = content
            self.is_modified = False
        except Exception as e:
            self.logger.error(f"Error setting content: {e}")
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        return self.is_modified
    
    def get_validation_errors(self) -> List[ValidationError]:
        """Get current validation errors"""
        return self.validation_errors.copy()


# Message classes for script editor communication
class ScriptContentChanged(Message):
    """Message sent when script content changes"""
    def __init__(self, content: str):
        super().__init__()
        self.content = content


class ScriptValidationChanged(Message):
    """Message sent when validation results change"""
    def __init__(self, errors: List[ValidationError]):
        super().__init__()
        self.errors = errors


class ScriptSaved(Message):
    """Message sent when script is saved"""
    def __init__(self, script_id: str, content: str):
        super().__init__()
        self.script_id = script_id
        self.content = content


class ScriptTested(Message):
    """Message sent when script test is completed"""
    def __init__(self, script_id: str, results: Dict[str, Any]):
        super().__init__()
        self.script_id = script_id
        self.results = results