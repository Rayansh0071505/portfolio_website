import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useMousePosition } from '../../hooks/useMousePosition';
import { useIsMobile } from '../../hooks/useMediaQuery';
import { Z_INDEX } from '../../utils/constants';

/**
 * Custom Cursor Component
 * Large ring cursor with small dot that follows mouse movement
 * Includes hover states for interactive elements
 */
export const CustomCursor = () => {
  const { x, y } = useMousePosition();
  const isMobile = useIsMobile();
  const [isHovering, setIsHovering] = useState(false);
  const [isClicking, setIsClicking] = useState(false);

  useEffect(() => {
    // Add hover detection for interactive elements
    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'A' ||
        target.tagName === 'BUTTON' ||
        target.classList.contains('cursor-hover') ||
        target.closest('a') ||
        target.closest('button')
      ) {
        setIsHovering(true);
      }
    };

    const handleMouseOut = () => {
      setIsHovering(false);
    };

    const handleMouseDown = () => {
      setIsClicking(true);
    };

    const handleMouseUp = () => {
      setIsClicking(false);
    };

    document.addEventListener('mouseover', handleMouseOver);
    document.addEventListener('mouseout', handleMouseOut);
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mouseover', handleMouseOver);
      document.removeEventListener('mouseout', handleMouseOut);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  // Don't render cursor on mobile/touch devices
  if (isMobile) return null;

  return (
    <div className="pointer-events-none fixed inset-0" style={{ zIndex: Z_INDEX.cursor }}>
      {/* Outer Ring */}
      <motion.div
        className="fixed top-0 left-0 rounded-full border-2 mix-blend-difference"
        style={{
          width: isHovering ? 60 : 40,
          height: isHovering ? 60 : 40,
          borderColor: isHovering ? '#14b8a6' : '#3b82f6',
          x: x - (isHovering ? 30 : 20),
          y: y - (isHovering ? 30 : 20),
        }}
        animate={{
          scale: isClicking ? 0.8 : 1,
          opacity: isHovering ? 0.8 : 0.6,
        }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 28,
          mass: 0.5,
        }}
      />

      {/* Inner Dot */}
      <motion.div
        className="fixed top-0 left-0 rounded-full bg-white mix-blend-difference"
        style={{
          width: isHovering ? 8 : 6,
          height: isHovering ? 8 : 6,
          x: x - (isHovering ? 4 : 3),
          y: y - (isHovering ? 4 : 3),
        }}
        animate={{
          scale: isClicking ? 0.5 : 1,
        }}
        transition={{
          type: 'spring',
          stiffness: 1000,
          damping: 40,
        }}
      />
    </div>
  );
};
