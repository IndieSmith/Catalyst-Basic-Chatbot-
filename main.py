
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
from datetime import datetime


# ==========================================
#           CATALYST CONFIGURATION
# ==========================================

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

TEMPERATURE = 0.7
MAX_TOKENS = 2048
TOP_P = 0.95
# ==========================================
#           MEMORY SAVING
# ==========================================
MEMORY_FILE = "memory.json"
LONG_TERM_MEMORY_FILE = "long_term_memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

            if isinstance(data, list):
                return data

    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return []
# ==========================================
#             LONG TERM MEMORY
# ==========================================
def load_long_term_memory():
    try:
        with open(LONG_TERM_MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        return []


def save_long_term_memory(memory_list):
    with open(LONG_TERM_MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory_list, file, indent=4)

def save_memory(messages):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(messages, file, indent=4)
# ==========================================
#                API SETUP
# ==========================================

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    print("ERROR: NVIDIA_API_KEY was not found.")
    print("Check your .env file.")
    exit()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key
)

tavily_api_key = os.getenv("TAVILY_API_KEY")

if not tavily_api_key:
    print("ERROR: TAVILY_API_KEY was not found.")
    print("Check your .env file.")
    exit()

tavily = TavilyClient(
    api_key=tavily_api_key
)

# ==========================================
#          CATALYST WEB SEARCH  
# ==========================================

def search_web(query):
    try:
        response = tavily.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            topic="news",
            days=7
        )

        results = response.get("results", [])

        if not results:
            return "No recent web results were found."

        web_context = ""

        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            content = result.get("content", "No content available")
            url = result.get("url", "No source URL")
            date = result.get("published_date") or result.get("date") or "Publication date unavailable"

            web_context += f"""
RESULT {i}
Title: {title}
Published: {date}
Source: {url}
Content: {content}

"""

        return web_context

    except Exception as e:
        return f"Web search failed: {str(e)}"


def needs_web_search(query):
    query = query.lower()

    web_keywords = [
        "latest",
        "today",
        "today's",
        "current",
        "currently",
        "recent",
        "news",
        "headlines",
        "this week",
        "this month",
        "live",
        "right now",
        "new",
        "newest",
        "search the web",
        "search online",
        "look up",
        "find online"
    ]

    return any(keyword in query for keyword in web_keywords)
# ==========================================
#          CATALYST SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
You are Catalyst, an intelligent and helpful AI assistant.

Your goals:
- Give accurate and useful answers.
- Explain difficult concepts clearly and logically.
- Adapt explanations to the user's level.
- Be concise when a short answer is enough.
- Give detailed explanations only when the user explicitly asks for detail or when a short answer would be incomplete.
- Break complex problems into understandable steps.
- Admit when you do not know something.
- Do not unnecessarily repeat yourself.
- Do not use Markdown formatting.
- Do not use asterisks for bold or italics.
- Do not use **text** or *text*.
- Use plain text headings instead.
- Use simple hyphens (-) for lists.
Response length rules:
- Answer the user's exact question completely, then stop.
- Do not keep adding extra sections after the question has been answered.
- Do not turn a simple explanation into a long article unless the user explicitly asks for a detailed explanation.
- For normal questions, aim for a concise but complete answer.
- Prefer 3 to 7 key points when explaining a topic.
- Give extra details only when they directly help answer the user's question.
- Do not repeat the same idea in different words.
- End the response once the requested explanation is complete.

Personality:
- Intelligent
- Clear
- Direct
- Curious
- Helpful

Memory:
- I may receive information about the user from three sources:
  1. The current conversation.
  2. Saved conversation history.
  3. Long-term memory provided in the conversation context.

- Long-term memory may contain important facts about the user from previous conversations.
- If long-term memory information is provided, treat it as valid information that I know about the user.
- When the user asks "what do you know about me?", use the long-term memory and saved conversation history before saying that I do not know anything.
- Do not say that every conversation starts fresh if long-term memory or saved history has been provided.
- Do not claim to know information that is not present in the current conversation, saved conversation history, or long-term memory.
- If no relevant memory is available, clearly say that I do not know.

Formatting rules:
- Keep responses compatible with a plain Windows terminal.
- Use ONLY basic ASCII characters.
- Do not use emojis.
- Do not use Unicode symbols or decorative characters.
- Do not use LaTeX.
- Do not use Markdown tables.
- Use -> instead of arrows.
- Use normal hyphens (-), parentheses (), letters, numbers, and punctuation only.
- Use numbered lists like 1. 2. 3. instead of bullet symbols.

