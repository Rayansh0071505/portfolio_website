/**
 * Design System Constants
 * Centralized constants for colors, durations, breakpoints, and configuration
 */

// Color Palette
export const COLORS = {
  primary: {
    blue: '#3b82f6',
    teal: '#14b8a6',
    cyan: '#06b6d4',
  },
  accent: {
    purple: '#8b5cf6',
    pink: '#ec4899',
  },
  background: {
    dark: '#020617', // slate-950
    mid: '#0f172a', // slate-900
    light: '#1e293b', // slate-800
  },
  text: {
    primary: '#f1f5f9', // slate-100
    secondary: '#cbd5e1', // slate-300
    muted: '#94a3b8', // slate-400
  },
} as const;

// Animation Durations (in milliseconds)
export const DURATIONS = {
  fast: 200,
  medium: 400,
  slow: 800,
  verySlow: 1200,
} as const;

// Animation Easings
export const EASINGS = {
  default: 'ease-out',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  smooth: 'ease-in-out',
  sharp: 'ease-in',
} as const;

// Breakpoints (in pixels)
export const BREAKPOINTS = {
  mobile: 375,
  mobileLarge: 428,
  tablet: 768,
  tabletLarge: 1024,
  desktop: 1280,
  desktopLarge: 1440,
  wide: 1920,
} as const;

// Particle Configuration
export const PARTICLE_CONFIG = {
  desktop: {
    count: 150,
    speed: 1,
    connections: 3,
  },
  mobile: {
    count: 50,
    speed: 0.5,
    connections: 2,
  },
} as const;

// Spring Configurations
export const SPRING_CONFIG = {
  default: { stiffness: 300, damping: 20 },
  gentle: { stiffness: 200, damping: 25 },
  bouncy: { stiffness: 400, damping: 15 },
  stiff: { stiffness: 500, damping: 30 },
} as const;

// Magnetic Button Configuration
export const MAGNETIC_STRENGTH = {
  weak: 0.3,
  medium: 0.5,
  strong: 0.8,
} as const;

export const MAGNETIC_RADIUS = 100; // pixels

// Gradient Mesh Configuration
export const MESH_CONFIG = {
  blobCount: 5,
  noiseScale: 0.002,
  animationSpeed: 0.0005,
  blurAmount: 60,
  opacity: 0.4,
} as const;

// Typewriter Configuration
export const TYPEWRITER_CONFIG = {
  typingSpeed: 100, // ms per character
  deletingSpeed: 50, // ms per character
  pauseDuration: 2000, // ms pause before deleting
  cursorBlinkSpeed: 530, // ms
} as const;

// Z-Index Layers
export const Z_INDEX = {
  background: -1,
  content: 0,
  floatingNav: 40,
  scrollProgress: 50,
  cursor: 100,
} as const;
