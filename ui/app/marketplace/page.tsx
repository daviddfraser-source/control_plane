"use client";

import Link from "next/link";

interface Template {
    href: string;
    label: string;
    description: string;
    category: string;
    emoji: string;
}

const templates: Template[] = [
    // Planning
    { href: "/marketplace/kanban", label: "Kanban Board", description: "Drag-and-drop column workflow with @dnd-kit, backlog semantics, and card metadata.", category: "Planning", emoji: "🗂️" },
    { href: "/marketplace/gantt", label: "Gantt Chart", description: "Interactive Gantt with drag-to-reschedule and dependency links via @svar-ui/react-gantt.", category: "Planning", emoji: "📈" },
    { href: "/marketplace/timeline", label: "Timeline", description: "Vertical event stream with grouped milestones and status markers.", category: "Planning", emoji: "🕒" },
    { href: "/marketplace/calendar", label: "Calendar", description: "Monthly/weekly event calendar with category filtering and event creation.", category: "Planning", emoji: "📅" },
    // AI & Assistants
    { href: "/marketplace/assistant", label: "RAG Assistant", description: "Prompt + markdown result + citation drawer. Wire to any LLM backend.", category: "AI & Assistants", emoji: "🤖" },
    { href: "/marketplace/chat", label: "Governed Chat", description: "Thread-based chat with message attribution and governance tags.", category: "AI & Assistants", emoji: "💬" },
    { href: "/marketplace/agent-console", label: "Agent Console", description: "Live agent run monitor with log streaming and packet linkage.", category: "AI & Assistants", emoji: "🖥️" },
    { href: "/marketplace/prompt-lab", label: "Prompt Lab", description: "Versioned prompt editor with draft/active/archived lifecycle and inline test runner.", category: "AI & Assistants", emoji: "🧪" },
    // Data
    { href: "/marketplace/data-table", label: "Data Table", description: "Full-featured table: sorting, filtering, bulk actions, CSV export, pagination.", category: "Data", emoji: "🗃️" },
    { href: "/marketplace/record-detail", label: "Record Detail", description: "Split-pane record view with activity feed, metadata, and edit drawer.", category: "Data", emoji: "🔍" },
    { href: "/marketplace/analytics-dash", label: "Analytics Dashboard", description: "KPI grid, sparkline charts, and date-range filters for operational metrics.", category: "Data", emoji: "📉" },
    { href: "/marketplace/search-center", label: "Search Center", description: "Keyboard-first search with grouped results, history, and quick actions.", category: "Data", emoji: "🔎" },
    { href: "/marketplace/import-mapping", label: "Import Mapping", description: "CSV/JSON field mapper with column preview and transformation preview.", category: "Data", emoji: "🗺️" },
    // Content
    { href: "/marketplace/documents", label: "Documents", description: "Document list with version badges, preview pane, and upload flow.", category: "Content", emoji: "📄" },
    { href: "/marketplace/knowledge", label: "Knowledge Base", description: "Searchable article library with category tree and markdown rendering.", category: "Content", emoji: "📚" },
    { href: "/marketplace/asset-manager", label: "Asset Manager", description: "File grid with filter, bulk selection, and preview modal.", category: "Content", emoji: "📁" },
    // Operations
    { href: "/marketplace/approvals", label: "Approvals", description: "Approval queue with assignee, SLA status, and approve/reject flow.", category: "Operations", emoji: "✅" },
    { href: "/marketplace/approval-designer", label: "Approval Designer", description: "Visual workflow builder for multi-stage approval routing.", category: "Operations", emoji: "🏗️" },
    { href: "/marketplace/sla-queue", label: "SLA Queue", description: "Priority queue with SLA countdown, escalation paths, and status matrix.", category: "Operations", emoji: "⏳" },
    { href: "/marketplace/incident-ops", label: "Incident Ops", description: "Incident management with severity triage, timeline, and runbook links.", category: "Operations", emoji: "🚨" },
    { href: "/marketplace/notifications", label: "Notifications", description: "Notification center with read/unread, categories, and bulk dismiss.", category: "Operations", emoji: "🔔" },
    { href: "/marketplace/event-timeline", label: "Event Timeline", description: "Chronological event stream with severity filters and metadata expansion.", category: "Operations", emoji: "🎞️" },
    // Reporting
    { href: "/marketplace/report-center", label: "Report Center", description: "Report catalog with schedule, run-now, and format export (PDF/CSV/JSON).", category: "Reporting", emoji: "📜" },
    { href: "/marketplace/audit-explorer", label: "Audit Explorer", description: "Advanced audit log with actor/event-type/date filters and export.", category: "Reporting", emoji: "🕵️" },
    // Administration
    { href: "/marketplace/rbac-matrix", label: "RBAC Matrix", description: "Role × permission matrix with toggle cells and bulk role assignment.", category: "Administration", emoji: "🔐" },
    { href: "/marketplace/integration-catalog", label: "Integration Catalog", description: "Card catalog of system integrations with status, config, and toggle.", category: "Administration", emoji: "🔌" },
    { href: "/marketplace/rules-engine", label: "Rules Engine", description: "Drag-and-drop rule builder with condition groups and action targets.", category: "Administration", emoji: "⚖️" },
    { href: "/marketplace/feature-flags", label: "Feature Flags", description: "Flag management with environment toggles, rollout %, and audit trail.", category: "Administration", emoji: "🚩" },
    { href: "/marketplace/settings-studio", label: "Settings Studio", description: "Tabbed settings UI with section groups, live preview, and save state.", category: "Administration", emoji: "🛠️" },
    // Forms & Wizards
    { href: "/marketplace/wizard", label: "Setup Wizard", description: "Multi-step form wizard with progress bar, validation, and review step.", category: "Forms & Wizards", emoji: "🧙" },
    { href: "/marketplace/new", label: "New Item Form", description: "Full-featured create form with inline validation, tags, and draft save.", category: "Forms & Wizards", emoji: "➕" },
];

