import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from auth.firebase_config import get_db
from businesslogic.pdfgenerator import generate_visit_pdf

from google.cloud.firestore_v1.base_query import FieldFilter


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────
BRANCH_OPTIONS = ["Mumbai", "KOTTAYAM", "COIMBATORE", "KOZHIKODE", "THRISSUR"]

DISPLAY_COLS = [
    "Date", "Branch", "Area", "Samira Team", "Customer", "Industry",
    "Customer Team", "Oldest Bill Date", "Period (Days)", "Total Outstanding",
    "Our Products offered / discussed", "Competitor products / prices",
    "Company Updates", "Market / End Market Updates", "Other Remarks",
    "Follow up", "Follow up Date", "Feedback of Previous Follow Up"
]

FIRESTORE_TO_DISPLAY = {
    "date":               "Date",
    "branch":             "Branch",
    "area":               "Area",
    "samira_team":        "Samira Team",
    "customer":           "Customer",
    "industry":           "Industry",
    "customer_team":      "Customer Team",
    "oldest_bill_date":   "Oldest Bill Date",
    "period_days":        "Period (Days)",
    "total_outstanding":  "Total Outstanding",
    "products_discussed": "Our Products offered / discussed",
    "competitor_info":    "Competitor products / prices",
    "company_updates":    "Company Updates",
    "market_updates":     "Market / End Market Updates",
    "other_remarks":      "Other Remarks",
    "follow_up":          "Follow up",
    "follow_up_date":     "Follow up Date",
    "feedback_of_previous_follow_up": "Feedback of Previous Follow Up"
}


# ─────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────
def fetch_report_data(branch: str, start_date: date, end_date: date) -> pd.DataFrame:
    """Fetch visit entries from Firestore filtered by branch and date range."""
    db = get_db()

    start_str = str(start_date)
    end_str   = str(end_date)

    docs = (
        db.collection("visit_entries")
          .where(filter=FieldFilter("branch", "==", branch))
          .where(filter=FieldFilter("date", ">=", start_str))
          .where(filter=FieldFilter("date", "<=", end_str))
          .order_by("date", direction="DESCENDING")
          .stream()
    )

    records = [doc.to_dict() for doc in docs]

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Rename to display columns
    df = df.rename(columns=FIRESTORE_TO_DISPLAY)

    # Keep only display columns that exist
    cols = [c for c in DISPLAY_COLS if c in df.columns]
    df = df[cols]

    # Format date column
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

    return df


# ─────────────────────────────────────────
# EXCEL GENERATOR
# ─────────────────────────────────────────
def to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Visit History")

        workbook  = writer.book
        worksheet = writer.sheets["Visit History"]

        uniform_format = workbook.add_format({
            "text_wrap": True,
            "valign":    "top",
            "border":    1
        })

        num_cols = len(df.columns)
        worksheet.set_column(0, num_cols - 1, 20, uniform_format)

    return output.getvalue()


