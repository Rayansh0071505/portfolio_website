import { useScroll, useSpring, motion } from 'framer-motion';
import { Z_INDEX } from '../../utils/constants';

/**
 * Scroll Progress Indicator
 * Shows page scroll progress with a gradient bar at the top
 */
export const ScrollProgress = () => {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });

  return (
    <motion.div
      className="fixed top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-teal-500 to-cyan-500 origin-left"
      style={{ scaleX, zIndex: Z_INDEX.scrollProgress }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
    />
  );
};
