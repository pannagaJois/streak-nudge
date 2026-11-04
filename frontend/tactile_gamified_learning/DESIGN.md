---
name: Tactile Gamified Learning
colors:
  surface: '#fbf9f8'
  surface-dim: '#dbd9d9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#eae8e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#3f4a36'
  inverse-surface: '#303030'
  inverse-on-surface: '#f2f0f0'
  outline: '#6f7b64'
  outline-variant: '#becbb1'
  surface-tint: '#2b6c00'
  primary: '#2b6c00'
  on-primary: '#ffffff'
  primary-container: '#58cc02'
  on-primary-container: '#1e5000'
  inverse-primary: '#6be026'
  secondary: '#8c5000'
  on-secondary: '#ffffff'
  secondary-container: '#fd9500'
  on-secondary-container: '#633700'
  tertiary: '#006590'
  on-tertiary: '#ffffff'
  tertiary-container: '#4abdff'
  on-tertiary-container: '#004a6b'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#87fe45'
  primary-fixed-dim: '#6be026'
  on-primary-fixed: '#082100'
  on-primary-fixed-variant: '#1f5100'
  secondary-fixed: '#ffdcbf'
  secondary-fixed-dim: '#ffb872'
  on-secondary-fixed: '#2d1600'
  on-secondary-fixed-variant: '#6a3b00'
  tertiary-fixed: '#c8e6ff'
  tertiary-fixed-dim: '#88ceff'
  on-tertiary-fixed: '#001e2e'
  on-tertiary-fixed-variant: '#004c6e'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  display-hero:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-hero-mobile:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-sm:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
  body-lg:
    fontFamily: Nunito Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  body-md:
    fontFamily: Nunito Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-sm:
    fontFamily: Nunito Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-lg:
    fontFamily: Outfit
    fontSize: 16px
    fontWeight: '700'
    lineHeight: 20px
    letterSpacing: 0.04em
  label-md:
    fontFamily: Outfit
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 18px
    letterSpacing: 0.03em
  label-sm:
    fontFamily: Outfit
    fontSize: 12px
    fontWeight: '800'
    lineHeight: 16px
    letterSpacing: 0.05em
  code-snippet:
    fontFamily: Nunito Sans
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system is engineered for high engagement, intrinsic motivation, and daily habit persistence within technically demanding domains. It combines the structured rigor of computer science education with the tactile, high-dopamine feedback loops of top-tier consumer gamification.

### Brand Personality & Emotional Voice
- **Playful & Urgent:** Celebrates micro-wins with explosive tactile feedback; uses playful urgency and light-hearted nudging ("Don't let your graph algorithms freeze!") to defend daily streaks.
- **Friendly & Approachable:** Eliminates the sterile, intimidating aesthetic typical of competitive programming portals. Abstract algorithmic concepts are framed as conquerable daily quests.
- **Punchy & Expressive:** High-contrast typography paired with direct, vivid copy that communicates clarity over academic pretense.

### Design Movement
**Tactile / Skeuomorphic Gamification:** The aesthetic relies on chunky, extruded physical affordances: raised "pushable" surfaces, pronounced bottom bevels (giving items a physical button-press travel distance), thick outlines, and vibrant color-blocked tokens. Elements feel physical, squishy, and immediately satisfying to interact with.

## Colors

The palette employs vibrant, un-muted game-state hues built atop ultra-clean feather neutrals. Every functional action maps to an unambiguous color identity.

### Palette Architecture
- **Primary (`#58CC02` - Electric Emerald):** Core progression, "Run Tests" success, practice loop completions, and primary interaction triggers. Accompanied by a 4px bottom border shade in Deep Emerald (`#46A302`).
- **Secondary (`#FF9600` - Flame Orange):** Daily streak counters, active milestones, and high-energy alert states. Bottom border shade in Deep Flame (`#CC7A00`).
- **Tertiary (`#1CB0F6` - Freeze Ice Blue):** Streak freezes, data structure concept tags, gems/credits, and informational hints. Bottom border shade in Deep Ice (`#1899D6`).
- **Destructive / Streak Danger (`#FF4B4B` - Fire Red):** Critical broken streak alerts, compilation errors, and urgent warnings. Bottom border shade in Deep Crimson (`#D63939`).
- **Neutrals & Surfaces:**
  - `Surface Base`: `#FFFFFF`
  - `Surface Canvas`: `#F7F7F7` (Soft Feather Grey)
  - `Border Neutral`: `#E5E5E5`
  - `Border Neutral Pressed`: `#CECECE`
  - `Text Neutral Dark`: `#4B4B4B` (Core body, off-black for softened readability)
  - `Text Neutral Muted`: `#AFAFAF`
  - `Text Charcoal Inverted`: `#111827` (Headlines)

## Typography

Typography establishes an energetic cadence through the pairing of two distinct typefaces:

1. **Outfit (Headlines & Labels):** Geometric, bold, and punchy. Used across all callouts, gamification metrics, titles, button text, and badges. Provides structural weight without becoming aggressive or rigid.
2. **Nunito Sans (Body & Code Narrative):** Rounded, ultra-readable, and friendly. Softens dense algorithmic problem descriptions, solution hints, and explanations while preserving high readability at smaller scales.

### Rules of Usage
- **Uppercase Labels:** All interactive buttons and stat labels leverage `label-*` tokens formatted in full uppercase with expanded letter-spacing (`0.03em` - `0.05em`) to simulate arcade-style physical placards.
- **Numerical Dominance:** Streak numbers and quest counts utilize `headline-lg` or `display-hero` with an ultra-bold weight (`800`).

