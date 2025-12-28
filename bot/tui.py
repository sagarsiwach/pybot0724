"""
Travian Bot - Modern Terminal UI
A beautiful fullscreen interface for managing Travian automation.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Input, Label, Log, ProgressBar
from textual.binding import Binding
from textual import on, work
from rich.text import Text
from datetime import datetime
import asyncio
import httpx
from bs4 import BeautifulSoup


def format_number(num_str: str) -> str:
    """Format large numbers with K/M/B/T/Q suffixes."""
    try:
        num = int(num_str)
        if num >= 1_000_000_000_000_000_000:  # Quintillion
            return f"{num / 1_000_000_000_000_000_000:.2f}Q"
        elif num >= 1_000_000_000_000_000:  # Quadrillion
            return f"{num / 1_000_000_000_000_000:.2f}Qa"
        elif num >= 1_000_000_000_000:  # Trillion
            return f"{num / 1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:  # Billion
            return f"{num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:  # Million
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:  # Thousand
            return f"{num / 1_000:.2f}K"
        else:
            return str(num)
    except:
        return num_str


class StatusPanel(Static):
    """Shows current status and stats."""
    
    def __init__(self, id=None):
        super().__init__(id=id)
        self.username = "Not logged in"
        self.storage = "---"
        self.granary = "---"
        self.wood = "---"
        self.clay = "---"
        self.iron = "---"
        self.crop = "---"
        self.session_status = "⚪ Offline"
        
    def compose(self) -> ComposeResult:
        yield Static(id="status-content")
        
    def on_mount(self):
        self.update_display()
        
    def update_display(self):
        content = f"""[bold cyan]╭─ Session ─────────────────────────────╮[/]
[bold cyan]│[/] 👤 User:   [yellow]{self.username}[/]
[bold cyan]│[/] 📡 Status: {self.session_status}
[bold cyan]╰───────────────────────────────────────╯[/]

[bold green]╭─ Storage & Granary ────────────────────╮[/]
[bold green]│[/] 📦 Warehouse: [white]{self.storage}[/]
[bold green]│[/] 🌾 Granary:   [white]{self.granary}[/]
[bold green]╰────────────────────────────────────────╯[/]

