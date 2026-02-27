export default function AppHome() {
    return (
        <div className="flex flex-col items-center justify-center h-full text-center p-12">
            <div className="max-w-lg space-y-6">
                <div className="w-16 h-16 rounded-2xl bg-token-primary/10 flex items-center justify-center mx-auto">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
                    </svg>
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-token-primary mb-2">Your App Lives Here</h1>
                    <p className="text-token-secondary leading-relaxed">
                        This is the <strong>App</strong> section — the product you are building. Replace this placeholder with your domain-specific pages.
                    </p>
                </div>
                <div className="grid grid-cols-1 gap-3 text-left">
                    <div className="p-4 rounded-xl border border-token-default bg-token-surface">
                        <p className="text-sm font-semibold text-token-primary mb-1">👉 Get started</p>
                        <p className="text-xs text-token-secondary">Add your pages to <code className="font-mono text-token-primary">app/(app)/</code> and register them in the App layout nav.</p>
                    </div>
                    <div className="p-4 rounded-xl border border-token-default bg-token-surface">
                        <p className="text-sm font-semibold text-token-primary mb-1">🗂️ Example page included</p>
                        <p className="text-xs text-token-secondary">
                            <a href="/dashboard" className="text-token-primary underline underline-offset-2">Dashboard</a> provides an operations snapshot for this UX starter.
                        </p>
                    </div>
                    <div className="p-4 rounded-xl border border-token-default bg-token-surface">
                        <p className="text-sm font-semibold text-token-primary mb-1">🧩 Reuse UI patterns</p>
                        <p className="text-xs text-token-secondary">
                            Explore the <a href="/marketplace" className="text-token-primary underline underline-offset-2">Marketplace</a> to reuse prebuilt pages and components.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
