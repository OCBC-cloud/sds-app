# SDSe — Access Tiers and Modes

**Status:** DESIGN ONLY. NOT COMMITTED TO CODE.
**Last updated:** 2026-09-28.
**Execute:** when the Chief decides.
**Related:** PROJECT_STATE.md, COMMERCIAL_MODEL.md.

This document describes the access modes of the SDSe app, the
access gate, the beta window, and the Owner role. It is a design.
It has not been implemented. The app runs today as it did
yesterday: open access, no gate, no tier filter.

When this design is executed, the app will gain five access
modes and a code-based gate. Until then, nothing changes.

---

## 1. The five access modes

Every user of the SDSe app has exactly one access mode. The
mode determines what the user sees. It does not determine what
the engine does. The engine is universal. Only the presentation
differs.

| Mode | Who | How they get in | Expiry |
|---|---|---|---|
| Owner | The Chief | Owner code or owner URL | Never |
| Beta | Invited testers | Beta code | Time-boxed |
| Studio | Paying team customers | Studio code | While paid |
| Pro | Paying individual customers | Pro code | While paid |
| Free | Anyone | Free code or no code | Never |

The modes are ordered by privilege. Owner sees everything.
Free sees the basics. Beta, Studio, and Pro see progressively
more of the commercial product.

The user is never asked their profession. The user is never
asked their role. A PE who pays nothing is a Free user. A
layman who pays for Studio sees the full product. The mode is
billing and invitation. Nothing else.

---

## 2. What each mode sees

The visibility of an input is one of three states:

  - **Editable** — the user sees the input and can change it.
  - **Read-only** — the user sees the input but cannot change it.
  - **Hidden** — the user does not see the input at all.

The following table is the doctrine. Each input belongs to one
of the six substructure categories (Shape, Membrane, Frame,
Cables, Foundation, Loads). The category is documented in
SUBSTRUCTURES.md. The specific exposure per input will be
listed there.

At a category level:

| Category | Owner | Beta | Studio | Pro | Free |
|---|---|---|---|---|---|
| Shape | Editable | Editable | Editable | Editable | Editable |
| Membrane | Editable | Editable | Editable | Editable | Read-only |
| Frame | Editable | Editable | Editable | Editable | Hidden |
| Cables | Editable | Editable | Editable | Editable | Hidden |
| Foundation | Editable | Editable | Editable | Read-only | Hidden |
| Loads | Editable | Editable | Read-only | Hidden | Hidden |

Notes:

  - The Owner sees and controls everything.
  - Beta testers see the full commercial product, watermarked.
  - Studio is the full commercial product.
  - Pro is the commercial product minus code checks and
    foundation design.
  - Free is a shape sketch with a read-only membrane and no
    structural detail.

The exact exposure for every input is defined in
SUBSTRUCTURES.md.

---

## 3. The access gate

The gate is a new page. It appears before Landing.

The user opens the app. The gate runs first. It asks for a
code. The user types the code. The app checks it against the
access code list.

If the code is valid and the window is open, the app sets the
access mode and moves to Landing.

If the code is invalid, expired, or missing, the app shows
"Access denied" and does not proceed.

The gate runs on every page load, not just on first visit. If
a code is revoked or expires during a session, the next page
load shows "Access denied". This closes the gap where a revoked
user keeps working with an active session.

### 3.1 Landing page link

The gate is the primary entry. The Landing page itself has no
login. The gate protects Landing.

### 3.2 Free tier

Free users can be allowed without a code, or with a simple
public code. The Chief decides which. The default design is: a
public free code, so that free usage can be counted.

---

## 4. The beta window

The beta is a time-limited invitation.

A beta code has:

  - a start date,
  - an end date,
  - a name,
  - a contact.

Between the start and end dates, the code works. Outside them,
it does not.

When the beta window closes, the code stops working. A beta
user who tries to open the app sees "Access denied". A beta
user who is already in the app sees "Access denied" on their
next page load.

The beta has a hard lock. There is no fallback to free. The
beta is a specific test with a specific end. When the test
ends, the test ends.

### 4.1 Beta watermark

