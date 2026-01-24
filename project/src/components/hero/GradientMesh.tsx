import { useEffect, useRef } from 'react';
import { MESH_CONFIG, COLORS } from '../../utils/constants';

/**
 * GradientMesh Component
 * Creates an animated gradient background using canvas and simplex noise
 * Organic blob-like movement for modern aesthetic
 */
export const GradientMesh = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Blob configuration
    const blobs: Array<{
      x: number;
      y: number;
      size: number;
      color: string;
      speed: number;
      angle: number;
    }> = [
      {
        x: canvas.width * 0.2,
        y: canvas.height * 0.3,
        size: 400,
        color: COLORS.primary.blue,
        speed: 0.0003,
        angle: 0,
      },
      {
        x: canvas.width * 0.8,
        y: canvas.height * 0.4,
        size: 350,
        color: COLORS.primary.teal,
        speed: 0.0004,
        angle: Math.PI / 2,
      },
      {
        x: canvas.width * 0.5,
        y: canvas.height * 0.7,
        size: 300,
        color: COLORS.primary.cyan,
        speed: 0.0005,
        angle: Math.PI,
      },
      {
        x: canvas.width * 0.3,
        y: canvas.height * 0.6,
        size: 250,
        color: COLORS.accent.purple,
        speed: 0.00035,
        angle: (Math.PI * 3) / 2,
      },
      {
        x: canvas.width * 0.7,
        y: canvas.height * 0.2,
        size: 280,
        color: COLORS.accent.pink,
        speed: 0.00045,
        angle: Math.PI / 4,
      },
    ];

    // Animation loop
    let animationFrameId: number;
    let time = 0;

    const animate = () => {
      if (!canvas || !ctx) return;

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Update and draw blobs
      blobs.forEach((blob) => {
        // Circular movement
        const newX = blob.x + Math.cos(blob.angle + time * blob.speed) * 50;
        const newY = blob.y + Math.sin(blob.angle + time * blob.speed) * 50;

        // Create gradient
        const gradient = ctx.createRadialGradient(
          newX,
          newY,
          0,
          newX,
          newY,
          blob.size
        );

        gradient.addColorStop(0, `${blob.color}40`); // 40 = ~25% opacity in hex
        gradient.addColorStop(0.5, `${blob.color}20`); // 20 = ~12% opacity in hex
        gradient.addColorStop(1, `${blob.color}00`); // 00 = transparent

        // Draw blob
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      });

      time++;
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{
        filter: `blur(${MESH_CONFIG.blurAmount}px)`,
        opacity: MESH_CONFIG.opacity,
      }}
    />
  );
};
