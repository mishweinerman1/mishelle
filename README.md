# mishelle

Personal site and context files for **Mishelle Weinerman** (pronounced *Mish-el Wine-er-man*).

## What's here

| File / folder | Purpose |
| --- | --- |
| `index.html` | Single-page contact/landing site. Header, short bio, and a sign-up form. |
| `style.css` | Styling for the landing page (centered card, teal accents). |
| `context/` | Context files describing who I am, what I like, and how I operate. |

## The website

A lightweight, dependency-free static page that serves as my point of contact on
the web. The sign-up form composes an email to `mishelle@auxinsights.com` using a
`mailto:` link — no backend or third-party service required.

### Running it locally

It's plain HTML/CSS/JS, so just open the file:

```bash
open index.html        # macOS
# or serve it
python3 -m http.server
```

### Possible upgrades

- Swap the `mailto:` form for a hosted form service (e.g. Formspree, Netlify
  Forms, or a small serverless function) to capture leads without opening an
  email client.
- Add analytics and a favicon.

## Context files

The [`context/`](./context) folder is meant to be a living description of me —
useful as background for collaborators, or as context for AI assistants I work
with.

- [`context/about.md`](./context/about.md) — who I am
- [`context/preferences.md`](./context/preferences.md) — what I like
- [`context/operating.md`](./context/operating.md) — how I operate
