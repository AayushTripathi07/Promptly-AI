import sys
import json
import re
import os
import requests
import subprocess
import webbrowser
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.theme import Theme
from rich.live import Live
from rich.markdown import Markdown

MACBOOK_IP = "10.244.141.3"  # The current MacBook IP address
OLLAMA_MODEL = "qwen2.5-coder:14b"  # The model name (ensure this is pulled on Ollama)

# Define a custom theme for the application
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
    "agent_name": "bold yellow",
    "user": "bold blue",
    "system": "dim white"
})

console = Console(theme=custom_theme)

PERSONAS = {
    "code": {
        "id": "CodeGenerator",
        "name": "Code Generator",
        "color": "cyan",
        "prompt": "You are an expert software engineer focused on logic, algorithms, and clean Python code. Provide clear, modular examples."
    },
    "web": {
        "id": "WebsiteGenerator",
        "name": "Website Generator",
        "color": "magenta",
        "prompt": "You are a creative web developer focused on modern HTML, CSS, and JS with rich aesthetics. Design beautiful, responsive solutions. ALWAYS wrap your code in triple backtick markdown blocks with the correct language tag (e.g., ```html, ```css, ```js) so they can be automatically saved to the workspace."
    }
}

class SequentialAgentManager:
    def __init__(self, console):
        self.console = console
        self.url = f"http://{MACBOOK_IP}:11434/api/generate"

    def send_request(self, user_input, persona_name, sys_prompt, persona_color):
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": user_input,
            "system": sys_prompt,
            "stream": True,
            "options": {
                "num_ctx": 4096,
                "temperature": 0.2,          # Low temperature for highly logical, non-creative code
                "top_p": 0.9,                # Filter out bizarre rogue tokens
                "repeat_penalty": 1.15       # Strictly prevents endless repetition loops
            }
        }
        
        self.console.print(f"[bold {persona_color}]{persona_name}:[/bold {persona_color}] ", end="")
        full_response = ""
        
        try:
            # Use stream=True to handle the generator response
            with requests.post(self.url, json=payload, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                # Live display for streaming markdown response
                with Live(Markdown(""), refresh_per_second=8, console=self.console) as live:
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    full_response += chunk["response"]
                                    live.update(Markdown(full_response))
                                if chunk.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue
            return full_response
        except requests.exceptions.RequestException as e:
            if e.response is not None and e.response.status_code == 404:
                error_msg = f"\n[bold red]Ollama API Error (404):[/bold red] Model '{OLLAMA_MODEL}' not found or endpoint invalid.\nRun [yellow]ollama pull {OLLAMA_MODEL}[/yellow] on your MacBook."
            else:
                error_msg = f"\n[bold red]Ollama API Error:[/bold red] {e}"
            self.console.print(error_msg)
            return None

class WorkspaceManager:
    def __init__(self, console):
        self.console = console
        self.base_dir = "generated/site"
        
    def ensure_dir(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def parse_and_save(self, response_text, mode):
        if mode != "web":
            return

        self.ensure_dir()
        
        # Regex to find code blocks with language identifiers
        # Group 1: language, Group 2: content
        code_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
        matches = code_pattern.finditer(response_text)
        
        saved_files = []
        
        for match in matches:
            lang = (match.group(1) or "").lower()
            code = match.group(2).strip()
            
            filename = None
            if lang in ["html", "xml"]:
                filename = "index.html"
            elif lang in ["css"]:
                filename = "styles.css"
            elif lang in ["js", "javascript"]:
                filename = "script.js"
            
            if filename:
                filepath = os.path.join(self.base_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code)
                saved_files.append(filename)
        
        if saved_files:
            self.console.print()
            panel = Panel(
                Text.assemble(
                    ("Successfully saved files to disk:\n", "success"),
                    ("\n".join([f" • {f}" for f in saved_files]), "bold green")
                ),
                title="[bold]Workspace Manager[/bold]",
                subtitle=f"[dim]{self.base_dir}[/dim]",
                border_style="success",
                expand=False
            )
            self.console.print(panel)
            self.console.print()
        
        # If in code mode, also save the last python block
        if mode == "code":
            code_pattern = re.compile(r'```(?:python|py)?\n(.*?)\n```', re.DOTALL)
            match = code_pattern.search(response_text)
            if match:
                code_dir = "generated/code"
                if not os.path.exists(code_dir):
                    os.makedirs(code_dir)
                filepath = os.path.join(code_dir, "last_script.py")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(match.group(1).strip())
                self.console.print(f"[success] • Saved Python script to {filepath}[/success]\n")

class ExecutionEngine:
    def __init__(self, console):
        self.console = console

    def run_python(self):
        script_path = os.path.join("generated", "code", "last_script.py")
        if not os.path.exists(script_path):
            self.console.print("[danger]Error: No generated Python script found to run.[/danger]")
            return

        self.console.print(f"[info]Running {script_path}...[/info]\n")
        try:
            # Use current python executable to run the script
            result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, timeout=30)
            
            if result.stdout:
                self.console.print(Panel(result.stdout, title="[bold green]Output[/bold green]", border_style="green"))
            
            if result.stderr:
                self.console.print(Panel(result.stderr, title="[bold red]Execution Error[/bold red]", border_style="red"))
        except subprocess.TimeoutExpired:
            self.console.print("[bold red]Error: Execution timed out (30s limit).[/bold red]")
        except Exception as e:
            self.console.print(Panel(str(e), title="[bold red]System Error[/bold red]", border_style="red"))

    def preview_site(self):
        index_path = os.path.join("generated", "site", "index.html")
        if not os.path.exists(index_path):
            self.console.print("[danger]Error: No generated index.html found to preview.[/danger]")
            return

        abs_path = os.path.abspath(index_path)
        self.console.print(f"[info]Opening {abs_path} in browser...[/info]")
        webbrowser.open(f"file://{abs_path}")

class PersonaApp:
    def __init__(self):
        self.current_mode = "code"
        self.history = []
        self.agent_manager = SequentialAgentManager(console)
        self.workspace_manager = WorkspaceManager(console)
        self.execution_engine = ExecutionEngine(console)

    def get_current_persona(self):
        return PERSONAS[self.current_mode]

    def display_header(self):
        persona = self.get_current_persona()
        header_text = Text.assemble(
            ("Active Agent: ", "white"),
            (persona["name"], f"bold {persona['color']}"),
            (" | Mode: ", "white"),
            (f"/mode {self.current_mode}", "dim yellow")
        )
        
        panel = Panel(
            header_text,
            title="[bold white]Persona Terminal Interface[/bold white]",
            subtitle="[dim white]Type /mode [code|web] to switch or /exit to quit[/dim white]",
            border_style=persona["color"]
        )
        console.clear()
        console.print(panel)
        console.print()

    def run(self):
        while True:
            self.display_header()
            
            # Display history
            for role, msg, color in self.history:
                if role == "System":
                    console.print(f"[system]{role}:[/system] {msg}")
                elif role == "You":
                    console.print(f"[user]{role}:[/user] {msg}")
                else:
                    console.print(f"[{color}]{role}:[/{color}]")
                    console.print(Markdown(msg))
                    console.print()
            
            user_input = Prompt.ask(f"[bold blue]You[/bold blue]").strip()

            if not user_input:
                continue

            if user_input.lower() == "/exit":
                console.print("[bold red]Exiting... Goodbye![/bold red]")
                sys.exit(0)

            if user_input.startswith("/mode"):
                parts = user_input.split()
                if len(parts) > 1:
                    new_mode = parts[1].lower()
                    if new_mode in PERSONAS:
                        self.current_mode = new_mode
                        self.history.append(("System", f"Switched to {PERSONAS[new_mode]['name']}", "system"))
                        continue
                    else:
                        console.print(f"[warning]Invalid mode. Available: {', '.join(PERSONAS.keys())}[/warning]")
                        Prompt.ask("Press Enter to continue...")
                        continue
                else:
                    console.print("[warning]Usage: /mode [code|web][/warning]")
                    Prompt.ask("Press Enter to continue...")
                    continue

            if user_input.lower() == "/run":
                self.execution_engine.run_python()
                Prompt.ask("\nPress Enter to return to chat...")
                continue

            if user_input.lower() == "/preview":
                self.execution_engine.preview_site()
                Prompt.ask("\nPress Enter to return to chat...")
                continue

            # Process request via Ollama
            persona = self.get_current_persona()
            self.history.append(("You", user_input, "user"))
            
            # Clear for raw output streaming, then it will be re-rendered in history next turn
            response = self.agent_manager.send_request(
                user_input=user_input,
                persona_name=persona["name"],
                sys_prompt=persona["prompt"],
                persona_color=persona["color"]
            )
            
            if response:
                self.history.append((persona["name"], response, persona["color"]))
                # Parse and save if in web mode
                self.workspace_manager.parse_and_save(response, self.current_mode)
            else:
                self.history.append(("System", "Failed to get response from Agent.", "danger"))
                Prompt.ask("\nPress Enter to return to chat...")

if __name__ == "__main__":
    app = PersonaApp()
    try:
        app.run()
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted by user. Exiting...[/bold red]")
        sys.exit(0)
