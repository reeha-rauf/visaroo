# Design: Webinars

Upcoming immigration webinars, filtered to the user's visa type and shown in their local
timezone. Verified creators and admins can post; everyone can browse and open the
registration link. Built on Visaroo's stack: FastAPI + SQLAlchemy, JWT auth with a `User.role`
check, and Pydantic validation.

Datetimes are stored in UTC and rendered in the browser's local timezone via `Intl`
(REQ-NF-1).

## Architecture

- **SQLAlchemy `Webinar` table** (SQLite in dev, Postgres-ready).
- **FastAPI `routers/webinars.py`** — CRUD for webinars.
- **Auth:** public GETs; POST/DELETE require a JWT and a role check (`creator` or `admin`).

---

## Data Model

The `Webinar` SQLAlchemy model (and its `WebinarOut` API shape):

```
Webinar {
  id: string                     // UUID, primary key
  title: string
  hostName: string
  hostType: 'official' | 'verified_creator' | 'community'
  postedBy?: int                 // FK -> users.id, set for creator-posted webinars
  startDateUtc: string           // ISO 8601 UTC
  durationMinutes?: number
  visaTypeTags: VisaTypeTag[]    // ['OPT', 'STEM_OPT'] or ['ALL']; JSON-encoded
  description: string            // max 280 chars
  registrationUrl: string
  speakerBio?: string
  relatedResources?: string[]    // JSON-encoded
  createdAt: datetime
  updatedAt: datetime
}

type VisaTypeTag = 'F-1' | 'OPT' | 'STEM_OPT' | 'H-1B' | 'H-4' | 'J-1' | 'ALL'
```

`visaTypeTags` and `relatedResources` are stored as JSON-encoded text columns.

### Query patterns
- **List upcoming:** load all, filter `startDateUtc > now` in the router (fine at demo scale).
- **List by visa type:** a webinar matches when its tags include the requested type or `ALL`.
- **Get by id:** `db.get(Webinar, id)`.
- **Delete by id + owner check:** load, verify `postedBy == user.id` (or `admin`), then delete.

At this scale (< 100 webinars) an in-router filter is fine; a dedicated index can be added if
the data grows.

---

## API Routes (FastAPI, `routers/webinars.py`)

```
GET    /webinars              — list; query params: ?visaType=STEM_OPT&includePast=true
GET    /webinars/{id}         — single webinar detail
POST   /webinars              — create (role: creator or admin)
DELETE /webinars/{id}         — delete (creator owns it, or admin)
```

GET routes are public. POST and DELETE require a valid JWT and a `User.role` check of
`creator` or `admin` (a regular user gets 403).

Sorting: upcoming ascending by `startDateUtc`; when `includePast=true`, past webinars are
included and sorted most-recent first.

---

## Frontend

### Page structure

```
/webinars
  <WebinarsPage>
    <FilterChips />              // All | F-1 | OPT | STEM OPT | H-1B | H-4 | J-1
    <WebinarList>
      <WebinarCard />            // one per webinar
    </WebinarList>
    <ShowPastToggle />
  </WebinarsPage>
```

### WebinarCard layout

```
[Host type badge]  [Visa type tags]
Title
Host name · Date & time (local) · Duration
Description (truncated at 2 lines with expand)
[Register →]
```

Host type badge colors:
- Official: blue
- Verified Creator: green
- Community: grey

### Default filter behavior
On page load, apply the user's visa type from their profile as the default filter. If there is
no profile, default to "All".

---

## Seed Data

For the demo, `scripts/seed_webinars.py` seeds a handful of realistic upcoming webinars
covering each host type and visa tag, e.g.:

- "OPT & STEM OPT: What You Need to Know in 2026" — SEVP (official), tags [OPT, STEM_OPT]
- "H-1B Cap Season 2027: Timeline and Preparation" — USCIS (official), tags [H-1B]
- "Navigating OPT Unemployment Rules" — university ISS (community), tags [OPT, STEM_OPT]
- "Travel on OPT: Re-entry Risks and How to Prepare" — verified creator, tags [OPT, STEM_OPT, F-1]
- "Immigration Policy Update: What Changed in Fall 2026" — verified creator, tags [ALL]

Run from the repo root: `python scripts/seed_webinars.py`.
