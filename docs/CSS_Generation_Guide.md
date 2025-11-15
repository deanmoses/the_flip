# CSS Generation Guide

This document contains instructions for AI assistants generating the project’s HTML/CSS. 

Focus on clean, modern, lightweight pages that rely only on system fonts and a single cached stylesheet.

## 1. Visual System

- **Typography:** Use the system stack `"Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif` but do not load remote fonts; if a name is missing locally the stack simply falls back.
- **Color Palette:**  
  - Primary: `#1f7aea` (links, primary buttons).  
  - Secondary: `#1b3a57` (headers, nav background).  
  - Accent: `#10b981` (success highlights).  
  - Warning: `#f59e0b`, Danger: `#ef4444`.  
  - Surface light: `#ffffff`, Surface muted: `#f5f7fb`, Border: `#e3e8ef`, Text base: `#1f2933`, Text muted: `#52606d`.
- **Spacing Scale:** 4 px base unit with tokens `space-1 = 4px`, `space-2 = 8px`, … up to `space-6 = 24px`. Keep vertical rhythm multiples of 4.
- **Radii & Shadows:** Base radius `4px`, cards `8px`. Single soft shadow `0 8px 20px rgba(15, 23, 42, 0.08)`.
- **Tokens:** Define CSS custom properties inside `:root` (`--color-primary`, `--space-3`, etc.) so components share consistent values.

## 2. Layout Rules

- **Container:** Max width 1200px, horizontal padding `space-4`. Body background `#f5f7fb`.
- **Header/Nav/Footer:** Persistent nav with sticky behavior on desktop (`position: sticky; top: 0;`). Footer simple text centered.
- **Responsive Breakpoints:**  
  - `@media (max-width: 1024px)` collapse sidebar into horizontal tabs.  
  - `@media (max-width: 768px)` stack header elements vertical, convert grids to one column.  
  - `@media (max-width: 480px)` full-width buttons, increase body padding.
- **Tables:** On <=768px, convert to card layout with CSS (`display: block`, pseudo labels) rather than forcing horizontal scrolling when possible.
- **Spacing:** Maintain `space-4` (16px) between stacked sections, `space-2` (8px) between tightly related elements.

## 3. Component Expectations

- **Buttons:** `.btn`, modifiers for primary/secondary/danger/ghost. Provide `:hover`, `:focus-visible`, and `:disabled` states with accessible contrast.
- **Badges/Tags:** Consistent height, uppercase text, left padding `space-2`.
- **Cards/Blocks:** `.card` for reusable white surfaces with padding `space-5`, `box-shadow` token.
- **Forms:** `.form-field` wrapper holding `<label>` and control. Inputs get `border: 1px solid var(--border-color)`, `border-radius: 6px`, focus ring `box-shadow: 0 0 0 3px rgba(31, 122, 234, 0.25)` while retaining visible outline.
- **Messages & Alerts:** `.alert`, `.alert--success`, `.alert--danger`, etc., leveraging palette tokens.
- **Lists (tasks/logs):** Flex layout with `gap` for metadata. Provide `.clickable-card` helper with `cursor: pointer` and subtle background change on hover.
- **Utilities:** Provide light utilities for spacing (`.mt-4`), layout (`.flex`, `.grid-two`), and text alignment to avoid inline style usage.

## 4. Accessibility & Interaction

- Maintain WCAG AA contrast for text/background combinations.
- Never remove outlines without providing `:focus-visible` alternatives.
- Respect `@media (prefers-reduced-motion: reduce)` by disabling transitions.
- Buttons and links should have hover + active states distinct from focus.
- Use semantic HTML elements (e.g., `<nav>`, `<main>`, `<section>`, `<table>`).

## 5. Organizational Rules

- **File Structure:** Create `tickets/static/tickets/css/` with `base.css` (reset + tokens), `layout.css`, `components.css`, and page modules (`machine.css`, `reports.css`). The final bundle imported in `base.html` can be concatenated/minified but author content lives in logical files.
- **No Inline Styles:** Templates should only use class names. Add page-specific CSS via additional `<link>` or block overrides instead of `style=` attributes.
- **Naming Methodologies:**  
  1. **BEM:** `block__element--modifier` (e.g., `task-card__meta--muted`). Clear intent, low collision risk.  
  2. **Namespaced Modules:** Prefix class names per page/component (e.g., `.machine-detail-header`, `.machine-detail-meta`). Works well when pages are isolated.  
  3. **Utility-First Hybrid:** Small reusable classes (`.text-muted`, `.gap-4`, `.flex-between`) combined with semantic wrappers. Enables rapid layout changes with fewer bespoke selectors. Pick one primary strategy and document modifiers/helpers.

## 6. Performance & Build

- Stick to vanilla CSS compiled once (no external fonts, minimal animations).  
- Use `@layer base, components, utilities;` to control cascade if desired.  
- Minify production CSS and ensure it is fingerprinted via Django’s `collectstatic`.  
- Document a command such as `npm run css:build` if tooling is added later, but current instructions assume plain CSS maintained manually.

## 7. Deliverables Checklist

1. Define tokens in `:root`.  
2. Write base reset + typography rules.  
3. Implement components with agreed naming method.  
4. Provide responsive behavior for header, main grids, tables, and cards at the specified breakpoints.  
5. Ensure no inline styles remain; all templates rely solely on classes.  
6. Verify focus styles and reduced-motion handling.  
7. Keep CSS lean (no unused classes or framework imports).
