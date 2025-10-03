import { useState, useCallback } from "react";
import { Search, Check, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface UsernameInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  isValidating?: boolean;
  isValid?: boolean | null;
  error?: string;
  suggestions?: string[];
  onSelectSuggestion?: (username: string) => void;
  className?: string;
}

export function UsernameInput({
  value,
  onChange,
  placeholder = "Enter name",
  isValidating = false,
  isValid = null,
  error,
  suggestions = [],
  onSelectSuggestion,
  className
}: UsernameInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    let inputValue = e.target.value;
    
    // Ensure @ prefix
    if (inputValue && !inputValue.startsWith('@')) {
      inputValue = '@' + inputValue;
    }
    
    // Remove @ if input is empty
    if (inputValue === '@') {
      inputValue = '';
    }
    
    onChange(inputValue);
    setShowSuggestions(inputValue.length > 1);
  }, [onChange]);

  const handleSuggestionClick = useCallback((name: string) => {
    onChange(name);
    setShowSuggestions(false);
    onSelectSuggestion?.(name);
  }, [onChange, onSelectSuggestion]);

  const handleFocus = () => {
    setIsFocused(true);
    if (value.length > 1) {
      setShowSuggestions(true);
    }
  };

  const handleBlur = () => {
    setIsFocused(false);
    // Delay hiding suggestions to allow for click
    setTimeout(() => setShowSuggestions(false), 150);
  };

  const getValidationIcon = () => {
    if (isValidating) {
      return <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />;
    }
    if (isValid === true) {
      return <Check className="h-4 w-4 text-success" />;
    }
    if (isValid === false || error) {
      return <AlertCircle className="h-4 w-4 text-destructive" />;
    }
    return null;
  };

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <div className="absolute left-3 top-1/2 transform -translate-y-1/2 flex items-center">
          <Search className="h-4 w-4 text-muted-foreground mr-2" />
          {!value && <span className="text-muted-foreground text-base">@</span>}
        </div>
        <input
          type="text"
          value={value}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          className={cn(
            "username-input",
            "pl-12 pr-12",
            isFocused && "ring-2 ring-primary border-transparent",
            error && "border-destructive ring-destructive",
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? "username-error" : undefined}
        />
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          {getValidationIcon()}
        </div>
      </div>

      {/* Error message */}
      {error && (
        <p id="username-error" className="mt-2 text-sm text-destructive flex items-center">
          <AlertCircle className="h-4 w-4 mr-1" />
          {error}
        </p>
      )}

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-popover border border-border rounded-xl shadow-lg max-h-48 overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="w-full px-4 py-3 text-left hover:bg-muted transition-colors duration-150 flex items-center min-h-[44px] first:rounded-t-xl last:rounded-b-xl"
              onClick={() => handleSuggestionClick(suggestion)}
              type="button"
            >
              <div className="flex items-center">
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center mr-3">
                  <span className="text-primary font-semibold text-sm">
                    {suggestion.replace('@', '').charAt(0).toUpperCase()}
                  </span>
                </div>
                <span className="text-base font-medium">{suggestion}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}