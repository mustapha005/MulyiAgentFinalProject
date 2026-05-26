# Switch SmileFlow from mock mode to real Google Calendar + Gmail

## 1. Create Google Cloud credentials

1. Go to Google Cloud Console.
2. Create or select a project.
3. Enable these APIs:
   - Google Calendar API
   - Gmail API
4. Configure OAuth consent screen.
   - For a school project, use **External** and add your own Gmail as a test user.
5. Create OAuth Client ID.
   - Application type: **Desktop app**.
6. Download the JSON file.
7. Rename it to:

```text
backend/credentials/google_credentials.json
```

## 2. Create your `.env`

From the backend folder:

```powershell
cp ../.env.example .env
mkdir credentials
```

Then edit `backend/.env`:

```env
APP_MODE=google
GOOGLE_CREDENTIALS_FILE=./credentials/google_credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=./credentials/token_calendar.json
GOOGLE_GMAIL_TOKEN_FILE=./credentials/token_gmail.json
GOOGLE_CALENDAR_ID=primary
EMAIL_PROVIDER=gmail_api
EMAIL_FROM=your-email@gmail.com
```

## 3. Run the backend

```powershell
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

On the first real Calendar/Gmail action, a browser window opens asking you to approve access.
After approval, SmileFlow creates:

```text
backend/credentials/token_calendar.json
backend/credentials/token_gmail.json
```

Do not commit these token files.

## 4. Test the full real flow

Patient chat example:

```text
My name is Sara Benali. My email is your-second-test-email@gmail.com. I have tooth pain and I am available Tuesday morning.
```

Then approve from the Doctor Dashboard.

Expected result:

1. Calendar free/busy is checked.
2. Doctor approval appears in the dashboard.
3. When approved, a real event is inserted into Google Calendar.
4. A real Gmail confirmation email is sent to the patient.

## Troubleshooting

### Browser does not open
Copy the OAuth URL from the terminal and open it manually.

### Scope changed error
Delete these files and retry:

```powershell
Remove-Item .\credentials\token_calendar.json -ErrorAction SilentlyContinue
Remove-Item .\credentials\token_gmail.json -ErrorAction SilentlyContinue
```

### Credentials file not found
Check that this file exists:

```text
backend/credentials/google_credentials.json
```

### You are not allowed to authenticate
Add your Gmail address as a test user in the OAuth consent screen.
