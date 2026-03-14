"""
Google Classroom Downloader
============================
Downloads ALL materials from ALL your Google Classroom courses:
- Course materials (PDFs, DOCX, PPTX, images, etc.)
- Assignments + attachments
- Announcements + attachments
- Google Docs/Sheets/Slides → exported as PDF

SETUP (run once):
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests

INSTRUCTIONS:
    1. Go to https://console.cloud.google.com/
    2. Create a new project
    3. Enable these APIs:
       - Google Classroom API
       - Google Drive API
    4. Go to "OAuth consent screen" → External → Add your Gmail
    5. Go to "Credentials" → Create OAuth 2.0 Client ID → Desktop App
    6. Download the JSON → rename it "credentials.json"
    7. Put credentials.json in the same folder as this script
    8. Run: python classroom_downloader.py
"""

import os
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
import re
import json
import requests
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# ── CONFIG ────────────────────────────────────────────────────
DOWNLOAD_DIR = "classroom_downloads"   # folder where everything will be saved
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]
# ──────────────────────────────────────────────────────────────

# Google Docs MIME types → export format
EXPORT_FORMATS = {
    "application/vnd.google-apps.document":     ("application/pdf", ".pdf"),
    "application/vnd.google-apps.spreadsheet":  ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
    "application/vnd.google-apps.presentation": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    "application/vnd.google-apps.drawing":      ("image/png", ".png"),
}

def sanitize(name):
    """Remove illegal filename characters."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def get_credentials():
    """Authenticate and return credentials."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds

def download_drive_file(drive_service, file_id, file_name, mime_type, dest_folder):
    """Download a file from Google Drive (handles Google Docs export too)."""
    dest_folder.mkdir(parents=True, exist_ok=True)

    try:
        if mime_type in EXPORT_FORMATS:
            # Google Doc/Sheet/Slide → export as PDF/XLSX/PPTX
            export_mime, ext = EXPORT_FORMATS[mime_type]
            if not file_name.endswith(ext):
                file_name += ext
            request = drive_service.files().export_media(
                fileId=file_id, mimeType=export_mime
            )
        else:
            request = drive_service.files().get_media(fileId=file_id)

        file_path = dest_folder / sanitize(file_name)
        # Skip if already downloaded
        if file_path.exists():
            print(f"  ⏭  Already exists: {file_name}")
            return

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        with open(file_path, "wb") as f:
            f.write(fh.getvalue())
        print(f"  ✅ Downloaded: {file_name}")

    except Exception as e:
        print(f"  ❌ Failed: {file_name} — {e}")

def download_url_file(url, file_name, dest_folder, headers):
    """Download a file from a direct URL."""
    dest_folder.mkdir(parents=True, exist_ok=True)
    file_path = dest_folder / sanitize(file_name)
    if file_path.exists():
        print(f"  ⏭  Already exists: {file_name}")
        return
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(r.content)
        print(f"  ✅ Downloaded: {file_name}")
    except Exception as e:
        print(f"  ❌ Failed: {file_name} — {e}")

def process_materials(materials, dest_folder, drive_service, creds):
    """Extract and download all attachments from a list of materials."""
    if not materials:
        return

    for mat in materials:
        # Drive file
        if "driveFile" in mat:
            df = mat["driveFile"].get("driveFile", mat["driveFile"])
            fid   = df.get("id")
            fname = df.get("title", fid)
            # Get mime type from Drive
            try:
                meta = drive_service.files().get(
                    fileId=fid, fields="mimeType,name"
                ).execute()
                mime = meta.get("mimeType", "")
                fname = meta.get("name", fname)
            except:
                mime = ""
            download_drive_file(drive_service, fid, fname, mime, dest_folder)

        # YouTube / external link — save as .txt
        elif "youtubeVideo" in mat:
            yt = mat["youtubeVideo"]
            link_file = dest_folder / sanitize(yt.get("title", "youtube") + ".txt")
            dest_folder.mkdir(parents=True, exist_ok=True)
            if not link_file.exists():
                link_file.write_text(f"YouTube: {yt.get('alternateLink', '')}\n")
                print(f"  🔗 Saved link: {link_file.name}")

        elif "link" in mat:
            lk = mat["link"]
            link_file = dest_folder / sanitize(lk.get("title", "link") + ".txt")
            dest_folder.mkdir(parents=True, exist_ok=True)
            if not link_file.exists():
                link_file.write_text(f"URL: {lk.get('url', '')}\n")
                print(f"  🔗 Saved link: {link_file.name}")

        # Form
        elif "form" in mat:
            fm = mat["form"]
            link_file = dest_folder / sanitize(fm.get("title", "form") + ".txt")
            dest_folder.mkdir(parents=True, exist_ok=True)
            if not link_file.exists():
                link_file.write_text(f"Form: {fm.get('formUrl', '')}\n")
                print(f"  🔗 Saved form link: {link_file.name}")

