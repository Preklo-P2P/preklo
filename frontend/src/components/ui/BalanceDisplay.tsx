import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

interface BalanceDisplayProps {
  usdcBalance: number;
  aptBalance: number;
  isLoading?: boolean;
}

export function BalanceDisplay({ usdcBalance, aptBalance, isLoading = false }: BalanceDisplayProps) {
  const [isVisible, setIsVisible] = useState(true);

  const formatBalance = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const totalUsdValue = usdcBalance + (aptBalance * 12.50); // Mock APT price

  if (isLoading) {
    return (
      <div className="balance-card animate-pulse">
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="h-4 bg-white/20 rounded w-24 mb-2"></div>
            <div className="h-8 bg-white/20 rounded w-32"></div>
          </div>
          <div className="h-10 w-10 bg-white/20 rounded-full"></div>
        </div>
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="h-3 bg-white/20 rounded w-16 mb-1"></div>
            <div className="h-6 bg-white/20 rounded w-20"></div>
          </div>
          <div className="flex-1">
            <div className="h-3 bg-white/20 rounded w-12 mb-1"></div>
            <div className="h-6 bg-white/20 rounded w-16"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="balance-card">
      <div className="flex justify-between items-start mb-6">
        <div>
          <p className="text-primary-foreground/80 text-sm font-medium mb-1">
            Total Balance
          </p>
          <p className="text-3xl font-bold text-primary-foreground">
            {isVisible ? `$${formatBalance(totalUsdValue)}` : "••••••"}
          </p>
        </div>
        <button
          onClick={() => setIsVisible(!isVisible)}
          className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label={isVisible ? "Hide balance" : "Show balance"}
        >
          {isVisible ? (
            <EyeOff className="h-5 w-5 text-primary-foreground" />
          ) : (
            <Eye className="h-5 w-5 text-primary-foreground" />
          )}
        </button>
      </div>

      <div className="flex gap-6">
        <div className="flex-1">
          <p className="text-primary-foreground/70 text-xs font-medium mb-1 uppercase tracking-wide">
            USDC
          </p>
          <p className="text-xl font-semibold text-primary-foreground">
            {isVisible ? formatBalance(usdcBalance) : "••••"}
          </p>
        </div>
        <div className="flex-1">
          <p className="text-primary-foreground/70 text-xs font-medium mb-1 uppercase tracking-wide">
            APT
          </p>
          <p className="text-xl font-semibold text-primary-foreground">
            {isVisible ? formatBalance(aptBalance) : "••••"}
          </p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-white/20">
        <div className="flex justify-between items-center text-xs text-primary-foreground/70">
          <span>Last updated</span>
          <span>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      </div>
    </div>
  );
}