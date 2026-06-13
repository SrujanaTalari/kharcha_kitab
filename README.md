# 📒 Kharcha Kitab — AI Expense Tracker

**खर्च किताब | ఖర్చు పుస్తకం**

A multilingual, AI-powered personal expense tracker built with Streamlit.
Supports English, Hindi, and Telugu with full i18n/l10n.

---

## Features

- **Multilingual UI** — English, हिन्दी, తెలుగు with a single click
- **Indian locale formatting** — ₹1,25,000 (not ₹125,000), lakh/crore display, localized dates
- **AI-powered insights** — Ask questions about your spending in your language
- **Local AI (Ollama)** — Fully offline, no API key needed
- **BYOK** — Bring your own OpenAI / Anthropic / Gemini key
- **Dashboard** — Charts, budget tracker, category breakdown
- **CSV export** — Download your data anytime

---

## Project Structure

```
kharcha_kitab/
├── app.py              ← Main Streamlit app
├── i18n.py             ← i18n/l10n utilities (translate, format currency/date)
├── ai_provider.py      ← Unified AI: Ollama, OpenAI, Anthropic, Gemini
├── data_manager.py     ← CSV-based expense storage
├── requirements.txt
├── expenses.csv        ← Auto-created on first run
└── locales/
    ├── en.json         ← English strings
    ├── hi.json         ← Hindi strings (हिन्दी)
    └── te.json         ← Telugu strings (తెలుగు)
```

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Set up Ollama for local AI
```bash
# Install Ollama from https://ollama.com
ollama pull llama3
ollama serve
```

### 3. Run the app
```bash
streamlit run app.py
```

---

## i18n / l10n Concepts Used

| Concept | Implementation |
|---------|---------------|
| **i18n** | All UI strings externalized to `locales/*.json`. `t("key", lang)` loads them. |
| **l10n** | `babel` library for locale-aware number/currency/date formatting |
| **Indian locale** | `hi_IN` and `te_IN` locale codes for ₹1,25,000 grouping |
| **Lakh/Crore** | Custom helper: ₹25 लाख / ₹25 లక్ష instead of ₹2,500,000 |
| **Date** | "12 जून 2026" (hi), "12 జూన్, 2026" (te), "12 Jun 2026" (en) |

---

## AI Provider Configuration

| Provider | Setup |
|----------|-------|
| **Ollama (local)** | Run `ollama serve` → set URL in Settings (default: http://localhost:11434) |
| **OpenAI** | Paste your `sk-...` key in Settings → AI Provider → OpenAI |
| **Anthropic** | Paste your `sk-ant-...` key in Settings |
| **Gemini** | Paste your Google AI Studio key in Settings |

> **BYOK Privacy**: API keys are stored only in Streamlit session state (browser memory). They are never written to disk or sent to any backend.

---

## Hackathon Checklist

- [x] 2-member team project
- [x] Streamlit stack
- [x] i18n implemented (externalized strings, language switcher)
- [x] l10n implemented (Indian number format, dates, lakh/crore)
- [x] At least 2 Indian languages (Hindi + Telugu)
- [x] AI-powered feature (expense insights, NL Q&A)
- [x] Local AI inference via Ollama
- [x] BYOK for OpenAI, Anthropic, Gemini
