import js from "@eslint/js";
import globals from "globals";

/**
 * ESLint configuration for Smart Contracts (Hardhat)
 */
export default [
  {
    ignores: [
      "node_modules/",
      "artifacts/",
      "cache/",
      "coverage/",
      "typechain-types/",
      "ignition/deployments/",
    ],
  },
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: {
        ...globals.node,
        ...globals.mocha,
        // Hardhat globals
        ethers: "readonly",
        network: "readonly",
        artifacts: "readonly",
        task: "readonly",
        subtask: "readonly",
        hre: "readonly",
      },
      sourceType: "module",
    },
    rules: {
      ...js.configs.recommended.rules,
      "no-unused-vars": ["error", { varsIgnorePattern: "^_", argsIgnorePattern: "^_" }],
    },
  },
];
