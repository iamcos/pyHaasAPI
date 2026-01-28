from typing import Optional, List
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Label, Button, DataTable, Static, ListView, ListItem, Input
from textual.screen import ModalScreen

from pyHaasAPI.core.project_manager import ProjectManager
from pyHaasAPI.models.project import ProjectConfig, LabProjectConfig

class AddLabModal(ModalScreen[Optional[LabProjectConfig]]):
    """Modal for adding a lab to a project from any server."""
    def __init__(self, tui_app):
        super().__init__()
        self.tui_app = tui_app
        self.selected_server: Optional[str] = None
        self.search_text: str = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-content"):
            yield Label("Add Lab to Project", id="modal-title")
            
            with Horizontal(id="server-filter-bar"):
                yield Label("Filter by Server:", id="server-filter-label")
                # Add "All" button
                yield Button("All", variant="default", id="server-all-btn", classes="server-filter-btn active")
                # Add buttons for each server
                for server_name in self.tui_app.server_manager.servers:
                     yield Button(server_name, variant="default", id=f"server-filter-{server_name}", classes="server-filter-btn")
            
            yield Input(placeholder="Search Labs...", id="lab-search-input")
            yield ListView(id="modal-lab-list")
            
            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", variant="error", id="cancel-btn")

    def on_mount(self) -> None:
        self.run_worker(self.fetch_all_labs())

    async def fetch_all_labs(self) -> None:
        list_view = self.query_one("#modal-lab-list", ListView)
        list_view.clear()
        
        self.query_one("#modal-title", Label).update("🔍 [yellow]Searching servers...[/]")
        
        from pyHaasAPI.api.lab.lab_api import LabAPI
        from pyHaasAPI.core.client import AsyncHaasClient
        from pyHaasAPI.config.api_config import APIConfig

        for server_name in self.tui_app.server_manager.servers:
            try:
                async with self.tui_app.server_manager.server_session(server_name):
                    config = APIConfig()
                    config.port = self.tui_app.server_manager.get_active_server_config().local_ports[0]
                    
                    async with AsyncHaasClient(config) as client:
                        auth = self.tui_app.get_auth_manager(server_name, client)
                        await auth.ensure_authenticated()
                        
                        lab_api = LabAPI(client, auth)
                        labs = await lab_api.get_labs()
                        
                        for lab in labs:
                            item = ListItem(Label(f"[{server_name}] {lab.name}"))
                            item.lab_data = LabProjectConfig(
                                lab_id=str(lab.lab_id),
                                lab_name=lab.name,
                                server_name=server_name
                            )
                            list_view.append(item)
            except Exception as e:
                continue
        
        self.query_one("#modal-title", Label).update("Add Lab to Project")
        self.apply_filters()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "server-all-btn":
            self.update_server_filter(None)
        elif event.button.id and event.button.id.startswith("server-filter-"):
            server_name = event.button.id.replace("server-filter-", "")
            self.update_server_filter(server_name)

    def update_server_filter(self, server_name: Optional[str]) -> None:
        self.selected_server = server_name
        
        # Update button styles
        for btn in self.query(".server-filter-btn"):
            btn.remove_class("active")
            
        if server_name is None:
            self.query_one("#server-all-btn").add_class("active")
        else:
            self.query_one(f"#server-filter-{server_name}").add_class("active")
            
        self.apply_filters()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.search_text = event.value.lower()
        self.apply_filters()

    def apply_filters(self) -> None:
        """Combine server selection and search text to filter the list."""
        list_view = self.query_one("#modal-lab-list", ListView)
        for item in list_view.children:
            if not hasattr(item, "lab_data"):
                continue
                
            lab = item.lab_data
            # Server match
            server_match = self.selected_server is None or lab.server_name == self.selected_server
            # Text match
            text_match = self.search_text in lab.lab_name.lower() or self.search_text in lab.server_name.lower()
            
            item.visible = server_match and text_match

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "lab_data"):
            self.dismiss(event.item.lab_data)

