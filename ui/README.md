# AI-Optimized Substrate Template

## Fast-start commands
- Lean startup (default):
  - `npm run bootstrap:core`
  - `npm run dev -- --port 3001`
- Full install with optional feature packages:
  - `npm run bootstrap:full`
  - `npm run dev -- --port 3001`

## Optional feature packages (on-demand)
- Terminal backend (`node-pty`):
  - `npm run feature:terminal:enable`
- E2E tooling (`playwright`):
  - `npm run feature:e2e:enable`
- DB/Prisma tooling (`@prisma/client`, `prisma`):
  - `npm run feature:db:enable`
- Reset to core-only install:
  - `npm run feature:core:reset`

## Opinionated defaults
- Next.js 16 App Router with server actions.
- Tailwind CSS + shadcn-inspired component primitives under `components/ui`.
- Zod schema enforcement for API inputs and environment variables.
- Prisma schema coupled with Supabase/Postgres and explicit adapter seam.

Use the docs in `docs/codex-migration/ai-substrate` as authoritative context when extending this template.
