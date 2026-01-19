# ==============================================================================
# CUSTOM STYLES - CSS for Enhanced Streamlit UI
# ==============================================================================
# Modern, premium styling for the exam scheduling platform
# Inspired by high-end SaaS designs: Glassmorphism, sleek typography, micro-animations
# ==============================================================================

CUSTOM_CSS = """
<style>
/* ==============================================================================
   GLOBAL STYLES & FONTS
============================================================================== */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary: #0061FF;
    --primary-gradient: linear-gradient(135deg, #0061FF 0%, #60EFFF 100%);
    --bg-dark: #0B0E14;
    --card-bg: rgba(23, 27, 34, 0.7);
    --border-color: rgba(255, 255, 255, 0.08);
    --text-primary: #FFFFFF;
    --text-secondary: #8A94A6;
    --success: #00D084;
    --warning: #FFAB00;
    --error: #FF5630;
}

* {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Base Body Styles */
.main {
    background-color: var(--bg-dark);
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 5rem !important;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes glow {
    0% { box-shadow: 0 0 5px rgba(0, 97, 255, 0.2); }
    50% { box-shadow: 0 0 20px rgba(0, 97, 255, 0.4); }
    100% { box-shadow: 0 0 5px rgba(0, 97, 255, 0.2); }
}

.kpi-card {
    animation: fadeIn 0.5s ease-out backwards;
}

/* Staggered delay for cards */
.kpi-card:nth-child(1) { animation-delay: 0.1s; }
.kpi-card:nth-child(2) { animation-delay: 0.2s; }
.kpi-card:nth-child(3) { animation-delay: 0.3s; }

/* Interactive elements */
button, .stButton>button {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

button:hover {
    transform: scale(1.02);
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
div[data-testid="stStatusWidget"] {display: none;}

/* ==============================================================================
   SIDEBAR CUSTOMIZATION
============================================================================== */
[data-testid="stSidebar"] {
    background-color: #0F1218;
    border-right: 1px solid var(--border-color);
}

[data-testid="stSidebarNav"] {
    background-image: none;
    padding-top: 2rem;
}

/* Links in sidebar */
[data-testid="stSidebarNav"] li a {
    border-radius: 12px;
    margin: 0.2rem 0.5rem;
    padding: 0.6rem 1rem;
    transition: all 0.2s ease;
}

[data-testid="stSidebarNav"] li a:hover {
    background-color: rgba(0, 97, 255, 0.1);
    color: var(--primary);
}

[data-testid="stSidebarNav"] li a[aria-current="page"] {
    background-color: rgba(0, 97, 255, 0.15);
    color: var(--primary);
    font-weight: 600;
}

/* ==============================================================================
   CARDS & KPI CONTAINERS
============================================================================== */
.kpi-card {
    background: var(--card-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.kpi-card:hover {
    transform: translateY(-5px);
    border-color: rgba(0, 97, 255, 0.3);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

.kpi-icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
    background: rgba(0, 97, 255, 0.1);
}

.kpi-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}

.kpi-label {
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-weight: 500;
}

.kpi-trend {
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 0.5rem;
}

.trend-up { color: var(--success); }
.trend-down { color: var(--error); }

/* ==============================================================================
   BUTTONS
============================================================================== */
.stButton > button {
    background: var(--primary-gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px rgba(0, 97, 255, 0.2) !important;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 97, 255, 0.4) !important;
}

.stButton > button:active {
    transform: scale(0.98);
}

/* Outline/Secondary Button */
div.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
}

/* ==============================================================================
   TABLES & DATAFRAMES
============================================================================== */
[data-testid="stDataFrame"] {
    background: var(--card-bg);
    border-radius: 16px;
    border: 1px solid var(--border-color);
}

/* ==============================================================================
   ALERTS
============================================================================== */
.success-banner {
    background: rgba(0, 208, 132, 0.08);
    border-left: 4px solid var(--success);
    padding: 1rem;
    border-radius: 8px;
    color: var(--success);
    margin: 1rem 0;
}

/* ==============================================================================
   PROGRESS BARS
============================================================================== */
.stProgress > div > div > div > div {
    background: var(--primary-gradient) !important;
}

/* ==============================================================================
   ANIMATIONS
============================================================================== */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeInUp 0.5s ease-out forwards;
}

/* Profiles at bottom of sidebar */
.sidebar-profile {
    position: fixed;
    bottom: 20px;
    left: 20px;
    width: 220px;
    padding: 12px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}
</style>
"""

def inject_custom_css():
    """Inject premium CSS into Streamlit."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def metric_card(value: str, label: str, icon: str = "⚡", trend: str = None, trend_up: bool = True) -> str:
    """
    Génère le HTML pour une carte KPI.
    trend_up=True -> vert (positif)
    trend_up=False -> rouge (négatif)
    """
    trend_html = ""
    if trend:
        trend_class = "trend-up" if trend_up else "trend-down"
        arrow = "✓" if trend_up else "⚠"
        trend_html = f'<div class="kpi-trend {trend_class}"><span>{arrow}</span> {trend}</div>'
        
    return f"""
    <div class="kpi-card fade-in">
        <div class="kpi-icon"><span style="font-size: 1.2rem;">{icon}</span></div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {trend_html}
    </div>
    """

def page_header(title: str, subtitle: str = "") -> str:
    """Generate a clean page header with breadcrumb feel."""
    return f"""
    <div style="margin-bottom: 2.5rem;" class="fade-in">
        <div style="font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">
            University Portal / {title}
        </div>
        <h1 style="font-size: 2.5rem; font-weight: 800; color: white; margin: 0; letter-spacing: -0.02em;">
            {title}
        </h1>
        <p style="color: var(--text-secondary); margin-top: 0.5rem; font-size: 1.1rem;">
            {subtitle}
        </p>
    </div>
    """

def conflict_indicator(dept: str, value: int, max_val: int = 20) -> str:
    """CSS progress-bar like conflict indicator."""
    pct = min(100, (value / max_val) * 100) if max_val > 0 else 0
    color = "var(--error)" if value > 5 else "var(--warning)" if value > 2 else "var(--success)"
    
    return f"""
    <div style="margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 0.9rem; font-weight: 500;">{dept}</span>
            <span style="font-size: 0.85rem; color: var(--text-secondary);">{value} Conflicts</span>
        </div>
        <div style="height: 8px; width: 100%; background: rgba(255,255,255,0.05); border-radius: 10px;">
            <div style="height: 100%; width: {pct}%; background: {color}; border-radius: 10px; transition: width 0.5s ease;"></div>
        </div>
    </div>
    """
