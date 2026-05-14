import streamlit as st
from datetime import datetime, date
from auth.firebase_config import get_db
from ReverseExcel.manage_customers import (
    load_customers,
    get_branches,
    get_areas,
    get_customer_names,
    get_industry,
)
from ReverseExcel.validate_entry import validate_entry_form


# ─────────────────────────────────────────
# FIRESTORE WRITE
# ─────────────────────────────────────────
def submit_visit_to_firestore(data: dict):
    db = get_db()
    db.collection("visit_entries").add({
        **data,
        "synced_to_sheet": False,
        "created_at": datetime.now().isoformat(),
    })


# ─────────────────────────────────────────
# MAIN FORM
# ─────────────────────────────────────────
def show_entry_form():

    # ── Styling ──
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Outfit:wght@300;400;500;600&display=swap');

    /* ── Root Variables ── */
    :root {
        --navy:      #1B2A4A;
        --gold:      #C9A84C;
        --gold-lt:   #E8C96A;
        --cream:     #FAF7F2;
        --warm-gray: #F0EBE1;
        --border:    #DDD5C5;
        --text:      #1B2A4A;
        --muted:     #6B7A99;
        --green:     #2E7D32;
        --green-lt:  #EEF6EE;
        --green-bd:  #A5D6A7;
    }
    
    /* ── Page background ── */
    [data-testid="stAppViewContainer"] {
        background-color: #FAF7F2 !important;
    }

    [data-testid="stAppViewContainer"] > .main {
        background-color: #FAF7F2 !important;
    }

    [data-testid="stHeader"] {
        background-color: #FAF7F2 !important;
    }

    /* ── Sidebar keeps its dark navy ── */
    [data-testid="stSidebar"] {
        background-color: #1B2A4A !important;
    }
                
    /* ── Sidebar button hover ── */
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(201, 168, 76, 0.15) !important;
        border-color: var(--gold) !important;
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] button {
        color: #FFFFFF !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        background-color: transparent !important;
    }

    /* ── Active/current page button ── */
    [data-testid="stSidebar"] button:active {
        background-color: rgba(201, 168, 76, 0.25) !important;
    }

    /* ── Form Header ── */
    .form-header {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: var(--navy);
        margin-bottom: 0.1rem;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    .form-subheader {
        font-family: 'Outfit', sans-serif;
        font-size: 1rem;
        font-weight: 400;
        color: var(--muted);
        margin-bottom: 1.8rem;
        line-height: 1.5;
    }

    /* ── Section Label ── */
    .section-label {
        font-family: 'Outfit', sans-serif;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--gold);
        margin-top: 2rem;
        margin-bottom: 0.8rem;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--border);
        position: relative;
    }
    .section-label::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 40px;
        height: 2px;
        background: var(--gold);
    }

    /* ── Streamlit widget labels ── */
    [data-testid="stWidgetLabel"] p,
    label,
    .stSelectbox label,
    .stTextInput label,
    .stNumberInput label,
    .stDateInput label,
    .stTextArea label {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        color: var(--navy) !important;
        letter-spacing: 0.01em !important;
    }

    /* ── Input fields ── */
    input, textarea, select,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1rem !important;
        color: var(--navy) !important;
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
        background: #FFFFFF !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s ease !important;
    }
    input:focus, textarea:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 3px rgba(201, 168, 76, 0.12) !important;
    }

    /* ── Select box ── */
    /* ── Fix selectbox internal search input ── */
    [data-testid="stSelectbox"] input {
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        background: transparent !important;
    }

    [data-testid="stSelectbox"] > div > div {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
        background: #FFFFFF !important;
        min-height: 46px !important;
    }

    /* ── Fix disabled selectbox ── */
    [data-testid="stSelectbox"][aria-disabled="true"] > div > div {
        background: var(--warm-gray) !important;
        color: var(--muted) !important;
        opacity: 0.7 !important;
    }

    /* ── Metric (Period Days) ── */
    [data-testid="stMetric"] {
        background: var(--warm-gray);
        border: 1.5px solid var(--border);
        border-radius: 10px;
        padding: 12px 16px;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Cormorant Garamond', serif !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: var(--navy) !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.8rem !important;
        color: var(--muted) !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }

    /* ── Review Card ── */
    .review-card {
        background: var(--cream);
        border: 1.5px solid var(--border);
        border-left: 5px solid var(--gold);
        border-radius: 12px;
        padding: 1.6rem 2rem;
        margin: 1.2rem 0;
        box-shadow: 0 2px 12px rgba(27, 42, 74, 0.06);
    }
    .review-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 8px 0;
        border-bottom: 1px solid var(--border);
        gap: 16px;
    }
    .review-row:last-child { border-bottom: none; }
    .review-key {
        font-family: 'Outfit', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--muted);
        min-width: 160px;
    }
    .review-val {
        font-family: 'Outfit', sans-serif;
        font-size: 0.92rem;
        font-weight: 600;
        color: var(--navy);
        text-align: right;
        max-width: 60%;
        word-break: break-word;
    }

    /* ── Success Box ── */
    .success-box {
        background: linear-gradient(135deg, #E8F5E9 0%, #F1F8E9 100%);
        border: 1.5px solid var(--green-bd);
        border-radius: 12px;
        padding: 2rem 2rem;
        text-align: center;
        color: var(--green);
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 1.15rem;
        box-shadow: 0 4px 16px rgba(46, 125, 50, 0.1);
    }

    /* ── Auto-fill Badge ── */
    .auto-fill-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: var(--green-lt);
        border: 1px solid var(--green-bd);
        border-radius: 20px;
        padding: 3px 12px;
        font-family: 'Outfit', sans-serif;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--green);
        margin-top: 6px;
        margin-left: 2px;
    }

    /* ── Divider styling ── */
    hr {
        border-color: var(--border) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Button overrides ── */
    [data-testid="stButton"] button {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        letter-spacing: 0.02em !important;
    }
    </style>
    """, unsafe_allow_html=True)    

    # ── Header ──
    st.markdown('<div class="form-header">➕ Add Visit Entry</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="form-subheader">Logged in as <b>{st.session_state["email"]}</b> · '
        f'Entry will be saved with your name and timestamp.</div>',
        unsafe_allow_html=True
    )

    if st.button("← Back to Dashboard", key="back_to_dash"):
        st.session_state["page"] = "dashboard"
        st.session_state.pop("entry_review", None)
        st.session_state.pop("entry_data", None)
        st.rerun()

    st.divider()

    # ── Success screen ──
    if st.session_state.get("entry_success"):
        st.markdown('<div class="success-box">✅ Visit entry submitted successfully!</div>', unsafe_allow_html=True)
        st.balloons()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add Another Entry", use_container_width=True):
                st.session_state.pop("entry_success", None)
                st.rerun()
        with col2:
            if st.button("📊 Go to Dashboard", use_container_width=True):
                st.session_state["page"] = "dashboard"
                st.session_state.pop("entry_success", None)
                st.rerun()
        return

    # ── Review screen ──
    if st.session_state.get("entry_review"):
        _show_review()
        return

    # ── Load customers for drill-down ──
    with st.spinner("Loading customer list..."):
        customers = load_customers()

    if not customers:
        st.warning("⚠️ No customers found. Ask admin to add customers first.")
        return

    # ══════════════════════════════════════
    # SECTION 1 — Visit Info
    # ══════════════════════════════════════
    st.markdown('<div class="section-label">📍 Visit Info</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        visit_date = st.date_input("Date *", value=date.today(), key="ef_date")

    # ── Drill-down: Branch → Area → Customer → Industry ──
    branches = get_branches(customers)

    with col2:
        branch = st.selectbox(
            "Branch *",
            ["— Select —"] + branches,
            key="ef_branch"
        )

    col3, col4 = st.columns(2)

    if branch and branch != "— Select —":
        areas = get_areas(customers, branch)
        with col3:
            area = st.selectbox(
                "Area *",
                ["— Select —"] + areas,
                key="ef_area"
            )
    else:
        with col3:
            st.selectbox("Area *", ["— Select Branch first —"], disabled=True, key="ef_area_disabled")
        area = ""

    col5, col6 = st.columns(2)

    if area and area != "— Select —":
        customer_names = get_customer_names(customers, branch, area)
        with col5:
            customer = st.selectbox(
                "Customer *",
                ["— Select —"] + customer_names,
                key="ef_customer"
            )
    else:
        with col5:
            st.selectbox("Customer *", ["— Select Area first —"], disabled=True, key="ef_customer_disabled")
        customer = ""

    # ── Auto-fill Industry ──
    if customer and customer != "— Select —":
        industry = get_industry(customers, customer)
        with col6:
            st.text_input(
                "Industry",
                value=industry,
                disabled=True,
                key="ef_industry",
                help="Auto-filled based on customer selection"
            )
        st.markdown(
            '<span class="auto-fill-badge">✓ Auto-filled from customer master</span>',
            unsafe_allow_html=True
        )
    else:
        with col6:
            st.text_input("Industry", value="", disabled=True, key="ef_industry_empty")
        industry = ""

    with col4:
        samira_team = st.text_input(
            "Samira Team *",
            placeholder="e.g. Mr. Rajan",
            key="ef_samira_team"
        )

    customer_team = st.text_input(
        "Customer Team",
        placeholder="e.g. Mr. Raj (Purchase), Ms. Priya (MD)",
        key="ef_customer_team"
    )

    # ══════════════════════════════════════
    # SECTION 2 — Financial Info
    # ══════════════════════════════════════
    st.markdown('<div class="section-label">💰 Financial Info</div>', unsafe_allow_html=True)

    col7, col8, col9 = st.columns(3)
    with col7:
        oldest_bill_date = st.date_input(
            "Oldest Bill Date",
            value=None,
            key="ef_oldest_bill"
        )
    with col8:
        if oldest_bill_date:
            period_days = (date.today() - oldest_bill_date).days
            st.metric("Period (Days)", f"{period_days} days")
        else:
            period_days = 0
            st.metric("Period (Days)", "—")

    with col9:
        total_outstanding = st.number_input(
            "Total Outstanding (₹)",
            min_value=0,
            value=0,
            step=1000,
            key="ef_outstanding"
        )

    # ══════════════════════════════════════
    # SECTION 3 — Discussion Notes
    # ══════════════════════════════════════
    st.markdown('<div class="section-label">🗒️ Discussion Notes</div>', unsafe_allow_html=True)

    products_discussed = st.text_area(
        "Our Products Offered / Discussed",
        placeholder="List products discussed during visit...",
        height=80,
        key="ef_products"
    )
    competitor_info = st.text_area(
        "Competitor Products / Prices",
        placeholder="Any competitor info gathered...",
        height=80,
        key="ef_competitor"
    )
    company_updates = st.text_area(
        "Company Updates",
        placeholder="Updates from customer's side...",
        height=80,
        key="ef_company"
    )
    market_updates = st.text_area(
        "Market / End Market Updates",
        placeholder="Market trends or end-market news...",
        height=80,
        key="ef_market"
    )
    other_remarks = st.text_area(
        "Other Remarks",
        placeholder="Any other notes...",
        height=80,
        key="ef_remarks"
    )

    feedback_of_previous_follow_up = st.text_area(
        "Feedback of Previous Follow Up",
        placeholder="...",
        height=80,
        key="ef_fb_prev_fu"
    )

    # ══════════════════════════════════════
    # SECTION 4 — Follow Up
    # ══════════════════════════════════════
    st.markdown('<div class="section-label">📅 Follow Up</div>', unsafe_allow_html=True)

    col10, col11 = st.columns(2)
    with col10:
        follow_up = st.selectbox(
            "Follow Up Required? *",
            ["", "Yes", "No"],
            key="ef_followup"
        )
    with col11:
        follow_up_date = None
        if follow_up == "Yes":
            follow_up_date = st.date_input(
                "Follow Up Date *",
                value=None,
                key="ef_followup_date"
            )

    st.divider()

    # ══════════════════════════════════════
    # VALIDATION + REVIEW
    # ══════════════════════════════════════
    if st.button("👁️👁️ Review Before Submitting", type="primary", use_container_width=True):
        errors = validate_entry_form(
        visit_date        = visit_date,
        branch            = branch,
        area              = area,
        customer          = customer,
        samira_team       = samira_team,
        customer_team     = customer_team,
        oldest_bill_date  = oldest_bill_date,
        total_outstanding = total_outstanding,
        follow_up         = follow_up,
        follow_up_date    = follow_up_date
        )
        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
        else:
            st.session_state["entry_data"] = {
                "date":               str(visit_date),
                "branch":             branch,
                "area":               area,
                "samira_team":        samira_team.strip(),
                "customer":           customer,
                "industry":           industry,
                "customer_team":      customer_team.strip(),
                "oldest_bill_date":   str(oldest_bill_date) if oldest_bill_date else "",
                "period_days":        period_days,
                "total_outstanding":  total_outstanding,
                "products_discussed": products_discussed.strip(),
                "competitor_info":    competitor_info.strip(),
                "company_updates":    company_updates.strip(),
                "market_updates":     market_updates.strip(),
                "other_remarks":      other_remarks.strip(),
                "feedback_of_previous_follow_up" :feedback_of_previous_follow_up.strip(),
                "follow_up":          follow_up,
                "follow_up_date":     str(follow_up_date) if follow_up_date else "",
                "submitted_by":       st.session_state["email"],
                "submitted_at":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            st.session_state["entry_review"] = True
            st.rerun()


# ─────────────────────────────────────────
# REVIEW + CONFIRM SCREEN
# ─────────────────────────────────────────
def _show_review():
    data = st.session_state.get("entry_data", {})

    st.markdown("### 👁️👁️ Review Your Entry")
    st.markdown("Please confirm all details before submitting.")

    fields = [
        ("Date",                   data.get("date")),
        ("Branch",                 data.get("branch")),
        ("Area",                   data.get("area")),
        ("Samira Team",            data.get("samira_team")),
        ("Customer",               data.get("customer")),
        ("Industry",               data.get("industry") or "—"),
        ("Customer Team",          data.get("customer_team") or "—"),
        ("Oldest Bill Date",       data.get("oldest_bill_date") or "—"),
        ("Period (Days)",          data.get("period_days")),
        ("Total Outstanding (₹)",  f"₹{data.get('total_outstanding', 0):,}"),
        ("Products Discussed",     data.get("products_discussed") or "—"),
        ("Competitor Info",        data.get("competitor_info") or "—"),
        ("Company Updates",        data.get("company_updates") or "—"),
        ("Market Updates",         data.get("market_updates") or "—"),
        ("Other Remarks",          data.get("other_remarks") or "—"),
        ("Feedback of Previous Follow Up", data.get("feedback_of_previous_follow_up") or "—"),
        ("Follow Up",              data.get("follow_up")),
        ("Follow Up Date",         data.get("follow_up_date") or "—"),
        ("Submitted By",           data.get("submitted_by")),
        ("Submitted At",           data.get("submitted_at")),
    ]

    rows_html = "".join([
        f'<div class="review-row">'
        f'<span class="review-key">{k}</span>'
        f'<span class="review-val">{v}</span>'
        f'</div>'
        for k, v in fields
    ])

    st.markdown(
        f'<div class="review-card">{rows_html}</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ Edit Entry", use_container_width=True):
    # ← Convert date strings back to date objects
            def parse_date(val):
                if not val or val == "None":
                    return None
                try:
                    from datetime import date
                    if isinstance(val, date):
                        return val
                    return datetime.strptime(str(val), "%Y-%m-%d").date()
                except:
                    return None
                
            data = st.session_state.get("entry_data", {})
            st.session_state["ef_date"]         = parse_date(data.get("date")) or date.today()
            st.session_state["ef_branch"]       = data.get("branch")
            st.session_state["ef_area"]         = data.get("area")
            st.session_state["ef_customer"]     = data.get("customer")
            st.session_state["ef_samira_team"]  = data.get("samira_team", "")
            st.session_state["ef_customer_team"]= data.get("customer_team", "")
            st.session_state["ef_oldest_bill"]  = parse_date(data.get("oldest_bill_date"))
            st.session_state["ef_period"]       = data.get("period_days", 0)
            st.session_state["ef_outstanding"]  = data.get("total_outstanding", 0)
            st.session_state["ef_products"]     = data.get("products_discussed", "")
            st.session_state["ef_competitor"]   = data.get("competitor_info", "")
            st.session_state["ef_company"]      = data.get("company_updates", "")
            st.session_state["ef_market"]       = data.get("market_updates", "")
            st.session_state["ef_remarks"]      = data.get("other_remarks", "")
            st.session_state["ef_fb_prev_fu"]   = data.get("feedback_of_previous_follow_up", "")            
            st.session_state["ef_followup"]     = data.get("follow_up", "")
            st.session_state["ef_followup_date"]= parse_date(data.get("follow_up_date")) or None
            st.session_state["entry_review"] = False
            st.rerun()

    with col2:
        if st.button("✅ Confirm & Submit", type="primary", use_container_width=True):
            try:
                submit_visit_to_firestore(st.session_state["entry_data"])
                st.session_state["entry_review"] = False
                st.session_state.pop("entry_data", None)
                st.session_state["entry_success"] = True
                st.rerun()
            except Exception as e:
                st.error(f"Failed to submit: {e}")