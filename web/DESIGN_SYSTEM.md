# Koroh Design System

This document outlines the consistent design system used across the Koroh platform.

## Color Palette

### Primary Colors (Teal-based)
- **Primary 600** (`teal-600`): `#0D9488` - Main brand color
- **Primary 700** (`teal-700`): `#0F766E` - Hover states for primary elements
- **Primary 50** (`teal-50`): `#F0FDFA` - Light backgrounds and subtle highlights

### Secondary Colors (Blue-based)
- **Secondary 500** (`blue-500`): `#3B82F6` - Used in gradients and accents
- **Secondary 600** (`blue-600`): `#2563EB` - Secondary actions

### Neutral Colors
- **Gray 900** (`gray-900`): `#111827` - Primary text
- **Gray 700** (`gray-700`): `#374151` - Secondary text
- **Gray 600** (`gray-600`): `#4B5563` - Body text
- **Gray 500** (`gray-500`): `#6B7280` - Muted text
- **Gray 200** (`gray-200`): `#E5E7EB` - Borders
- **Gray 50** (`gray-50`): `#F9FAFB` - Light backgrounds

## Typography

### Headings
- **Main Headings**: `font-bold text-gray-900`
- **Section Headings**: `font-semibold text-gray-700`
- **Accent Text**: `text-teal-600`

### Body Text
- **Primary**: `text-gray-600`
- **Muted**: `text-gray-500`

## Components

### Navigation
- **Brand Logo**: `text-2xl font-bold text-teal-600`
- **Navigation Links**: `text-gray-700 hover:text-teal-600 font-medium transition-colors duration-200`
- **Background**: `bg-white border-b border-gray-200 sticky top-0 z-50`

### Buttons
- **Primary**: `bg-teal-600 hover:bg-teal-700 text-white font-medium rounded-lg transition-colors duration-200`
- **Secondary**: `bg-white hover:bg-gray-50 text-teal-600 border border-teal-600 font-medium rounded-lg transition-colors duration-200`
- **Ghost**: `bg-transparent hover:bg-teal-50 text-teal-600 font-medium rounded-lg transition-colors duration-200`

### Backgrounds
- **Primary**: `bg-white`
- **Secondary**: `bg-gray-50`
- **Accent**: `bg-gradient-to-br from-teal-50 to-blue-50`
- **Dark**: `bg-gray-900`

## Layout Patterns

### Public Pages Structure
```
<PublicNavigation />
<main>
  <!-- Page content -->
</main>
<PublicFooter />
```

### Auth Pages Structure
```
<div className="min-h-screen bg-gradient-to-br from-teal-50 to-blue-50 flex flex-col">
  <PublicNavigation currentPage="login|register" />
  <div className="flex-1 flex flex-col justify-center">
    <!-- Auth form content -->
  </div>
  <PublicFooter />
</div>
```

## Reusable Components

### PublicNavigation
- **Props**: `showAuthButtons?: boolean`, `currentPage?: 'home' | 'login' | 'register'`
- **Usage**: Consistent navigation across all public pages
- **Features**: 
  - Shows all navigation links (Jobs, Companies, Networking, Insights) on every page
  - Responsive mobile menu with collapsible navigation
  - Conditional auth buttons based on current page
  - Links to homepage sections from any page (using `/#section` format)

### PublicFooter
- **Usage**: Consistent footer across all public pages
- **Features**: Company links, social media, copyright

## Usage Guidelines

1. **Import the design system**: `import { cssClasses } from '@/lib/design-system'`
2. **Use consistent colors**: Always use the predefined color classes
3. **Maintain spacing**: Use consistent padding and margins
4. **Responsive design**: Ensure all components work on mobile, tablet, and desktop
5. **Accessibility**: Maintain proper contrast ratios and semantic HTML

## File Structure

```
web/
├── lib/
│   └── design-system.ts          # Color definitions and CSS classes
├── components/
│   └── layout/
│       ├── public-navigation.tsx # Reusable navigation
│       └── public-footer.tsx     # Reusable footer
└── app/
    ├── page.tsx                  # Homepage
    └── auth/
        ├── login/page.tsx        # Login page
        └── register/page.tsx     # Register page
```

## Benefits

1. **Consistency**: All pages use the same color scheme and components
2. **Maintainability**: Changes to colors or styles can be made in one place
3. **Reusability**: Navigation and footer components are shared across pages
4. **Responsive**: All components adapt to different screen sizes
5. **Accessibility**: Consistent focus states and color contrast
6. **Performance**: Shared components reduce bundle size