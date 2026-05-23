# Closira — Bloom Aesthetics Chatbot

A CLI-based AI customer support workflow built for the Closira AI Engineering Intern assignment. It simulates how a small business can handle inbound customer enquiries using an AI receptionist grounded in a predefined SOP.

---

## Approach

The bot handles a conversation in four stages:

1. **FAQ** — Answers customer questions strictly from `sop.json`. If the answer isn't in the SOP, it escalates instead of guessing.
2. **Lead Qualification** — After answering initial questions, asks three structured questions to qualify the customer (visit history, treatment interest, timeline).
3. **Escalation** — Detects triggers like complaints, medical questions, pricing negotiation, or out-of-scope queries. Ends the conversation and hands off to a human.
4. **Summary** — At the end of every session (normal exit or escalation), generates a structured summary with customer intent, qualification answers, SOP gaps, and recommended next action.

The entire SOP is injected into the system prompt on every API call. The model is explicitly instructed to answer only from that data. Escalation is handled via a structured output tag `[ESCALATE: reason]` that the Python code parses — this makes it deterministic rather than relying on model confidence.

---

## Dependencies

```
google-generativeai
```

Install with:

```bash
pip install google-generativeai
```

> **Note:** `google-generativeai` is deprecated. It still works but will show a FutureWarning on startup. It has not been migrated to `google-genai` yet to keep the code simple for this assignment.

---

## Setup

1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd closira
   ```

2. **Install dependency**
   ```bash
   pip install google-generativeai
   ```

3. **Add your Gemini API key**

   Open `main.py` and replace the key on line 7:
   ```python
   genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
   ```

   Get a free key at [aistudio.google.com](https://aistudio.google.com) → Get API Key.

   > **India users:** Google AI Studio is geo-blocked in India. Use a VPN connected to a US or UK server to create the key and run the bot.

4. **Make sure `sop.json` is in the same folder as `main.py`**

---

## How to Run

```bash
python main.py
```

Type your message and press Enter. Type `bye`, `quit`, or `exit` to end the session and generate a summary.

---

## File Structure

```
closira/
├── main.py                        # Main chatbot logic
├── sop.json                       # SOP data — single source of truth for the bot
├── prompt_design.md               # Prompt decisions and reasoning
├── README.md                      # This file
└── test_transcripts/
    ├── 01_faq.md                  # In-SOP question
    ├── 02_out_of_scope.md         # Out-of-scope question
    ├── 03_escalation.md           # Angry customer / complaint
    ├── 04_lead_qualification.md   # Full qualification flow
    └── 05_summary.md              # Session summary
```

---

## Trade-offs and Known Limitations

- **Escalation depends on model output format.** The bot detects escalation by parsing the `[ESCALATE: reason]` tag from the model's reply. If Gemini occasionally omits this tag despite the instruction, the escalation won't trigger. This is rare but possible.

- **Full history sent on every call.** The model has no memory between calls, so the entire conversation history is included in every prompt. This works fine for short sessions but token cost grows with conversation length.

- **SOP is hardcoded and small.** The SOP is a single JSON file injected directly into the prompt. This approach does not scale to large knowledge bases — for that, a RAG (retrieval-augmented generation) setup would be needed.

- **Gemini model used:** `gemini-2.5-flash`. Model availability may change; if a 404 error occurs, update the model name in `main.py` line 75.

- **No persistent storage.** Conversation history and summaries exist only for the duration of the session. Summaries are printed to the terminal but not saved to a file.
