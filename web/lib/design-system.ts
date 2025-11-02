/**
 * Koroh Design System
 * Consistent colors, spacing, and design tokens across the application
 */

export const colors = {
  // Primary brand colors (teal-based)
  primary: {
    50: 'rgb(240 253 250)',   // teal-50
    100: 'rgb(204 251 241)',  // teal-100
    200: 'rgb(153 246 228)',  // teal-200
    300: 'rgb(94 234 212)',   // teal-300
    400: 'rgb(45 212 191)',   // teal-400
    500: 'rgb(20 184 166)',   // teal-500
    600: 'rgb(13 148 136)',   // teal-600 - Main brand color
    700: 'rgb(15 118 110)',   // teal-700
    800: 'rgb(17 94 89)',     // teal-800
    900: 'rgb(19 78 74)',     // teal-900
  },
  
  // Secondary colors (blue-based for gradients and accents)
  secondary: {
    50: 'rgb(239 246 255)',   // blue-50
    100: 'rgb(219 234 254)',  // blue-100
    200: 'rgb(191 219 254)',  // blue-200
    300: 'rgb(147 197 253)',  // blue-300
    400: 'rgb(96 165 250)',   // blue-400
    500: 'rgb(59 130 246)',   // blue-500
    600: 'rgb(37 99 235)',    // blue-600
    700: 'rgb(29 78 216)',    // blue-700
    800: 'rgb(30 64 175)',    // blue-800
    900: 'rgb(30 58 138)',    // blue-900
  },
  
  // Neutral colors
  neutral: {
    50: 'rgb(249 250 251)',   // gray-50
    100: 'rgb(243 244 246)',  // gray-100
    200: 'rgb(229 231 235)',  // gray-200
    300: 'rgb(209 213 219)',  // gray-300
    400: 'rgb(156 163 175)',  // gray-400
    500: 'rgb(107 114 128)',  // gray-500
    600: 'rgb(75 85 99)',     // gray-600
    700: 'rgb(55 65 81)',     // gray-700
    800: 'rgb(31 41 55)',     // gray-800
    900: 'rgb(17 24 39)',     // gray-900
  },
  
  // Status colors
  success: {
    500: 'rgb(34 197 94)',    // green-500
    600: 'rgb(22 163 74)',    // green-600
  },
  
  warning: {
    500: 'rgb(245 158 11)',   // amber-500
    600: 'rgb(217 119 6)',    // amber-600
  },
  
  error: {
    500: 'rgb(239 68 68)',    // red-500
    600: 'rgb(220 38 38)',    // red-600
  },
  
  // Special colors for gradients and highlights
  gradient: {
    from: 'rgb(20 184 166)',  // teal-500
    to: 'rgb(59 130 246)',    // blue-500
  }
} as const;

export const spacing = {
  xs: '0.5rem',    // 8px
  sm: '0.75rem',   // 12px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
  '3xl': '4rem',   // 64px
} as const;

export const borderRadius = {
  sm: '0.375rem',  // 6px
  md: '0.5rem',    // 8px
  lg: '0.75rem',   // 12px
  xl: '1rem',      // 16px
  '2xl': '1.5rem', // 24px
} as const;

export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
} as const;

// CSS class utilities for consistent styling
export const cssClasses = {
  // Primary button styles
  button: {
    primary: 'bg-teal-600 hover:bg-teal-700 text-white font-medium rounded-lg transition-colors duration-200',
    secondary: 'bg-white hover:bg-gray-50 text-teal-600 border border-teal-600 font-medium rounded-lg transition-colors duration-200',
    ghost: 'bg-transparent hover:bg-teal-50 text-teal-600 font-medium rounded-lg transition-colors duration-200',
  },
  
  // Text styles
  text: {
    heading: 'font-bold text-gray-900',
    subheading: 'font-semibold text-gray-700',
    body: 'text-gray-600',
    muted: 'text-gray-500',
    accent: 'text-teal-600',
  },
  
  // Background styles
  background: {
    primary: 'bg-white',
    secondary: 'bg-gray-50',
    accent: 'bg-gradient-to-br from-teal-50 to-blue-50',
    dark: 'bg-gray-900',
  },
  
  // Navigation styles
  nav: {
    container: 'bg-white border-b border-gray-200 sticky top-0 z-50',
    link: 'text-gray-700 hover:text-teal-600 font-medium transition-colors duration-200',
    brand: 'text-2xl font-bold text-teal-600',
  }
} as const;