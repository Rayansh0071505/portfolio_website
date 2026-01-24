import { useState, useEffect } from 'react';

type ScrollDirection = 'up' | 'down' | null;

/**
 * Custom hook to detect scroll direction
 * Returns 'up', 'down', or null
 */
export const useScrollDirection = (threshold: number = 10): ScrollDirection => {
  const [scrollDirection, setScrollDirection] = useState<ScrollDirection>(null);

  useEffect(() => {
    let lastScrollY = window.scrollY;
    let ticking = false;

    const updateScrollDirection = () => {
      const scrollY = window.scrollY;

      if (Math.abs(scrollY - lastScrollY) < threshold) {
        ticking = false;
        return;
      }

      setScrollDirection(scrollY > lastScrollY ? 'down' : 'up');
      lastScrollY = scrollY > 0 ? scrollY : 0;
      ticking = false;
    };

    const onScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(updateScrollDirection);
        ticking = true;
      }
    };

    window.addEventListener('scroll', onScroll);

    return () => window.removeEventListener('scroll', onScroll);
  }, [threshold]);

  return scrollDirection;
};
