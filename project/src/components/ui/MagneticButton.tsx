import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { ReactNode, useRef, MouseEvent } from 'react';
import { MAGNETIC_RADIUS, SPRING_CONFIG } from '../../utils/constants';
import { cn } from '../../utils/cn';

interface MagneticButtonProps {
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  strength?: number;
  className?: string;
}

/**
 * MagneticButton Component
 * Button that follows cursor within a magnetic field radius
 * Includes smooth spring animations and multiple variants
 */
export const MagneticButton = ({
  children,
  href,
  onClick,
  variant = 'primary',
  strength = 0.5,
  className = '',
}: MagneticButtonProps) => {
  const ref = useRef<HTMLButtonElement | HTMLAnchorElement>(null);

  // Motion values for button position
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  // Spring physics for smooth movement
  const springX = useSpring(x, SPRING_CONFIG.default);
  const springY = useSpring(y, SPRING_CONFIG.default);

  const handleMouseMove = (e: MouseEvent<HTMLButtonElement | HTMLAnchorElement>) => {
    if (!ref.current) return;

    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const distanceX = e.clientX - centerX;
    const distanceY = e.clientY - centerY;
    const distance = Math.sqrt(distanceX ** 2 + distanceY ** 2);

    // Only apply magnetic effect within radius
    if (distance < MAGNETIC_RADIUS) {
      x.set(distanceX * strength);
      y.set(distanceY * strength);
    }
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  // Variant styles
  const variantClasses = {
    primary: 'bg-gradient-to-r from-blue-500 to-teal-500 text-white shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50',
    secondary: 'bg-transparent border-2 border-blue-500 text-blue-400 hover:bg-blue-500/10 hover:border-blue-400',
    ghost: 'bg-slate-800/50 text-slate-300 hover:bg-slate-800/70 hover:text-white',
  };

  const baseClasses = 'relative px-8 py-4 rounded-lg font-medium transition-all duration-300 cursor-pointer overflow-hidden group';

  const Tag = href ? motion.a : motion.button;

  return (
    <Tag
      ref={ref as any}
      href={href}
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        x: springX,
        y: springY,
      }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={cn(baseClasses, variantClasses[variant], className, 'cursor-hover')}
    >
      {/* Ripple effect on hover */}
      <span className="absolute inset-0 overflow-hidden rounded-lg">
        <span className="absolute inset-0 bg-white/20 transform scale-0 group-hover:scale-100 transition-transform duration-500 rounded-full" />
      </span>

      {/* Content */}
      <span className="relative z-10">{children}</span>
    </Tag>
  );
};