## Layout & Spacing

The layout philosophy follows a responsive container grid with dedicated app side-rails on larger viewports and an anchor tab rail on mobile devices.

### Grid & Structure
- **Desktop (1024px+):** Fixed 260px tactical sidebar for daily navigation (Quests, Daily Tree, Leaderboard, Freezes), followed by a central quest tracking stream (max 780px) and a persistent floating right widget rail (320px) for streak status, problem counter, and hearts/freezes.
- **Tablet (768px - 1023px):** Collapsed iconography sidebar (72px), single fluid column for problem paths and stats.
- **Mobile (<768px):** Sticky top bar tracking streaks and currency items; bottom sticky utility nav (64px); 100% fluid central scroll stream.

### Spacing Tokens Application
- `space-xs` (4px): Inline indicator separation, icon-to-counter gaps.
- `space-sm` (8px): Internal badge padding, dense list margins.
- `space-md` (16px): Card internal padding, button inline padding, standard gap between form modules.
- `space-lg` (24px): Inter-card stacking gaps, quest step separators.
- `space-xl` (40px): Section breaks, major path milestone distances.

## Elevation & Depth

Visual hierarchy is maintained without blur-heavy or diffuse drop-shadows. Instead, depth is physically extruded using thick solid base borders, mimicking 3D tactile buttons and layered plastic surfaces.

### Extrusion Mechanics
1. **Interactive Objects (Buttons, Selectable Chips):**
   - Base state: Crisp 2px perimeter border (`#E5E5E5` or darker hue of button's primary fill) plus an unblurred 4px bottom border offset simulating an extruded floor.
   - Hover state: 10% brightness increase, maintain 4px extrusion.
   - Active/Pressed state: The element transforms `translateY(4px)` while the bottom extrusion border collapses to 0px. The user physically "pushes" the element flush into the screen.
2. **Elevated Containers & Cards:**
   - Outlined by a solid 2px border in `#E5E5E5`.
   - Structural drop: Grounded by a solid 4px to 6px offset drop border in `#CECECE` (or an element-specific darker shade), ensuring objects rest tangibly on `#F7F7F7`.
3. **Overlays & Modals:**
   - Backdrops use a semi-opaque `#000000` with 40% opacity.
   - Modals use an 8px solid offset border with `translateY(-4px)` to pop distinctly above the plane.

## Shapes

The design uses deeply rounded corners to reinforce warmth, approachability, and safety against failure.

### Shape Tokens & Assignments
- **Inputs and Standard Containers:** Applied at `rounded-lg` (16px) for solid boundary definition.
- **Primary Interactive Cards & Challenge Nodes:** Applied at `rounded-xl` (24px) to create friendly, handheld "tile" aesthetics.
- **Gamified Badges & Milestones:** Full circle or pill shapes (`9999px`) for quick visual scanning.
- **Inner Borders:** Nested interior items match the exterior radius minus the padding distance to maintain clean concentric geometry.

## Components

### 1. Tactile Buttons
- **Primary Action (Emerald):** Background `#58CC02`, text `#FFFFFF`, border-bottom `4px solid #46A302`.
- **Secondary / Streak Save (Flame):** Background `#FF9600`, text `#FFFFFF`, border-bottom `4px solid #CC7A00`.
- **Tertiary / Neutral Outline:** Background `#FFFFFF`, text `#4B4B4B`, border `2px solid #E5E5E5`, border-bottom `4px solid #E5E5E5`.
- **Interaction:** `active:translate-y-1 active:border-b-0` transition over `80ms ease-out`.

### 2. Cards & Algorithmic Modules
- Container background is pure `#FFFFFF` with `2px solid #E5E5E5` and a solid `4px` base border.
- Completed topic modules shift border and fill to subtle tinted pastels with vibrant emerald badges.
- Cards feature top-right badge anchors for difficulty indicators (e.g., "Easy", "Medium", "Hard") with saturated difficulty-coded pills.

### 3. Streak & Stat Chips
- Compact pills with an interior icon (e.g., fire for streaks, snowflake for freezes, lightning for problem count).
- Light tinted background (e.g., Flame at 12% opacity) surrounded by a matching solid border.
- Text uses `label-md` in bold contrast.

### 4. Interactive Quiz & Solution Nodes
- Selection items (multiple choice DSA options or code snippet lines) behave like wide horizontal buttons:
  - Default: White background, 2px grey border, 3px bottom grey border.
  - Selected: Ice Blue background tint (`#E8F7FE`), border `#1CB0F6`, bottom border `#1899D6`.
  - Correct feedback: Green tint (`#EDF9E5`), border `#58CC02`.
  - Incorrect feedback: Red tint (`#FDEEEE`), border `#FF4B4B`.

### 5. Milestone & Path Node Badges
- Node circles (64px × 64px) marking daily algorithm challenges along an SVG road path.
- Active nodes feature an animated pulsing halo; completed nodes display a solid checkmark with an extruded emerald base; locked nodes appear in neutral grey (`#E5E5E5`) with flattened elevation.

### 6. Inputs & Code Inputs
- Input fields use a 2px border in `#E5E5E5`, a flat white surface, and high-contrast text.
- Focus state updates the border to `#1CB0F6` with a solid 2px outline ring in ice-blue tint.