#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI.core.server_manager import ServerManager, ServerConfig
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.cli.download_cli import DownloadCLI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.api.market.market_api import MarketAPI
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.models.lab import StartLabExecutionRequest
import json
from datetime import datetime

class InteractiveMenu:
    def __init__(self):
        self.settings = Settings()
        self.server_manager = ServerManager(self.settings)
        self.download_cli = DownloadCLI()
        self.download_cli.server_manager = self.server_manager # Share the same server manager
        self.projects_file = Path("projects.json")
        self.projects = self._load_projects()

    def _load_projects(self):
        if self.projects_file.exists():
            try:
                with open(self.projects_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_projects(self):
        with open(self.projects_file, 'w') as f:
            json.dump(self.projects, f, indent=2)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title):
        print("=" * 50)
        print(f" {title.center(48)} ")
        print("=" * 50)

    async def run(self):
        while True:
            self.clear_screen()
            self.print_header("pyHaasAPI v2 Interactive Menu")
            print("\n1. Download HaasScripts")
            print("2. Manage Servers")
            print("3. Lab Run Projects")
            print("4. Bot Management")
            print("5. Exit")
            
            choice = input("\nSelect an option (1-5): ").strip()
            
            if choice == '1':
                await self.menu_download_scripts()
            elif choice == '2':
                await self.menu_manage_servers()
            elif choice == '3':
                await self.menu_lab_runs()
            elif choice == '4':
                await self.menu_manage_bots()
            elif choice == '5':
                print("Goodbye!")
                break
            else:
                input("\nInvalid choice. Press Enter to continue...")

    async def menu_lab_runs(self):
        while True:
            self.clear_screen()
            self.print_header("Lab Run Projects")
            print("\n1. Create New Project")
            print("2. List/Run Projects")
            print("3. Back to main menu")
            
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == '1':
                await self.create_lab_project()
            elif choice == '2':
                await self.list_projects()
            elif choice == '3':
                break

    async def create_lab_project(self):
        self.clear_screen()
        self.print_header("Create New Lab Run Project")
        
        name = input("\nProject Name: ").strip()
        if not name: return

        # 1. Sweep View Lab Selection
        print("\n🔍 Fetching Labs from all servers...")
        all_labs = await self.sweep_select_labs()
        if not all_labs:
            print("❌ No labs found on any server.")
            input("\nPress Enter to continue...")
            return
        
        print("\nSelect Template Labs (comma-separated indices):")
        for i, (srv, lab) in enumerate(all_labs, 1):
            print(f"{i}. [{srv}] {lab.name} (ID: {lab.lab_id})")
        
        indices = input("\nIndices: ").strip()
        try:
            selected_templates = [all_labs[int(i.strip()) - 1] for i in indices.split(',') if i.strip()]
        except:
            print("Invalid selection.")
            return

        # 2. Fuzzy Market Selection
        print("\n🔍 Fetching Markets (this may take a moment)...")
        markets = await self.fuzzy_select_markets()
        if not markets:
            print("❌ No markets selected.")
            input("\nPress Enter to continue...")
            return

        # 3. Backtest Period
        print("\n📅 Backtest Period (YYYY-MM-DD):")
        start_str = input("Start Date [2024-01-01]: ").strip() or "2024-01-01"
        end_str = input("End Date [2024-02-01]: ").strip() or "2024-02-01"
        
        try:
            start_unix = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp())
            end_unix = int(datetime.strptime(end_str, "%Y-%m-%d").timestamp())
        except:
            print("❌ Invalid date format.")
            return

        # Save project
        project_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.projects[project_id] = {
            "name": name,
            "templates": [{"server": srv, "lab_id": lab.lab_id, "name": lab.name} for srv, lab in selected_templates],
            "markets": markets,
            "start_unix": start_unix,
            "end_unix": end_unix,
            "created_at": datetime.now().isoformat()
        }
        self._save_projects()
        print(f"\n✅ Project '{name}' created with {len(selected_templates)} templates and {len(markets)} markets.")
        input("\nPress Enter to continue...")

    async def list_projects(self):
        while True:
            self.clear_screen()
            self.print_header("Lab Run Projects")
            if not self.projects:
                print("\nNo projects found.")
                input("\nPress Enter to continue...")
                break
            
            p_list = list(self.projects.items())
            for i, (pid, p) in enumerate(p_list, 1):
                print(f"{i}. {p['name']} ({len(p['templates'])} templates, {len(p['markets'])} markets)")
            
            print(f"\n{len(p_list) + 1}. Back")
            
            choice = input("\nSelect project to RUN or 'q' to delete: ").strip()
            if choice == str(len(p_list) + 1): break
            
            if choice.startswith('d ') or choice.startswith('q '):
                try:
                    pid = p_list[int(choice.split()[1]) - 1][0]
                    del self.projects[pid]
                    self._save_projects()
                    print("Project deleted.")
                    continue
                except: pass
                
            try:
                project = p_list[int(choice) - 1][1]
                await self.run_project(project)
                input("\nPress Enter to continue...")
            except: pass

    async def run_project(self, project):
        print(f"\n🚀 Running Project: {project['name']}")
        
        for template in project['templates']:
            server_name = template['server']
            template_id = template['lab_id']
            
            print(f"\n🌐 Connecting to {server_name} for template {template['name']}...")
            if not await self.server_manager.switch_server(server_name):
                print(f"❌ Failed to connect to {server_name}, skipping.")
                continue
            
            # Setup APIs
            config = APIConfig()
            config.port = self.server_manager.get_active_server_config().local_ports[0]
            client = AsyncHaasClient(config)
            auth = AuthenticationManager(client, config)
            await auth.authenticate()
            lab_api = LabAPI(client, auth)
            
            for market in project['markets']:
                print(f"   ⮑ Cloning for {market}...")
                try:
                    new_name = f"Project {project['name']} - {template['name']} - {market}"
                    cloned_lab = await lab_api.clone_lab(template_id, new_name)
                    
                    print(f"   ⮑ Updating market to {market}...")
                    await lab_api.update_lab_details(cloned_lab.lab_id, {"market": market})
                    
                    print(f"   ⮑ Starting backtest...")
                    req = StartLabExecutionRequest(
                        lab_id=cloned_lab.lab_id,
                        start_unix=project['start_unix'],
                        end_unix=project['end_unix']
                    )
                    await lab_api.start_lab_execution(req)
                    print(f"   ✅ Lab created and started.")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            await client.close()

    async def fuzzy_select_markets(self) -> List[str]:
        # Connect to default server (srv03) to fetch markets
        if not await self.server_manager.switch_server("srv03"):
             print("❌ Failed to connect to srv03 to fetch markets.")
             return []
        
        config = APIConfig()
        config.port = self.server_manager.get_active_server_config().local_ports[0]
        client = AsyncHaasClient(config)
        auth = AuthenticationManager(client, config)
        await auth.authenticate()
        market_api = MarketAPI(client, auth)
        
        all_markets = await market_api.get_all_markets()
        await client.close()
        
        tags = [m.market for m in all_markets]
        selected = []
        
        while True:
            self.clear_screen()
            self.print_header("Market Selection (Fuzzy)")
            print(f"Selected ({len(selected)}): {', '.join(selected[:3])}{'...' if len(selected)>3 else ''}")
            
            query = input("\nSearch filter (or 'DONE' to finish, 'ALL' for currently filtered): ").strip()
            if query.upper() == 'DONE': break
            
            filtered = [t for t in tags if query.lower() in t.lower()]
            
            if query.upper() == 'ALL':
                selected.extend([f for f in filtered if f not in selected])
                continue

            print("\nMatching markets:")
            for i, t in enumerate(filtered[:20], 1):
                mark = "[x]" if t in selected else "[ ]"
                print(f"{i}. {mark} {t}")
            
            if len(filtered) > 20: print(f"... and {len(filtered)-20} more.")
            
            choice = input("\nSelect index to toggle (or ENTER to search again): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(filtered[:20]):
                    tag = filtered[idx]
                    if tag in selected: selected.remove(tag)
                    else: selected.append(tag)
            except:
                pass
        
        return selected

    async def sweep_select_labs(self):
        all_labs_with_server = []
        for server_name in self.server_manager.servers.keys():
            print(f"   Connecting to {server_name}...")
            if not await self.server_manager.switch_server(server_name):
                continue
            
            config = APIConfig()
            config.port = self.server_manager.get_active_server_config().local_ports[0]
            client = AsyncHaasClient(config)
            auth = AuthenticationManager(client, config)
            await auth.authenticate()
            lab_api = LabAPI(client, auth)
            
            try:
                labs = await lab_api.get_labs()
                for l in labs:
                    all_labs_with_server.append((server_name, l))
            except: pass
            
            await client.close()
        return all_labs_with_server

    async def menu_manage_bots(self):
        self.clear_screen()
        self.print_header("Bot Management")
        
        # Sweep all bots
        all_bots = []
        for server_name in self.server_manager.servers.keys():
            print(f"   Fetching bots from {server_name}...")
            if not await self.server_manager.switch_server(server_name):
                continue
            
            config = APIConfig()
            config.port = self.server_manager.get_active_server_config().local_ports[0]
            client = AsyncHaasClient(config)
            auth = AuthenticationManager(client, config)
            await auth.authenticate()
            bot_api = BotAPI(client, auth)
            
            try:
                bots = await bot_api.get_all_bots()
                for b in bots:
                    all_bots.append((server_name, b))
            except: pass
            await client.close()
        
        self.clear_screen()
        self.print_header("Bot Management")
        if not all_bots:
            print("\nNo bots found.")
        else:
            print(f"\n{'Server':<10} {'Name':<30} {'Status':<15}")
            print("-" * 55)
            for srv, bot in all_bots:
                print(f"{srv:<10} {bot.name[:30]:<30} {bot.status:<15}")
        
        input("\nPress Enter to continue...")

    async def menu_manage_servers(self):
        while True:
            self.clear_screen()
            self.print_header("Manage Servers")
            
            print("\nCurrent Servers:")
            for name, status in self.server_manager.servers.items():
                config = status.config
                print(f"- {name}: {config.username}@{config.hostname}")
            
            print("\n1. Add Server")
            print("2. Edit Server")
            print("3. Back to main menu")
            
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == '1':
                await self.add_server()
            elif choice == '2':
                await self.edit_server()
            elif choice == '3':
                break

    async def add_server(self):
        print("\n--- Add New Server ---")
        name = input("Server Name (e.g., my_server): ").strip()
        if not name: return
        
        hostname = input("Hostname/IP: ").strip()
        username = input("Username [prod]: ").strip() or "prod"
        ssh_key = input("SSH Key Path [~/.ssh/id_rsa]: ").strip() or os.path.expanduser("~/.ssh/id_rsa")
        
        config = ServerConfig(
            name=name,
            hostname=hostname,
            username=username,
            ssh_key_path=ssh_key
        )
        
        try:
            self.server_manager.add_server(config)
            print(f"✅ Server '{name}' added.")
        except Exception as e:
            print(f"❌ Error: {e}")
        input("\nPress Enter to continue...")

    async def edit_server(self):
        servers = list(self.server_manager.servers.keys())
        if not servers:
            print("No servers available to edit.")
            input("\nPress Enter to continue...")
            return

        print("\nSelect server to edit:")
        for i, s in enumerate(servers, 1):
            print(f"{i}. {s}")
        
        try:
            idx = int(input("\nChoice: ").strip()) - 1
            if idx < 0 or idx >= len(servers): raise ValueError()
            old_name = servers[idx]
            current = self.server_manager.servers[old_name].config
            
            print(f"\nEditing {old_name} (Leave blank to keep current value):")
            new_name = input(f"New Name [{current.name}]: ").strip() or current.name
            hostname = input(f"Hostname [{current.hostname}]: ").strip() or current.hostname
            username = input(f"Username [{current.username}]: ").strip() or current.username
            ssh_key = input(f"SSH Key Path [{current.ssh_key_path}]: ").strip() or current.ssh_key_path
            
            new_config = ServerConfig(
                name=new_name,
                hostname=hostname,
                username=username,
                ssh_key_path=ssh_key
            )
            
            self.server_manager.edit_server(old_name, new_config)
            print(f"✅ Server '{old_name}' updated.")
        except (ValueError, IndexError):
            print("Invalid input.")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    menu = InteractiveMenu()
    asyncio.run(menu.run())
