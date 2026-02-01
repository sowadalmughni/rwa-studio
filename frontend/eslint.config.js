import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

export default [
  { ignores: ["dist"] },
  // Config for Node.js config files (vite, vitest, etc.)
  {
    files: ["*.config.js", "*.config.ts"],
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
  // Config for test setup files
  {
    files: ["src/test/**/*.js"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
        ...globals.node,
        // Vitest globals
        beforeAll: "readonly",
        afterAll: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        describe: "readonly",
        it: "readonly",
        expect: "readonly",
        vi: "readonly",
      },
      sourceType: "module",
    },
    rules: {
      ...js.configs.recommended.rules,
    },
  },
  // Config for shadcn/ui components - less strict
  {
    files: ["src/components/ui/**/*.jsx"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: "latest",
        ecmaFeatures: { jsx: true },
        sourceType: "module",
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      // shadcn/ui components export variants alongside components
      "react-refresh/only-export-components": "off",
      // Allow unused vars starting with uppercase, underscore, or in destructuring patterns
      "no-unused-vars": ["error", { varsIgnorePattern: "^[A-Z_]", argsIgnorePattern: "^_" }],
    },
  },
  // Main React source files
  {
    files: ["**/*.{js,jsx}"],
    ignores: ["*.config.js", "*.config.ts", "src/test/**/*.js", "src/components/ui/**/*.jsx"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
        process: "readonly",
      },
      parserOptions: {
        ecmaVersion: "latest",
        ecmaFeatures: { jsx: true },
        sourceType: "module",
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      "no-unused-vars": ["error", { varsIgnorePattern: "^[A-Z_]", argsIgnorePattern: "^[A-Z_]" }],
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
    },
  },
];
