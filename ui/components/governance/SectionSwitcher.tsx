"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Terminal, Blocks, type LucideIcon } from "lucide-react";

export type Section = "app" | "dev" | "marketplace";

const sections: { id: Section; label: string; href: string; icon: LucideIcon }[] = [
    { id: "app", label: "App", href: "/", icon: LayoutDashboard },
    { id: "dev", label: "Control Plane", href: "/dev/wbs", icon: Terminal },
    { id: "marketplace", label: "Marketplace", href: "/marketplace", icon: Blocks },
];
const devControlPlaneEnabled =
    process.env.NODE_ENV !== "production" ||
    process.env.NEXT_PUBLIC_ENABLE_DEV_CONTROL_PLANE === "1";

function getActiveSection(pathname: string): Section {
    if (pathname.startsWith("/dev")) return "dev";
    if (pathname.startsWith("/marketplace")) return "marketplace";
    return "app";
}

interface SectionSwitcherProps {
    collapsed?: boolean;
}

export function SectionSwitcher({ collapsed = false }: SectionSwitcherProps) {
    const pathname = usePathname();
    const active = getActiveSection(pathname);
    const visibleSections = sections.filter((section) => devControlPlaneEnabled || section.id !== "dev");

    return (
        <div className={`flex ${collapsed ? "flex-col items-center gap-1 px-2 py-2" : "flex-col gap-1 px-3 py-2"}`}>
            {!collapsed && (
                <p className="text-[10px] uppercase tracking-widest text-token-tertiary font-semibold mb-1 px-1">
                    Workspace
                </p>
            )}
            {visibleSections.map((s) => {
                const Icon = s.icon;
                const isActive = active === s.id;
                return (
                    <Link
                        key={s.id}
                        href={s.href}
                        title={collapsed ? s.label : undefined}
                        className={`
              flex items-center gap-2.5 rounded-lg transition-all text-sm font-medium
              ${collapsed ? "justify-center w-9 h-9" : "px-2.5 py-2"}
              ${isActive
                                ? "bg-[var(--section-accent,var(--primary))] text-white shadow-sm"
                                : "text-token-secondary hover:bg-token-inset hover:text-token-primary"
                            }
            `}
                    >
                        <Icon size={16} className="shrink-0" />
                        {!collapsed && <span>{s.label}</span>}
                    </Link>
                );
            })}
        </div>
    );
}
