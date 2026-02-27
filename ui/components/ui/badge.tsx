"use client";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "primary" | "success" | "warning" | "danger" | "info" | "outline";
  className?: string;
}

const variantStyles: Record<string, string> = {
  default: "bg-token-inset text-token-secondary",
  primary: "bg-[var(--primary-100)] text-[var(--primary-800)]",
  success: "bg-status-success text-[var(--success-700)]",
  warning: "bg-status-warning text-[#92400e]",
  danger: "bg-status-danger text-[var(--danger-700)]",
  info: "bg-[var(--primary-50)] text-[var(--primary-800)]",
  outline: "bg-transparent text-token-secondary border border-token-default",
};

export function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${variantStyles[variant]} ${className}`}>
      {children}
    </span>
  );
}
