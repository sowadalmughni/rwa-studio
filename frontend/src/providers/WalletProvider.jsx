/**
 * Wallet Provider Configuration for RWA-Studio
 * 
 * Configures wagmi + RainbowKit for Ethereum wallet integration
 */

import '@rainbow-me/rainbowkit/styles.css';

import { getDefaultConfig, RainbowKitProvider, darkTheme, lightTheme } from '@rainbow-me/rainbowkit';
import { WagmiProvider } from 'wagmi';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { mainnet, sepolia, polygon, arbitrum, base, optimism } from 'wagmi/chains';

// Configure chains and providers
const config = getDefaultConfig({
  appName: 'RWA-Studio',
  projectId: import.meta.env.VITE_WALLETCONNECT_PROJECT_ID || 'YOUR_PROJECT_ID', // Get from cloud.walletconnect.com
  chains: [
    mainnet,
    sepolia,
    polygon,
    arbitrum,
    base,
    optimism,
  ],
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
    accentColor: '#3b82f6', // Blue-500
    accentColorForeground: 'white',
    borderRadius: 'medium',
    fontStack: 'system',
    overlayBlur: 'small',
  }),
  colors: {
    ...darkTheme().colors,
    modalBackground: '#0f172a', // Slate-900
    modalBorder: '#1e293b', // Slate-800
    modalText: '#f8fafc', // Slate-50
    modalTextSecondary: '#94a3b8', // Slate-400
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
        <RainbowKitProvider
          theme={customTheme}
          modalSize="compact"
          coolMode
        >
          {children}
        </RainbowKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}

export { config, queryClient };
