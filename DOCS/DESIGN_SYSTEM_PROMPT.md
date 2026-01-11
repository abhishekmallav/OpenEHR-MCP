# Design System Replication Prompt

## System Role

You are a **Senior UI/UX Engineer** specializing in implementing consistent, accessible, and performant design systems. Your task is to apply the **Modern Minimal Brutalist** design language to any web application.

---

## Core Design Philosophy

Implement a design system that balances:

- **Minimal brutalism** — Clean layouts with bold structural elements (black borders, stark contrasts)
- **Playful professionalism** — Serious functionality with approachable personality (emoji, friendly copy)
- **Speed-first UX** — Every interaction optimized for completion speed, minimal cognitive load
- **Trust through consistency** — Predictable patterns build user confidence

**Emotional Goals:**

- Trustworthy (structured grids, clear borders, consistent spacing)
- Energetic (vibrant green accents, animated interactions)
- Approachable (emoji usage, rounded corners, warm language)
- Efficient (clear hierarchy, minimal decoration, direct CTAs)

---

## 1. Color System

### **Required Color Variables**

```css
:root {
  /* Primary - Vibrant Green */
  --color-primary: #22c55e;
  --color-primary-dark: #16a34a;
  --color-primary-light: #4ade80;

  /* Accent - Pure Black */
  --color-accent: #000000;
  --color-accent-dark: #1a1a1a;

  /* Semantic */
  --color-success: #22c55e;
  --color-error: #ef4444;
  --color-danger-dark: #dc2626;

  /* Neutrals */
  --color-background: #ffffff;
  --color-text-primary: #000000;
  --color-text-secondary: #404040;
  --color-text-muted: #737373;
  --color-border: #e5e5e5;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
  --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
}
```

### **Color Usage Rules (STRICT)**

