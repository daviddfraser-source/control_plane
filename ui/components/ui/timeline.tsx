"use client";

import React from "react";

export interface TimelineItem {
    title: React.ReactNode;
    children: React.ReactNode;
    color?: "blue" | "green" | "red" | "orange" | "gray";
}

export interface TimelineProps {
    items: TimelineItem[];
    className?: string;
}

export function Timeline({ items, className = "" }: TimelineProps) {
    const colorMap = {
        blue: "bg-blue-500 border-blue-500",
        green: "bg-green-500 border-green-500",
        red: "bg-red-500 border-red-500",
        orange: "bg-orange-500 border-orange-500",
        gray: "bg-gray-400 border-gray-400",
    };

    return (
        <div className={`relative pl-4 border-l border-token-default ml-4 ${className}`}>
            {items.map((item, index) => {
                const dotColorClass = colorMap[item.color || "blue"];

                return (
                    <div key={index} className="mb-8 relative last:mb-0">
                        {/* Timeline Dot */}
                        <div className={`absolute -left-[21px] top-1 h-[10px] w-[10px] rounded-full border-2 bg-white ${dotColorClass}`} />

                        {/* Timeline Content */}
                        <div className="pl-4">
                            <div className="text-sm font-medium text-token-secondary mb-1">
                                {item.title}
                            </div>
                            <div className="text-token-primary">
                                {item.children}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
