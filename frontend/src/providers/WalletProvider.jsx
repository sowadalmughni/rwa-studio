/**
 * Wallet Provider Configuration for RWA-Studio
 *
 * Configures wagmi + RainbowKit for Ethereum wallet integration
 *
 * SECURITY: WalletConnect projectId must be set via environment variable
 * - Create project at https://cloud.walletconnect.com
 * - Set VITE_WALLETCONNECT_PROJECT_ID in .env file
 */

import "@rainbow-me/rainbowkit/styles.css";

import {
  getDefaultConfig,
  RainbowKitProvider,
  darkTheme,
  lightTheme,
} from "@rainbow-me/rainbowkit";
import { WagmiProvider } from "wagmi";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { mainnet, sepolia, polygon, arbitrum, base, optimism } from "wagmi/chains";

/**
 * Get WalletConnect project ID from environment
 * SECURITY: No fallback to placeholder in production to prevent accidental deployment
 */
const getProjectId = () => {
  const projectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID;

  // In production, require the project ID
  if (import.meta.env.PROD && (!projectId || projectId === "YOUR_PROJECT_ID")) {
    console.error(
      "[SECURITY ERROR] VITE_WALLETCONNECT_PROJECT_ID is not configured. " +
        "Wallet connections will fail. " +
        "Create a project at https://cloud.walletconnect.com and add the ID to your .env file."
    );
    // Return empty string - WalletConnect will fail gracefully
    return "";
  }

  // In development, warn if using placeholder
  if (!projectId || projectId === "YOUR_PROJECT_ID") {
    console.warn(
      "[DEV WARNING] VITE_WALLETCONNECT_PROJECT_ID is not set. " +
        "WalletConnect may not work. Get a free project ID from https://cloud.walletconnect.com"
    );
    // Allow development to proceed with degraded functionality
    return projectId || "";
  }

  return projectId;
};

// Configure chains and providers
const config = getDefaultConfig({
  appName: "RWA-Studio",
  projectId: getProjectId(),
  chains: [mainnet, sepolia, polygon, arbitrum, base, optimism],
  ssr: false, // Disable SSR since we're using Vite/React
});

// Create query client for react-query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 30, // 30 minutes
    },
  },
});

// Custom theme based on RWA-Studio branding
const customTheme = {
  ...darkTheme({
    accentColor: "#3b82f6", // Blue-500
    accentColorForeground: "white",
    borderRadius: "medium",
    fontStack: "system",
    overlayBlur: "small",
  }),
  colors: {
    ...darkTheme().colors,
    modalBackground: "#0f172a", // Slate-900
    modalBorder: "#1e293b", // Slate-800
    modalText: "#f8fafc", // Slate-50
    modalTextSecondary: "#94a3b8", // Slate-400
  },
};

/**
 * WalletProvider Component
 * Wraps the application with necessary providers for wallet functionality
 */
export function WalletProvider({ children }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <RainbowKitProvider theme={customTheme} modalSize="compact" coolMode>
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}

export { config, queryClient };
