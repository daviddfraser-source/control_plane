import abilityMapData from "./ability-map.json";

type Role = "reader" | "editor" | "admin" | "support";
const abilityMap: Record<Role, string[]> = abilityMapData as Record<Role, string[]>;

export function getPolicyForRole(role: Role) {
  return abilityMap[role] ?? abilityMap.reader;
}
