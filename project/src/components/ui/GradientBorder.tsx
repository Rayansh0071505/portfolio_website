import { ReactNode } from 'react';
import { cn } from '../../utils/cn';

interface GradientBorderProps {
  children: ReactNode;
  className?: string;
  borderWidth?: number;
  animate?: boolean;
  colors?: string[];
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
}

/**
 * GradientBorder Component
 * Wraps content with an animated gradient border
 * Uses a padding technique to create the border effect
 */
export const GradientBorder = ({
  children,
  className = '',
  borderWidth = 2,
  animate = true,
  colors = ['#3b82f6', '#14b8a6', '#8b5cf6'],
  rounded = 'lg',
}: GradientBorderProps) => {
  const roundedClasses = {
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    full: 'rounded-full',
  };

  const gradientStyle = {
    background: `linear-gradient(135deg, ${colors.join(', ')})`,
    padding: `${borderWidth}px`,
  };

  return (
    <div
      className={cn(
        'relative',
        roundedClasses[rounded],
        animate && 'animate-rotate-gradient',
        className
      )}
      style={gradientStyle}
    >
      {/* Inner container with background */}
      <div className={cn('bg-slate-900 h-full w-full', roundedClasses[rounded])}>
        {children}
      </div>
    </div>
  );
};