class ProjectScreen(Vertical):
    """Screen for managing backtesting projects."""
    def __init__(self, tui_app):
        super().__init__()
        self.tui_app = tui_app
        self.project_manager = tui_app.project_manager
        self.orchestrator = tui_app.project_orchestrator
        self.selected_project: Optional[ProjectConfig] = None

    def compose(self) -> ComposeResult:
        yield Label("Backtesting Projects", id="screen-title")
        
        with Horizontal(id="project-layout-container"):
            with Vertical(id="project-list-sidebar"):
                yield Label("Your Projects", classes="sidebar-label")
                yield ListView(id="project-list")
                yield Button("New Project", variant="success", id="new-project-btn")
            
            with Vertical(id="project-detail-view"):
                yield Label("Project Details", id="project-detail-title")
                yield DataTable(id="project-labs-table")
                yield Horizontal(
                    Button("Run All Steps", variant="primary", id="run-project-btn"),
                    Button("Add Lab", variant="success", id="add-lab-btn"),
                    Button("Move Up", id="move-up-btn"),
                    Button("Move Down", id="move-down-btn"),
                    Button("Remove Lab", variant="error", id="remove-lab-btn"),
                    classes="button-bar"
                )

    def on_mount(self) -> None:
        self.refresh_project_list()
        table = self.query_one("#project-labs-table", DataTable)
        table.add_columns("Lab Name", "Server", "Priority", "Status")
        table.cursor_type = "row"

    def refresh_project_list(self) -> None:
        list_view = self.query_one("#project-list", ListView)
        list_view.clear()
        
        projects = self.project_manager.projects
        if not projects:
            list_view.append(ListItem(Label("[dim]No projects yet[/]")))
            return

        for name in projects:
            item = ListItem(Label(f"📁 {name}"))
            item.project_name = name 
            list_view.append(item)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id != "project-list":
            return
        self._handle_selection(event.item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "project-list":
            return
        try:
            self._handle_selection(event.item)
        except Exception as e:
            self.tui_app.notify(f"Error selecting project: {e}", severity="error")

    def _handle_selection(self, item: Optional[ListItem]) -> None:
        if not item or not hasattr(item, "project_name"):
            return
            
        project_name = item.project_name
        project = self.project_manager.get_project(project_name)
        if project:
            self.selected_project = project
            self.show_project_details(project)

    def show_project_details(self, project: ProjectConfig) -> None:
        self.query_one("#project-detail-title", Label).update(f"Project: [bold cyan]{project.name}[/]")
        table = self.query_one("#project-labs-table", DataTable)
        table.clear()
        
        for i, lab in enumerate(project.labs):
            table.add_row(
                lab.lab_name,
                lab.server_name,
                str(lab.priority),
                "[green]Ready[/]" if lab.enabled else "[dim]Disabled[/]",
                key=f"lab-{i}"
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-project-btn":
            self.tui_app.push_screen(NewProjectModal(), self.handle_new_project)
        
        elif not self.selected_project:
            self.tui_app.notify("Select a project first!", severity="warning")
            return

        elif event.button.id == "run-project-btn":
            self.run_worker(self.orchestrator.run_project(self.selected_project))

        elif event.button.id == "add-lab-btn":
            self.tui_app.push_screen(AddLabModal(self.tui_app), self.handle_add_lab)

        elif event.button.id == "move-up-btn":
            self.move_lab(-1)

        elif event.button.id == "move-down-btn":
            self.move_lab(1)

        elif event.button.id == "remove-lab-btn":
            self.remove_selected_lab()

    def handle_add_lab(self, lab_config: Optional[LabProjectConfig]) -> None:
        if lab_config and self.selected_project:
            if self.project_manager.add_lab_to_project(self.selected_project.name, lab_config):
                self.tui_app.notify(f"Added {lab_config.lab_name} to {self.selected_project.name}")
                self.show_project_details(self.selected_project)
            else:
                self.tui_app.notify("Lab already in project", severity="warning")

    def move_lab(self, direction: int):
        table = self.query_one("#project-labs-table", DataTable)
        if table.cursor_row is None:
            return
        
        idx = table.cursor_row
        new_idx = idx + direction
        
        if 0 <= new_idx < len(self.selected_project.labs):
            labs = self.selected_project.labs
            labs[idx], labs[new_idx] = labs[new_idx], labs[idx]
            self.project_manager.save_projects()
            self.show_project_details(self.selected_project)
            table.move_cursor(row=new_idx)

    def remove_selected_lab(self):
        table = self.query_one("#project-labs-table", DataTable)
        if table.cursor_row is None:
            return
        
        idx = table.cursor_row
        del self.selected_project.labs[idx]
        self.project_manager.save_projects()
        self.show_project_details(self.selected_project)

    def handle_new_project(self, project_name: str | None) -> None:
        if project_name:
            try:
                project = self.project_manager.create_project(project_name)
                self.refresh_project_list()
                self.selected_project = project
                self.show_project_details(project)
                self.tui_app.notify(f"Project '{project_name}' created!")
            except ValueError as e:
                self.tui_app.notify(str(e), severity="error")

class NewProjectModal(ModalScreen[str]):
    """Modal for creating a new project."""
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-content"):
            yield Label("Create New Project", id="modal-title")
            yield Input(placeholder="Project Name", id="project-name-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Create", variant="success", id="create-btn")
                yield Button("Cancel", variant="error", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            name = self.query_one("#project-name-input", Input).value
            if name:
                self.dismiss(name)
            else:
                self.app.notify("Project name cannot be empty", severity="warning")
        else:
            self.dismiss(None)
