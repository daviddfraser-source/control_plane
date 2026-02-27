"use client";
import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "danger" | "outline" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  size?: "sm" | "md";
}

const variantStyles: Record<Variant, string> = {
  primary: "bg-token-primary text-token-inverse hover:bg-[var(--primary-dark)] shadow-token-xs",
  secondary: "bg-token-inset text-token-primary border border-token-default hover:border-token-strong",
  danger: "bg-[var(--danger)] text-token-inverse hover:bg-[var(--danger-700)]",
  outline: "bg-transparent text-token-secondary border border-token-default hover:bg-token-inset",
  ghost: "bg-transparent text-token-secondary hover:bg-token-inset hover:text-token-primary",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", loading, size = "md", className = "", children, disabled, ...props }, ref) => {
    const sizeClass = size === "sm" ? "px-3 py-1 text-[var(--text-sm)]" : "px-4 py-2 text-[var(--text-base)]";
    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center gap-2 rounded-[var(--radius-lg)] font-medium transition-all focus-visible:outline-2 focus-visible:outline-[var(--primary)] focus-visible:outline-offset-2 whitespace-nowrap ${sizeClass} ${variantStyles[variant]} ${(disabled || loading) ? "opacity-50 cursor-not-allowed pointer-events-none" : ""} ${className}`}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <span className="inline-block w-3.5 h-3.5 border-2 border-current border-r-transparent rounded-full animate-spin" />}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
