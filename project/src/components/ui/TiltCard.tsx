import { ReactNode, useRef, useState, MouseEvent } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

interface TiltCardProps {
  children: ReactNode;
  className?: string;
  tiltMaxAngle?: number;
  perspective?: number;
  scale?: number;
  glare?: boolean;
  maxGlare?: number;
}

/**
 * TiltCard Component
 * Custom 3D tilt effect using Framer Motion
 * Responds to mouse movement with perspective transforms
 */
export const TiltCard = ({
  children,
  className = '',
  tiltMaxAngle = 10,
  scale = 1.02,
}: TiltCardProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;

    const rect = ref.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateXValue = ((y - centerY) / centerY) * -tiltMaxAngle;
    const rotateYValue = ((x - centerX) / centerX) * tiltMaxAngle;

    setRotateX(rotateXValue);
    setRotateY(rotateYValue);
  };

  const handleMouseLeave = () => {
    setRotateX(0);
    setRotateY(0);
  };

  return (
    <motion.div
      ref={ref}
      className={cn('tilt-card', className)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={{
        rotateX,
        rotateY,
      }}
      whileHover={{ scale }}
      transition={{
        type: 'spring',
        stiffness: 400,
        damping: 30,
      }}
      style={{
        transformStyle: 'preserve-3d',
        perspective: 1000,
      }}
    >
      {children}
    </motion.div>
  );
};
