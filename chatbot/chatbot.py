# Imports and Setup
import os  # For accessing environment variables
import time  # For timing how long the reasoning process takes
from openai import OpenAI  # For API clients
from rich.panel import Panel  # For fancy console output with colors and formatting
from dotenv import load_dotenv  # Loads environment variables from a .env file
from rich.syntax import Syntax
from rich import print as rprint
from prompt_toolkit.styles import Style  # For creating better command-line interfaces
from prompt_toolkit import PromptSession

# Load environment variables
load_dotenv()

# Model Constants
OPENROUTER_MODEL = "meta-llama/llama-3.2-11b-vision-instruct:free"

class ModelChain:
    # Initialization
    def __init__(self):
        # Initialize OpenRouter client
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        
        self.openrouter_messages = []
        self.current_model = OPENROUTER_MODEL

    # Model Selection Methods
    def set_model(self, model_name):
        self.current_model = model_name

    def get_model_display_name(self):
        return self.current_model

    # OpenRouter Response Method
    def get_openrouter_response(self, user_input):
        prompt = f"<question>{user_input}</question>\n\n"
        
        self.openrouter_messages.append({"role": "user", "content": prompt})
        
        rprint(f"[green]{self.get_model_display_name()}[/]")
        
        try:
            completion = self.openrouter_client.chat.completions.create(
                model=self.current_model,
                messages=self.openrouter_messages,
                stream=True
            )
            
            full_response = ""
            for chunk in completion:
                try:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content is not None:
                        content_piece = delta.content
                        full_response += content_piece
                        print(content_piece, end="", flush=True)
                except Exception as e:
                    rprint(f"\n[red]Error processing chunk: {str(e)}[/]")
                    continue
                    
        except Exception as e:
            rprint(f"\n[red]Error in streaming response: {str(e)}[/]")
            return "Error occurred while streaming response"
        
        self.openrouter_messages.append({"role": "assistant", "content": full_response})
        
        print("\n")
        return full_response

# Main Function
def main():
    chain = ModelChain()
    
    # Initialize prompt session with styling
    style = Style.from_dict({
        'prompt': 'orange bold',
    })
    session = PromptSession(style=style)
    
    rprint(Panel.fit(
        "[bold cyan]CLI Based Chatbot[/]",
        title="[bold cyan]CHATBOT 🧠[/]",
        border_style="cyan"
    ))
    rprint("[yellow]Commands:[/]")
    rprint(" • Type [bold red]'quit'[/] to exit")
    rprint(" • Type [bold magenta]'model <name>'[/] to change the OpenRouter model")
    rprint(" • Type [bold magenta]'clear'[/] to clear chat history\n")

    # Main Loop
    while True:
        try:
            user_input = session.prompt("\nYou: ", style=style).strip()
            
            if user_input.lower() == 'quit':
                print("\nGoodbye! 👋")
                break

            if user_input.lower() == 'clear':
                chain.openrouter_messages = []
                rprint("\n[magenta]Chat history cleared![/]\n")
                continue
                
            if user_input.lower().startswith('model '):
                new_model = user_input[6:].strip()
                chain.set_model(new_model)
                print(f"\nChanged model to: {chain.get_model_display_name()}\n")
                continue
            
            openrouter_response = chain.get_openrouter_response(user_input)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

if __name__ == "__main__":
    main()