# ─────────────────────────────────────────
# HTML PREVIEW BUILDER
# ─────────────────────────────────────────
def build_html_preview(df: pd.DataFrame, branch: str, start_date: date, end_date: date, submitted_by: str) -> str:
    start_fmt = start_date.strftime("%d %b %Y")
    end_fmt   = end_date.strftime("%d %b %Y")


    return f"""
    <div style="font-family: Georgia, serif; max-width: 900px; margin: 0 auto;
                background: #FFFFFF; border: 1px solid #D9D0BE; border-radius: 8px;
                overflow: hidden;">

        <!-- Header -->
        <div style="background: #1B2A4A; padding: 24px 32px;">
            <div style="font-size: 11px; letter-spacing: 3px; color: #C9A84C;
                        text-transform: uppercase; margin-bottom: 6px;">
                Visit Report
            </div>
            <div style="font-size: 22px; color: #FFFFFF; font-weight: 700; margin-bottom: 4px;">
                {branch} Branch
            </div>
            <div style="font-size: 13px; color: #8A9BBB;">
                {start_fmt} — {end_fmt}
            </div>
        </div>

        <!-- Meta -->
        <div style="background: #F5F1EA; padding: 12px 32px; border-bottom: 1px solid #E8E0D0;
                    font-size: 12px; color: #5A6A85; display: flex; gap: 32px;">
            <span>📊 <b>{len(df)}</b> visits</span>
            <span>👤 Submitted by <b>{submitted_by}</b></span>
            <span>🕐 Generated on <b>{datetime.now().strftime("%d %b %Y, %H:%M")}</b></span>
        </div>

        <!-- Summary Stats -->
        <div style="padding: 24px 32px; display: flex; gap: 16px; flex-wrap: wrap;">
            <div style="flex:1; min-width:120px; background:#F5F1EA; border:1px solid #E8E0D0;
                        border-radius:8px; padding:16px; text-align:center;">
                <div style="font-size:28px; font-weight:700; color:#1B2A4A;">{len(df)}</div>
                <div style="font-size:11px; color:#5A6A85; text-transform:uppercase; letter-spacing:1px;">Total Visits</div>
            </div>
            <div style="flex:1; min-width:120px; background:#F5F1EA; border:1px solid #E8E0D0;
                        border-radius:8px; padding:16px; text-align:center;">
                <div style="font-size:28px; font-weight:700; color:#1B2A4A;">{df["Customer"].nunique() if "Customer" in df.columns else "—"}</div>
                <div style="font-size:11px; color:#5A6A85; text-transform:uppercase; letter-spacing:1px;">Unique Customers</div>
            </div>
            <div style="flex:1; min-width:120px; background:#F5F1EA; border:1px solid #E8E0D0;
                        border-radius:8px; padding:16px; text-align:center;">
                <div style="font-size:28px; font-weight:700; color:#1B2A4A;">{df["Area"].nunique() if "Area" in df.columns else "—"}</div>
                <div style="font-size:11px; color:#5A6A85; text-transform:uppercase; letter-spacing:1px;">Areas Covered</div>
            </div>
        </div>

        <!-- Attachment note -->
        <div style="padding: 0 32px 24px 32px;">
            <div style="background: #EEF6EE; border: 1px solid #A5D6A7; border-radius: 8px;
                        padding: 12px 16px; font-size: 12px; color: #2E7D32;">
                📎 <b>2 attachments included:</b> Visit_Report.xlsx and Visit_Report.pdf
            </div>
        </div>

        <!-- Footer -->
        <div style="padding: 16px 32px; background: #F5F1EA; border-top: 1px solid #E8E0D0;
                    font-size: 11px; color: #5A6A85; text-align: center;">
            This report was generated and submitted by {submitted_by} via the Jeekay Dashboard.
        </div>
    </div>
    """



# ─────────────────────────────────────────
# EMAIL SENDER
# ─────────────────────────────────────────
def send_report_email(
    df: pd.DataFrame,
    branch: str,
    start_date: date,
    end_date: date,
    submitted_by: str,
    excel_bytes: bytes,
    pdf_bytes: bytes,
):
    sender      = st.secrets["gmail"]["sender_email"]
    password    = st.secrets["gmail"]["app_password"]
    recipients  = st.secrets["report_emails"]["recipients"]
    reply_to    = submitted_by  # logged in user's email

    start_fmt = start_date.strftime("%d %b %Y")
    end_fmt   = end_date.strftime("%d %b %Y")
    subject   = f"Visit Report — {branch} Branch — {start_fmt} to {end_fmt}"

    # ── Build email ──
    msg = MIMEMultipart("mixed")
    msg["Subject"]  = subject
    msg["From"]     = f"Jeekay Dashboard <{sender}>"
    msg["To"]       = ", ".join(recipients)
    msg["Reply-To"] = reply_to

    # ── HTML body ──
    html_body = build_html_preview(df, branch, start_date, end_date, submitted_by)
    msg.attach(MIMEText(html_body, "html"))

    # ── Excel attachment ──
    filename_base = f"Visit_Report_{branch}_{start_date}_{end_date}".replace("/", "-").replace(" ", "_")

    excel_part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    excel_part.set_payload(excel_bytes)
    encoders.encode_base64(excel_part)
    excel_part.add_header("Content-Disposition", "attachment", filename=f"{filename_base}.xlsx")
    msg.attach(excel_part)

    # ── PDF attachment ──
    pdf_part = MIMEBase("application", "pdf")
    pdf_part.set_payload(pdf_bytes)
    encoders.encode_base64(pdf_part)
    pdf_part.add_header("Content-Disposition", "attachment", filename=f"{filename_base}.pdf")
    msg.attach(pdf_part)

    # ── Send ──
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())


