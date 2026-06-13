"""
ai_provider.py — Unified AI interface
Supports: Ollama (local), OpenAI (BYOK), Anthropic (BYOK), Gemini (BYOK)
"""
import json
import requests
import streamlit as st


def get_ai_response(prompt: str, system: str = "") -> str:
    """
    Route the prompt to whichever AI provider is configured in session state.
    Returns the model's text response or an error string.
    """
    provider = st.session_state.get("ai_provider", "anthropic")

    try:
        if provider == "ollama":
            return _call_ollama(prompt, system)
        elif provider == "openai":
            return _call_openai(prompt, system)
        elif provider == "anthropic":
            return _call_anthropic(prompt, system)
        elif provider == "gemini":
            return _call_gemini(prompt, system)
        elif provider == "groq":
            return _call_groq(prompt, system)
        elif provider == "openrouter":
            return _call_openrouter(prompt, system)
        else:
            return "Unknown provider selected."
    except Exception as e:
        return f"Error: {str(e)}"


# ── Ollama ──────────────────────────────────────────────────────────────────

def _call_ollama(prompt: str, system: str) -> str:
    url = st.session_state.get("ollama_url", "http://localhost:11434")
    model = st.session_state.get("ollama_model", "llama3")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        f"{url}/api/chat",
        json={"model": model, "messages": messages, "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


# ── OpenAI ──────────────────────────────────────────────────────────────────

def _call_openai(prompt: str, system: str) -> str:
    api_key = st.session_state.get("openai_key", "")
    if not api_key:
        return "OpenAI API key not set. Please add it in Settings."

    import openai
    client = openai.OpenAI(api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1000,
    )
    return resp.choices[0].message.content


# ── Anthropic ───────────────────────────────────────────────────────────────

def _call_anthropic(prompt: str, system: str) -> str:
    api_key = st.session_state.get("anthropic_key", "")
    if not api_key:
        return "Anthropic API key not set. Please add it in Settings."

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    kwargs = {"model": "claude-haiku-4-5-20251001", "max_tokens": 1000,
              "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system

    resp = client.messages.create(**kwargs)
    return resp.content[0].text


# ── Gemini ──────────────────────────────────────────────────────────────────

def _call_gemini(prompt: str, system: str) -> str:
    api_key = st.session_state.get("gemini_key", "")
    if not api_key:
        return "Gemini API key not set. Please add it in Settings."

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-2.0-flash-lite",
        system_instruction=system if system else None,
    )
    resp = model.generate_content(prompt)
    return resp.text



# ── Groq ────────────────────────────────────────────────────────────────────

def _call_groq(prompt: str, system: str) -> str:
    api_key = st.session_state.get("groq_key", "")
    if not api_key:
        return "Groq API key not set. Please add it in Settings."
    from groq import Groq
    client = Groq(api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=messages,
        max_tokens=1000,
    )
    return resp.choices[0].message.content


# ── OpenRouter ───────────────────────────────────────────────────────────────

def _call_openrouter(prompt: str, system: str) -> str:
    api_key = st.session_state.get("openrouter_key", "")
    if not api_key:
        return "OpenRouter API key not set."
    import openai
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=messages,
        max_tokens=1000,
    )
    return resp.choices[0].message.content

# ── System prompt builder ───────────────────────────────────────────────────

def build_system_prompt(expenses_summary: str, lang: str) -> str:
    lang_name = {"en": "English", "hi": "Hindi", "te": "Telugu"}.get(lang, "English")
    return f"""You are a helpful personal finance assistant called Kharcha Kitab.
You MUST respond ONLY in {lang_name}.
Be concise, friendly, and use simple language suitable for everyday users.
Use Indian number formatting (lakhs, crores) and the ₹ symbol.

Here is the user's expense data:
{expenses_summary}

Answer the user's question based on this data. If you cannot answer from the data, say so politely."""

def load_keys_from_secrets():
    try:
        if "anthropic_key" in st.secrets:
            st.session_state["anthropic_key"] = st.secrets["anthropic_key"]
        if "openai_key" in st.secrets:
            st.session_state["openai_key"] = st.secrets["openai_key"]
        if "gemini_key" in st.secrets:
            st.session_state["gemini_key"] = st.secrets["gemini_key"]
    except Exception:
        pass
