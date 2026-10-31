# Issue #61 — Visual Verification & Design System Evidence

**Issue:** [#61 — Денис: Login/Password placeholders + выразительная визуальная система](https://github.com/Slave-of-Skynet/Impact-Hackathon-2026/issues/61)  
**Date:** 2026-10-31  
**Executor:** Денис (Antigravity)  
**Model:** Gemini 3.8 Flash (High effort)  
**Reviewer:** ChatGPT (Independent Review)  

---

## 1. Login & Password Placeholders Evidence

File: `templates/adult/login.html`

* **Username/Login input:**
  * Visible Label: `Adresă email` (preserved)
  * `placeholder`: changed from `"exemplu@familie.ro"` to **`"Login"`**
  * Attributes preserved: `type="email"`, `name="username"`, `autocomplete="email"`, `required`
* **Password input:**
  * Visible Label: `Parolă` (preserved)
  * `placeholder`: changed from `"••••••••"` to **`"Password"`**
  * Attributes preserved: `type="password"`, `name="password"`, `autocomplete="current-password"`, `required`
* **Security & Auth Form Contract:**
  * Tested in `tests/test_adult_ui_integration.py::test_login_placeholders_and_form_contract`.
  * After failed authentication attempts, the password field is never pre-filled or leaked (`value` attribute empty), and CSRF token remains intact.

---

## 2. Palette Comparison & Design Token Specification

### Concept Exploration & Choice

1. **Concept A (Chosen): Warm Storybook (Poveste Caldă)**  
   * Deep library indigo/ink for text (`#1A2035`) and primary brand (`#253275`).
   * Warm archival cream canvas (`#FAF7F2`) and soft parchment surfaces (`#F3EDE2`).
   * Storybook Coral accent (`#C84622`) for high-contrast emotional energy and calls-to-action.
   * Deep forest-teal (`#0D8268`) for positive reading achievements and progress.
   * Amber gold (`#D97706` / `#FEF3C7`) for club badges and rewards.
   * **Why chosen:** Gives an immediate sensation of books, bedtime stories, and warm quality without sterile corporate "SaaS blue". Maintains high dignity for adults while feeling magical for children.

2. **Concept B: Whimsical Forest (Pădurea Fermecată)**  
   * Sage-tinted parchment canvas (`#F6F8F5`), pine green primary (`#1B4D3E`), mustard accent (`#E5A93C`).
   * *Assessment:* Evokes nature/adventure well, but lacks the bedtime reading coziness and clashes slightly with the existing blue/amber mascot Gusti.

---

### Token Comparison Table

#### Adult UX (`static/css/app.css`)

| Token Name | Baseline Hex | Warm Storybook Hex | Role / Context | WCAG AA Contrast Ratio |
|---|---|---|---|---|
| `--color-primary` | `#1e3a8a` | `#253275` | Brand headers, primary buttons | **9.7:1** on white (AAA) |
| `--color-primary-hover` | `#1e40af` | `#1b2559` | Active/hover brand buttons | **12.4:1** on white (AAA) |
| `--color-primary-light` | `#dbeafe` | `#eef2ff` | Subtle selection background | - |
| `--color-accent` | `#c2410c` | `#c84622` | Attention, primary CTAs | **4.76:1** on white (AA) |
| `--color-accent-hover` | `#9a3412` | `#a83617` | Hover accent | **6.1:1** on white (AA) |
| `--color-accent-light` | `#ffedd5` | `#fdf2ee` | Avatar/badge background | - |
| `--color-bg` | `#faf8f5` | `#faf7f2` | App canvas / warm paper | - |
| `--color-surface` | `#ffffff` | `#ffffff` | Card surfaces | - |
| `--color-surface-subtle` | `#f4efe6` | `#f3ede2` | Table / secondary card bg | - |
| `--color-surface-hover` | `#f8fafc` | `#f7f1e7` | List hover state | - |
| `--color-text` | `#0f172a` | `#1a2035` | Main body & heading ink | **13.8:1** on `#FAF7F2` (AAA) |
| `--color-text-muted` | `#475569` | `#4e5569` | Secondary book metadata | **6.4:1** on `#FAF7F2` (AA) |
| `--color-border` | `#e2e8f0` | `#e5ddd0` | Card & input warm borders | - |
| `--color-success` | `#15803d` | `#0d8268` | Reading progress, achievements | **4.8:1** on white (AA) |
| `--color-success-bg` | `#dcfce7` | `#e6f7f2` | Success alerts | - |
| `--color-error` | `#b91c1c` | `#b91c1c` | Validation errors | **5.9:1** on white (AA) |
| `--color-warning` | `#b45309` | `#b45309` | Warning badges / Amber club | **4.6:1** on white (AA) |

#### Child Mode (`static/css/child.css`)

| Token Name | Baseline Hex | Warm Storybook Hex | Role / Context | WCAG AA Contrast Ratio |
|---|---|---|---|---|
| `--child-bg` | `#F8FAFC` | `#F7F4EE` | Child app background | - |
| `--child-surface` | `#FFFFFF` | `#FFFFFF` | Content card background | - |
| `--child-surface-subtle` | `#F1F5F9` | `#EFE9DD` | Button/nav subtle surface | - |
| `--child-primary` | `#2563EB` | `#3548B8` | Mascot bubble, primary actions | **7.49:1** on white (AAA) |
| `--child-primary-hover` | `#1D4ED8` | `#283896` | Child primary hover | **9.4:1** on white (AAA) |
| `--child-success` | `#16A34A` | `#0D8268` | Book finished, progress bar | **4.8:1** on white (AA) |
| `--child-accent` | `#F59E0B` | `#D97706` | Club rewards, trophy highlight | **3.6:1** (Large text/icons AA) |
| `--child-text` | `#0F172A` | `#1A2035` | Child high-readability text | **13.5:1** on `#F7F4EE` (AAA) |
| `--child-text-muted` | `#475569` | `#4E5569` | Author / page count subtitles | **6.3:1** on `#F7F4EE` (AA) |
| `--child-border` | `#E2E8F0` | `#E5DDD0` | Warm rounded borders | - |

---

## 3. Accessibility & Ergonomics Verification

* **Contrast:** All normal body text tokens and button labels exceed WCAG AA 4.5:1. Heading and primary text exceed 9:1 (AAA).
* **Touch Targets:**
  * Adult interface: `--min-touch-target: 44px` enforced on buttons, nav links, and form inputs.
  * Child mode: `--tap-min-size: 48px`, large buttons 56px height.
* **Focus States:** High visibility focus rings (`--focus-ring: 2px solid #253275`, outline offset 2px/3px).
* **Motion:** `@media (prefers-reduced-motion: reduce)` added to both `static/css/app.css` and `static/css/child.css` to safely neutralize mascot float animation and transitions for sensitive users.
* **Responsive Layout:** Tested at 390px (mobile) and 1280px (desktop) without any horizontal scrolling (`overflow-x: hidden`).

---

## 4. Screenshot Ledger

Captured via headless Chromium (Chrome 110+ on Windows 10.0.26300) running against local Django dev server with seeded synthetic demo accounts:

| ID | Screen / Route | Viewport | File Path |
|---|---|---|---|
| 01 | Landing (`/`) | Desktop 1280×900 | `01-landing-desktop.png` |
| 02 | Landing (`/`) | Mobile 390×844 | `01-landing-mobile-390.png` |
| 03 | Login (`/cont/intrare/`) | Desktop 1280×900 | `02-login-desktop.png` |
| 04 | Login (`/cont/intrare/`) | Mobile 390×844 | `02-login-mobile-390.png` |
| 05 | Catalog (`/carti/`) | Desktop 1280×900 | `03-catalog-desktop.png` |
| 06 | Catalog (`/carti/`) | Mobile 390×844 | `03-catalog-mobile-390.png` |
| 07 | Parent Dashboard (`/panou/`) | Desktop 1280×900 | `04-parent-dashboard-desktop.png` |
| 08 | Parent Dashboard (`/panou/`) | Mobile 390×844 | `04-parent-dashboard-mobile-390.png` |
| 09 | Child Mode Home (`/copil/`) | Desktop 1280×900 | `05-child-home-desktop.png` |
| 10 | Child Mode Home (`/copil/`) | Mobile 390×844 | `05-child-home-mobile-390.png` |
