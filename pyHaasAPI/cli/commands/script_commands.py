"""
Script command handlers - Direct calls to ScriptAPI
"""

from typing import Any
from ..base import BaseCLI


class ScriptCommands:
    """Script command handlers - thin wrappers around ScriptAPI"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle script commands"""
        script_api = self.cli.script_api
        
        if not script_api:
            self.cli.logger.error("Script API not initialized")
            return 1
        
        try:
            if action == 'list':
                # Direct API call
                scripts = await script_api.get_all_scripts()
                self.cli.format_output(scripts, args.output_format, args.output_file)
                return 0
                
            elif action == 'create':
                # Direct API call
                if not args.name or not args.source:
                    self.cli.logger.error("--name and --source are required")
                    return 1
                
                script = await script_api.create_script(
                    name=args.name,
                    source_code=args.source,
                    description=args.description or ""
                )
                self.cli.format_output([script], args.output_format, args.output_file)
                return 0
                
            elif action == 'edit':
                # Direct API call
                if not args.script_id or not args.source:
                    self.cli.logger.error("--script-id and --source are required")
                    return 1
                
                script = await script_api.edit_script(
                    script_id=args.script_id,
                    source_code=args.source,
                    description=args.description
                )
                self.cli.format_output([script], args.output_format, args.output_file)
                return 0
                
            elif action == 'delete':
                # Direct API call
                if not args.script_id:
                    self.cli.logger.error("--script-id is required")
                    return 1
                
                success = await script_api.delete_script(args.script_id)
                if success:
                    self.cli.logger.info(f"Script {args.script_id} deleted")
                    return 0
                else:
                    self.cli.logger.error("Failed to delete script")
                    return 1
                    
            elif action == 'test':
                # Direct API call
                if not args.script_id:
                    self.cli.logger.error("--script-id is required")
                    return 1
                
                result = await script_api.test_script(args.script_id)
                self.cli.format_output([result], args.output_format, args.output_file)
                return 0
                
            elif action == 'publish':
                # Direct API call
                if not args.script_id:
                    self.cli.logger.error("--script-id is required")
                    return 1
                
                success = await script_api.publish_script(args.script_id)
                if success:
                    self.cli.logger.info(f"Script {args.script_id} published")
                    return 0
                else:
                    self.cli.logger.error("Failed to publish script")
                    return 1
                    
            else:
                self.cli.logger.error(f"Unknown script action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing script command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1



