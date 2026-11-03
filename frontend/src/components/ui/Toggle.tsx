import React from 'react';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  sublabel?: string;
  disabled?: boolean;
  id?: string;
}

export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  label,
  sublabel,
  disabled = false,
  id = 'custom-toggle',
}) => {
  return (
    <div className="flex items-center gap-2.5 min-h-[36px]">
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-claude-primary focus-visible:ring-offset-2 focus-visible:ring-offset-claude-canvas ${
          checked ? 'bg-claude-primary border-claude-primary' : 'bg-claude-hairline border-claude-muted-soft/40'
        } ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
      >
        <span
          aria-hidden="true"
          className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-xs ring-0 transition duration-200 ease-in-out ${
            checked ? 'translate-x-5' : 'translate-x-0.5'
          }`}
        />
      </button>
      <label
        htmlFor={id}
        className="cursor-pointer text-xs font-sans select-none"
      >
        <span className="text-claude-ink font-medium">{label}</span>
        {sublabel && <span className="text-claude-muted ml-1.5">({sublabel})</span>}
      </label>
    </div>
  );
};
