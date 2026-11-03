import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'dark';
export type ButtonSize = 'xs' | 'sm' | 'md';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  active?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'sm',
  active = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const sizeClasses = {
    xs: 'px-2.5 py-1 text-xs min-h-[36px] sm:min-h-[32px]',
    sm: 'px-3 py-1.5 text-xs min-h-[36px] sm:min-h-[32px]',
    md: 'px-4 py-2 text-sm',
  }[size];

  const variantClasses = {
    primary:
      'bg-claude-primary hover:bg-claude-primary-active text-white border border-claude-primary-active/50 shadow-sm active:bg-claude-primary-active',
    secondary: active
      ? 'bg-claude-surface-cream-strong text-claude-ink border border-claude-muted-soft/40 shadow-xs'
      : 'bg-claude-canvas hover:bg-claude-surface-soft text-claude-body border border-claude-hairline hover:border-claude-muted-soft/40',
    outline: active
      ? 'bg-claude-primary/10 text-claude-primary border-claude-primary/50'
      : 'bg-transparent text-claude-body border-claude-hairline hover:bg-claude-surface-soft hover:text-claude-ink',
    ghost:
      'bg-transparent hover:bg-claude-surface-soft text-claude-muted hover:text-claude-ink border-transparent',
    dark: active
      ? 'bg-claude-primary text-white border-claude-primary'
      : 'bg-claude-surface-dark-elevated text-claude-on-dark border border-white/10 hover:bg-claude-surface-dark-soft',
  }[variant];

  return (
    <button
      type="button"
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-1.5 rounded-claude-md font-sans font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-primary ${sizeClasses} ${variantClasses} ${
        disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer active:scale-[0.98]'
      } ${className}`}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
};
