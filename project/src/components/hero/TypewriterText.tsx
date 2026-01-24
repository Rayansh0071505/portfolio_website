import { motion } from 'framer-motion';
import { useTypewriter } from '../../hooks/useTypewriter';

interface TypewriterTextProps {
  words: string[];
  className?: string;
}

/**
 * TypewriterText Component
 * Animated typewriter effect that cycles through words
 * Includes blinking cursor
 */
export const TypewriterText = ({ words, className = '' }: TypewriterTextProps) => {
  const { text } = useTypewriter({ words, loop: true });

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="text-gradient from-blue-400 via-teal-400 to-cyan-400 font-display font-bold"
      >
        {text}
      </motion.span>
      <motion.span
        className="ml-1 w-0.5 h-8 md:h-12 bg-teal-400 animate-cursor-blink"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      />
    </div>
  );
};
