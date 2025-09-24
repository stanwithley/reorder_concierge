import os

from dotenv import load_dotenv

load_dotenv()

# Google Sheets
SHEET_ID = os.getenv("SHEET_ID", "")
GOOGLE_CREDS_PATH = os.getenv("GOOGLE_CREDENTIALS_JSON_PATH", "credentials.json")
TTL_HOURS = int(os.getenv("TTL_HOURS", "24"))
INVENTORY_SHEET_NAME = os.getenv("INVENTORY_SHEET_NAME", "Sheet1")
PO_LOG_SHEET_NAME = os.getenv("PO_LOG_SHEET_NAME", "po_log")

# App + HITL
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "owner@example.com")
HITL_SIGNING_KEY = os.getenv("HITL_SIGNING_KEY", "change-me")

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() == "true"
