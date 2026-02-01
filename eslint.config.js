import js from "@eslint/js";
import globals from "globals";

/**
 * Root ESLint configuration for RWA-Studio monorepo
 * This config is used by lint-staged for pre-commit hooks
 */
export default [
  {
    ignores: [
      "node_modules/",
      "frontend/",
      "e2e/",
      "smart-contracts/",
      "backend/",
      "dist/",
      "coverage/",
    ],
  },
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.node,
      },
      sourceType: "module",
    },
    rules: {
      ...js.configs.recommended.rules,
    },
  },
];
