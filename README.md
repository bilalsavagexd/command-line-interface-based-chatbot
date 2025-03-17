# CLI Chatbot with Persistent Memory 🤖

A command-line interface chatbot built in Python that features conversation persistence using MongoDB and integration with OpenRouter API for LLM interactions.

## Features ✨

- **Persistent Conversations**: All chat histories are stored in MongoDB
- **Multiple Conversation Threads**: Switch between different conversation sessions
- **Model Flexibility**: Compatible with OpenRouter's LLM models
- **Interactive CLI**: Rich text formatting and intuitive command system
- **Real-time Streaming**: Messages are streamed in real-time for better interaction
- **Conversation Management**: Export, clear, or switch between conversation threads

## Installation 🚀

1. Clone the repository:
```bash
git clone <repository-url>
cd chatbot
```

2. Install the package using pip:
```bash
pip install -e .
```

3. Create a `.env` file in the project root with your credentials:
```env
OPENROUTER_API_KEY=your_api_key_here
MONGODB_URI=your_mongodb_uri  # defaults to mongodb://localhost:27017/
```

## Usage 💻

Start the chatbot by running:
```bash
chatbot
```

### Available Commands

- `quit` - Exit the application
- `clear` - Clear current chat history
- `model <name>` - Change the OpenRouter model
- `threads` - List all available conversation threads
- `switch <thread_id>` - Switch to a different conversation thread
- `export` - Export current conversation history

## Dependencies 📦

- colorama
- openai
- prompt-toolkit
- pyperclip
- python-dotenv
- rich
- pymongo


## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.
