"use client";

interface Crumb {
  label: string;
  href?: string;
}

interface BreadcrumbNavProps {
  items: Crumb[];
}

export function BreadcrumbNav({ items }: BreadcrumbNavProps) {
  return (
    <nav className="flex items-center gap-1 text-xs text-token-tertiary px-6 py-1 bg-token-surface border-b border-token-muted">
      {items.map((crumb, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <span className="text-token-tertiary">/</span>}
          {crumb.href ? (
            <a href={crumb.href} className="text-token-link no-underline hover:underline">{crumb.label}</a>
          ) : (
            <span>{crumb.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
