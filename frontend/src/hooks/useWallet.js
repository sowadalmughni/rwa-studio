/**
 * useWallet Hook for RWA-Studio
 *
 * Custom hook that provides wallet state and authentication functions
 */

import { useAccount, useDisconnect, useChainId, useSignMessage, useSwitchChain } from "wagmi";
import { useConnectModal, useAccountModal, useChainModal } from "@rainbow-me/rainbowkit";
import { useState, useCallback, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

/**
 * Hook for wallet authentication and state management
 */
export function useWallet() {
  const { address, isConnected, isConnecting, connector } = useAccount();
  const { disconnect } = useDisconnect();
  const chainId = useChainId();
  const { signMessageAsync } = useSignMessage();
  const { switchChainAsync } = useSwitchChain();
  const { openConnectModal } = useConnectModal();
  const { openAccountModal } = useAccountModal();
  const { openChainModal } = useChainModal();

  const [authToken, setAuthToken] = useState(() => localStorage.getItem("rwa_studio_token"));
  const [user, setUser] = useState(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [error, setError] = useState(null);

  // Load user data if token exists
  useEffect(() => {
    if (authToken && !user) {
      fetchCurrentUser();
    }
  }, [authToken]);

  // Clear auth when wallet disconnects
  useEffect(() => {
    if (!isConnected && authToken) {
      logout();
    }
  }, [isConnected]);

  /**
   * Fetch current user data from the API
   */
  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setUser(data.data.user);
        }
      } else {
        // Token expired or invalid
        logout();
      }
    } catch (err) {
      console.error("Failed to fetch user:", err);
    }
  };

  /**
   * Authenticate with wallet signature
   */
  const authenticateWithWallet = useCallback(async () => {
    if (!address) {
      setError("Wallet not connected");
      return null;
    }

    setIsAuthenticating(true);
    setError(null);

    try {
      // For full security, we should:
      // 1. Get a nonce from the server
      // 2. Sign the nonce with the wallet
      // 3. Verify the signature on the server
      // For now, we use a simplified approach

      const response = await fetch(`${API_BASE_URL}/auth/login/wallet`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          wallet_address: address,
          // In production, add signature verification
        }),
      });

      const data = await response.json();

      if (data.success) {
        setAuthToken(data.data.access_token);
        setUser(data.data.user);
        localStorage.setItem("rwa_studio_token", data.data.access_token);
        localStorage.setItem("rwa_studio_refresh_token", data.data.refresh_token);
        return data.data;
      } else {
        setError(data.error || "Authentication failed");
        return null;
      }
    } catch (err) {
      setError(err.message || "Network error");
      return null;
    } finally {
      setIsAuthenticating(false);
    }
  }, [address]);

  /**
   * Connect wallet and authenticate
   */
  const connectAndAuthenticate = useCallback(async () => {
    if (!isConnected) {
      openConnectModal?.();
      return;
    }

    return authenticateWithWallet();
  }, [isConnected, openConnectModal, authenticateWithWallet]);

  /**
   * Logout and clear session
   */
  const logout = useCallback(async () => {
    try {
      if (authToken) {
        // Notify server about logout
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        });
      }
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      setAuthToken(null);
      setUser(null);
      localStorage.removeItem("rwa_studio_token");
      localStorage.removeItem("rwa_studio_refresh_token");
      disconnect();
    }
  }, [authToken, disconnect]);

  /**
   * Refresh access token
   */
  const refreshToken = useCallback(async () => {
    const refreshToken = localStorage.getItem("rwa_studio_refresh_token");
    if (!refreshToken) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      });

      const data = await response.json();

      if (data.success) {
        setAuthToken(data.data.access_token);
        localStorage.setItem("rwa_studio_token", data.data.access_token);
        return data.data.access_token;
      } else {
        logout();
        return null;
      }
    } catch (err) {
      console.error("Token refresh failed:", err);
      logout();
      return null;
    }
  }, [logout]);

  /**
   * Sign a message with the connected wallet
   */
  const signMessage = useCallback(
    async (message) => {
      try {
        return await signMessageAsync({ message });
      } catch (err) {
        setError(err.message);
        return null;
      }
    },
    [signMessageAsync]
  );

  /**
   * Switch to a different chain
   */
  const switchChain = useCallback(
    async (targetChainId) => {
      try {
        await switchChainAsync({ chainId: targetChainId });
        return true;
      } catch (err) {
        setError(err.message);
        return false;
      }
    },
    [switchChainAsync]
  );

  /**
   * Get shortened address for display
   */
  const shortenedAddress = address ? `${address.slice(0, 6)}...${address.slice(-4)}` : null;

  return {
    // Wallet state
    address,
    shortenedAddress,
    isConnected,
    isConnecting,
    chainId,
    connector,

    // Auth state
    authToken,
    user,
    isAuthenticated: !!authToken && !!user,
    isAuthenticating,
    error,

    // Actions
    connectAndAuthenticate,
    authenticateWithWallet,
    logout,
    refreshToken,
    signMessage,
    switchChain,

    // Modal openers
    openConnectModal,
    openAccountModal,
    openChainModal,

    // Clear error
    clearError: () => setError(null),
  };
}

export default useWallet;