# ─────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────
def show_weekly_report():

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Outfit:wght@300;400;500;600&display=swap');

    :root {
        --navy:      #1B2A4A;
        --gold:      #C9A84C;
        --gold-lt:   #E8C96A;
        --cream:     #FAF7F2;
        --warm-gray: #F0EBE1;
        --border:    #DDD5C5;
        --muted:     #6B7A99;
    }

    /* ── Page background ── */
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main {
        background-color: var(--cream) !important;
    }
    [data-testid="stHeader"] {
        background-color: var(--cream) !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: var(--navy) !important;
    }
    [data-testid="stSidebar"] button {
        color: #FFFFFF !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        background-color: transparent !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(201, 168, 76, 0.15) !important;
        border-color: var(--gold) !important;
        color: #FFFFFF !important;
    }

    /* ── Header ── */
    .wr-header {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: var(--navy);
        margin-bottom: 0.1rem;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    .wr-sub {
        font-family: 'Outfit', sans-serif;
        font-size: 1rem;
        font-weight: 400;
        color: var(--muted);
        margin-bottom: 1.8rem;
        line-height: 1.5;
    }

    /* ── Section Label ── */
    .wr-section {
        font-family: 'Outfit', sans-serif;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--gold);
        border-bottom: 2px solid var(--border);
        padding-bottom: 8px;
        margin: 2rem 0 1rem 0;
        position: relative;
    }
    .wr-section::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 40px;
        height: 2px;
        background: var(--gold);
    }

    /* ── Widget labels ── */
    [data-testid="stWidgetLabel"] p,
    label {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        color: var(--navy) !important;
    }

    /* ── Inputs ── */
    input, textarea, select,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1rem !important;
        color: var(--navy) !important;
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
        background: #FFFFFF !important;
    }
    input:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 3px rgba(201, 168, 76, 0.12) !important;
    }

    /* ── Selectbox ── */
    [data-testid="stSelectbox"] > div > div {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
        background: #FFFFFF !important;
        min-height: 46px !important;
    }
    [data-testid="stSelectbox"] input {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* ── Date input ── */
    [data-testid="stDateInput"] input {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
    }

    /* ── Stat boxes ── */
    .stat-box {
        background: #FFFFFF;
        border: 1.5px solid var(--border);
        border-radius: 12px;
        padding: 1.4rem 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(27, 42, 74, 0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stat-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(27, 42, 74, 0.1);
    }
    .stat-val {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2.4rem;
        font-weight: 700;
        color: var(--navy);
        line-height: 1;
        margin-bottom: 6px;
    }
    .stat-key {
        font-family: 'Outfit', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* ── Preview frame ── */
    .preview-frame {
        border: 1.5px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
        margin-top: 1rem;
        box-shadow: 0 4px 16px rgba(27, 42, 74, 0.08);
    }

    /* ── Buttons ── */
    [data-testid="stButton"] button {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        letter-spacing: 0.02em !important;
    }

    /* ── Download buttons ── */
    [data-testid="stDownloadButton"] button {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
    }

    /* ── Caption ── */
    [data-testid="stCaptionContainer"] p {
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.88rem !important;
        color: var(--muted) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="wr-header">📬 Mail Weekly Report</div>', unsafe_allow_html=True)
    st.markdown('<div class="wr-sub">Select Branch and date range to generate and send the Visit Report.</div>', unsafe_allow_html=True)

    if st.button("← Back to Dashboard", key="back_from_wr"):
        st.session_state["page"] = "dashboard"
        st.session_state.pop("wr_df", None)
        st.rerun()

    st.divider()

    # ══════════════════════════════════════
    # FILTERS
    # ══════════════════════════════════════
    st.markdown('<div class="wr-section">📍 Select Branch & Date Range</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        branch = st.selectbox("Branch *", ["— Select —"] + BRANCH_OPTIONS, key="wr_branch")
    with col2:
        start_date = st.date_input(
            "From *",
            value=date.today() - timedelta(days=7),
            key="wr_start"
        )
    with col3:
        end_date = st.date_input(
            "To *",
            value=date.today(),
            key="wr_end"
        )

    # Validate date range
    if start_date and end_date and start_date > end_date:
        st.error("⚠️ Start date cannot be after end date.")
        return

    # ── Generate Report Button ──

    if st.button("🔍 Generate Report", type="primary", use_container_width=True, key="wr_generate"):
        if not branch or branch == "— Select —":
            st.error("⚠️ Please select a branch.")
        else:
            with st.spinner("Fetching visit data..."):
                df = fetch_report_data(branch, start_date, end_date)
            if df.empty:
                st.warning(f"⚠️ No visit entries found.")
                # ← Clear any previous report
                st.session_state.pop("wr_df", None)
                st.session_state.pop("wr_branch_val", None)
            else:
                # ← Tag report with current user's uid
                st.session_state["wr_df"]         = df
                st.session_state["wr_branch_val"] = branch
                st.session_state["wr_start_val"]  = start_date
                st.session_state["wr_end_val"]    = end_date
                st.session_state["wr_owner"]      = st.session_state["uid"]  # ← tag owner
    
    # ── Only show report if it belongs to current user ──
    df = st.session_state.get("wr_df")
    report_owner = st.session_state.get("wr_owner")
    current_uid  = st.session_state.get("uid")

    if df is not None:
        branch_changed = st.session_state.get("wr_branch_val") != branch
        start_changed  = st.session_state.get("wr_start_val")  != start_date
        end_changed    = st.session_state.get("wr_end_val")    != end_date
        wrong_user     = report_owner != current_uid

        if branch_changed or start_changed or end_changed or wrong_user:
            st.session_state.pop("wr_df", None)
            st.session_state.pop("wr_owner", None)
            df = None

    # ══════════════════════════════════════
    # REPORT READY — show options
    # ══════════════════════════════════════
    df = st.session_state.get("wr_df")

    if df is not None and not df.empty:
        branch     = st.session_state.get("wr_branch_val", branch)
        start_date = st.session_state.get("wr_start_val", start_date)
        end_date   = st.session_state.get("wr_end_val", end_date)
        submitted_by = st.session_state["email"]

        st.divider()

        # ── Stats ──
        st.markdown('<div class="wr-section">📊 Report Summary</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="stat-box"><div class="stat-val">{len(df)}</div><div class="stat-key">Total Visits</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-box"><div class="stat-val">{df["Customer"].nunique() if "Customer" in df.columns else "—"}</div><div class="stat-key">Unique Customers</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-box"><div class="stat-val">{df["Area"].nunique() if "Area" in df.columns else "—"}</div><div class="stat-key">Areas Covered</div></div>', unsafe_allow_html=True)
        #with c4:
            #follow_yes = len(df[df["Follow up"] == "Yes"]) if "Follow up" in df.columns else 0
            #st.markdown(f'<div class="stat-box"><div class="stat-val">{follow_yes}</div><div class="stat-key">Follow-ups Pending</div></div>', unsafe_allow_html=True)

        # ── Generate files ──
        excel_bytes = to_excel(df)
        pdf_bytes   = generate_visit_pdf(df, "All", "All", branch).getvalue()

        st.divider()

        # ── Action buttons ──
        st.markdown('<div class="wr-section">⚡ Actions</div>', unsafe_allow_html=True)

        col_dl, col_mail = st.columns(2)

        with col_dl:
            filename_base = f"Visit_Report_{branch}_{start_date}_{end_date}".replace("/", "-").replace(" ", "_")

            st.download_button(
                label="📥 Download Excel",
                data=excel_bytes,
                file_name=f"{filename_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="wr_dl_excel"
            )
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name=f"{filename_base}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="wr_dl_pdf"
            )

        with col_mail:
            if st.button("📧 Send Email to Management", use_container_width=True, type="primary", key="wr_send"):
                try:
                    with st.spinner("Sending email..."):
                        send_report_email(
                            df           = df,
                            branch       = branch,
                            start_date   = start_date,
                            end_date     = end_date,
                            submitted_by = submitted_by,
                            excel_bytes  = excel_bytes,
                            pdf_bytes    = pdf_bytes,
                        )
                    st.success(f"✅ Report emailed successfully! Recipients will see it's from {submitted_by}.")
                except Exception as e:
                    st.error(f"❌ Failed to send email: {e}")

        # ══════════════════════════════════════
        # EMAIL PREVIEW
        # ══════════════════════════════════════
        st.divider()
        st.markdown('<div class="wr-section">👁️ Email Preview</div>', unsafe_allow_html=True)
        st.caption("This is exactly what the email will look like when received.")

        html_preview = build_html_preview(df, branch, start_date, end_date, submitted_by)

        with st.container():
            st.iframe(
                html_preview,
                height=600
            )