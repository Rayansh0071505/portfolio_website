import { motion, Variants } from 'framer-motion';
import { ReactNode } from 'react';
import { fadeInUp, fadeInDown, fadeInLeft, fadeInRight } from '../../utils/animations';

interface FadeInViewProps {
  children: ReactNode;
  direction?: 'up' | 'down' | 'left' | 'right';
  delay?: number;
  duration?: number;
  className?: string;
  once?: boolean;
}

/**
 * FadeInView Component
 * Wrapper that fades in content when it enters viewport
 * Supports different slide directions
 */
export const FadeInView = ({
  children,
  direction = 'up',
  delay = 0,
  duration = 0.8,
  className = '',
  once = true,
}: FadeInViewProps) => {
  const getVariant = (): Variants => {
    const variants = {
      up: fadeInUp,
      down: fadeInDown,
      left: fadeInLeft,
      right: fadeInRight,
    };
    return variants[direction];
  };

  const variant = getVariant();

  // Create custom variant with delay and duration
  const customVariant: Variants = {
    hidden: variant.hidden,
    visible: {
      ...variant.visible,
      transition: {
        duration,
        delay,
        ease: 'easeOut',
      },
    },
  };

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once, margin: '-100px' }}
      variants={customVariant}
      className={className}
    >
      {children}
    </motion.div>
  );
};
