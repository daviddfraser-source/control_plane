/**
 * Optional shell: hook-based extensibility layer for governance events.
 * Migrated from app/src/ui/optionalShell.ts for Next.js template library.
 */

export interface OptionalShellConfig {
  enabled: boolean;
  extensionPanelsEnabled: boolean;
  customHooksEnabled: boolean;
}

export interface ShellHookContext {
  packetId?: string;
  tenantId?: string;
  event: string;
}

export type ShellHook = (context: ShellHookContext) => void;

export class OptionalShell {
  private hooks: Record<string, ShellHook[]> = {};
  private readonly config: OptionalShellConfig;

  constructor(config: OptionalShellConfig) {
    this.config = config;
  }

  registerHook(event: string, hook: ShellHook): void {
    if (!this.config.enabled || !this.config.customHooksEnabled) {
      return;
    }
    this.hooks[event] = this.hooks[event] || [];
    this.hooks[event].push(hook);
  }

  emit(event: string, context: Omit<ShellHookContext, "event">): void {
    if (!this.config.enabled) {
      return;
    }
    const callbacks = this.hooks[event] || [];
    for (const callback of callbacks) {
      callback({ ...context, event });
    }
  }

  isDisabledModeSafe(): boolean {
    return !this.config.enabled;
  }
}
