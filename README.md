# Catalyst-Basic-Chatbot-

A basic version of the Catalyst AI chatbot project.

This repository contains the core chatbot implementation, including conversation handling, environment configuration, long-term memory, and project dependencies.

## Features

- AI-powered chatbot
- Conversation-based interactions
- Long-term memory support
- Environment variable configuration
- Customizable system behavior
- Python-based implementation

## Project Structure

```text
Catalyst-Basic-Chatbot-
├── .gitignore
├── README.md
├── long_term_memory.json
├── main.py
└── requirements.txt
```

## Files

### `main.py`

Contains the main logic and functionality of the Catalyst chatbot.

### `long_term_memory.json`

Stores the chatbot's long-term memory data.

### `requirements.txt`

Contains the Python dependencies required to run the project.

### `.gitignore`

Prevents sensitive files, virtual environments, and unnecessary Python cache files from being uploaded to GitHub.


## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file and add the required environment variables.

Then run the chatbot:

```bash
python main.py
```

## Tech Stack

- Python
- OpenAI API
- Tavily API
- python-dotenv

## Project Status

Currently under active development.

This repository contains the basic chatbot implementation of Catalyst AI. Additional capabilities and improvements are being developed separately.

## Catalyst AI

For the broader Catalyst AI project, including its overall vision, features, and future development, see the [main Catalyst AI repository](https://github.com/IndieSmith/Catalyst-AI).
