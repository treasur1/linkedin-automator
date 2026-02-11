# Compliant Outreach Tool Plan (Telegram Bot or Web App)

## Important boundary
Do **not** build a system that scrapes LinkedIn for personal emails or automates actions that violate platform terms.

Instead, build an outreach assistant that uses:
- Public company channels (careers pages, generic contact addresses such as `careers@` or `info@` when publicly listed).
- Job-board APIs and official partner integrations.
- User-imported contacts where you have permission.

---

## Product goal
Help a job seeker organize and run targeted, lawful outreach for roles like receptionist or customer service.

## Core features
1. **Company discovery (lawful sources)**
   - Search by location, industry, company size.
   - Pull openings from official sources/APIs.
2. **Role filtering**
   - Tags: receptionist, front desk, customer service, call center, admin assistant.
   - Keyword + seniority filters.
3. **Contact capture (consent/public only)**
   - Store company-level contacts from public pages.
   - Track source URL and timestamp for auditability.
4. **Outreach tracking**
   - Email template management.
   - Status pipeline: planned → sent → replied → interview.
5. **Telegram bot interface**
   - `/add_company`, `/add_contact`, `/find_jobs`, `/queue_email`, `/status`.
6. **Compliance safeguards**
   - Rate limiting, robots.txt respect for crawling your own approved sources.
   - Block personal-email scraping patterns.
   - Unsubscribe handling and suppression list.

---

## Suggested architecture
- **Frontend**: Next.js (or simple React dashboard)
- **Bot**: Telegram Bot API (webhook mode)
- **Backend**: FastAPI or Node.js (NestJS/Express)
- **DB**: PostgreSQL
- **Queue**: Redis + Celery/BullMQ for scheduled outreach
- **Email**: SendGrid, Mailgun, or SES with domain authentication (SPF/DKIM/DMARC)

### Data model (minimal)
- `companies(id, name, website, industry, location, source)`
- `roles(id, company_id, title, location, url, posted_at)`
- `contacts(id, company_id, email, type, source_url, consent_status)`
- `campaigns(id, name, template_id, created_at)`
- `messages(id, campaign_id, contact_id, status, sent_at, reply_at)`
- `suppression_list(id, email, reason, created_at)`

---

## Telegram bot command examples
- `/find_roles receptionist london`
- `/save_company Acme https://acme.com/careers`
- `/add_contact Acme careers@acme.com source:https://acme.com/contact`
- `/queue_email careers@acme.com template:frontdesk_intro`
- `/pipeline`

---

## Implementation phases
1. **MVP (1–2 weeks)**
   - Company + role + contact CRUD
   - Telegram commands for quick entry
   - Basic dashboard table and filters
2. **Outreach automation (week 3)**
   - Templating, queueing, status updates
   - Bounce and suppression management
3. **Intelligence layer (week 4+)**
   - Match score based on role relevance/location
   - Follow-up reminders

---

## Practical strategy for job applications
- Prioritize applying through official job postings first.
- Use outreach emails as a supplement, not a replacement.
- Keep messages short and role-specific.
- Limit volume and personalize to improve response rates.

## Example outreach template
Subject: Interest in Front Desk / Customer Service Opportunities

Hello Hiring Team,

I’m reaching out to express interest in current or upcoming Front Desk / Customer Service roles at {{company_name}}.
I have experience in {{relevant_experience}} and would value the opportunity to apply.

If helpful, I can share my CV and availability immediately.

Thank you for your time,
{{name}}
{{phone}}
{{email}}

---

## What to avoid
- Scraping private/personal emails from LinkedIn profiles.
- Mass unsolicited emailing without suppression/unsubscribe controls.
- Sending deceptive messages or impersonating recruiters.