[bold yellow]╭─ Resources ─────────────────────────────╮[/]
[bold yellow]│[/] 🪵 Wood: [white]{self.wood}[/]
[bold yellow]│[/] 🧱 Clay: [white]{self.clay}[/]
[bold yellow]│[/] ⛏️  Iron: [white]{self.iron}[/]
[bold yellow]│[/] 🌾 Crop: [white]{self.crop}[/]
[bold yellow]╰──────────────────────────────────────────╯[/]"""
        self.query_one("#status-content", Static).update(content)


class LogPanel(ScrollableContainer):
    """Scrollable log panel."""
    
    def compose(self) -> ComposeResult:
        yield Log(id="activity-log", highlight=True)
        
    def add_log(self, message: str, level: str = "info"):
        log = self.query_one("#activity-log", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "success":
            prefix = "[green]✓[/]"
        elif level == "error":
            prefix = "[red]✗[/]"
        elif level == "warning":
            prefix = "[yellow]⚠[/]"
        else:
            prefix = "[blue]→[/]"
            
        log.write_line(f"[dim]{timestamp}[/] {prefix} {message}")


class MainMenu(Static):
    """Main menu with action buttons."""
    
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]⚔️  ACTIONS[/]", classes="menu-header")
        yield Button("📦 Increase Storage", id="btn-storage", variant="primary")
        yield Button("⚡ Increase Production", id="btn-production", variant="primary")
        yield Button("🏗️  Construction", id="btn-construction", variant="default")
        yield Button("⚔️  Attack Village", id="btn-attack", variant="warning")
        yield Button("🗺️  Find Empty Spots", id="btn-find-spots", variant="default")
        yield Static("", classes="spacer")
        yield Static("[bold cyan]🏰 VILLAGES[/]", classes="menu-header")
        yield Button("📋 Fetch Villages", id="btn-villages", variant="default")
        yield Button("✏️  Rename Village", id="btn-rename", variant="default")
        yield Static("", classes="spacer")
        yield Static("[bold yellow]⚙️  SESSION[/]", classes="menu-header")
        yield Button("🔐 Login", id="btn-login", variant="success")
        yield Button("🔄 Refresh Stats", id="btn-refresh", variant="default")
        yield Button("🚪 Logout", id="btn-logout", variant="error")


class TravianBotApp(App):
    """Main Travian Bot Application."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #sidebar {
        width: 34;
        background: $panel;
        border-right: solid $primary;
        padding: 1;
    }
    
    #content {
        width: 1fr;
        padding: 1;
    }
    
    #status-panel {
        height: auto;
        margin-bottom: 1;
    }
    
    #log-panel {
        height: 1fr;
        border: solid $primary;
        background: $surface-darken-1;
    }
    
    .menu-header {
        margin-top: 1;
        margin-bottom: 0;
        text-style: bold;
    }
    
    .spacer {
        height: 1;
    }
    
    Button {
        width: 100%;
        margin: 1 0;
    }
    
    #activity-log {
        scrollbar-gutter: stable;
    }
    
    Header {
        background: $primary-darken-2;
    }
    
    Footer {
        background: $primary-darken-3;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("l", "login", "Login"),
        Binding("s", "storage", "Storage"),
        Binding("p", "production", "Production"),
        Binding("r", "refresh", "Refresh"),
        Binding("escape", "back", "Back"),
    ]
    
    TITLE = "Travian Bot"
    SUB_TITLE = "gotravspeed.com Automation"
    
    def __init__(self):
        super().__init__()
        self.session_manager = None
        self.cookies = None
        self.conn = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Vertical(id="sidebar"):
                yield MainMenu()
            with Vertical(id="content"):
                yield StatusPanel(id="status-panel")
                yield LogPanel(id="log-panel")
        yield Footer()
        
    def on_mount(self):
        self.log_message("Welcome to Travian Bot!", "success")
        self.log_message("Press [bold]L[/] to login or click the Login button")
        self.log_message("Use keyboard shortcuts shown in the footer")
        
    def log_message(self, message: str, level: str = "info"):
        log_panel = self.query_one("#log-panel", LogPanel)
        log_panel.add_log(message, level)
        
    def update_status(self, **kwargs):
        status = self.query_one("#status-panel", StatusPanel)
        for key, value in kwargs.items():
            setattr(status, key, value)
        status.update_display()
        
    @on(Button.Pressed, "#btn-login")
    def on_login_pressed(self):
        self.action_login()
        
    @on(Button.Pressed, "#btn-storage")
    def on_storage_pressed(self):
        self.action_storage()
        
    @on(Button.Pressed, "#btn-production")
    def on_production_pressed(self):
        self.action_production()
        
    @on(Button.Pressed, "#btn-refresh")
    def on_refresh_pressed(self):
        self.action_refresh()
        
    @on(Button.Pressed, "#btn-villages")
    def on_villages_pressed(self):
        self.log_message("Fetching villages...", "info")
        
    @on(Button.Pressed, "#btn-logout")
    def on_logout_pressed(self):
        self.session_manager = None
        self.cookies = None
        self.update_status(
            session_status="⚪ Offline",
            username="Not logged in",
            storage="---",
            granary="---",
            wood="---",
            clay="---",
            iron="---",
            crop="---"
        )
        self.log_message("Logged out", "warning")
        
    def action_login(self):
        self.log_message("Starting login process...", "info")
        self.do_login()
        
    def action_storage(self):
        if not self.session_manager:
            self.log_message("Please login first!", "error")
            return
        self.log_message("Starting storage increase...", "info")
        self.do_storage_increase()
        
    def action_production(self):
        if not self.session_manager:
            self.log_message("Please login first!", "error")
            return
        self.log_message("Starting production increase...", "info")
        self.do_production_increase()
        
    def action_refresh(self):
        if not self.cookies:
            self.log_message("Please login first!", "error")
            return
        self.log_message("Refreshing stats...", "info")
        self.do_refresh()
        
    @work(thread=True)
    def do_login(self):
        """Perform login in background."""
        try:
            from bot.database import init_db
            from bot.session_manager import SessionManager
            
            self.log_message("Initializing database...", "info")
            self.conn = init_db()
            
            # Hardcoded credentials for now
            username = "abaddon"
            password = "bristleback"
            civilization = "roman"
            
            self.log_message(f"Logging in as [yellow]{username}[/]...", "info")
            
            self.session_manager = SessionManager(username, password, civilization, self.conn)
            self.cookies = asyncio.run(self.session_manager.login())
            
            if self.cookies:
                self.update_status(
                    username=username,
                    session_status="🟢 Online"
                )
                self.log_message("Login successful!", "success")
                
                # Fetch current stats
                self._fetch_stats_sync()
            else:
                self.log_message("Login failed!", "error")
                
        except Exception as e:
            self.log_message(f"Error: {str(e)}", "error")
            
    @work(thread=True)
    def do_refresh(self):
        """Refresh wrapper."""
        self._fetch_stats_sync()
        
    def _fetch_stats_sync(self):
        """Fetch current storage/production stats from game."""
        if not self.cookies:
            return
            
        try:
            self.log_message("Fetching game stats...", "info")
            
            with httpx.Client(cookies=self.cookies) as client:
                response = client.get(
                    "https://fun.gotravspeed.com/village1.php",
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Parse resource data from the #res div
                res_div = soup.find('div', id='res')
                if res_div:
                    # Warehouse capacity
                    ware = res_div.find('div', class_='ware')
                    if ware:
                        self.update_status(storage=format_number(ware.text.strip()))
                    
                    # Granary capacity
                    gran = res_div.find('div', class_='gran')
                    if gran:
                        self.update_status(granary=format_number(gran.text.strip()))
                    
                    # Resources
                    wood = res_div.find('div', class_='wood')
                    if wood:
                        self.update_status(wood=format_number(wood.text.strip()))
                        
                    clay = res_div.find('div', class_='clay')
                    if clay:
                        self.update_status(clay=format_number(clay.text.strip()))
                        
                    iron = res_div.find('div', class_='iron')
                    if iron:
                        self.update_status(iron=format_number(iron.text.strip()))
                        
                    crop = res_div.find('div', class_='crop')
                    if crop:
                        self.update_status(crop=format_number(crop.text.strip()))
                    
                    self.log_message("Stats updated!", "success")
                else:
                    self.log_message("Could not find resource data", "warning")
                    
        except Exception as e:
            self.log_message(f"Error fetching stats: {str(e)}", "error")
            
    @work(thread=True)
    def do_storage_increase(self):
        """Increase storage in background."""
        if not self.cookies:
            return
            
        try:
            from bot.storage import increase_storage_async
            from bot.database import init_db
            
            # Create new DB connection for this thread
            thread_conn = init_db()
            
            loops = 10  # Start with 10 loops
            self.log_message(f"Running storage increase ({loops} loops)...", "info")
            
            asyncio.run(increase_storage_async(
                username="abaddon",
                password="bristleback", 
                loops=loops,
                conn=thread_conn,
                cookies=self.cookies
            ))
            
            self.log_message(f"Storage increase complete!", "success")
            
            # Refresh stats
            self._fetch_stats_sync()
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}", "error")
            
    @work(thread=True)
    def do_production_increase(self):
        """Increase production in background."""
        if not self.cookies:
            return
            
        try:
            from bot.production import increase_production_async
            from bot.database import init_db
            
            # Create new DB connection for this thread
            thread_conn = init_db()
            
            loops = 10
            self.log_message(f"Running production increase ({loops} loops)...", "info")
            
            asyncio.run(increase_production_async(
                username="abaddon",
                password="bristleback",
                loops=loops,
                conn=thread_conn,
                cookies=self.cookies
            ))
            
            self.log_message(f"Production increase complete!", "success")
            
            # Refresh stats
            self._fetch_stats_sync()
            
        except Exception as e:
            self.log_message(f"Error: {str(e)}", "error")


def main():
    """Entry point for the TUI app."""
    app = TravianBotApp()
    app.run()


if __name__ == "__main__":
    main()
