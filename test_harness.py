import sys
import os
from persona_chat import SequentialAgentManager, WorkspaceManager, PERSONAS, console

def run_test():
    console.print("[bold cyan]Starting Automated Testing for Capstone Project...[/bold cyan]")
    
    agent = SequentialAgentManager(console)
    wrk = WorkspaceManager(console)
    persona = PERSONAS["web"]
    
    prompt = """Create a breathtaking, ultra-premium Sports News Website using ONLY HTML and CSS (NO JAVASCRIPT).

ARCHITECTURE (CSS-Only Navigation):
- You must build everything inside a single HTML file.
- Implement an interconnected look with 7 distinct content sections: Home, Football, Cricket, Basketball, Tennis, Golf, eSports.
- Use anchor links in a sticky Navbar (<a href="#football">Football</a>) to let users smoothly jump to each section.
- You can use 'html { scroll-behavior: smooth; }' in CSS to make the jumps feel like page transitions.

DESIGN & CSS:
- Use a stunning deep dark background (e.g., #0f172a) with vibrant neon cyan highlights.
- Navbar must use glassmorphism (rgba background with backdrop-filter: blur(12px)) and be fixed to the top.
- Each section (e.g., id="football") must be min-height: 100vh with padding-top: 100px so the navbar doesn't overlap content.
- Format the news inside each section using a beautiful CSS Grid of cards with dummy text.
- Cards must have a luxurious background (e.g., #1e293b), border-radius: 16px, padding: 2rem, and a glowing neon border on hover using box-shadow.

HTML STRUCTURE & DATA INJECTION:
- One glass Navbar with links to all 7 sections.
- 7 distinct <section> blocks for each sport.
- CRITICAL requirement for cards: You MUST generate EXACTLY 4 news cards inside EVERY single sport section (28 cards total). Do NOT be lazy.
- CRITICAL requirement for data: DO NOT use "Lorem Ipsum" or generic placeholder text. Inside every single card, write realistic, tailored news headlines and summaries specific to that sport (e.g., specific final scores, player transfers, or tournament highlights).
- Include a 'Back to Top' (<a href="#home">) button at the bottom of each section.

Must Output exactly two markdown blocks: ```html and ```css. Do NOT output ```js!"""

    console.print("[yellow]Sending prompt to remote Ollama server... Please wait![/yellow]")
    
    response = agent.send_request(prompt, persona["name"], persona["prompt"], persona["color"])
    
    if response:
        console.print("\n[bold green]Response successfully parsed. Triggering Workspace Manager...[/bold green]")
        wrk.parse_and_save(response, "web")
        console.print("[bold green]Test complete. Files generated in generated/site/[/bold green]")
    else:
        console.print("[bold red]No response received from model.[/bold red]")

if __name__ == "__main__":
    run_test()