Every output produced during a beta session carries a "BETA"
marker:

  - the 3D viewer has a BETA badge in the corner,
  - every render prompt carries a BETA prefix,
  - the results page shows a BETA countdown ("Beta ends in
    N days").

The watermark prevents the beta output from being mistaken for
a paid output.

---

## 5. The Owner role

The Owner is the Chief. There is exactly one Owner.

The Owner has:

  - unlimited access to every input, every structure, every
    mode,
  - the MBS Tester page, which is not visible to any other mode,
  - an Owner tools panel on the Studio page (see
    UI_ARCHITECTURE.md),
  - the ability to switch their own session between modes for
    testing (so the Owner can see what a Free user sees, what a
    Studio user sees, etc.).

The Owner identifies themselves in one of two ways:

  1. A special Owner code, entered at the gate. The code never
     expires.
  2. A special URL, `?owner=1`, bookmarked on the Chief's phone.
     The URL flag bypasses the gate and sets the mode to Owner.

The Owner URL is not secret in a strong sense. It is not
advertised. It is not linked from anywhere. If it is ever
guessed, the Owner code rotates.

---

## 6. The MBS Tester

The MBS Tester is a page inside the SDSe app, not a separate
app. It is reached by:

  - a Landing page button, shown only when the access mode is
    Owner, or
  - a direct URL parameter, `?page=tester_mbs`, which the Owner
    bookmarks.

The Tester is never visible to a Beta tester, a Studio user, a
Pro user, or a Free user. It is Owner-only.

The Tester is the development lab. Its purpose is to prove the
engines. It is not a product feature.

---

## 7. The access code file

The access codes live in a single file in the repository. The
file is not shown to any user. It is read by the gate on every
page load.

Format (Python):

    ACCESS_CODES = {
        "OWNER-XXXX-XXXX": {
            "name": "The Chief",
            "contact": "(not needed)",
            "mode": "owner",
            "start": "2026-01-01",
            "end": None,
            "note": "Owner. Never expires.",
        },
        "BETA-X7K2-9MNP": {
            "name": "Tester A",
            "contact": "tester.a@example.com",
            "mode": "beta",
            "start": "2026-09-28",
            "end": "2026-10-28",
            "note": "Engineer friend. Testing user flow.",
        },
        "STUDIO-QW34-RT56": {
            "name": "Fabricator Co.",
            "contact": "sales@fabricator.example",
            "mode": "studio",
            "start": "2026-11-01",
            "end": None,
            "note": "Paid Studio seat.",
        },
    }

Fields:

  - **name** — a human-readable label. Not shown to the user.
  - **contact** — email or phone. Not shown to the user. Used
    only by the Chief when a notification is needed.
  - **mode** — one of owner, beta, studio, pro, free.
  - **start** — the date the code becomes valid. Format
    YYYY-MM-DD.
  - **end** — the date the code becomes invalid. Format
    YYYY-MM-DD. `None` means it never expires.
  - **note** — a free-text note. Not shown to the user.

To revoke a code, the Chief deletes the entry and commits. On
the next page load, the code is no longer in the list. The
user is locked out.

To extend a code, the Chief edits the `end` date and commits.

To add a code, the Chief adds a new entry and commits.

### 7.1 Privacy

The access code file contains names and contacts. The Chief
maintains it. It is never exposed to the app's users.

At commercial launch, when real user accounts exist, the
access codes become the invitation mechanism. A code is
redeemed once by a user, who then has a real account. The
contact becomes the user's login. The access code file shrinks
to invitations only.

---

## 8. URL resilience

The Streamlit URL is `sds-modular-preview.streamlit.app`. This
URL is tied to the app record inside Streamlit Cloud, not to
the code. If the app record is deleted, the URL dies. The code
survives in GitHub and can be redeployed at a new URL.

The following layers prevent a URL loss from becoming a
business loss:

### 8.1 A custom domain

The Chief registers a domain (for example, `sdse.app` or
`sdse.ocbc-cloud.com`). The domain points to the current
Streamlit URL via a redirect.

Users are given the domain, never the raw Streamlit URL. When
the Streamlit URL changes, the redirect is updated. The users
see no change.

Cost: roughly USD 10–15 per year. Redirect: free via
Cloudflare, GitHub Pages, or the registrar's control panel.

### 8.2 A status page

A simple page at `sdse.app/status` announces the current
Streamlit URL and any planned downtime. It is the fallback if
the domain redirect fails.

### 8.3 A user contact list

Every access code has a contact field. The Chief can export
the list at any time. If the app goes dark, the Chief can
notify every user by email.

The three layers catch three failure cases:

  1. Streamlit URL changes. The domain redirect covers it.
  2. The domain redirect fails. The status page covers it.
  3. The domain and the URL are both gone. The contact list
     covers it.

None of the three is urgent today. All three are cheap. Each
one prevents a business-ending loss at commercial launch.

---

## 9. What the gate does not do

The gate does not provide real authentication. It does not
protect against a determined attacker who guesses a code. It
does not encrypt traffic (Streamlit Cloud provides HTTPS). It
does not manage payments.

The gate is a light access control for the testing and early
commercial phase. When real subscription management is built,
the gate becomes the invitation layer on top of a proper
account system.

---

## 10. Execution plan

When the Chief decides, the following files are added or
changed. Nothing is done until then.

**New files:**

  - `data/access_codes.py` — the code list.
  - `ui/access_gate.py` — the gate page.
  - `core/access.py` — the code validation and mode setting.

**Changed files:**

  - `core/navigation.py` — the gate runs before any page.
  - `core/state.py` — an `access_mode` variable.
  - `ui/landing.py` — the MBS Tester button is Owner-only.
  - `ui/studio.py` — an Owner tools panel, if the mode is
    Owner.

**Unchanged files:**

  - `app.py`, `engine/*`, `data/*` (other than the new
    access_codes.py), `viewers/*`, `ui/workshops/*`.

**Effort:** 2 to 3 hours of focused work, in chunks, with the
usual commit discipline.

**Risk:** low. The gate is additive. It does not modify any
existing function. If the gate fails, the app can be reverted
by removing the gate from `navigation.py`.

---

## 11. Document history

Created: 2026-09-28.
  - Five access modes defined: Owner, Beta, Studio, Pro, Free.
  - Access gate designed.
  - Beta window designed.
  - Owner role defined.
  - Access code file format defined.
  - URL resilience plan defined.
  - Execution plan defined.
  - Status: DESIGN ONLY. NOT EXECUTED.
