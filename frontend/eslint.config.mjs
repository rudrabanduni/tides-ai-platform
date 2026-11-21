import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __dirname = dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({ baseDirectory: __dirname });

// Previously this file exported an empty array, so `npm run lint` checked nothing.
const eslintConfig = [
  {
    ignores: [".next/**", "node_modules/**", "test-results/**", "playwright-report/**", "next-env.d.ts"],
  },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      // Legacy pages use loosely typed API payloads; keep visible but non-blocking.
      "@typescript-eslint/no-explicit-any": "warn",
    },
  },
];

export default eslintConfig;
