import { motion, Variants } from 'framer-motion';
import { ReactNode } from 'react';
import { staggerContainer, staggerItem } from '../../utils/animations';

interface StaggerContainerProps {
  children: ReactNode;
  staggerDelay?: number;
  delayChildren?: number;
  className?: string;
  once?: boolean;
}

/**
 * StaggerContainer Component
 * Animates children with staggered timing
 * Children should be wrapped in StaggerItem components
 */
export const StaggerContainer = ({
  children,
  staggerDelay = 0.1,
  delayChildren = 0.2,
  className = '',
  once = true,
}: StaggerContainerProps) => {
  const customVariant: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: staggerDelay,
        delayChildren,
      },
    },
  };

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once, margin: '-50px' }}
      variants={customVariant}
      className={className}
    >
      {children}
    </motion.div>
  );
};

interface StaggerItemProps {
  children: ReactNode;
  className?: string;
}

/**
 * StaggerItem Component
 * Individual item within a StaggerContainer
 */
export const StaggerItem = ({ children, className = '' }: StaggerItemProps) => {
  return (
    <motion.div variants={staggerItem} className={className}>
      {children}
    </motion.div>
  );
};
