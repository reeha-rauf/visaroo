# Requirements: Webinars

## Overview
Surface upcoming immigration-related webinars filtered to the user's visa type, with calendar download and creator posting support.

---

## Functional Requirements

### REQ-1: Webinar List
- Display a list of upcoming webinars sorted by date ascending
- Past webinars hidden by default; "Show past webinars" toggle reveals them sorted by date descending
- Each webinar card shows: title, host name, date and time (in user's local timezone), visa type tags, and a registration link
- Empty state when no upcoming webinars match the user's status: "No upcoming webinars for your status. Check back soon."

### REQ-2: Filtering
- Default view: show only webinars tagged with the user's visa type or tagged "All"
- Filter toggle: user can switch to "All webinars" to see everything
- Filter by visa type chip row: F-1, OPT, STEM OPT, H-1B, H-4, J-1, All
- Only one filter active at a time

### REQ-3: Webinar Card
Each card must display:
- Title
- Host name and host type: Official (USCIS/SEVP/government), Verified Creator, Community
- Date and time in user's local timezone with UTC offset shown
- Duration (if provided)
- Visa type tags (multi-select; a webinar can cover multiple types)
- Short description (max 280 characters)
- Registration / watch link (external)
- "Add to calendar" button — downloads .ics for that single webinar

### REQ-4: Calendar Download
- Each webinar card has an "Add to calendar" button
- Clicking downloads a `.ics` file for that single event
- VEVENT includes: SUMMARY (title), DTSTART, DTEND (or DTSTART + duration), DESCRIPTION (description + registration link), URL (registration link)
- A "Download all (.ics)" button at the top of the page downloads all upcoming webinars matching the current filter as a single .ics file

### REQ-5: Creator Webinar Posting
- Verified Creator accounts (Cognito group) can post webinars via the same posting interface as news updates
- Webinar post type requires: title, host, date/time (UTC), duration, visa type tags (at least one), description, registration link
- Posted webinars appear in the list immediately after save
- Admins can delete any webinar; creators can delete only their own

### REQ-6: Admin-Curated Webinars
- An admin interface (or direct DynamoDB seeding for v1) allows pre-loading webinars from newsletter sources
- For the demo: seed at least 5 real upcoming webinars covering OPT, STEM OPT, and H-1B

### REQ-7: Webinar Detail Page (optional for v1)
- `/webinars/:id` — full detail view
- Shows all card fields plus: full description, speaker bio (optional), related resources (optional)
- Roadmap: recording link added after the event

---

## Non-Functional Requirements

### REQ-NF-1: Timezone handling
- All datetimes stored in UTC in DynamoDB
- Displayed in the user's browser local timezone using the Intl API
- UTC offset shown alongside local time so users in different timezones can verify

### REQ-NF-2: No scraping
- Webinars are entered manually by admins or creators
- No automated scraping of newsletter content in v1

### REQ-NF-3: Performance
- Webinar list loads in under 500ms
- .ics generation is synchronous and returns in under 200ms

---

## Out of Scope
- Video hosting or recording storage
- Waitlist or RSVP tracking
- Email reminders for webinars (roadmap)
- Automated newsletter parsing (roadmap)
