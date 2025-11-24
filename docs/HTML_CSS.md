# HTML & CSS Development Guide

This is a guide for developers and AI assistants creating HTML and CSS.

Focus on clean, modern, lightweight mobile-first pages that rely only on system fonts and a single cached stylesheet.

## 1. Design System Reference

When generating the initial stylesheets, use the color tokens, spacing scales, baseline layout rules, and other scaffold details from [`scaffolding/HTML_CSS_Scaffold.md`](scaffolding/HTML_CSS_Scaffold.md). Review that file when regenerating the base stylesheet or updating global design tokens.

The rest of this guide focuses on day-to-day markup and component expectations.

## 2. Things to Avoid

- **Do not introduce new font stacks** or load remote fonts. Rely on the font stack defined in the base stylesheet.
- **Do not hardcode colors, spacing, or shadows.** Reference the CSS variables and tokens established in the base stylesheet.
- **Do not use inline styles (`style=`)** — rely on reusable classes or scoped CSS files instead.
- **Do not drop new component patterns** without documenting them; align with the component expectations below.
- **Do not remove focus outlines** without providing explicit `:focus-visible` styles with equal or better visibility.

## 3. Component Expectations

- **Buttons:** `.btn` base class with modifiers `.btn-primary`, `.btn-secondary`, etc. Provide `:hover`, `:focus-visible`, and `:disabled` states with accessible contrast.
- **Badges/Tags:** `.badge` base class with status modifiers like `.badge-open`, `.badge-closed`, `.badge-fixing`. Use positioning utilities (`.badge-status` for right-align) when needed.
- **Cards/Blocks:** `.card` for reusable white surfaces with padding `space-5`, `box-shadow` token. Use BEM elements for card parts: `.card__header`, `.card__body`, `.card__footer`.
- **Forms:** `.form-field` wrapper holding `<label>` and control. Inputs get `border: 1px solid var(--border-color)`, `border-radius: 6px`, focus ring `box-shadow: 0 0 0 3px rgba(31, 122, 234, 0.25)` while retaining visible outline.
- **Messages & Alerts:** `.message` base class with type modifiers `.message-success`, `.message-error`, `.message-warning`, `.message-info`, leveraging palette tokens.
- **List Cards:** Use flex layouts with `gap` for metadata rows. Machine cards use `.machine-card` with elements like `.machine-card__row`, `.machine-card__name`, `.machine-card__meta` for structured components.
- **Utilities:** Provide light utilities for spacing, layout (`.hidden`, `.text-muted`, `.badge-status`), and common patterns to avoid inline style usage.

## 4. Accessibility & Interaction

- Maintain WCAG AA contrast for text/background combinations.
- Never remove outlines without providing `:focus-visible` alternatives.
- Respect `@media (prefers-reduced-motion: reduce)` by disabling transitions.
- Buttons and links should have hover + active states distinct from focus.
- Use semantic HTML elements (e.g., `<nav>`, `<main>`, `<section>`, `<table>`).

## 5. Organizational Rules

- **File Structure:** Place CSS sources under the project’s `static/css/` directory (or equivalent) with files such as `base.css` (reset + tokens), `layout.css`, `components.css`, and page-specific modules (`dashboard.css`, `reports.css`, etc.). Concatenate/minify them into a single bundle that the main layout template includes.
- **No Inline Styles:** Templates should only use class names. Add page-specific CSS via additional `<link>` tags or template blocks instead of `style=` attributes.
- **Naming Methodology: BEM-ish (Relaxed BEM)**

  This project uses a "BEM-ish" approach that keeps BEM's structural benefits while simplifying modifier syntax:

  **Use `Block__Element` (double underscore) for component hierarchy:**
  - `.machine-card__row` - row is part of machine-card
  - `.machine-card__name` - name is part of machine-card
  - `.breadcrumb__trail` - trail is part of breadcrumb
  - Makes component structure immediately clear

  **Use `Block-modifier` (single hyphen) for variants/states:**
  - `.badge-open`, `.badge-closed`, `.badge-fixing`
  - `.btn-primary`, `.btn-secondary`
  - `.breadcrumb-with-actions`
  - Simpler than strict BEM's double-hyphen (`--`)
  - Matches industry practice and common CSS frameworks

  **Why not strict BEM?**
  - Strict BEM uses `Block--modifier` (double hyphen) but this adds cognitive load
  - Single hyphens are more common in the wild (Bootstrap, etc.)
  - Internal consistency is more valuable than rigid convention

  **Examples from this codebase:**
  - Component structure: `.machine-card`, `.machine-card__row`, `.machine-card__name`
  - Component variants: `.badge-open`, `.badge-broken`, `.btn-primary`
  - Utility classes: `.text-muted`, `.hidden`, `.badge-status` (positioning helper)

  **When to use each pattern:**
  - `Block__Element` when creating component subparts (header, body, footer, meta, etc.)
  - `Block-modifier` when adding variants (colors, sizes, states)
  - Simple names for standalone utilities (`.card`, `.btn`, `.hidden`)

## 6. Performance & Build

- Stick to vanilla CSS compiled once (no external fonts, minimal animations).
- Use `@layer base, components, utilities;` to control cascade if desired.
- Minify production CSS and ensure it is fingerprinted via Django’s `collectstatic`.
- Document a command such as `npm run css:build` if tooling is added later, but current instructions assume plain CSS maintained manually.

## 7. Deliverables Checklist

 - Reference the tokens defined in the scaffold doc.
 - Write base reset + typography rules.
 - Implement components with agreed naming method.
 - Provide responsive behavior for header, main grids, tables, and cards at the specified breakpoints.
 - Ensure no inline styles remain; all templates rely solely on classes.
 - Verify focus styles and reduced-motion handling.
 - Keep CSS lean: no unused classes or framework imports.
