import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from auth.firebase_config import get_db
from datetime import datetime

from google.cloud.firestore_v1.base_query import FieldFilter

# ─────────────────────────────────────────
# SHEET HEADERS
# Must match exact order of row building below
# ─────────────────────────────────────────
HEADERS = [
    "Date",
    "Branch",
    "Area",
    "Samira Team",
    "Customer",
    "Industry",
    "Customer Team",
    "Oldest Bill Date",
    "Period (Days)",
    "Total Outstanding",
    "Our Products offered / discussed",
    "Competitor products / prices",
    "Company Updates",
    "Market / End Market Updates",
    "Other Remarks",
    "Follow up",
    "Follow up Date",
    "Feedback of Previous Follow Up",
    "Submitted By",
    "Submitted At",
]

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ─────────────────────────────────────────
# SHEET CONNECTION
# ─────────────────────────────────────────
def get_visit_sheet():
    """Connect to the visit entry sheet."""
    try:
        creds_dict = st.secrets["gcp_service_account"]
    except Exception:
        import os, json
        creds_dict = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    sheet_id = st.secrets["spreadsheets"]["visit_entry_data"]
    spreadsheet = client.open_by_key(sheet_id)

    # Use Sheet1 for visit data
    try:
        worksheet = spreadsheet.worksheet("VisitData")
    except Exception:
        # Create sheet if it doesn't exist
        worksheet = spreadsheet.add_worksheet(title="VisitData", rows=10000, cols=25)

    return worksheet


# ─────────────────────────────────────────
# ENSURE HEADERS EXIST
# ─────────────────────────────────────────
def ensure_headers(worksheet):
    """Write headers if row 1 is empty."""
    first_row = worksheet.row_values(1)
    if not first_row or first_row[0] != "Date":
        worksheet.insert_row(HEADERS, index=1)
        print("✅ Headers written to sheet")


# ─────────────────────────────────────────
# BUILD ROW FROM FIRESTORE DOC
# ─────────────────────────────────────────
def build_row(data: dict) -> list:
    """Convert Firestore document dict to sheet row."""
    return [
        data.get("date", ""),
        data.get("branch", ""),
        data.get("area", ""),
        data.get("samira_team", ""),
        data.get("customer", ""),
        data.get("industry", ""),
        data.get("customer_team", ""),
        data.get("oldest_bill_date", ""),
        data.get("period_days", 0),
        data.get("total_outstanding", 0),
        data.get("products_discussed", ""),
        data.get("competitor_info", ""),
        data.get("company_updates", ""),
        data.get("market_updates", ""),
        data.get("other_remarks", ""),
        data.get("follow_up", ""),
        data.get("follow_up_date", ""),
        data.get("feedback_of_previous_follow_up"),
        data.get("submitted_by", ""),
        data.get("submitted_at", ""),
    ]


# ─────────────────────────────────────────
# MAIN SYNC FUNCTION
# ─────────────────────────────────────────
def sync_visits_to_sheet():
    """
    Reads all unsynced visit_entries from Firestore
    and appends them to Google Sheets.
    Marks each doc as synced after writing.
    Returns (synced_count, error_count)
    """
    db = get_db()

    # ── Fetch unsynced entries ──
    unsynced_docs = list(
        db.collection("visit_entries")
          .where(filter=FieldFilter("synced_to_sheet", "==", False))
          .stream()
    )

    if not unsynced_docs:
        return 0, 0

    synced_count = 0
    error_count = 0

    try:
        worksheet = get_visit_sheet()
        ensure_headers(worksheet)

        for doc in unsynced_docs:
            try:
                data = doc.to_dict()
                row = build_row(data)

                # Append to sheet
                worksheet.append_row(row, value_input_option="USER_ENTERED")

                # Mark as synced in Firestore
                db.collection("visit_entries").document(doc.id).update({
                    "synced_to_sheet": True,
                    "synced_at": datetime.now().isoformat()
                })

                synced_count += 1

            except Exception as e:
                print(f"[sync ERROR] doc {doc.id}: {e}")
                error_count += 1
                # Don't mark as synced — will retry next time
                continue

    except Exception as e:
        print(f"[sync SHEET ERROR] {e}")
        return synced_count, error_count + len(unsynced_docs) - synced_count

    return synced_count, error_count


# ─────────────────────────────────────────
# SILENT SYNC — call this on dashboard load
# ─────────────────────────────────────────
def silent_sync():
    """
    Runs sync silently in background.
    Shows no UI unless there's an error.
    """
    try:
        synced, errors = sync_visits_to_sheet()
        if synced > 0:
            print(f"[sync] ✅ {synced} entries synced to sheet")
        if errors > 0:
            print(f"[sync] ⚠️ {errors} entries failed to sync")
    except Exception as e:
        print(f"[sync] Failed: {e}")


# ─────────────────────────────────────────
# ADMIN SYNC — call this from admin panel
# Shows UI feedback
# ─────────────────────────────────────────
def admin_sync():
    """
    Runs sync with visible UI feedback.
    Call from admin panel if admin wants to force sync.
    """
    with st.spinner("Syncing to Google Sheets..."):
        synced, errors = sync_visits_to_sheet()

    if synced == 0 and errors == 0:
        st.info("✅ Everything already synced — no pending entries.")
    elif synced > 0 and errors == 0:
        st.success(f"✅ {synced} entries synced to Google Sheets!")
    elif synced > 0 and errors > 0:
        st.warning(f"⚠️ {synced} entries synced, {errors} failed. Will retry on next sync.")
    else:
        st.error("❌ Sync failed. Check logs.")