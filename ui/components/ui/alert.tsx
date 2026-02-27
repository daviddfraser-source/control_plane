"use client";

import React from "react";

export interface AlertProps {
    title?: React.ReactNode;
    description?: React.ReactNode;
    type?: "success" | "info" | "warning" | "error";
    className?: string;
    showIcon?: boolean;
}

export function Alert({ title, description, type = "info", className = "", showIcon = false }: AlertProps) {
    const styles = {
        success: "bg-green-50 border-green-200 text-green-800",
        info: "bg-blue-50 border-blue-200 text-blue-800",
        warning: "bg-amber-50 border-amber-200 text-amber-800",
        error: "bg-red-50 border-red-200 text-red-800",
    };

    const icons = {
        success: "✓",
        info: "i",
        warning: "!",
        error: "✕",
    };

    return (
        <div className={`p-4 rounded-xl border flex gap-3 items-start ${styles[type]} ${className}`}>
            {showIcon && (
                <span className="shrink-0 mt-0.5 font-bold opacity-80" aria-hidden="true">
                    {icons[type]}
                </span>
            )}
            <div className="flex flex-col gap-1">
                {title && <span className="font-semibold text-sm">{title}</span>}
                {description && <span className="text-sm opacity-90">{description}</span>}
            </div>
        </div>
    );
}
