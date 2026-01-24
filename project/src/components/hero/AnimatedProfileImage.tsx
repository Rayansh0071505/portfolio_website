import { motion } from 'framer-motion';
import { heroImage } from '../../utils/animations';

/**
 * AnimatedProfileImage Component
 * Professional circular profile image with static gradient border
 * Clean and elegant appearance
 */
export const AnimatedProfileImage = () => {
  return (
    <motion.div
      className="relative w-64 h-64 md:w-80 md:h-80 mx-auto"
      variants={heroImage}
      initial="hidden"
      animate="visible"
    >
      {/* Static Gradient Border (No rotation) */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-br from-blue-500 via-blue-600 to-cyan-500 p-1">
        {/* Inner container */}
        <div className="relative w-full h-full rounded-full bg-slate-950 p-2">
          {/* Subtle Glow effect */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 blur-2xl animate-glow-pulse" />

          {/* Profile Image */}
          <img
            src="/edit.jpg"
            alt="Rayansh Srivastava"
            className="relative w-full h-full rounded-full object-cover shadow-2xl"
          />

          {/* Subtle shine overlay */}
          <div className="absolute inset-0 rounded-full overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent" />
          </div>
        </div>
      </div>
    </motion.div>
  );
};
