# Imports and Setup
import os
import time
import uuid
from openai import OpenAI
from rich.panel import Panel
from dotenv import load_dotenv
from rich.syntax import Syntax
from rich import print as rprint
from prompt_toolkit.styles import Style
from prompt_toolkit import PromptSession
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Model Constants
OPENROUTER_MODEL = "meta-llama/llama-3.2-11b-vision-instruct:free"
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

class ModelChain:
    # Initialization
    def __init__(self, thread_id=None):
        # Initialize OpenRouter client
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        
        self.current_model = OPENROUTER_MODEL
        
        # Set up MongoDB connection
        self.mongo_client = MongoClient(MONGODB_URI)
        self.db = self.mongo_client["chatbot_memory"]
        self.conversations = self.db["conversations"]
        
        # Create or retrieve conversation thread
        self.thread_id = thread_id if thread_id else str(uuid.uuid4())
        self.load_conversation_history()
        
        rprint(f"[yellow]Using conversation ID: {self.thread_id}[/]")

    # Load conversation history from MongoDB
    def load_conversation_history(self):
        conversation = self.conversations.find_one({"thread_id": self.thread_id})
        if conversation:
            self.openrouter_messages = conversation["messages"]
            rprint(f"[green]Loaded existing conversation with {len(self.openrouter_messages)} messages[/]")
        else:
            self.openrouter_messages = []
            rprint("[green]Created new conversation[/]")
            # Create a new conversation document
            self.conversations.insert_one({
                "thread_id": self.thread_id,
                "messages": self.openrouter_messages,
                "created_at": time.time(),
                "updated_at": time.time()
            })
    
    # Save conversation history to MongoDB
    def save_conversation_history(self):
        self.conversations.update_one(
            {"thread_id": self.thread_id},
            {
                "$set": {
                    "messages": self.openrouter_messages,
                    "updated_at": time.time()
                }
            }
        )

    # Model Selection Methods
    def set_model(self, model_name):
        self.current_model = model_name
        self.save_conversation_history()

    def get_model_display_name(self):
        return self.current_model

    # OpenRouter Response Method
    def get_openrouter_response(self, user_input):
        prompt = user_input
        
        self.openrouter_messages.append({"role": "user", "content": prompt})
        # Save immediately after user message
        self.save_conversation_history()
        
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
        # Save after receiving assistant response
        self.save_conversation_history()
        
        print("\n")
        return full_response
    
    # Clear conversation history
    def clear_history(self):
        self.openrouter_messages = []
        self.save_conversation_history()

# Function to list all available conversation threads
def list_conversation_threads(mongo_client):
    db = mongo_client["chatbot_memory"]
    conversations = db["conversations"]
    
    threads = list(conversations.find({}, {"thread_id": 1, "updated_at": 1, "messages": 1}))
    
    if not threads:
        rprint("[yellow]No existing conversations found[/]")
        return None
    
    rprint("[yellow]Available conversation threads:[/]")
    for i, thread in enumerate(threads):
        # Get first few messages as preview
        message_preview = ""
        for msg in thread.get("messages", [])[:2]:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if len(content) > 30:
                    content = content[:27] + "..."
                message_preview = f'"{content}"'  # Fixed quotes here
                break
                
        # Format timestamp
        timestamp = time.strftime('%Y-%m-%d %H:%M', time.localtime(thread.get("updated_at", 0)))
        
        # Show thread info
        rprint(f"  {i+1}. ID: [cyan]{thread['thread_id']}[/] - Last updated: {timestamp} - Messages: {len(thread.get('messages', []))} - Preview: {message_preview}")
    
    return threads

# Main Function
def main():
    # Initialize MongoDB client for thread management
    mongo_client = MongoClient(MONGODB_URI)
    
    # Prompt for thread selection or create new
    thread_choice = input("Do you want to (n)ew conversation or (l)oad existing? [n/l]: ").lower()
    
    thread_id = None
    if thread_choice == 'l':
        threads = list_conversation_threads(mongo_client)
        if threads:
            thread_num = input("Enter thread number to load (or press Enter for new): ")
            if thread_num and thread_num.isdigit() and 0 < int(thread_num) <= len(threads):
                thread_id = threads[int(thread_num)-1]["thread_id"]
    
    # Initialize model chain with selected thread
    chain = ModelChain(thread_id)
    
    # Initialize prompt session with styling
    style = Style.from_dict({
        'prompt': 'orange bold',
    })
    session = PromptSession(style=style)
    
    rprint(Panel.fit(
        "[bold cyan]CLI Based Chatbot with Persistent Memory[/]",
        title="[bold cyan]CHATBOT 🧠[/]",
        border_style="cyan"
    ))
    rprint("[yellow]Commands:[/]")
    rprint(" • Type [bold red]'quit'[/] to exit")
    rprint(" • Type [bold magenta]'model <name>'[/] to change the OpenRouter model")
    rprint(" • Type [bold magenta]'clear'[/] to clear chat history")
    rprint(" • Type [bold magenta]'threads'[/] to list available conversation threads")
    rprint(" • Type [bold magenta]'switch <thread_id>'[/] to switch to a different conversation")
    rprint(" • Type [bold magenta]'export'[/] to export the current conversation history\n")

    # Main Loop
    while True:
        try:
            user_input = session.prompt("\nYou: ", style=style).strip()
            
            if user_input.lower() == 'quit':
                print("\nGoodbye! 👋")
                break

            if user_input.lower() == 'clear':
                chain.clear_history()
                rprint("\n[magenta]Chat history cleared![/]\n")
                continue
                
            if user_input.lower().startswith('model '):
                new_model = user_input[6:].strip()
                chain.set_model(new_model)
                print(f"\nChanged model to: {chain.get_model_display_name()}\n")
                continue
                
            if user_input.lower() == 'threads':
                list_conversation_threads(mongo_client)
                continue
                
            if user_input.lower().startswith('switch '):
                new_thread_id = user_input[7:].strip()
                # Check if thread exists
                if mongo_client["chatbot_memory"]["conversations"].find_one({"thread_id": new_thread_id}):
                    # Create a new chain with the selected thread
                    chain = ModelChain(new_thread_id)
                    rprint(f"\n[magenta]Switched to conversation: {new_thread_id}[/]\n")
                else:
                    rprint(f"\n[red]Thread {new_thread_id} not found[/]\n")
                continue
                
            if user_input.lower() == 'export':
                # Simple export to console
                rprint("\n[yellow]Conversation export:[/]")
                for msg in chain.openrouter_messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    rprint(f"[cyan]{role.upper()}:[/] {content}\n")
                continue
            
            openrouter_response = chain.get_openrouter_response(user_input)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

if __name__ == "__main__":
    main()