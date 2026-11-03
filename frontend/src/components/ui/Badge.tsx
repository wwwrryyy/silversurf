import React from 'react';

export type BadgeVariant =
  | 'coral'
  | 'teal'
  | 'amber'
  | 'cream'
  | 'dark'
  | 'red';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  dot?: boolean;
  pulse?: boolean;
}

const variantStyles: Record<BadgeVariant, { bg: string; text: string; border: string; dot: string }> = {
  coral: {
    bg: 'bg-claude-primary/10',
    text: 'text-claude-primary',
    border: 'border-claude-primary/25',
    dot: 'bg-claude-primary',
  },
  teal: {
    bg: 'bg-claude-teal/15',
    text: 'text-[#246b5d]',
    border: 'border-claude-teal/30',
    dot: 'bg-claude-teal',
  },
  amber: {
    bg: 'bg-claude-amber/15',
    text: 'text-[#965c15]',
    border: 'border-claude-amber/30',
    dot: 'bg-claude-amber',
  },
  cream: {
    bg: 'bg-claude-surface-card',
    text: 'text-claude-body-strong',
    border: 'border-claude-hairline',
    dot: 'bg-claude-muted',
  },
  dark: {
    bg: 'bg-claude-surface-dark-elevated',
    text: 'text-claude-on-dark',
    border: 'border-white/10',
    dot: 'bg-claude-primary',
  },
  red: {
    bg: 'bg-claude-error/10',
    text: 'text-claude-error',
    border: 'border-claude-error/30',
    dot: 'bg-claude-error',
  },
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'cream',
  className = '',
  dot = false,
  pulse = false,
}) => {
  const styles = variantStyles[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-sans font-medium border ${styles.bg} ${styles.text} ${styles.border} ${className}`}
    >
      {dot && (
        <span className="relative flex h-2 w-2">
          {pulse && (
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${styles.dot}`}
            />
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${styles.dot}`} />
        </span>
      )}
      {children}
    </span>
  );
};
