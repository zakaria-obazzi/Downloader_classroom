Downloads **everything** from all your Google Classroom courses automatically.
PDFs, DOCX, PPTX, Google Docs (exported as PDF), Slides, Sheets, assignments, announcements.

---

---

## ⚙️ Setup — Step by Step

### Step 1 — Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **"Select a project"** → **"New Project"**
3. Name it `classroom-downloader` → click **Create**

---

### Step 2 — Enable the APIs

1. In the search bar at the top, search **"Google Classroom API"**
2. Click it → click **"Enable"**
3. Go back, search **"Google Drive API"**
4. Click it → click **"Enable"**

---

### Step 3 — Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** → click **Create**
3. Fill in:
   - App name: `Classroom Downloader`
   - User support email: your Gmail
   - Developer contact: your Gmail
4. Click **Save and Continue** 
5. Under **Test users** → click **+ Add Users**
6. Add your own Gmail address → click **Save**

---

### Step 4 — Create Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth 2.0 Client IDs**
3. Application type: **Desktop App**
4. Name: `classroom-downloader`
5. Click **Create**
6. Click **Download JSON**
7. Rename the file to exactly: **`credentials.json`**
8. Put it in the same folder as `classroom_downloader.py`

---

### Step 5 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 6 — Run

```bash
python classroom_downloader.py
```

- A browser window opens → login with your Google account
- Click **Allow** on all permission screens
- A `token.json` file is created automatically (don't share this!)
- Downloads start — files saved to `classroom_downloads/` folder

---

## 📂 Output Structure

```
classroom_downloads/
├── Course Name 1/
│   ├── Materials/
│   │   ├── Chapter 1/
│   │   │   ├── lecture.pdf
│   │   │   └── slides.pptx
│   ├── Assignments/
│   │   ├── TP1/
│   │   │   └── subject.pdf
│   └── Announcements/
│       └── _all_announcements.txt
├── Course Name 2/
│   └── ...
```

---

## ❓ Common Errors

| Error | Fix |
|-------|-----|
| `403 Classroom API disabled` | Enable it in Google Cloud Console (Step 2) |
| `Access blocked: not verified` | Add your Gmail as Test User (Step 3) |
| `Scope has changed` | Delete `token.json` and run again |
| `credentials.json not found` | Make sure it's in the same folder as the script |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |

---

## 📌 Notes

- Re-run anytime to download new files (already downloaded files are skipped)
- Google Docs → exported as `.pdf`
- Google Sheets → exported as `.xlsx`
- Google Slides → exported as `.pptx`
- YouTube links and external URLs → saved as `.txt` files
