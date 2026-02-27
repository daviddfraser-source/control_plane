"use client";

import { SelectHTMLAttributes, forwardRef } from "react";

interface SelectOption {
    value: string;
    label: string;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "children"> {
    options: SelectOption[];
    label?: string;
    error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
    ({ options, label, error, className = "", ...props }, ref) => {
        const defaultClasses = "w-full appearance-none px-3 py-2 rounded-[var(--radius-lg)] text-[var(--text-base)] font-[var(--font-sans)] bg-token-surface text-token-primary border transition-all outline-none";
        const stateClass = error
            ? "border-status-danger focus:shadow-[0_0_0_3px_rgba(220,38,38,0.1)]"
            : "border-token-strong focus:border-token-primary focus:shadow-[0_0_0_3px_rgba(37,99,235,0.1)]";

        return (
            <div className="space-y-1 relative">
                {label && <label className="block text-[var(--text-sm)] font-medium text-token-primary">{label}</label>}
                <div className="relative">
                    <select
                        ref={ref}
                        className={`${defaultClasses} ${stateClass} ${className} pr-10`}
                        {...props}
                    >
                        {options.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-token-tertiary hover:text-token-secondary">
                        <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                        </svg>
                    </div>
                </div>
                {error && <p className="text-xs text-status-danger">{error}</p>}
            </div>
        );
    }
);
Select.displayName = "Select";
