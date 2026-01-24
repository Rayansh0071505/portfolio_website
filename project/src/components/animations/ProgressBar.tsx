import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

interface ProgressBarProps {
  percentage: number;
  label?: string;
  color?: 'blue' | 'teal' | 'cyan' | 'purple' | 'pink';
  height?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
  className?: string;
  once?: boolean;
}

/**
 * ProgressBar Component
 * Animated progress bar for skills or stats
 * Animates when entering viewport
 */
export const ProgressBar = ({
  percentage,
  label,
  color = 'blue',
  height = 'md',
  showPercentage = true,
  className = '',
  once = true,
}: ProgressBarProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once, margin: '-50px' });

  const colorClasses = {
    blue: 'bg-gradient-to-r from-blue-500 to-blue-600',
    teal: 'bg-gradient-to-r from-teal-500 to-teal-600',
    cyan: 'bg-gradient-to-r from-cyan-500 to-cyan-600',
    purple: 'bg-gradient-to-r from-purple-500 to-purple-600',
    pink: 'bg-gradient-to-r from-pink-500 to-pink-600',
  };

  const heightClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div ref={ref} className={`w-full ${className}`}>
      {/* Label and Percentage */}
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-sm text-slate-300">{label}</span>}
          {showPercentage && (
            <motion.span
              className="text-sm text-slate-400 font-medium"
              initial={{ opacity: 0 }}
              animate={{ opacity: isInView ? 1 : 0 }}
              transition={{ delay: 0.5 }}
            >
              {percentage}%
            </motion.span>
          )}
        </div>
      )}

      {/* Progress Bar Background */}
      <div className={`w-full bg-slate-800/50 rounded-full overflow-hidden ${heightClasses[height]}`}>
        {/* Progress Bar Fill */}
        <motion.div
          className={`${heightClasses[height]} ${colorClasses[color]} rounded-full shadow-lg`}
          style={{
            boxShadow: `0 0 20px ${color === 'blue' ? 'rgba(59, 130, 246, 0.4)' :
                                   color === 'teal' ? 'rgba(20, 184, 166, 0.4)' :
                                   color === 'cyan' ? 'rgba(6, 182, 212, 0.4)' :
                                   color === 'purple' ? 'rgba(139, 92, 246, 0.4)' :
                                   'rgba(236, 72, 153, 0.4)'}`,
          }}
          initial={{ width: 0 }}
          animate={{ width: isInView ? `${percentage}%` : 0 }}
          transition={{
            duration: 1.5,
            ease: 'easeOut',
            delay: 0.2,
          }}
        />
      </div>
    </div>
  );
};
