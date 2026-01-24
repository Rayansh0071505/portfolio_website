import { motion, useScroll, useTransform } from 'framer-motion';
import { ReactNode, useRef } from 'react';

interface ParallaxSectionProps {
  children: ReactNode;
  speed?: number; // 0.5 = slower, 1 = normal, 2 = faster
  className?: string;
}

/**
 * ParallaxSection Component
 * Creates parallax scrolling effect for backgrounds or elements
 * Speed < 1 = slower than scroll, Speed > 1 = faster than scroll
 */
export const ParallaxSection = ({
  children,
  speed = 0.5,
  className = '',
}: ParallaxSectionProps) => {
  const ref = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end start'],
  });

  // Transform scroll progress to Y translation
  // Negative values for upward movement as you scroll down
  const y = useTransform(scrollYProgress, [0, 1], [0, (speed - 1) * 100]);

  return (
    <motion.div ref={ref} style={{ y }} className={className}>
      {children}
    </motion.div>
  );
};
