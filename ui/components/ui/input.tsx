"use client";
import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  success?: string;
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ error, success, label, className = "", ...props }, ref) => {
    const stateClass = error ? "border-status-danger focus:shadow-[0_0_0_3px_rgba(220,38,38,0.1)]"
      : success ? "border-status-success focus:shadow-[0_0_0_3px_rgba(5,150,105,0.1)]"
      : "border-token-strong focus:border-token-primary focus:shadow-[0_0_0_3px_rgba(37,99,235,0.1)]";
    return (
      <div className="space-y-1">
        {label && <label className="block text-[var(--text-sm)] font-medium text-token-primary">{label}</label>}
        <input
          ref={ref}
          className={`w-full px-3 py-2 rounded-[var(--radius-lg)] text-[var(--text-base)] font-[var(--font-sans)] bg-token-surface text-token-primary border transition-all outline-none ${stateClass} ${className}`}
          {...props}
        />
        {error && <p className="text-xs text-status-danger">{error}</p>}
        {success && <p className="text-xs text-status-success">{success}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
