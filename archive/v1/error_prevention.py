"""
Comprehensive Error Prevention System

This module provides automated detection and prevention of common API and Pydantic usage errors.
"""

import ast
import logging
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any
import inspect

logger = logging.getLogger(__name__)

class ErrorPreventionSystem:
    """Comprehensive system to prevent common API and Pydantic usage errors."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues_found = []
        
    def scan_for_missing_auth_params(self) -> List[Dict[str, Any]]:
        """Scan all API functions for missing authentication parameters."""
        logger.info("🔍 Scanning for missing authentication parameters...")
        
        issues = []
        
        # Check pyHaasAPI/api.py for functions missing auth params
        api_file = self.project_root / "pyHaasAPI" / "api.py"
        if api_file.exists():
            issues.extend(self._check_api_file_auth_params(api_file))
        
        return issues
    
    def _check_api_file_auth_params(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check a specific API file for missing authentication parameters."""
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find all executor.execute calls
            execute_pattern = r'executor\.execute\(\s*endpoint="([^"]+)",\s*response_type=[^,]+,\s*query_params=\{(.*?)\},'
            
            for match in re.finditer(execute_pattern, content, re.DOTALL):
                endpoint = match.group(1)
                query_params = match.group(2)
                
                # Check if userid and interfacekey are missing
                if endpoint in ["Labs", "Bot", "Scripts", "Accounts"]:
                    if "userid" not in query_params or "interfacekey" not in query_params:
                        # Find the function name
                        func_name = self._find_function_name(content, match.start())
                        
                        issues.append({
                            'type': 'missing_auth_params',
                            'file': str(file_path),
                            'function': func_name,
                            'endpoint': endpoint,
                            'missing_params': self._get_missing_auth_params(query_params),
                            'line': content[:match.start()].count('\n') + 1
                        })
        
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
        
        return issues
    
    def _find_function_name(self, content: str, position: int) -> str:
        """Find the function name containing the given position."""
        lines = content[:position].split('\n')
        for line in reversed(lines):
            if line.strip().startswith('def '):
                return line.strip().split('(')[0].replace('def ', '')
        return "unknown"
    
    def _get_missing_auth_params(self, query_params: str) -> List[str]:
        """Get list of missing authentication parameters."""
        missing = []
        if "userid" not in query_params:
            missing.append("userid")
        if "interfacekey" not in query_params:
            missing.append("interfacekey")
        return missing
    
    def scan_for_pydantic_get_usage(self) -> List[Dict[str, Any]]:
        """Scan for incorrect .get() usage on Pydantic models."""
        logger.info("🔍 Scanning for Pydantic model .get() usage errors...")
        
        issues = []
        
        # Scan all Python files in pyHaasAPI
        for py_file in self.project_root.glob("pyHaasAPI/**/*.py"):
            if py_file.name == "__init__.py":
                continue
                
            issues.extend(self._check_pydantic_usage(py_file))
        
        return issues
    
    def _check_pydantic_usage(self, file_path: Path) -> List[Dict[str, Any]]:
        """Check a file for incorrect Pydantic model usage."""
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find .get( patterns that might be on Pydantic models
            get_pattern = r'(\w+)\.get\('
            
            for match in re.finditer(get_pattern, content):
                variable_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                # Check if this variable is likely a Pydantic model
                if self._is_likely_pydantic_model(content, variable_name, match.start()):
                    issues.append({
                        'type': 'pydantic_get_usage',
                        'file': str(file_path),
                        'variable': variable_name,
                        'line': line_num,
                        'suggestion': f"Use {variable_name}.attribute_name or getattr({variable_name}, 'attribute_name', default)"
                    })
        
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
        
        return issues
    
    def _is_likely_pydantic_model(self, content: str, variable_name: str, position: int) -> bool:
        """Check if a variable is likely a Pydantic model."""
        # Look for common Pydantic model patterns
        pydantic_patterns = [
            r'HaasBot\(',
            r'LabDetails\(',
            r'BacktestRuntimeData\(',
            r'CloudMarket\(',
            r'LabExecutionUpdate\(',
            r'AuthenticatedSessionResponse\(',
        ]
        
        # Check if the variable is assigned from a Pydantic model
        before_position = content[:position]
        for pattern in pydantic_patterns:
            if f"{variable_name} = " in before_position and pattern in before_position:
                return True
        
        return False
    
    def generate_fixes(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate fix suggestions for found issues."""
        fixes = []
        
        for issue in issues:
            if issue['type'] == 'missing_auth_params':
                fix = self._generate_auth_param_fix(issue)
                fixes.append(fix)
            elif issue['type'] == 'pydantic_get_usage':
                fix = self._generate_pydantic_fix(issue)
                fixes.append(fix)
        
        return fixes
    
    def _generate_auth_param_fix(self, issue: Dict[str, Any]) -> str:
        """Generate fix for missing authentication parameters."""
        missing_params = issue['missing_params']
        fix_lines = []
        
        for param in missing_params:
            if param == "userid":
                fix_lines.append('            "userid": getattr(executor.state, \'user_id\', None),')
            elif param == "interfacekey":
                fix_lines.append('            "interfacekey": getattr(executor.state, \'interface_key\', None),')
        
        return f"""
File: {issue['file']}
Function: {issue['function']}
Line: {issue['line']}
Issue: Missing authentication parameters: {', '.join(missing_params)}

Fix: Add these lines to the query_params dictionary:
{chr(10).join(fix_lines)}
"""
    
    def _generate_pydantic_fix(self, issue: Dict[str, Any]) -> str:
        """Generate fix for Pydantic model .get() usage."""
        return f"""
File: {issue['file']}
Line: {issue['line']}
Issue: Using .get() on Pydantic model {issue['variable']}

Fix: Replace {issue['variable']}.get('attribute') with:
  - {issue['variable']}.attribute_name (direct access)
  - getattr({issue['variable']}, 'attribute_name', default) (with default)
"""
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run comprehensive error prevention check."""
        logger.info("🛡️ Running comprehensive error prevention check...")
        
        results = {
            'auth_param_issues': self.scan_for_missing_auth_params(),
            'pydantic_issues': self.scan_for_pydantic_get_usage(),
            'total_issues': 0,
            'fixes': []
        }
        
        results['total_issues'] = len(results['auth_param_issues']) + len(results['pydantic_issues'])
        results['fixes'] = self.generate_fixes(results['auth_param_issues'] + results['pydantic_issues'])
        
        # Log results
        logger.info(f"📊 Error Prevention Check Results:")
        logger.info(f"  🔐 Missing auth params: {len(results['auth_param_issues'])}")
        logger.info(f"  🏗️ Pydantic usage errors: {len(results['pydantic_issues'])}")
        logger.info(f"  📝 Total issues: {results['total_issues']}")
        
        return results

def create_linting_rules():
    """Create linting rules to catch these errors automatically."""
    rules = {
        "pydantic-get-usage": {
            "description": "Prevent .get() usage on Pydantic models",
            "pattern": r"(\w+)\.get\(",
            "message": "Use attribute access or getattr() instead of .get() on Pydantic models"
        },
        "missing-auth-params": {
            "description": "Ensure API functions have required authentication parameters",
            "pattern": r'query_params=\{[^}]*"channel":\s*"[^"]*",\s*[^}]*\}',
            "message": "API functions must include userid and interfacekey parameters"
        }
    }
    
    return rules

def main():
    """Main function to run error prevention checks."""
    system = ErrorPreventionSystem()
    results = system.run_comprehensive_check()
    
    if results['total_issues'] > 0:
        print("\n🔧 Fixes needed:")
        for fix in results['fixes']:
            print(fix)
        
        print(f"\n❌ Found {results['total_issues']} issues that need fixing")
        return False
    else:
        print("\n✅ No issues found! Code is clean.")
        return True

if __name__ == "__main__":
    main()





