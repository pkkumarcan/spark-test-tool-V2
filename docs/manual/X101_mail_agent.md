# X101 — Mail Agent

**Purpose:** Email organization agent — read, search, summarize, and manage emails.  
**Created:** 2026-07-09 (V3 — V2 agent integration docs)  
**Estimated time:** 10 minutes

---

## Overview

The mail agent connects to email accounts via IMAP and provides AI-powered email management: search, summarize, draft replies, and organize.

---

## Features

| Feature | Description |
|---------|-------------|
| **Email search** | Search emails by sender, subject, date, content |
| **Summarize** | AI-powered email summarization |
| **Draft reply** | Generate draft replies using LLM |
| **Organize** | Move emails to folders, mark as read |
| **Stats** | Email volume, response time, top contacts |

---

## Architecture

```
User Request → Mail Agent → IMAP Server → Email Data → LLM Processing → Response
```

### Components

| Component | Purpose |
|-----------|---------|
| IMAP Client | Connect to email server |
| LLM Client | Process and generate text |
| Search Index | Fast email search |
| Response Generator | Format results |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/mail/emails` | GET | List emails |
| `/api/mail/stats` | GET | Email statistics |
| `/api/mail/sync/start` | POST | Start email sync |

---

## Email Operations

### List Emails
```bash
GET /api/mail/emails
```

Returns:
```json
{
  "emails": [
    {
      "id": "msg-123",
      "subject": "Q3 Report Ready",
      "from": "boss@company.com",
      "date": "2026-07-09T14:30:00Z",
      "snippet": "The Q3 report is ready for review..."
    }
  ]
}
```

### Search Emails
```bash
POST /api/mail/search
{
  "query": "from:boss subject:report",
  "limit": 10
}
```

### Summarize
```bash
POST /api/mail/summarize
{
  "email_id": "msg-123"
}
```

Returns:
```json
{
  "summary": "Boss reports Q3 numbers are ready. Revenue up 15%. Needs review by Friday.",
  "action_items": ["Review Q3 report", "Respond by Friday"],
  "priority": "high"
}
```

### Draft Reply
```bash
POST /api/mail/draft
{
  "email_id": "msg-123",
  "tone": "professional"
}
```

---

## Mail Agent Prompt

```
You are Spark Mail Agent, an AI email assistant.
Your capabilities:
- Search emails by sender, subject, date, content
- Summarize email threads
- Draft professional replies
- Organize emails into folders
- Generate email statistics

When the user asks about emails, use the available tools to fetch and process them.
Keep responses concise and actionable.
```

---

## Configuration

### Environment Variables

```bash
# IMAP settings
MAIL_IMAP_HOST=imap.gmail.com
MAIL_IMAP_PORT=993
MAIL_IMAP_USER=your-email@gmail.com
MAIL_IMAP_PASSWORD=your-app-password

# LLM
SPARK_OLLAMA_BASE_URL=http://localhost:11434
SPARK_DEFAULT_MODEL=qwen3:8b
```

### Gmail Setup

1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password (not regular password) in `.env`

---

## Usage Examples

### Via Dashboard
1. Navigate to Mail page
2. Ask: "Summarize my unread emails"
3. Agent fetches and summarizes

### Via API
```bash
curl http://localhost:8080/api/mail/emails
```

---

## Limitations

- **Read-only by default** — draft replies require user confirmation
- **IMAP only** — no Exchange/ActiveSync support
- **Single account** — multi-account support planned
- **No real-time sync** — manual sync trigger required
