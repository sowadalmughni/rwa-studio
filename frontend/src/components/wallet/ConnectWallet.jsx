/**
 * ConnectWallet Button Component for RWA-Studio
 * 
 * A customizable button that handles wallet connection and authentication
 */

import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useWallet } from '../../hooks/useWallet';
import { Button } from '../ui/button';
import { Wallet, LogOut, User, ChevronDown, Shield, AlertCircle } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { Badge } from '../ui/badge';

/**
 * Custom ConnectWallet component with RWA-Studio branding
 */
export function ConnectWallet({ showBalance = true, variant = 'default' }) {
  const { 
    isConnected, 
    isAuthenticated,
    user,
    logout,
    authenticateWithWallet,
    isAuthenticating,
    error,
    shortenedAddress
  } = useWallet();

  return (
    <ConnectButton.Custom>
      {({
        account,
        chain,
        openAccountModal,
        openChainModal,
        openConnectModal,
        authenticationStatus,
        mounted,
      }) => {
        const ready = mounted && authenticationStatus !== 'loading';
        const connected = ready && account && chain;

        return (
          <div
            {...(!ready && {
              'aria-hidden': true,
              style: {
                opacity: 0,
                pointerEvents: 'none',
                userSelect: 'none',
              },
            })}
          >
            {(() => {
              if (!connected) {
                return (
                  <Button
                    onClick={openConnectModal}
                    variant={variant}
                    className="gap-2"
                  >
                    <Wallet className="h-4 w-4" />
                    Connect Wallet
                  </Button>
                );
              }

              if (chain.unsupported) {
                return (
                  <Button
                    onClick={openChainModal}
                    variant="destructive"
                    className="gap-2"
                  >
                    <AlertCircle className="h-4 w-4" />
                    Wrong Network
                  </Button>
                );
              }

              return (
                <div className="flex items-center gap-2">
                  {/* Chain Selector */}
                  <Button
                    onClick={openChainModal}
                    variant="outline"
                    size="sm"
                    className="gap-2"
                  >
                    {chain.hasIcon && (
                      <div
                        className="h-4 w-4 overflow-hidden rounded-full"
                        style={{ background: chain.iconBackground }}
                      >
                        {chain.iconUrl && (
                          <img
                            alt={chain.name ?? 'Chain icon'}
                            src={chain.iconUrl}
                            className="h-4 w-4"
                          />
                        )}
                      </div>
                    )}
                    {chain.name}
                  </Button>

                  {/* Account Menu */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" className="gap-2">
                        {showBalance && account.displayBalance && (
                          <span className="hidden sm:inline">
                            {account.displayBalance}
                          </span>
                        )}
                        <span>{account.displayName}</span>
                        <ChevronDown className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    
                    <DropdownMenuContent align="end" className="w-56">
                      <DropdownMenuLabel className="font-normal">
                        <div className="flex flex-col space-y-1">
                          {isAuthenticated ? (
                            <>
                              <p className="text-sm font-medium leading-none flex items-center gap-2">
                                {user?.username}
                                <Badge variant="secondary" className="text-xs">
                                  {user?.role}
                                </Badge>
                              </p>
                              <p className="text-xs leading-none text-muted-foreground">
                                {user?.email}
                              </p>
                            </>
                          ) : (
                            <>
                              <p className="text-sm font-medium leading-none">
                                {account.displayName}
                              </p>
                              <p className="text-xs leading-none text-muted-foreground">
                                Not authenticated
                              </p>
                            </>
                          )}
                        </div>
                      </DropdownMenuLabel>
                      
                      <DropdownMenuSeparator />
                      
                      <DropdownMenuItem onClick={openAccountModal}>
                        <Wallet className="mr-2 h-4 w-4" />
                        <span>Wallet Details</span>
                      </DropdownMenuItem>
                      
                      {!isAuthenticated && (
                        <DropdownMenuItem 
                          onClick={authenticateWithWallet}
                          disabled={isAuthenticating}
                        >
                          <Shield className="mr-2 h-4 w-4" />
                          <span>{isAuthenticating ? 'Authenticating...' : 'Authenticate'}</span>
                        </DropdownMenuItem>
                      )}
                      
                      {isAuthenticated && (
                        <DropdownMenuItem>
                          <User className="mr-2 h-4 w-4" />
                          <span>Profile Settings</span>
                        </DropdownMenuItem>
                      )}
                      
                      <DropdownMenuSeparator />
                      
                      <DropdownMenuItem 
                        onClick={logout}
                        className="text-red-500 focus:text-red-500"
                      >
                        <LogOut className="mr-2 h-4 w-4" />
                        <span>Disconnect</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              );
            })()}
          </div>
        );
      }}
    </ConnectButton.Custom>
  );
}

export default ConnectWallet;
