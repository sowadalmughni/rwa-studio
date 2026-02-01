import js from "@eslint/js";
import globals from "globals";

/**
 * ESLint configuration for E2E tests (Playwright)
 */
export default [
  {
    ignores: ["node_modules/", "playwright-report/", "test-results/"],
  },
  {
    files: ["**/*.{js,mjs}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.node,
        // Playwright globals
        page: "readonly",
        browser: "readonly",
        context: "readonly",
      },
      sourceType: "module",
    },
    rules: {
      ...js.configs.recommended.rules,
      "no-unused-vars": ["error", { varsIgnorePattern: "^_", argsIgnorePattern: "^_" }],
    },
  },
];