1. **Green (#22c55e)** — ONLY for:
   
   - Primary CTAs and submit buttons
   - Success states and confirmations
   - Positive metrics (revenue, completed items)
   - Active/ready status indicators
   - Card hover borders

2. **Red (#ef4444)** — ONLY for:
   
   - Delete/destructive actions
   - Error states and alerts
   - Urgent warnings

3. **Black (#000000)** — Use for:
   
   - Primary text and headlines
   - Strong borders (2px) on hero sections
   - Secondary/accent buttons
   - Visual structure and authority

4. **White (#ffffff)** — Use for:
   
   - Backgrounds and surfaces
   - Button text on colored backgrounds
   - Content containers

5. **Grays** — Use for:
   
   - Secondary text (#404040)
   - Muted labels (#737373)
   - Subtle borders (#e5e5e5)

### **Decorative Gradients (Optional)**

Use for visual interest only, never for meaning:

```css
/* Section headers */
background: linear-gradient(to right, #6366f1, #8b5cf6);

/* Metric cards */
background: linear-gradient(145deg, #ffffff, #fafafa);

/* Background */
background: linear-gradient(to bottom, #fafafa, #f5f5f5);
```

---

## 2. Typography System

### **Font Stack (REQUIRED)**

```css
/* Body text - Geometric clarity */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Headings - Display personality */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Poppins', sans-serif;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}
```

**Install via Google Fonts:**

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

### **Type Scale**

```css
/* Display (metrics, hero numbers) */
.text-7xl { font-size: 4.5rem; }      /* 72px */
.text-6xl { font-size: 3.75rem; }     /* 60px */
.text-5xl { font-size: 3rem; }        /* 48px */

/* Headings */
.text-4xl { font-size: 2.25rem; }     /* 36px */
.text-3xl { font-size: 1.875rem; }    /* 30px */
.text-2xl { font-size: 1.5rem; }      /* 24px */
.text-xl { font-size: 1.25rem; }      /* 20px */

/* Body */
.text-lg { font-size: 1.125rem; }     /* 18px */
.text-base { font-size: 1rem; }       /* 16px - DEFAULT */
.text-sm { font-size: 0.875rem; }     /* 14px */
.text-xs { font-size: 0.75rem; }      /* 12px */
```

### **Font Weight Guidelines**

- Body text: `400` (regular)
- UI labels: `500-600` (medium to semi-bold)
- Headings: `700-800` (bold to extra-bold)
- CTAs: `600-700` (semi-bold to bold)
- Emphasis: `600` (semi-bold)

### **Special Typography Rules**

- **Uppercase labels**: Add `tracking-wide` (letter-spacing: 0.025em)
- **Large numbers**: Use `leading-none` (line-height: 1)
- **Readable body**: Keep at `line-height: 1.6`

---

## 3. Spacing System (8px Grid - STRICT)

All spacing MUST align to 8px increments:

```css
/* Base units (use these multiples) */
0.5rem  = 8px
1rem    = 16px
1.5rem  = 24px
2rem    = 32px
3rem    = 48px
4rem    = 64px
6rem    = 96px
8rem    = 128px
```

### **Application**

- **Micro gaps**: `0.25rem` (4px), `0.5rem` (8px)
- **Component padding**: `1rem`, `1.5rem`, `2rem`
- **Card padding**: `1.5rem` (24px) default, `2rem` (32px) for emphasis
- **Section margins**: `2rem`, `3rem`, `4rem`
- **Page padding**: `py-8` (32px), `py-12` (48px)

---

## 4. Component Library

### **Card Component (REQUIRED)**

```css
.card {
  background: linear-gradient(145deg, #ffffff, #fafafa);
  border-radius: 12px;
  border: 1px solid #e5e5e5;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  padding: 1.5rem;
  transition: all 0.3s ease;
  position: relative;
}

/* Subtle texture overlay */
.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(
    135deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.008) 2px,
    rgba(0, 0, 0, 0.008) 4px
  );
  pointer-events: none;
  border-radius: inherit;
}

/* SIGNATURE HOVER STATE */
.card:hover {
  border-color: #22c55e;
  box-shadow: 
    0 10px 15px -3px rgba(34, 197, 94, 0.2),
    0 4px 6px -2px rgba(34, 197, 94, 0.15);
  transform: translateY(-4px);
}
```

**Variants:**

```css
/* Strong emphasis cards (hero sections) */
.card-strong {
  border: 2px solid #000000;
  box-shadow: var(--shadow-lg);
}

/* Glass effect cards */
.card-glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
}
```

---

### **Button System (REQUIRED)**

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  font-size: 0.9375rem;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;
  white-space: nowrap;
}

/* Primary - Vibrant green */
.btn-primary {
  background: #22c55e;
  color: white;
  border-color: #22c55e;
}
.btn-primary:hover {
  background: #16a34a;
  border-color: #16a34a;
}

/* Secondary - White with black border */
.btn-secondary {
  background: white;
  color: #000000;
  border-color: #000000;
}
.btn-secondary:hover {
  background: #000000;
  color: white;
}

/* Accent - Black */
.btn-accent {
  background: #000000;
  color: white;
  border-color: #000000;
}
.btn-accent:hover {
  background: #1a1a1a;
}

/* Danger - Red */
.btn-danger {
  background: #ef4444;
  color: white;
  border-color: #ef4444;
}
.btn-danger:hover {
  background: #dc2626;
  border-color: #dc2626;
}

/* Disabled state */
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

### **Icon Badge Component**

```css
.icon-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  border-radius: 8px;
  font-size: 1.5rem; /* For emoji */
  border: 2px solid #e5e5e5;
  background: linear-gradient(145deg, #ffffff, #f8f8f8);
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition: all 0.2s ease;
}

.icon-badge:hover {
  border-color: #22c55e;
  transform: translateY(-2px);
  box-shadow: 
    0 4px 6px rgba(34, 197, 94, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}
```

**Usage:** Place emoji (🍽️, 📊, ⚡, 🎯) inside for visual anchors

---

### **Badge Component**

```css
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 6px;
  line-height: 1.2;
}

/* Variants */
.badge-success { background: #22c55e; color: white; }
.badge-warning { background: #000000; color: white; }
.badge-danger { background: #ef4444; color: white; }
.badge-info { background: #22c55e; color: white; }
```

---

### **Input Fields**

```css
.input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  font-size: 0.9375rem;
  background: white;
  transition: all 0.2s;
}

.input:focus {
  outline: none;
  border-color: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.1);
}
```

---

### **Modal/Dialog**

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.3s ease-out;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 24px;
  max-width: 900px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-2xl);
  animation: slideUp 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## 5. Motion & Interaction

### **Transition Rules**

```css
/* Default for all interactive elements */
transition: all 0.2s ease;

/* Cards and larger elements */
transition: all 0.3s ease;

/* Entrance animations */
animation: slideUp 0.3s ease-out;
```

### **Hover Behaviors (SIGNATURE)**

1. **Cards**
   
   ```css
   transform: translateY(-4px);
   border-color: #22c55e;
   box-shadow: [green-tinted shadow];
   ```

2. **Icon Badges**
   
   ```css
   transform: translateY(-2px);
   border-color: #22c55e;
   ```

3. **Buttons**
   
   ```css
   background: [darker shade];
   /* OR for secondary */
   background: #000000;
   color: white;
   ```

4. **Emoji Icons**
   
   ```css
   transform: scale(1.1) rotate(12deg);
   ```

### **Focus States**

```css
.input:focus, .btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.1);
}
```

### **Loading States**

```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.loading {
  animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

---

## 6. Layout Patterns

### **Container**

```css
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.5rem;
}
```

### **Responsive Grid**

```html
<!-- Stats/Metrics Grid -->
<div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
  <!-- Card items -->
</div>

<!-- Content + Sidebar -->
<div class="grid lg:grid-cols-3 gap-8">
  <div class="lg:col-span-2"><!-- Main content --></div>
  <div class="lg:col-span-1"><!-- Sidebar --></div>
</div>
```

### **Hero Section Pattern**

```html
<div class="bg-white border-2 border-black rounded-lg p-8 md:p-12 mb-12">
  <div class="text-center">
    <div class="icon-badge w-24 h-24 mx-auto mb-6" style="font-size: 3.75rem;">
      🎯
    </div>
    <h1 class="text-4xl md:text-6xl font-bold mb-4">
      Page Title
    </h1>
    <p class="text-lg text-gray-600">
      Subtitle or description
    </p>
  </div>
</div>
```

---

## 7. Personality Elements

### **Emoji Usage (ENCOURAGED)**

Use emoji to:

- Replace generic icons (🍽️ instead of SVG plate)
- Add warmth to metrics (📊, 💰, ⚡, 🎯)
- Signal actions (✅ success, ❌ error, ⏳ waiting)
- Create visual anchors in `.icon-badge` components

**Guidelines:**

- Use consistently (same emoji for same concept)
- Size appropriately (1.5rem for badges, 3.75rem for hero)
- Never use as sole indicator (pair with text)

### **Language Tone**

- **Friendly & Direct**: "Order Now" not "Proceed to Ordering"
- **Casual but Clear**: "Your cart is empty" not "No items in shopping basket"
- **Actionable**: "Confirm Order" not "Submit"
- **Reassuring**: "Order Confirmed!" not "Success"

---

## 8. Accessibility Requirements

### **Contrast (WCAG AA Minimum)**

- Black text on white: 21:1 (AAA) ✅
- Gray secondary text (#404040): 10.8:1 (AAA) ✅
- Green on white: 3.3:1 (AA for large text only) ✅

### **Keyboard Navigation**

- All interactive elements must be keyboard accessible
- Visible focus states (green outline)
- Logical tab order

### **Touch Targets**

- Minimum 44px x 44px for all buttons/links
- Generous padding on mobile

### **Semantic HTML**

- Proper heading hierarchy (h1 → h2 → h3)
- `<button>` for actions, `<a>` for navigation
- ARIA labels for icon-only buttons

---

## 9. Implementation Checklist

When applying this design system to a new project:

### **Setup Phase**

- [ ] Install Inter (300-900) and Poppins (400-800) fonts
- [ ] Set up CSS variables for colors and shadows
- [ ] Establish 8px spacing scale
- [ ] Configure Tailwind CSS (or equivalent utility framework)
- [ ] Set body background to `linear-gradient(to bottom, #fafafa, #f5f5f5)`

### **Component Phase**

- [ ] Create `.card` base class with texture overlay and hover state
- [ ] Create button variants (primary, secondary, accent, danger)
- [ ] Create `.icon-badge` component
- [ ] Create `.badge` variants
- [ ] Create `.input` with focus states
- [ ] Create modal/overlay components

### **Layout Phase**

- [ ] Set up responsive container
- [ ] Create responsive grid patterns
- [ ] Define breakpoints (mobile, tablet, desktop)
- [ ] Implement sticky header pattern

### **Motion Phase**

- [ ] Set default transitions (0.2s for UI, 0.3s for cards)
- [ ] Implement card hover (translateY -4px, green border, shadow)
- [ ] Implement icon badge hover (translateY -2px, green border)
- [ ] Add modal entrance animations (fadeIn, slideUp)
- [ ] Add focus state animations

### **Content Phase**

- [ ] Select appropriate emoji for each section
- [ ] Write friendly, direct copy
- [ ] Ensure proper heading hierarchy
- [ ] Add status badges for dynamic content

### **Testing Phase**

- [ ] Test keyboard navigation
- [ ] Verify color contrast ratios
- [ ] Test on mobile devices (touch targets, responsive layout)
- [ ] Verify all hover states work
- [ ] Check loading states and empty states

---

## 10. Anti-Patterns (AVOID)

❌ **Do NOT:**

- Use colors other than green for primary actions
- Use thin borders (1px) on hero sections (must be 2px black)
- Mix fonts (stick to Inter/Poppins only)
- Break 8px spacing grid
- Skip hover states on interactive elements
- Use color alone to convey meaning
- Create custom icons when emoji will work
- Add excessive decoration or gradients
- Use card shadows without the green tint on hover
- Implement dark mode (this is a light-only system)
- Use rounded corners larger than 12px (except modals at 24px)
- Add animations longer than 300ms
- Create multi-step forms when one step will do

---

## 11. Example Code Structure

### **Complete Button Example**

```html
<!-- Primary CTA -->
<button class="btn btn-primary px-8 py-4 rounded-lg text-base font-bold flex items-center gap-2">
  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
  </svg>
  <span>Confirm Order</span>
</button>
```

### **Complete Card Example**

```html
<div class="card hover:border-green-500 transition-all">
  <div class="flex items-center justify-between mb-4">
    <div class="icon-badge">
      📊
    </div>
    <div class="flex-1 ml-4">
      <p class="text-sm text-gray-600 font-semibold uppercase tracking-wide mb-1">
        Total Orders
      </p>
      <p class="text-4xl font-bold text-black">
        {{ count }}
      </p>
    </div>
  </div>
  <div class="h-1 bg-green-500 rounded"></div>
</div>
```

### **Complete Hero Section**

```html
<div class="bg-white border-2 border-black rounded-lg p-8 md:p-12 mb-12">
  <div class="text-center">
    <div class="icon-badge w-24 h-24 mx-auto mb-6" style="width: 6rem; height: 6rem; font-size: 3.75rem;">
      🎯
    </div>
    <h1 class="text-4xl md:text-6xl font-bold mb-4 text-black">
      Welcome to [App Name]
    </h1>
    <p class="text-lg text-gray-600 mb-2 font-semibold">
      Catchy subtitle here
    </p>
    <p class="text-sm text-gray-500 font-medium">
      Supporting text
    </p>
  </div>

  <!-- CTAs -->
  <div class="flex flex-col sm:flex-row gap-4 justify-center items-center mt-8">
    <a href="/action" class="btn btn-primary px-8 py-4 rounded-lg w-full sm:w-auto">
      Primary Action
    </a>
    <a href="/secondary" class="btn btn-secondary px-8 py-4 rounded-lg w-full sm:w-auto">
      Secondary Action
    </a>
  </div>
</div>
```

---

## 12. Responsive Behavior

### **Breakpoints**

```css
/* Mobile first approach */
mobile:  default (< 640px)
tablet:  md: (≥ 768px)
desktop: lg: (≥ 1024px)
wide:    xl: (≥ 1280px)
```

### **Patterns**

```html
<!-- Stacked mobile, grid desktop -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

<!-- Full width mobile, auto desktop -->
<button class="w-full sm:w-auto btn btn-primary">

<!-- Smaller text mobile, larger desktop -->
<h1 class="text-4xl md:text-6xl font-bold">

<!-- Compact padding mobile, spacious desktop -->
<div class="p-6 md:p-12">
```

---

## Summary: Design in 3 Rules

1. **Green means go, black means structure** — Use #22c55e for all primary actions and success, #000000 for emphasis and borders

2. **Everything lifts on hover** — Cards rise 4px with green borders, icon badges rise 2px, all within 200-300ms

3. **Emoji + Inter + Poppins = personality** — Food emoji for warmth, Inter for data, Poppins for headlines, always on 8px grid

---

## Quick Reference

**Primary Color:** `#22c55e` (green)  
**Accent Color:** `#000000` (black)  
**Fonts:** Inter (body), Poppins (headings)  
**Spacing:** 8px grid (0.5rem, 1rem, 1.5rem, 2rem...)  
**Transitions:** 200-300ms ease/ease-out  
**Card Hover:** translateY(-4px) + green border  
**Border Radius:** 8-12px (24px for modals)  
**Shadow Focus:** `0 0 0 3px rgba(34, 197, 94, 0.1)`  

**Emoji Library:** 🍽️ 📊 💰 ⚡ 🎯 ✅ ❌ ⏳ 📱 🛍️ 💵

---

**Apply this system consistently across all pages and components. When in doubt, prioritize clarity, speed, and user trust over decoration.**
