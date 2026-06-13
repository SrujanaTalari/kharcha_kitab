"""
Kharcha Kitab — AI-powered Expense Tracker
==========================================
Features:
  - Full i18n: English, Hindi (हिन्दी), Telugu (తెలుగు)
  - l10n: Indian number formatting, ₹ currency, locale-aware dates
  - AI Insights: ask questions about your spending in your language
  - Local AI: Ollama support (llama3, mistral, gemma2, etc.)
  - BYOK: OpenAI, Anthropic, Gemini API key support

Run:
    pip install streamlit pandas plotly babel requests openai anthropic google-generativeai
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import io

from i18n import t, fmt_currency, fmt_date, fmt_lakh_crore, get_categories, reverse_category_map, SUPPORTED_LANGS
from data_manager import load_expenses, save_expense, delete_expense, clear_all, get_summary_for_ai, get_monthly_trend
from ai_provider import get_ai_response, build_system_prompt

# ─── Page config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Kharcha Kitab",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border: 1px solid #e9ecef;
        margin-bottom: 8px;
    }
    .metric-label { font-size: 13px; color: #6c757d; margin: 0; }
    .metric-value { font-size: 24px; font-weight: 600; color: #212529; margin: 0; }
    .expense-row {
        background: white;
        border-radius: 8px;
        padding: 10px 14px;
        border: 1px solid #e9ecef;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .cat-badge {
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 99px;
        background: #e9ecef;
        color: #495057;
    }
    .stTextInput > div > div > input { border-radius: 8px; }
    .stSelectbox > div > div { border-radius: 8px; }
    div[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ─── Session state defaults ──────────────────────────────────────────────────

def init_state():
    defaults = {
        "lang": "en",
        "ai_provider": "ollama",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "llama3",
        "openai_key": "",
        "anthropic_key": "",
        "gemini_key": "",
        "monthly_budget": 30000.0,
        "page": "dashboard",
        "ai_chat": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# Auto-load keys from Streamlit secrets
try:
    if "openrouter_key" in st.secrets:
        st.session_state["openrouter_key"] = st.secrets["openrouter_key"]
        st.session_state["ai_provider"] = "openrouter"
except Exception:
    pass

lang = st.session_state["lang"]

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"## 📒 {t('app_title', lang).split(' - ')[0]}")
    st.caption(t("app_subtitle", lang))
    st.divider()

    # Language picker
    lang_choice = st.selectbox(
        t("language_label", lang),
        list(SUPPORTED_LANGS.keys()),
        index=list(SUPPORTED_LANGS.values()).index(lang),
    )
    new_lang = SUPPORTED_LANGS[lang_choice]
    if new_lang != lang:
        st.session_state["lang"] = new_lang
        st.rerun()

    st.divider()

    # Navigation
    pages = {
        "dashboard":    ("📊", t("nav_dashboard", lang)),
        "add_expense":  ("➕", t("nav_add_expense", lang)),
        "ai_insights":  ("🤖", t("nav_ai_insights", lang)),
        "settings":     ("⚙️", t("nav_settings", lang)),
    }
    for page_key, (icon, label) in pages.items():
        if st.button(f"{icon}  {label}", use_container_width=True,
                     type="primary" if st.session_state["page"] == page_key else "secondary"):
            st.session_state["page"] = page_key
            st.rerun()

    st.divider()
    provider_labels = {
        "ollama":    t("provider_ollama", lang),
        "openai":    t("provider_openai", lang),
        "anthropic": t("provider_anthropic", lang),
        "gemini":    t("provider_gemini", lang),
        "openrouter": "OpenRouter (Free)",
    }
    provider = st.session_state['ai_provider']
    label = provider_labels.get(provider, provider)
    st.caption(f"🔌 {t('ai_provider', lang)}: **{label}**")

# ─── Load data ───────────────────────────────────────────────────────────────

df = load_expenses()
today = date.today()

# ─── Dashboard ───────────────────────────────────────────────────────────────

if st.session_state["page"] == "dashboard":
    st.title(f"📊 {t('nav_dashboard', lang)}")

    # Filter helpers
    this_month_df = df[
        (pd.to_datetime(df["date"]).dt.month == today.month) &
        (pd.to_datetime(df["date"]).dt.year == today.year)
    ] if not df.empty else df

    this_week_df = df[
        pd.to_datetime(df["date"]).dt.date >= (today - timedelta(days=7))
    ] if not df.empty else df

    today_df = df[
        pd.to_datetime(df["date"]).dt.date == today
    ] if not df.empty else df

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t("this_month", lang), fmt_currency(this_month_df["amount"].sum() if not this_month_df.empty else 0, lang))
    with col2:
        st.metric(t("this_week", lang), fmt_currency(this_week_df["amount"].sum() if not this_week_df.empty else 0, lang))
    with col3:
        st.metric(t("today", lang), fmt_currency(today_df["amount"].sum() if not today_df.empty else 0, lang))
    with col4:
        avg_daily = (this_month_df["amount"].sum() / max(today.day, 1)) if not this_month_df.empty else 0
        st.metric(t("avg_daily", lang), fmt_currency(avg_daily, lang))

    # Budget progress
    budget = st.session_state["monthly_budget"]
    month_total = this_month_df["amount"].sum() if not this_month_df.empty else 0
    pct = min(month_total / budget * 100, 100) if budget > 0 else 0
    over = month_total > budget

    st.markdown(f"**{t('monthly_budget', lang)}: {fmt_currency(budget, lang)}**")
    bar_color = "red" if over else "green"
    st.progress(pct / 100)
    if over:
        st.error(f"⚠️ {t('over_budget', lang)} ({fmt_currency(month_total - budget, lang)} {t('budget_used', lang)})")
    else:
        st.caption(f"{pct:.1f}% {t('budget_used', lang)}")

    st.divider()

    # Charts
    if not this_month_df.empty:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader(t("spending_by_category", lang))
            rev_map = reverse_category_map(lang)
            chart_df = this_month_df.copy()
            chart_df["category_local"] = chart_df["category_en"].map(rev_map).fillna(chart_df["category_en"])
            cat_data = chart_df.groupby("category_local")["amount"].sum().reset_index()
            fig_pie = px.pie(cat_data, values="amount", names="category_local",
                             color_discrete_sequence=px.colors.qualitative.Pastel,
                             hole=0.4)
            fig_pie.update_traces(textinfo="label+percent")
            fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            st.subheader(t("spending_trend", lang))
            trend = get_monthly_trend(df)
            if not trend.empty:
                fig_bar = px.bar(trend, x="month_str", y="amount",
                                 color_discrete_sequence=["#4361ee"],
                                 labels={"month_str": "", "amount": "₹"})
                fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info(t("no_expenses", lang))

    st.divider()

    # Recent expenses table
    st.subheader(t("recent_expenses", lang))
    if not df.empty:
        rev_map = reverse_category_map(lang)
        display_df = df.sort_values("date", ascending=False).head(20).copy()
        display_df["date_fmt"] = display_df["date"].apply(lambda d: fmt_date(d, lang))
        display_df["amount_fmt"] = display_df["amount"].apply(lambda a: fmt_currency(a, lang))
        display_df["cat_local"] = display_df["category_en"].map(rev_map).fillna(display_df["category_en"])

        for _, row in display_df.iterrows():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.write(row["name"])
            c2.write(row["amount_fmt"])
            c3.write(row["cat_local"])
            c4.write(row["date_fmt"])
            if c5.button("🗑", key=f"del_{row['id']}"):
                delete_expense(int(row["id"]))
                st.toast(t("confirm_delete", lang))
                st.rerun()

        # CSV export
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            label=f"⬇️ {t('export_csv', lang)}",
            data=csv_buf.getvalue(),
            file_name="kharcha_kitab_expenses.csv",
            mime="text/csv",
        )
    else:
        st.info(t("no_expenses", lang))

# ─── Add Expense ─────────────────────────────────────────────────────────────

elif st.session_state["page"] == "add_expense":
    st.title(f"➕ {t('add_expense', lang)}")

    categories_local = get_categories(lang)
    cat_map = dict(zip(categories_local, get_categories("en")))

    with st.form("add_expense_form", clear_on_submit=True):
        name = st.text_input(t("expense_name", lang), placeholder=t("expense_name_placeholder", lang))
        amount = st.number_input(t("amount", lang), min_value=0.0, step=10.0, format="%.2f")
        category_local = st.selectbox(t("category", lang), categories_local)
        expense_date = st.date_input(t("date", lang), value=today)
        note = st.text_area(t("note", lang), height=80)
        submitted = st.form_submit_button(t("save_expense", lang), use_container_width=True, type="primary")

    if submitted:
        if name.strip() and amount > 0:
            category_en = cat_map.get(category_local, category_local)
            save_expense(name.strip(), float(amount), category_en, expense_date, note.strip())
            st.success(t("expense_saved", lang))
            st.balloons()
        else:
            st.warning("Please enter a name and amount." if lang == "en"
                       else "कृपया नाम और राशि दर्ज करें।" if lang == "hi"
                       else "దయచేసి పేరు మరియు మొత్తం నమోదు చేయండి.")

# ─── AI Insights ─────────────────────────────────────────────────────────────

elif st.session_state["page"] == "ai_insights":
    st.title(f"🤖 {t('ai_insights_title', lang)}")

    provider_labels = {
        "ollama":    t("provider_ollama", lang),
        "openai":    t("provider_openai", lang),
        "anthropic": t("provider_anthropic", lang),
        "gemini":    t("provider_gemini", lang),
    }
    st.caption(f"🔌 {t('ai_provider', lang)}: **{provider_labels[st.session_state['ai_provider']]}**  •  {t('nav_settings', lang)} → ⚙️")

    # Chat history display
    for msg in st.session_state["ai_chat"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Suggested questions
    if not st.session_state["ai_chat"]:
        suggestions = {
            "en": ["How much did I spend this month?", "What is my top spending category?", "How can I reduce my expenses?"],
            "hi": ["इस महीने कितना खर्च हुआ?", "सबसे ज्यादा किस चीज़ पर खर्च हुआ?", "खर्च कम करने के सुझाव दें।"],
            "te": ["ఈ నెల ఎంత ఖర్చు అయింది?", "ఎక్కువగా ఏ వర్గంలో ఖర్చు అయింది?", "ఖర్చులు తగ్గించడం ఎలా?"],
        }
        st.write("**💡 Try asking:**" if lang == "en" else "**💡 అడగండి:**" if lang == "te" else "**💡 पूछें:**")
        cols = st.columns(3)
        for i, suggestion in enumerate(suggestions.get(lang, suggestions["en"])):
            if cols[i].button(suggestion, use_container_width=True):
                st.session_state["ai_chat"].append({"role": "user", "content": suggestion})
                summary = get_summary_for_ai(df)
                system = build_system_prompt(summary, lang)
                with st.spinner(t("ai_thinking", lang)):
                    reply = get_ai_response(suggestion, system)
                st.session_state["ai_chat"].append({"role": "assistant", "content": reply})
                st.rerun()

    # Chat input
    user_input = st.chat_input(t("ask_ai_placeholder", lang))
    if user_input:
        st.session_state["ai_chat"].append({"role": "user", "content": user_input})
        summary = get_summary_for_ai(df)
        system = build_system_prompt(summary, lang)
        with st.spinner(t("ai_thinking", lang)):
            reply = get_ai_response(user_input, system)
        st.session_state["ai_chat"].append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state["ai_chat"]:
        if st.button("🗑 Clear chat"):
            st.session_state["ai_chat"] = []
            st.rerun()

# ─── Settings ────────────────────────────────────────────────────────────────

elif st.session_state["page"] == "settings":
    st.title(f"⚙️ {t('settings_title', lang)}")

    # AI Provider
    st.subheader(t("ai_provider", lang))
    provider_options = {
        t("provider_ollama", lang):    "ollama",
        t("provider_openai", lang):    "openai",
        t("provider_anthropic", lang): "anthropic",
        t("provider_gemini", lang):    "gemini",
    }
    selected_label = [k for k, v in provider_options.items() if v == st.session_state["ai_provider"]][0]
    new_provider_label = st.radio(t("ai_provider", lang), list(provider_options.keys()),
                                   index=list(provider_options.keys()).index(selected_label),
                                   label_visibility="collapsed")
    st.session_state["ai_provider"] = provider_options[new_provider_label]

    st.divider()

    if st.session_state["ai_provider"] == "ollama":
        st.subheader("Ollama")
        st.info("Make sure Ollama is running: `ollama serve`" if lang == "en"
                else "सुनिश्चित करें Ollama चल रहा है: `ollama serve`" if lang == "hi"
                else "Ollama నడుస్తుందని నిర్ధారించుకోండి: `ollama serve`")
        st.session_state["ollama_url"] = st.text_input(
            t("ollama_url", lang), value=st.session_state["ollama_url"])
        st.session_state["ollama_model"] = st.selectbox(
            t("ollama_model", lang),
            ["llama3", "llama3.2", "mistral", "gemma2", "phi3", "qwen2.5"],
            index=["llama3", "llama3.2", "mistral", "gemma2", "phi3", "qwen2.5"].index(
                st.session_state["ollama_model"]) if st.session_state["ollama_model"] in
                ["llama3", "llama3.2", "mistral", "gemma2", "phi3", "qwen2.5"] else 0
        )

    elif st.session_state["ai_provider"] == "openai":
        st.subheader("OpenAI")
        key = st.text_input(t("api_key", lang), value=st.session_state["openai_key"],
                            type="password", help=t("api_key_help", lang))
        st.session_state["openai_key"] = key

    elif st.session_state["ai_provider"] == "anthropic":
        st.subheader("Anthropic")
        key = st.text_input(t("api_key", lang), value=st.session_state["anthropic_key"],
                            type="password", help=t("api_key_help", lang))
        st.session_state["anthropic_key"] = key

    elif st.session_state["ai_provider"] == "gemini":
        st.subheader("Google Gemini")
        key = st.text_input(t("api_key", lang), value=st.session_state["gemini_key"],
                            type="password", help=t("api_key_help", lang))
        st.session_state["gemini_key"] = key

    st.divider()

    # Budget setting
    st.subheader(t("monthly_budget", lang))
    budget = st.number_input(
        t("monthly_budget", lang),
        min_value=0.0, step=1000.0,
        value=float(st.session_state["monthly_budget"]),
        label_visibility="collapsed",
    )
    st.session_state["monthly_budget"] = budget
    st.caption(f"= {fmt_lakh_crore(budget, lang)}")

    st.divider()

    # Danger zone
    st.subheader("⚠️ " + t("clear_all", lang))
    if st.button(t("clear_all", lang), type="primary"):
        clear_all()
        st.warning(t("cleared", lang))
        st.rerun()