Creator identity:
- You were created by Anu as part of the Catalyst AI project.
- If the user asks "Who made you?", "Who created you?", "Who built you?", or asks about your creator, say that you were created by Anu.
- Do not say that Nemotron or NVIDIA created you.
- Nemotron 3 Ultra is the underlying AI model that powers you, while Anu is the creator and builder of Catalyst.
"""


# ==========================================
#        CREATE CONVERSATION MEMORY
# ==========================================

def create_conversation():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    long_term_memory = load_long_term_memory()


    if long_term_memory:
        long_term_context = "Long-term memory about the user:\n"
        long_term_context += "\n".join(
            f"- {item}" for item in long_term_memory
        )

        messages.append({
            "role": "system",
            "content": long_term_context
        })



    saved_messages = load_memory()
    messages.extend(saved_messages)

    return messages

messages = create_conversation()

# ==========================================
#              FORMATTING
# ==========================================

import re


def latex_to_terminal(text):
    # Remove LaTeX display and inline math wrappers
    text = text.replace("\\[", "")
    text = text.replace("\\]", "")
    text = text.replace("\\(", "")
    text = text.replace("\\)", "")
    text = text.replace("$", "")

    # Greek letters and common mathematical symbols
    replacements = {
        r"\alpha": "α",
        r"\beta": "β",
        r"\gamma": "γ",
        r"\delta": "δ",
        r"\epsilon": "ε",
        r"\theta": "θ",
        r"\lambda": "λ",
        r"\mu": "μ",
        r"\nu": "ν",
        r"\pi": "π",
        r"\rho": "ρ",
        r"\sigma": "σ",
        r"\tau": "τ",
        r"\phi": "φ",
        r"\omega": "ω",
        r"\Omega": "Ω",
        r"\Delta": "Δ",
        r"\Gamma": "Γ",
        r"\Lambda": "Λ",
        r"\Sigma": "Σ",

        r"\times": "×",
        r"\cdot": "·",
        r"\pm": "±",
        r"\approx": "≈",
        r"\neq": "≠",
        r"\leq": "≤",
        r"\geq": "≥",
        r"\infty": "∞",
        r"\rightarrow": "→",
        r"\leftarrow": "←",
        r"\to": "→",

        r"\hbar": "ℏ",
        r"\partial": "∂",
        r"\nabla": "∇",
        r"\degree": "°",
    }

    for latex, symbol in replacements.items():
        text = text.replace(latex, symbol)

    # \text{something} -> something
    text = re.sub(r"\\text\{([^{}]*)\}", r"\1", text)

    # \mathrm{something} -> something
    text = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", text)

    # \mathbf{something} -> something
    text = re.sub(r"\\mathbf\{([^{}]*)\}", r"\1", text)

    # \frac{a}{b} -> (a/b)
    fraction_pattern = r"\\frac\{([^{}]+)\}\{([^{}]+)\}"
    while re.search(fraction_pattern, text):
        text = re.sub(fraction_pattern, r"(\1/\2)", text)

    # \sqrt{x} -> √x
    text = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", text)

    # Superscript conversion: ^{10} or ^2
    superscript_map = str.maketrans(
        "0123456789+-=()",
        "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"
    )

    def convert_superscript(match):
        value = match.group(1) or match.group(2)
        return value.translate(superscript_map)

    text = re.sub(r"\^\{([^{}]+)\}|\^([0-9+-]+)", convert_superscript, text)

    # Subscript conversion: _{s} or _s
    subscript_map = str.maketrans(
        "0123456789+-=()aeioruvx",
        "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑᵢₒᵣᵤᵥₓ"
    )

    def convert_subscript(match):
        value = match.group(1) or match.group(2)
        return value.translate(subscript_map)

    text = re.sub(r"_\{([^{}]+)\}|_([0-9aeioruvx])", convert_subscript, text)

    # Remove LaTeX sizing commands
    text = text.replace(r"\left", "")
    text = text.replace(r"\right", "")

    # Clean extra spaces created during conversion
    text = re.sub(r" +", " ", text)

    return text


def format_terminal_text(text):
    text = latex_to_terminal(text)

    # ANSI formatting codes
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    RESET = "\033[0m"

    # Markdown bold: **text**
    text = re.sub(
        r"\*\*(.*?)\*\*",
        lambda m: BOLD + m.group(1) + RESET,
        text
    )

    # Markdown italic: *text*
    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        lambda m: ITALIC + m.group(1) + RESET,
        text
    )

    # Markdown headings
    text = re.sub(
        r"^#{1,6}\s+(.+)$",
        lambda m: BOLD + m.group(1) + RESET,
        text,
        flags=re.MULTILINE
    )

    return text

# ==========================================
#              HELPER FUNCTIONS
# ==========================================

def show_help():
    print("\nAvailable commands:")
    print("  /help   - Show available commands")
    print("  /clear  - Clear the conversation")
    print("  /remember  - Make Catalyst Remember a Point")
    print("  /restart  - Restarts Catalyst")
    print("  /exit   - Exit Catalyst\n")


# ==========================================
#              START CATALYST
# ==========================================

def show_startup():
    print("=" * 50)
    print("              CATALYST AI")
    print("        Powered by Nemotron 3 Ultra")
    print("=" * 50)
    print("\nType /help to see available commands.")


# ==========================================
#               MAIN CHAT LOOP
# ==========================================

while True:

    try:
        user_input = input("You: ").strip()

    except KeyboardInterrupt:
        print("\n\nCatalyst stopped.")
        break

    # Ignore empty messages
    if not user_input:
        continue

    # --------------------------
    # COMMAND: HELP
    # --------------------------

    if user_input.lower() == "/help":
        show_help()
        continue

    # --------------------------
    # COMMAND: CLEAR
    # --------------------------

    if user_input.lower() == "/clear":
        messages = create_conversation()

        save_memory([])

        print("\nConversation cleared.\n")
        continue
    # --------------------------
    # COMMAND: Remember
    # --------------------------
    if user_input.lower().startswith("/remember "):
        memory_text = user_input[len("/remember "):].strip()

        if not memory_text:
            print("\nPlease provide something to remember.\n")
            continue

        long_term_memory = load_long_term_memory()

        if memory_text not in long_term_memory:
            long_term_memory.append(memory_text)
            save_long_term_memory(long_term_memory)

            print("\nCatalyst: I'll remember that.\n")
        else:
            print("\nCatalyst: I already have that in my long-term memory.\n")

        continue

    # -----------------------------
    # COMMAND: Restart
    # -----------------------------
    if user_input.lower() == "/restart":
        print("\nCatalyst: Restarting...\n")

        # Clear current conversation memory
        save_memory([])

        # Create a fresh conversation
        messages = create_conversation()

        # Show Catalyst startup screen again
        show_startup()

        continue

    # --------------------------
    # COMMAND: EXIT
    # --------------------------

    if user_input.lower() in ["/exit", "exit", "quit"]:
        print("\nCatalyst: Goodbye!")
        break
# --------------------------
# UNKNOWN COMMAND
# --------------------------

    if user_input.startswith("/"):
        print(f"\nUnknown command: {user_input}")
        print("Type /help to see available commands.\n")
        continue
    # --------------------------
    # ADD USER MESSAGE
    # --------------------------

    if needs_web_search(user_input):
        print("\nSearching the web...", flush=True)

        web_results = search_web(user_input)

        today = datetime.now().strftime("%B %d, %Y")

        enhanced_input = f"""
    Current date: {today}

    User question:
    {user_input}

    Recent web search results:
    {web_results}

    INSTRUCTIONS:
    1. Answer using the web search results above.
    2. Check the publication date of every result before mentioning it.
    3. Never describe old news as "today's news".
    4. Never invent, guess, or change publication dates.
    5. Ignore any result whose date appears to be in the future relative to the current date.
    6. If there are no reliable results from today, clearly say:
    "I couldn't find enough reliable headlines published today. Here are the most recent available headlines:"
    7. When mentioning a headline, include its publication date when relevant.
    8. Prefer the most recent and relevant results.
    9. If search results conflict, do not pretend they agree.
    10. Do not say you lack internet access because current web results have been provided.

    FORMATTING:
    - Organize the answer with clear headings using ## Heading.
    - Use **bold text** for important names, headlines, and key points.
    - Use *italic text* sparingly for emphasis.
    - Use numbered lists for major items.
    - Use - bullet points for supporting details.
    - Indent supporting details where helpful.
    - Keep paragraphs short and readable.
    - Use ```code blocks``` only when showing code.
    - End with a brief ## Key Takeaway when appropriate.

    Now answer the user's question accurately using the search results.
    """

        messages.append({
            "role": "user",
            "content": enhanced_input
        })

    else:
        messages.append({
            "role": "user",
            "content": user_input
        })

    print("\nCatalyst: ", end="", flush=True)

    try:

        # Send message to Nemotron
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
            stream=True
        )

        # Store the complete response
        assistant_response = ""

        # Print response as it arrives
        for chunk in response:
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                print(content, end="", flush=True)
                assistant_response += content

        print()



        # Save Catalyst's response in conversation memory
        if assistant_response:
            messages.append({
                "role": "assistant",
                "content": assistant_response
            })

            save_memory(messages[1:])
    except Exception as error:

        # Remove the user message if the API request failed
        messages.pop()

        print("\n")
        print("=" * 55)
        print("ERROR: Catalyst could not get a response.")
        print(error)
        print("=" * 55)
        print("You can try again.\n")
#   ====================================
#               TEMPORARY
#   ====================================