const categories = [...new Set(templates.map(t => t.category))];

const categoryColors: Record<string, string> = {
    "Planning": "bg-blue-50 text-blue-700 border-blue-200",
    "AI & Assistants": "bg-purple-50 text-purple-700 border-purple-200",
    "Data": "bg-green-50 text-green-700 border-green-200",
    "Content": "bg-orange-50 text-orange-700 border-orange-200",
    "Operations": "bg-red-50 text-red-700 border-red-200",
    "Reporting": "bg-amber-50 text-amber-700 border-amber-200",
    "Administration": "bg-slate-50 text-slate-700 border-slate-200",
    "Forms & Wizards": "bg-violet-50 text-violet-700 border-violet-200",
};

export default function MarketplacePage() {
    return (
        <div className="p-8 space-y-10 max-w-7xl mx-auto">
            {/* Header */}
            <div className="space-y-2 pb-6 border-b border-token-default">
                <h1 className="text-3xl font-bold tracking-tight text-token-primary">Template Marketplace</h1>
                <p className="text-token-secondary">
                    {templates.length} ready-to-use UI patterns. Browse, preview, and copy into your App section.
                </p>
                <div className="flex flex-wrap gap-2 pt-2">
                    {categories.map(cat => (
                        <span
                            key={cat}
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${categoryColors[cat] ?? "bg-gray-50 text-gray-700 border-gray-200"}`}
                        >
                            {cat}
                        </span>
                    ))}
                </div>
            </div>

            {/* Grid by category */}
            {categories.map(category => (
                <section key={category}>
                    <div className="flex items-center gap-3 mb-4">
                        <h2 className="text-lg font-semibold text-token-primary">{category}</h2>
                        <span className="text-xs text-token-tertiary font-medium">
                            {templates.filter(t => t.category === category).length} templates
                        </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {templates
                            .filter(t => t.category === category)
                            .map(template => (
                                <Link
                                    key={template.href}
                                    href={template.href}
                                    className="group relative flex flex-col gap-3 p-5 rounded-xl border border-token-default bg-token-surface hover:border-[#7c3aed] hover:shadow-md transition-all duration-200"
                                >
                                    <div className="flex items-start justify-between">
                                        <span className="text-2xl">{template.emoji}</span>
                                        <span
                                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border ${categoryColors[template.category] ?? "bg-gray-50 text-gray-700 border-gray-200"}`}
                                        >
                                            {template.category}
                                        </span>
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-token-primary mb-1 group-hover:text-[#7c3aed] transition-colors">
                                            {template.label}
                                        </h3>
                                        <p className="text-sm text-token-secondary leading-relaxed">
                                            {template.description}
                                        </p>
                                    </div>
                                    <div className="mt-auto pt-3 border-t border-token-muted flex items-center gap-2">
                                        <span className="text-xs font-medium text-[#7c3aed] group-hover:underline">
                                            Open template →
                                        </span>
                                    </div>
                                </Link>
                            ))}
                    </div>
                </section>
            ))}
        </div>
    );
}
