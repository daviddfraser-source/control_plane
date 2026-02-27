import { z } from "zod";

export const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  SHADOW_DATABASE_URL: z.string().url(),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  FEATURE_FLAG_BETA: z
    .string()
    .transform((value) => value === "true")
});

export type EnvSchema = z.infer<typeof envSchema>;

export function parseEnv() {
  return envSchema.parse(process.env);
}
