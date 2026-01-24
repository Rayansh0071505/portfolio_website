import { Variants } from 'framer-motion';
import { DURATIONS, EASINGS } from './constants';

/**
 * Framer Motion Animation Variants Library
 * Centralized animation configurations for consistency
 */

// Fade In Animations
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: DURATIONS.medium / 1000, ease: EASINGS.default },
  },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: DURATIONS.slow / 1000, ease: EASINGS.default },
  },
};

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: DURATIONS.slow / 1000, ease: EASINGS.default },
  },
};

export const fadeInLeft: Variants = {
  hidden: { opacity: 0, x: -40 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: DURATIONS.slow / 1000, ease: EASINGS.default },
  },
};

export const fadeInRight: Variants = {
  hidden: { opacity: 0, x: 40 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: DURATIONS.slow / 1000, ease: EASINGS.default },
  },
};

// Scale Animations
export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: DURATIONS.medium / 1000, ease: EASINGS.default },
  },
};

export const scaleInBounce: Variants = {
  hidden: { opacity: 0, scale: 0.5 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: DURATIONS.slow / 1000,
      ease: EASINGS.bounce
    },
  },
};

// Slide Animations
export const slideInUp: Variants = {
  hidden: { y: '100%' },
  visible: {
    y: 0,
    transition: { duration: DURATIONS.slow / 1000, ease: EASINGS.default },
  },
};

export const slideInDown: Variants = {
  hidden: { y: '-100%' },
  visible: {
    y: 0,
    transition: { duration: DURATIONS.slow / 1000, ease: EASINGS.default },
  },
};

// Rotate Animations
export const rotateIn: Variants = {
  hidden: { opacity: 0, rotate: -180 },
  visible: {
    opacity: 1,
    rotate: 0,
    transition: { duration: DURATIONS.slow / 1000, ease: EASINGS.default },
  },
};

// Flip Animations
export const flipIn: Variants = {
  hidden: { opacity: 0, rotateX: -90 },
  visible: {
    opacity: 1,
    rotateX: 0,
    transition: { duration: DURATIONS.slow / 1000, ease: EASINGS.default },
  },
};

// Stagger Containers
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

export const staggerFastContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

export const staggerSlowContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.3,
    },
  },
};

// Stagger Items (to be used within stagger containers)
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: DURATIONS.medium / 1000 },
  },
};

// Hero Animations
export const heroImage: Variants = {
  hidden: { opacity: 0, scale: 0.5, rotate: -10 },
  visible: {
    opacity: 1,
    scale: 1,
    rotate: 0,
    transition: {
      duration: 1,
      ease: EASINGS.default,
      delay: 0.2,
    },
  },
};

export const heroText: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: DURATIONS.slow / 1000,
      ease: EASINGS.default,
    },
  },
};

// Card Hover Animations
export const cardHover = {
  rest: { scale: 1 },
  hover: {
    scale: 1.02,
    transition: {
      duration: DURATIONS.fast / 1000,
      ease: EASINGS.default,
    },
  },
};

export const cardHoverLift = {
  rest: { scale: 1, y: 0 },
  hover: {
    scale: 1.05,
    y: -8,
    transition: {
      duration: DURATIONS.medium / 1000,
      ease: EASINGS.default,
    },
  },
};

// Button Animations
export const buttonTap = {
  scale: 0.95,
};

export const magneticButton = {
  rest: { x: 0, y: 0 },
  hover: (custom: { x: number; y: number }) => ({
    x: custom.x,
    y: custom.y,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 20,
    },
  }),
};

// Page Transitions
export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: DURATIONS.slow / 1000,
      ease: EASINGS.default,
    },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: {
      duration: DURATIONS.medium / 1000,
      ease: EASINGS.sharp,
    },
  },
};

// Utility: Create custom fade in with delay
export const createFadeIn = (delay: number = 0, duration: number = DURATIONS.medium): Variants => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      duration: duration / 1000,
      delay,
      ease: EASINGS.default,
    },
  },
});

// Utility: Create custom slide in
export const createSlideIn = (
  direction: 'up' | 'down' | 'left' | 'right',
  distance: number = 40,
  delay: number = 0
): Variants => {
  const axis = direction === 'up' || direction === 'down' ? 'y' : 'x';
  const value = direction === 'down' || direction === 'right' ? distance : -distance;

  return {
    hidden: { opacity: 0, [axis]: value },
    visible: {
      opacity: 1,
      [axis]: 0,
      transition: {
        duration: DURATIONS.slow / 1000,
        delay,
        ease: EASINGS.default,
      },
    },
  };
};
