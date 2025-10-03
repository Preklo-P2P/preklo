import { useState, useCallback } from "react";
import { DollarSign, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface AmountInputProps {
  value: string;
  onChange: (value: string) => void;
  currency: "USDC" | "APT";
  onCurrencyChange: (currency: "USDC" | "APT") => void;
  maxAmount?: number;
  placeholder?: string;
  error?: string;
  suggestions?: number[];
  onSelectSuggestion?: (amount: number) => void;
  className?: string;
}

const defaultSuggestions = [10, 25, 50, 100];

export function AmountInput({
  value,
  onChange,
  currency,
  onCurrencyChange,
  maxAmount,
  placeholder = "0.00",
  error,
  suggestions = defaultSuggestions,
  onSelectSuggestion,
  className
}: AmountInputProps) {
  const [isFocused, setIsFocused] = useState(false);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    let inputValue = e.target.value;
    
    // Only allow numbers and decimal point
    inputValue = inputValue.replace(/[^0-9.]/g, '');
    
    // Prevent multiple decimal points
    const decimalCount = (inputValue.match(/\./g) || []).length;
    if (decimalCount > 1) {
      inputValue = inputValue.substring(0, inputValue.lastIndexOf('.'));
    }
    
    // Limit to 2 decimal places
    if (inputValue.includes('.')) {
      const parts = inputValue.split('.');
      if (parts[1] && parts[1].length > 2) {
        inputValue = parts[0] + '.' + parts[1].substring(0, 2);
      }
    }
    
    onChange(inputValue);
  }, [onChange]);

  const handleSuggestionClick = useCallback((amount: number) => {
    onChange(amount.toString());
    onSelectSuggestion?.(amount);
  }, [onChange, onSelectSuggestion]);

  const formatSuggestion = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const numericValue = parseFloat(value) || 0;
  const hasError = error || (maxAmount && numericValue > maxAmount);
  const errorMessage = error || (maxAmount && numericValue > maxAmount ? `Maximum amount is ${maxAmount} ${currency}` : '');

  return (
    <div className={cn("space-y-4", className)}>
      {/* Amount Input */}
      <div className="relative">
        <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
          <DollarSign className="h-5 w-5 text-muted-foreground" />
        </div>
        <input
          type="text"
          inputMode="decimal"
          value={value}
          onChange={handleInputChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          className={cn(
            "username-input",
            "pl-10 pr-20 text-2xl font-semibold text-center",
            isFocused && "ring-2 ring-primary border-transparent",
            hasError && "border-destructive ring-destructive",
          )}
          aria-invalid={!!hasError}
          aria-describedby={hasError ? "amount-error" : undefined}
        />
        
        {/* Currency Selector */}
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          <div className="flex bg-muted rounded-lg p-1">
            <button
              type="button"
              onClick={() => onCurrencyChange("USDC")}
              className={cn(
                "px-3 py-1 text-xs font-semibold rounded transition-colors duration-150 min-h-[32px]",
                currency === "USDC" 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              USDC
            </button>
            <button
              type="button"
              onClick={() => onCurrencyChange("APT")}
              className={cn(
                "px-3 py-1 text-xs font-semibold rounded transition-colors duration-150 min-h-[32px]",
                currency === "APT" 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              APT
            </button>
          </div>
        </div>
      </div>

      {/* Error message */}
      {hasError && (
        <p id="amount-error" className="text-sm text-destructive flex items-center">
          <AlertCircle className="h-4 w-4 mr-1" />
          {errorMessage}
        </p>
      )}

      {/* Balance info */}
      {maxAmount && (
        <div className="text-sm text-muted-foreground text-center">
          Balance: {maxAmount} {currency}
        </div>
      )}

      {/* Quick Amount Suggestions */}
      <div className="grid grid-cols-4 gap-2">
        {suggestions.map((amount) => (
          <button
            key={amount}
            type="button"
            onClick={() => handleSuggestionClick(amount)}
            className="py-2 px-3 text-sm font-medium text-muted-foreground bg-muted hover:bg-muted/80 rounded-lg transition-colors duration-150 min-h-[44px] flex items-center justify-center"
          >
            {formatSuggestion(amount)}
          </button>
        ))}
      </div>
    </div>
  );
}