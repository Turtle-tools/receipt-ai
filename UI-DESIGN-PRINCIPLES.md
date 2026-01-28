# UI Design Principles for Receipt AI

**Goal:** Create an interface that is extremely easy to use and aesthetically pleasing.

---

## Core Design Laws (from lawsofux.com)

### 1. Aesthetic-Usability Effect
> "Users perceive aesthetically pleasing design as more usable."

**Apply:**
- Clean, modern visual design
- Consistent color palette
- Professional typography
- Subtle shadows and depth
- White space is our friend

### 2. Hick's Law
> "Decision time increases with choices."

**Apply:**
- One primary action per screen
- Limit options - don't overwhelm
- Progressive disclosure
- Smart defaults

### 3. Fitts's Law
> "Larger, closer targets are easier to hit."

**Apply:**
- Big, obvious buttons
- Adequate touch targets (44px minimum)
- Primary actions in thumb-reach zones (mobile)
- Important buttons at corners/edges

### 4. Jakob's Law
> "Users prefer your site to work like others they know."

**Apply:**
- Standard UI patterns
- Expected placement (logo top-left, CTA top-right)
- Familiar icons
- Conventional workflows

### 5. Doherty Threshold
> "Productivity soars at <400ms response."

**Apply:**
- Instant feedback on all actions
- Loading states and progress indicators
- Optimistic UI updates
- Skeleton screens while loading

### 6. Law of Proximity
> "Close elements are perceived as grouped."

**Apply:**
- Group related controls
- Clear visual separation between sections
- Consistent spacing system

### 7. Cognitive Load
> "Minimize mental effort required."

**Apply:**
- Simple, clear language
- One task at a time
- Remember user preferences
- Auto-fill when possible

---

## Receipt AI Specific Design

### Primary User Flow
```
Upload → Extract → Review → Push to QBO
```

Each step should be:
- Obvious (what do I do?)
- Simple (how do I do it?)
- Satisfying (that felt good!)

### Upload Experience

**DO:**
- Large, obvious drop zone
- Drag-and-drop + click to upload
- Clear file type hints
- Instant preview after drop
- Fun micro-animation on drop

**DON'T:**
- Hidden upload button
- Confusing file picker
- No feedback after upload

### Extraction Review

**DO:**
- Side-by-side: Document | Extracted Data
- Editable fields with inline validation
- Confidence indicators (green = high, yellow = review)
- One-click corrections
- Auto-suggestions for vendors/categories

**DON'T:**
- Long forms
- Separate pages for each field
- No context of original document

### QBO Push

**DO:**
- One-click "Push to QuickBooks"
- Clear success confirmation
- Link to view in QBO
- Undo option (if possible)

**DON'T:**
- Multiple confirmation dialogs
- Confusing options
- No feedback on success

---

## Color Palette

```css
/* Primary - Trust & Action */
--primary: #2563eb;      /* Blue */
--primary-hover: #1d4ed8;

/* Success - Completion */
--success: #16a34a;      /* Green */

/* Warning - Attention */
--warning: #f59e0b;      /* Amber */

/* Error - Problems */
--error: #dc2626;        /* Red */

/* Neutral - Text & Background */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-500: #6b7280;
--gray-700: #374151;
--gray-900: #111827;
```

## Typography

```css
/* Font Stack */
font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Scale */
--text-xs: 0.75rem;   /* 12px - Labels */
--text-sm: 0.875rem;  /* 14px - Body small */
--text-base: 1rem;    /* 16px - Body */
--text-lg: 1.125rem;  /* 18px - Subheadings */
--text-xl: 1.25rem;   /* 20px - Headings */
--text-2xl: 1.5rem;   /* 24px - Page titles */
```

## Spacing System

```css
/* 4px base unit */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
```

## Component Patterns

### Buttons
- Primary: Solid blue, white text
- Secondary: White with border
- Destructive: Red for delete actions
- All buttons: 44px minimum height, rounded corners

### Cards
- White background
- Subtle shadow (shadow-sm)
- Rounded corners (rounded-lg)
- Consistent padding (p-6)

### Forms
- Large inputs (h-12)
- Clear labels above
- Helpful placeholder text
- Inline validation

### Empty States
- Friendly illustration
- Clear call-to-action
- Helpful suggestion

---

## Micro-interactions

### Upload Drop
- Border color change on dragover
- Subtle scale animation
- Success checkmark animation

### Button Click
- Scale down slightly (0.98)
- Smooth color transition

### Loading
- Skeleton screens (not spinners)
- Progress bars for longer operations
- Pulse animation for processing

### Success
- Green checkmark animation
- Confetti for major achievements (first upload, first push)

---

## Mobile Considerations

- Touch targets: 44px minimum
- Thumb-friendly button placement
- Collapsible sections
- Native-feeling gestures
- Consider camera upload flow

---

## Accessibility

- WCAG 2.1 AA compliance
- Color contrast 4.5:1 minimum
- Keyboard navigation
- Screen reader labels
- Focus indicators

---

*"Design is not just what it looks like. Design is how it works." — Steve Jobs*
