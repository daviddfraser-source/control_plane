"use client";

import { ReactNode, useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
    GitBranch, Package, TerminalSquare, Network,
    ClipboardList, AlertTriangle, Settings, ChevronLeft, ChevronRight, type LucideIcon
} from "lucide-react";
import { SectionSwitcher } from "@/components/governance/SectionSwitcher";
import { ThemeToggle } from "@/components/governance/ThemeToggle";
import { CommandPalette } from "@/components/governance/CommandPalette";
import { TtydDock } from "@/components/governance/TtydDock";

interface NavItem { href: string; label: string; icon: LucideIcon }

const devNav: NavItem[] = [
    { href: "/dev/wbs", label: "WBS Viewer", icon: GitBranch },
    { href: "/dev/packets", label: "Packets", icon: Package },
    { href: "/dev/graph", label: "Dependency Graph", icon: Network },
    { href: "/dev/audit", label: "Audit Log", icon: ClipboardList },
    { href: "/dev/risks", label: "Risk Register", icon: AlertTriangle },
    { href: "/dev/terminal", label: "CLI Terminal", icon: TerminalSquare },
    { href: "/dev/settings", label: "Settings", icon: Settings },
];

export default function DevLayout({ children }: { children: ReactNode }) {
    const [collapsed, setCollapsed] = useState(false);
    const [cmdOpen, setCmdOpen] = useState(false);
    const [termOpen, setTermOpen] = useState(false);
    const pathname = usePathname();
    const router = useRouter();

    useEffect(() => {
        const saved = localStorage.getItem("sidebar-collapsed");
        if (saved === "true") setCollapsed(true);
    }, []);

    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); setCmdOpen(true); }
            if ((e.metaKey || e.ctrlKey) && e.key === "`") { e.preventDefault(); setTermOpen(p => !p); }
        };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, []);

    const toggle = () => {
        const next = !collapsed;
        setCollapsed(next);
        localStorage.setItem("sidebar-collapsed", String(next));
    };

    const currentLabel = devNav.find(
        (item) => pathname === item.href || pathname?.startsWith(item.href + "/")
    )?.label ?? "Control Plane";

    return (
        <div
            className="flex h-screen overflow-hidden"
            style={{ "--section-accent": "#475569" } as React.CSSProperties}
        >
            {/* Sidebar */}
            <aside
                className={`flex flex-col bg-token-elevated border-r border-token-default transition-all duration-300 ${collapsed ? "w-16" : "w-64"}`}
                role="navigation"
                aria-label="Control Plane navigation"
            >
                {/* Logo */}
                <div className="h-14 flex items-center px-4 border-b border-token-default shrink-0">
                    {!collapsed && (
                        <span className="text-base font-bold text-token-primary tracking-tight">Substrate</span>
                    )}
                    {collapsed && <span className="text-lg">⬡</span>}
                </div>

                {/* Section Switcher */}
                <div className="border-b border-token-default">
                    <SectionSwitcher collapsed={collapsed} />
                </div>

                {/* Dev Nav */}
                <nav className="flex-1 overflow-y-auto py-3">
                    <div className="px-2">
                        {!collapsed && (
                            <p className="px-3 mb-2 text-[10px] uppercase tracking-widest text-token-tertiary font-semibold">
                                Tooling
                            </p>
                        )}
                        <ul className="space-y-0.5 list-none m-0 p-0">
                            {devNav.map((item) => {
                                const Icon = item.icon;
                                const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
                                return (
                                    <li key={item.href}>
                                        <Link
                                            href={item.href}
                                            title={collapsed ? item.label : undefined}
                                            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                                                ? "bg-[var(--section-accent)] text-white"
                                                : "text-token-secondary hover:bg-token-inset hover:text-token-primary"
                                                }`}
                                        >
                                            <Icon size={16} />
                                            {!collapsed && <span>{item.label}</span>}
                                        </Link>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                </nav>

                {/* Footer */}
                <div className="p-2 border-t border-token-default space-y-1">
                    <button
                        onClick={toggle}
                        className="w-full flex items-center justify-center px-3 py-2 text-sm text-token-tertiary hover:text-token-primary hover:bg-token-inset rounded-lg transition-colors"
                    >
                        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    </button>
                </div>
            </aside>

            {/* Main */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="h-14 bg-token-elevated border-b border-token-default flex items-center justify-between px-6 shrink-0">
                    <p className="text-sm font-semibold text-token-primary">{currentLabel}</p>
                    <div className="flex items-center gap-2">
                        <ThemeToggle />
                        <button
                            onClick={() => setTermOpen(true)}
                            className="px-2.5 py-1.5 text-xs text-token-tertiary bg-token-inset rounded-lg border border-token-default hover:border-token-strong transition-colors font-mono"
                            title="Open terminal (Ctrl+`)"
                        >
                            CLI
                        </button>
                        <button
                            onClick={() => setCmdOpen(true)}
                            className="px-2.5 py-1.5 text-xs text-token-tertiary bg-token-inset rounded-lg border border-token-default hover:border-token-strong transition-colors font-mono"
                        >
                            ⌘K
                        </button>
                    </div>
                </header>

                <main className="flex-1 overflow-auto">
                    {children}
                </main>
            </div>

            <CommandPalette
                open={cmdOpen}
                onClose={() => setCmdOpen(false)}
                commands={devNav.map((item) => ({
                    label: item.label,
                    action: () => router.push(item.href),
                }))}
            />
            <TtydDock open={termOpen} onClose={() => setTermOpen(false)} />
        </div>
    );
}
