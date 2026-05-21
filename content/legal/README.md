# Legal content source

Production legal pages are loaded from **[`legacy/`](../legacy/)** HTML exports via `GET /api/legal/{slug}`:

| Slug | File |
|------|------|
| `terms` | `legacy/Terms.html` |
| `disclosure` | Section 1.5 (`#term1005`) from `legacy/Terms.html` |
| `terms-summary` | Key summary block for enrollment agreements step |
| `faq` | `legacy/faq.html` |
| `privacy` | `legacy/privacy.html` |
| `legal` | `legacy/legal.html` |

Markdown files in this folder are deprecated; edit the legacy HTML or add extraction logic in `backend/app/legal_content.py`.
