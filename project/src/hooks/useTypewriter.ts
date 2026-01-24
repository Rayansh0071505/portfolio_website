import { useState, useEffect, useRef } from 'react';
import { TYPEWRITER_CONFIG } from '../utils/constants';

interface TypewriterOptions {
  words: string[];
  loop?: boolean;
  typingSpeed?: number;
  deletingSpeed?: number;
  pauseDuration?: number;
}

/**
 * Custom hook for typewriter effect
 * Cycles through an array of words with typing animation
 */
export const useTypewriter = ({
  words,
  loop = true,
  typingSpeed = TYPEWRITER_CONFIG.typingSpeed,
  deletingSpeed = TYPEWRITER_CONFIG.deletingSpeed,
  pauseDuration = TYPEWRITER_CONFIG.pauseDuration,
}: TypewriterOptions) => {
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentText, setCurrentText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (words.length === 0) return;

    const currentWord = words[currentWordIndex];

    const handleTyping = () => {
      // If paused, wait before starting to delete
      if (isPaused) {
        timeoutRef.current = setTimeout(() => {
          setIsPaused(false);
          setIsDeleting(true);
        }, pauseDuration);
        return;
      }

      // Deleting
      if (isDeleting) {
        if (currentText.length === 0) {
          setIsDeleting(false);
          const nextIndex = currentWordIndex + 1;

          // If we've cycled through all words and loop is false, stop
          if (nextIndex >= words.length && !loop) {
            return;
          }

          setCurrentWordIndex(nextIndex % words.length);
        } else {
          setCurrentText(currentWord.substring(0, currentText.length - 1));
          timeoutRef.current = setTimeout(handleTyping, deletingSpeed);
        }
      }
      // Typing
      else {
        if (currentText.length === currentWord.length) {
          // Finished typing current word, pause before deleting
          setIsPaused(true);
          timeoutRef.current = setTimeout(handleTyping, pauseDuration);
        } else {
          setCurrentText(currentWord.substring(0, currentText.length + 1));
          timeoutRef.current = setTimeout(handleTyping, typingSpeed);
        }
      }
    };

    timeoutRef.current = setTimeout(
      handleTyping,
      isDeleting ? deletingSpeed : typingSpeed
    );

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [currentText, isDeleting, isPaused, currentWordIndex, words, loop, typingSpeed, deletingSpeed, pauseDuration]);

  return { text: currentText, isDeleting };
};
