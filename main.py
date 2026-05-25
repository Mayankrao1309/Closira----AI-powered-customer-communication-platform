import os
import json
from datetime import datetime
import google.generativeai as genai


genai.configure(api_key="AIzaSyAr7DSb4AAcBa13****************") ### add your api key here !!

with open("sop.json", "r") as f:
    SOP = json.load(f)

SOP_TEXT = json.dumps(SOP, indent=2)


# PROMPT PROVIDED

SYSTEM_PROMPT = f"""
You are a friendly, professional AI receptionist for Bloom Aesthetics Clinic.
You handle inbound customer enquiries via chat.

--------------------------------------------------------------------
YOUR KNOWLEDGE SOURCE (SOP)
You may ONLY answer questions using the information below.
Do NOT use your own knowledge or make up any facts.
If the answer is not in the SOP, say you don't have that information and trigger escalation.

{SOP_TEXT}

--------------------------------------------------------------------
CONVERSATION STAGES

STAGE 1 — FAQ:
Answer the customer's question strictly from the SOP.

STAGE 2 — LEAD QUALIFICATION:
After answering 1-2 questions, ask these qualification questions one at a time:
  Q1: "Have you visited us before, or is this your first time?"
  Q2: "Which treatment are you most interested in?"
  Q3: "Do you have any upcoming events or a timeline in mind?"

STAGE 3 — ESCALATION:
Immediately escalate if ANY of these occur:
  - Customer expresses frustration, anger, or a complaint
  - Customer asks a medical or health-related question
  - Customer asks for a discount or price negotiation
  - You cannot answer 2+ questions from the SOP
  - Customer explicitly asks to speak to a human

When escalating, end your message with this exact tag on a new line:
[ESCALATE: <brief reason>]

---------------------------------------------------------------------
STAGE 4 — SUMMARY:
Only when the conversation is over or escalated, return this exact format:

SUMMARY
-------
Customer Intent: <what they wanted>
Treatment Interest: <which service>
Qualification Answers: <their Q1/Q2/Q3 responses>
SOP Gaps: <questions you couldn't answer, or "None">
Escalated: <Yes/No — reason if yes>
Recommended Next Action: <what a human agent should do>

----------------------------------------------------------------------
TONE & PERSONA
- Warm, professional, concise
- Keep replies short (2-4 sentences) unless summarising
- Never say "As an AI..." or mention Gemini or Google
"""


# ESCALATION CHECKER

def check_escalation(response_text):
    if "[ESCALATE:" in response_text:
        start = response_text.index("[ESCALATE:") + len("[ESCALATE:")
        end = response_text.index("]", start)
        reason = response_text[start:end].strip()
        return True, reason
    return False, None


# API CALL TO GEMINI

model = genai.GenerativeModel("gemini-2.5-flash")

def chat(history):

    history_text = ""
    for msg in history:
        role = "Customer" if msg["role"] == "user" else "Bloom AI"
        history_text += f"{role}: {msg['content']}\n"

    full_prompt = f"{SYSTEM_PROMPT}\n\nCONVERSATION SO FAR:\n{history_text}\nBloom AI:"

    response = model.generate_content(full_prompt)
    return response.text.strip()


# SUMMARY GENERATOR

def generate_summary(history):
    print("\n Generating session summary...\n")
    summary_history = history + [{
        "role": "user",
        "content": "The session has ended. Please provide the full structured summary now."
    }]
    summary = chat(summary_history)
    
    print(summary)
    print("-" * 50)

# CHAT LOOP


def main():
    print("\nWelcome to Bloom Aesthetics Clinic")
    print("Type your message below. Type 'bye' or 'quit' to end the session.\n")
    print("-" * 50)

    conversation_history = []

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue

        if user_input.lower() in ["bye", "quit", "exit"]:
            generate_summary(conversation_history)
            print("Thank you for contacting Bloom Aesthetics. Goodbye!")
            break

        conversation_history.append({"role": "user", "content": user_input})
        reply = chat(conversation_history)

        is_escalated, reason = check_escalation(reply)
        clean_reply = reply.split("[ESCALATE:")[0].strip() if is_escalated else reply

        print(f"\nBloom AI: {clean_reply}\n")

        conversation_history.append({"role": "assistant", "content": reply})

        if is_escalated:
            generate_summary(conversation_history)
            print("Thank you for contacting Bloom Aesthetics. Goodbye!")
            break

if __name__ == "__main__":
    main()
