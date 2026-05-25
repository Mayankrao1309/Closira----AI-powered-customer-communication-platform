# Prompt Design — Bloom Aesthetics Chatbot

---

## Full System Prompt

```
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
```

---

## Design Decisions

### 1. SOP Injected Directly Into the Prompt
The entire `sop.json` file is serialised and embedded into the system prompt on every API call. This means the model always has the full business context available and there is no ambiguity about what data it is allowed to use. The instruction "You may ONLY answer questions using the information below" is placed immediately before the SOP data, not buried at the end, so it is the first constraint the model sees before any content.

### 2. Staged Conversation Flow
The prompt defines four explicit stages in order: FAQ -> Lead Qualification -> Escalatio-> Summary. This gives the model a clear progression to follow rather than deciding on its own when to ask qualification questions or when to wrap up. The stages are labelled and separated clearly so the model does not conflate them.

### 3. Qualification Questions Are Fixed
The three qualification questions are hardcoded in the prompt rather than left to the model to decide. This ensures every session collects the same structured data, which makes the final summary consistent and useful for a human agent following up.

### 4. Summary Triggered Externally
The summary is not triggered by the model deciding the conversation is over. It is triggered by the Python code — either when the user types `bye/quit/exit` or when an escalation is detected. The code injects a specific instruction into the conversation history: `"The session has ended. Please provide the full structured summary now."` This prevents the model from generating summaries mid-conversation.

### 5. No AI Self-Identification
The prompt explicitly instructs the model never to say "As an AI..." or mention Gemini or Google. For an SMB customer-facing context, breaking the persona undermines trust and makes the interaction feel impersonal.

---

## Hallucination Prevention

The primary guard against hallucination is the SOP constraint in the system prompt:

> "You may ONLY answer questions using the information below. Do NOT use your own knowledge or make up any facts."

This is reinforced by the escalation rule:

> "If the answer is not in the SOP, say you don't have that information and trigger escalation."

Rather than asking the model to try its best when it doesn't know something, it is instructed to stop and escalate. This means the failure mode for an unknown question is a handoff to a human, not a guessed answer. The model is never given a fallback like "use your best judgement" which would open the door to fabrication.

The SOP data itself is small and specific — prices, hours, services, booking policy. There is little room for the model to drift into unrelated territory because the conversation context is always anchored to a narrow domain.

---

## Escalation Logic

Escalation is rule-based via structured output parsing, not probabilistic.

Working:

The prompt instructs the model to append a specific tag to its reply when any escalation condition is met:
```
[ESCALATE: <brief reason>]
```

The Python function `check_escalation()` parses this tag from the model's response using simple string matching:

```python
def check_escalation(response_text):
    if "[ESCALATE:" in response_text:
        start = response_text.index("[ESCALATE:") + len("[ESCALATE:")
        end = response_text.index("]", start)
        reason = response_text[start:end].strip()
        return True, reason
    return False, None
```

If the tag is found, the clean reply (without the tag) is shown to the customer, the summary is generated, and the chat loop breaks. The escalation reason is extracted and available for logging or handoff.

**Escalation triggers defined in the prompt:**
- Customer expresses frustration, anger, or a complaint
- Customer asks a medical or health-related question
- Customer asks for a discount or price negotiation
- Model cannot answer 2 or more questions from the SOP
- Customer explicitly asks to speak to a human

**Why this approach:**
Parsing a structured tag is deterministic. It does not rely on the model's internal confidence score (which is not exposed via the API) or on sentiment analysis as a separate step. The model decides whether to escalate based on the conversation, signals it via the tag, and the Python layer acts on it. The only failure mode is if the model occasionally omits the tag — which is rare but noted as a known limitation.
