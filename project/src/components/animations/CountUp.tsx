import { useEffect, useRef, useState } from 'react';
import { motion, useSpring, useInView } from 'framer-motion';

interface CountUpProps {
  end: number;
  start?: number;
  duration?: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  className?: string;
  once?: boolean;
}

/**
 * CountUp Component
 * Animates numbers counting up from start to end
 * Triggers when element enters viewport
 */
export const CountUp = ({
  end,
  start = 0,
  duration = 2,
  decimals = 0,
  suffix = '',
  prefix = '',
  className = '',
  once = true,
}: CountUpProps) => {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once });
  const [displayValue, setDisplayValue] = useState(start);

  const springValue = useSpring(start, {
    stiffness: 50,
    damping: 30,
    duration: duration * 1000,
  });

  useEffect(() => {
    if (isInView) {
      springValue.set(end);
    }
  }, [isInView, springValue, end]);

  useEffect(() => {
    const unsubscribe = springValue.on('change', (latest) => {
      setDisplayValue(latest);
    });

    return () => unsubscribe();
  }, [springValue]);

  return (
    <motion.span ref={ref} className={className}>
      {prefix}
      {displayValue.toFixed(decimals)}
      {suffix}
    </motion.span>
  );
};