def main():
    print("🔐 Authenticating with Google...")
    creds = get_credentials()

    classroom = build("classroom", "v1", credentials=creds)
    drive     = build("drive",     "v3", credentials=creds)

    print("\n📚 Fetching your courses...")
    courses_result = classroom.courses().list(courseStates=["ACTIVE"]).execute()
    courses = courses_result.get("courses", [])

    if not courses:
        print("No active courses found.")
        return

    print(f"Found {len(courses)} course(s).\n")

    base = Path(DOWNLOAD_DIR)

    for course in courses:
        course_id   = course["id"]
        course_name = sanitize(course.get("name", course_id))
        print(f"\n{'='*60}")
        print(f"📖 Course: {course_name}")
        print(f"{'='*60}")

        course_dir = base / course_name

        # ── 1. COURSE MATERIALS ──────────────────────────────────
        print("\n  📂 Course Materials...")
        try:
            mats = classroom.courses().courseWorkMaterials().list(
                courseId=course_id
            ).execute().get("courseWorkMaterial", [])

            for mat in mats:
                title     = sanitize(mat.get("title", "untitled"))
                mat_dir   = course_dir / "Materials" / title
                print(f"\n    📄 {title}")
                process_materials(
                    mat.get("materials", []), mat_dir, drive, creds
                )
        except Exception as e:
            print(f"  ⚠️  Could not fetch materials: {e}")

        # ── 2. COURSEWORK (Assignments) ──────────────────────────
        print("\n  📝 Assignments...")
        try:
            coursework = classroom.courses().courseWork().list(
                courseId=course_id
            ).execute().get("courseWork", [])

            for cw in coursework:
                title  = sanitize(cw.get("title", "untitled"))
                cw_dir = course_dir / "Assignments" / title
                print(f"\n    📋 {title}")
                process_materials(
                    cw.get("materials", []), cw_dir, drive, creds
                )
        except Exception as e:
            print(f"  ⚠️  Could not fetch assignments: {e}")

        # ── 3. ANNOUNCEMENTS ─────────────────────────────────────
        print("\n  📢 Announcements...")
        try:
            announcements = classroom.courses().announcements().list(
                courseId=course_id
            ).execute().get("announcements", [])

            for ann in announcements:
                ann_id  = ann.get("id", "unknown")
                ann_dir = course_dir / "Announcements"
                process_materials(
                    ann.get("materials", []), ann_dir, drive, creds
                )

            if announcements:
                # Save all announcement texts to a single file
                ann_dir = course_dir / "Announcements"
                ann_dir.mkdir(parents=True, exist_ok=True)
                ann_file = ann_dir / "_all_announcements.txt"
                with open(ann_file, "w", encoding="utf-8") as f:
                    for ann in announcements:
                        f.write(f"[{ann.get('creationTime', '')}]\n")
                        f.write(ann.get("text", "") + "\n")
                        f.write("-" * 40 + "\n")
                print(f"    💬 Saved {len(announcements)} announcements")
        except Exception as e:
            print(f"  ⚠️  Could not fetch announcements: {e}")

    print(f"\n\n✅ ALL DONE! Files saved to: {Path(DOWNLOAD_DIR).absolute()}")

if __name__ == "__main__":
    main()
