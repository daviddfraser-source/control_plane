export type PermissionContext = {
  userId: string;
  role: "reader" | "editor" | "admin" | "support";
  orgId: string;
};

type AllowRule = { action: string; resource: string };

export function defineAbilities(ctx: PermissionContext) {
  const roleRules: Record<PermissionContext["role"], AllowRule[]> = {
    reader: [{ action: "read", resource: "item" }],
    editor: [
      { action: "read", resource: "item" },
      { action: "create", resource: "item" }
    ],
    admin: [{ action: "*", resource: "*" }],
    support: [{ action: "read", resource: "item" }]
  };

  const rules = roleRules[ctx.role] ?? roleRules.reader;

  return {
    can(action: string, resource: string) {
      return rules.some((rule) => {
        const actionMatches = rule.action === "*" || rule.action === action;
        const resourceMatches = rule.resource === "*" || rule.resource === resource;
        return actionMatches && resourceMatches;
      });
    },
    cannot(action: string, resource: string) {
      return !this.can(action, resource);
    }
  };
}
