import { useCallback } from 'react';
import Particles from '@tsparticles/react';
import { loadSlim } from '@tsparticles/slim';
import type { Engine } from '@tsparticles/engine';
import { PARTICLE_CONFIG, COLORS } from '../../utils/constants';
import { useIsMobile } from '../../hooks/useMediaQuery';

/**
 * ParticleBackground Component
 * Interactive particle system with connections
 * Reduces complexity on mobile devices for performance
 */
export const ParticleBackground = () => {
  const isMobile = useIsMobile();
  const config = isMobile ? PARTICLE_CONFIG.mobile : PARTICLE_CONFIG.desktop;

  const particlesInit = useCallback(async (engine: Engine) => {
    await loadSlim(engine);
  }, []);

  return (
    <Particles
      id="tsparticles"
      init={particlesInit}
      options={{
        background: {
          color: {
            value: 'transparent',
          },
        },
        fpsLimit: 60,
        interactivity: {
          events: {
            onHover: {
              enable: !isMobile,
              mode: 'grab',
            },
            resize: {
              enable: true,
            },
          },
          modes: {
            grab: {
              distance: 140,
              links: {
                blink: false,
                consent: false,
                opacity: 0.5,
              },
            },
          },
        },
        particles: {
          color: {
            value: [COLORS.primary.blue, COLORS.primary.teal, COLORS.primary.cyan],
          },
          links: {
            color: COLORS.primary.teal,
            distance: 150,
            enable: true,
            opacity: 0.3,
            width: 1,
          },
          move: {
            direction: 'none',
            enable: true,
            outModes: {
              default: 'bounce',
            },
            random: false,
            speed: config.speed,
            straight: false,
          },
          number: {
            density: {
              enable: true,
            },
            value: config.count,
          },
          opacity: {
            value: { min: 0.1, max: 0.5 },
            animation: {
              enable: true,
              speed: 0.5,
              sync: false,
            },
          },
          shape: {
            type: 'circle',
          },
          size: {
            value: { min: 1, max: 3 },
          },
        },
        detectRetina: true,
      }}
      className="absolute inset-0 w-full h-full pointer-events-none"
    />
  );
};
