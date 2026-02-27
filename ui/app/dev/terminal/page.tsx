"use client";

import { PtyTerminal } from "@/components/governance/PtyTerminal";

export default function TerminalPage() {
    return (
        <div className="h-full flex flex-col">
            <div className="bg-token-elevated border-b border-token-border-default px-4 py-3">
                <h1 className="text-base font-semibold text-token-primary">CLI Terminal</h1>
                <p className="text-xs text-token-secondary">
                    Embedded PTY session. Use <code className="font-mono">python3 .governance/wbs_cli.py</code> commands here.
                </p>
                <p className="text-xs text-token-tertiary mt-1">
                    If terminal backend is unavailable, enable it with <code className="font-mono">npm run feature:terminal:enable</code>.
                </p>
            </div>
            <div className="flex-1 min-h-0 bg-[#1a1a1a]">
                <PtyTerminal />
            </div>
        </div>
    );
}
