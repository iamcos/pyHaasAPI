"""
Script CLI module using v2 APIs and centralized managers.
Provides script management functionality.
"""

import asyncio
import argparse
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli_ref.base import EnhancedBaseCLI
from pyHaasAPI.core.logging import get_logger


class ScriptCLI(EnhancedBaseCLI):
    """Script management CLI using v2 APIs and centralized managers"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("script_cli")

    async def list_scripts(self) -> Dict[str, Any]:
        """List all available scripts"""
        try:
            self.logger.info("Listing all scripts")
            
            if not self.script_api:
                return {"error": "Script API not available"}
            
            scripts = await self.script_api.list_scripts()
            
            return {
                "success": True,
                "scripts": scripts,
                "count": len(scripts) if scripts else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error listing scripts: {e}")
            return {"error": str(e)}

    async def get_script_details(self, script_id: str) -> Dict[str, Any]:
        """Get script details"""
        try:
            self.logger.info(f"Getting script details for {script_id}")
            
            if not self.script_api:
                return {"error": "Script API not available"}
            
            script = await self.script_api.get_script_details(script_id)
            
            if script:
                return {
                    "success": True,
                    "script": script
                }
            else:
                return {
                    "success": False,
                    "error": f"Script {script_id} not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting script details: {e}")
            return {"error": str(e)}

    async def get_script_code(self, script_id: str) -> Dict[str, Any]:
        """Get script source code"""
        try:
            self.logger.info(f"Getting script code for {script_id}")
            
            if not self.script_api:
                return {"error": "Script API not available"}
            
            code = await self.script_api.get_script_code(script_id)
            
            if code:
                return {
                    "success": True,
                    "script_id": script_id,
                    "code": code
                }
            else:
                return {
                    "success": False,
                    "error": f"Could not retrieve code for script {script_id}"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting script code: {e}")
            return {"error": str(e)}

    async def create_script(self, name: str, code: str, description: str = "") -> Dict[str, Any]:
        """Create a new script"""
        try:
            self.logger.info(f"Creating script: {name}")
            
            if not self.script_api:
                return {"error": "Script API not available"}
            
            script = await self.script_api.create_script(
                name=name,
                code=code,
                description=description
            )
            
            if script:
                return {
                    "success": True,
                    "script": script,
                    "message": f"Script '{name}' created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create script"
                }
                
        except Exception as e:
            self.logger.error(f"Error creating script: {e}")
            return {"error": str(e)}

    async def update_script(self, script_id: str, name: str = None, code: str = None, description: str = None) -> Dict[str, Any]:
        """Update an existing script"""
        try:
            self.logger.info(f"Updating script {script_id}")
            
            if not self.script_api:
                return {"error": "Script API not available"}
            
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if code is not None:
                update_data['code'] = code
            if description is not None:
                update_data['description'] = description
            
            if not update_data:
                return {"error": "No update data provided"}
            
            success = await self.script_api.update_script(script_id, update_data)
            
            if success:
                return {
                    "success": True,
                    "message": f"Script {script_id} updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to update script {script_id}"
                }
                
        except Exception as e:
            self.logger.error(f"Error updating script: {e}")
            return {"error": str(e)}

    def print_scripts_report(self, scripts_data: Dict[str, Any]):
        """Print scripts report"""
        try:
            if "error" in scripts_data:
                print(f"❌ Error: {scripts_data['error']}")
                return
            
            scripts = scripts_data.get("scripts", [])
            count = scripts_data.get("count", 0)
            
            print("\n" + "="*80)
            print("📜 SCRIPTS REPORT")
            print("="*80)
            print(f"📊 Total Scripts: {count}")
            print("-"*80)
            
            if scripts:
                for script in scripts:
                    script_id = getattr(script, 'id', 'Unknown')
                    script_name = getattr(script, 'name', 'Unknown')
                    description = getattr(script, 'description', 'No description')
                    status = getattr(script, 'status', 'Unknown')
                    
                    print(f"📜 {script_name}")
                    print(f"   ID: {script_id}")
                    print(f"   Description: {description}")
                    print(f"   Status: {status}")
                    print()
            else:
                print("No scripts found")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing scripts report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_script_details_report(self, script_data: Dict[str, Any]):
        """Print script details report"""
        try:
            if "error" in script_data:
                print(f"❌ Error: {script_data['error']}")
                return
            
            if not script_data.get("success", False):
                print(f"❌ {script_data.get('error', 'Unknown error')}")
                return
            
            script = script_data.get("script")
            if not script:
                print("❌ No script data available")
                return
            
            print("\n" + "="*80)
            print("📜 SCRIPT DETAILS")
            print("="*80)
            
            # Basic info
            script_id = getattr(script, 'id', 'Unknown')
            script_name = getattr(script, 'name', 'Unknown')
            description = getattr(script, 'description', 'No description')
            status = getattr(script, 'status', 'Unknown')
            
            print(f"📜 {script_name}")
            print(f"   ID: {script_id}")
            print(f"   Description: {description}")
            print(f"   Status: {status}")
            
            # Additional details
            if hasattr(script, 'created_at'):
                print(f"   Created: {script.created_at}")
            if hasattr(script, 'updated_at'):
                print(f"   Updated: {script.updated_at}")
            if hasattr(script, 'version'):
                print(f"   Version: {script.version}")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing script details report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_script_code_report(self, code_data: Dict[str, Any]):
        """Print script code report"""
        try:
            if "error" in code_data:
                print(f"❌ Error: {code_data['error']}")
                return
            
            if not code_data.get("success", False):
                print(f"❌ {code_data.get('error', 'Unknown error')}")
                return
            
            script_id = code_data.get("script_id", "Unknown")
            code = code_data.get("code", "")
            
            print("\n" + "="*80)
            print("📜 SCRIPT CODE")
            print("="*80)
            print(f"📜 Script ID: {script_id}")
            print("-"*80)
            
            if code:
                # Show first 50 lines of code
                lines = code.split('\n')
                for i, line in enumerate(lines[:50]):
                    print(f"{i+1:3d}: {line}")
                
                if len(lines) > 50:
                    print(f"... and {len(lines) - 50} more lines")
            else:
                print("No code available")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing script code report: {e}")
            print(f"❌ Error generating report: {e}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Script Management CLI")
    parser.add_argument("--list", action="store_true", help="List all scripts")
    parser.add_argument("--details", type=str, help="Get script details by ID")
    parser.add_argument("--code", type=str, help="Get script code by ID")
    parser.add_argument("--create", action="store_true", help="Create a new script")
    parser.add_argument("--update", type=str, help="Update script by ID")
    
    # Script creation/update arguments
    parser.add_argument("--name", type=str, help="Script name")
    parser.add_argument("--description", type=str, help="Script description")
    parser.add_argument("--code-file", type=str, help="Path to script code file")
    
    args = parser.parse_args()
    
    cli = ScriptCLI()
    
    # Connect
    if not await cli.connect():
        print("❌ Failed to connect to APIs")
        return
    
    try:
        if args.list:
            # List scripts
            scripts_data = await cli.list_scripts()
            cli.print_scripts_report(scripts_data)
            
        elif args.details:
            # Get script details
            script_data = await cli.get_script_details(args.details)
            cli.print_script_details_report(script_data)
            
        elif args.code:
            # Get script code
            code_data = await cli.get_script_code(args.code)
            cli.print_script_code_report(code_data)
            
        elif args.create:
            # Create new script
            if not all([args.name, args.code_file]):
                print("❌ Missing required arguments for script creation")
                print("Required: --name, --code-file")
                return
            
            # Read code from file
            try:
                with open(args.code_file, 'r') as f:
                    code = f.read()
            except Exception as e:
                print(f"❌ Error reading code file: {e}")
                return
            
            script_data = await cli.create_script(
                name=args.name,
                code=code,
                description=args.description or ""
            )
            
            if script_data.get("success"):
                print(f"✅ {script_data['message']}")
            else:
                print(f"❌ {script_data.get('error', 'Unknown error')}")
                
        elif args.update:
            # Update script
            if not any([args.name, args.code_file, args.description]):
                print("❌ No update data provided")
                return
            
            update_data = {}
            if args.name:
                update_data['name'] = args.name
            if args.description:
                update_data['description'] = args.description
            if args.code_file:
                try:
                    with open(args.code_file, 'r') as f:
                        update_data['code'] = f.read()
                except Exception as e:
                    print(f"❌ Error reading code file: {e}")
                    return
            
            update_result = await cli.update_script(args.update, **update_data)
            if update_result.get("success"):
                print(f"✅ {update_result['message']}")
            else:
                print(f"❌ {update_result.get('error', 'Unknown error')}")
                
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

