/**
 * Mobile-First Layout Component
 * Provides responsive layout with safe area support and touch-friendly interactions
 */

import React, { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { pwaManager, PWAState } from '@/lib/pwa';

interface MobileLayoutProps {
  children: React.ReactNode;
  className?: string;
  showHeader?: boolean;
  showFooter?: boolean;
  headerContent?: React.ReactNode;
  footerContent?: React.ReactNode;
  safeArea?: boolean;
  maxWidth?: 'mobile' | 'tablet' | 'desktop' | 'full';
}

export function MobileLayout({
  children,
  className,
  showHeader = true,
  showFooter = true,
  headerContent,
  footerContent,
  safeArea = true,
  maxWidth = 'mobile',
}: MobileLayoutProps) {
  const [pwaState, setPwaState] = useState<PWAState>(pwaManager.getState());
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const unsubscribe = pwaManager.subscribe(setPwaState);
    return unsubscribe;
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const maxWidthClasses = {
    mobile: 'max-w-mobile mx-auto',
    tablet: 'max-w-tablet mx-auto',
    desktop: 'max-w-4xl mx-auto',
    full: 'max-w-full',
  };

  return (
    <div className={cn(
      'min-h-screen bg-background text-foreground',
      safeArea && 'safe-area-padding',
      className
    )}>
      {/* PWA Update Banner */}
      {pwaState.hasUpdate && (
        <div className="bg-primary text-primary-foreground p-3 text-center">
          <p className="text-sm">New version available!</p>
          <button
            onClick={() => pwaManager.skipWaiting()}
            className="underline text-sm mt-1 touch-target"
          >
            Update now
          </button>
        </div>
      )}

      {/* Offline Indicator */}
      {!pwaState.isOnline && (
        <div className="bg-warning text-warning-foreground p-2 text-center text-sm">
          You're offline. Some features may be limited.
        </div>
      )}

      {/* Header */}
      {showHeader && (
        <header className={cn(
          'sticky top-0 z-safe bg-background/95 backdrop-blur-sm border-b border-border transition-shadow duration-200',
          isScrolled && 'shadow-sm',
          safeArea && 'pt-safe-top'
        )}>
          <div className={cn('container mx-auto px-4', maxWidthClasses[maxWidth])}>
            {headerContent || (
              <div className="flex items-center justify-between h-16">
                <div className="flex items-center gap-2">
                  <img 
                    src="/Preklo logo.png" 
                    alt="Preklo" 
                    className="h-8 w-auto"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  {/* Add header actions here */}
                </div>
              </div>
            )}
          </div>
        </header>
      )}

      {/* Main Content */}
      <main className={cn(
        'flex-1',
        showHeader && 'pt-0',
        showFooter && 'pb-20',
        safeArea && 'pb-safe-bottom'
      )}>
        <div className={cn('container mx-auto px-4', maxWidthClasses[maxWidth])}>
          {children}
        </div>
      </main>

      {/* Footer */}
      {showFooter && (
        <footer className={cn(
          'fixed bottom-0 left-0 right-0 z-safe bg-background/95 backdrop-blur-sm border-t border-border',
          safeArea && 'pb-safe-bottom'
        )}>
          <div className={cn('container mx-auto px-4', maxWidthClasses[maxWidth])}>
            {footerContent || (
              <div className="flex items-center justify-around h-16">
                {/* Add footer navigation here */}
                <button className="touch-target flex flex-col items-center space-y-1">
                  <div className="w-6 h-6 bg-primary rounded-full" />
                  <span className="text-xs">Home</span>
                </button>
                <button className="touch-target flex flex-col items-center space-y-1">
                  <div className="w-6 h-6 bg-muted rounded-full" />
                  <span className="text-xs">Send</span>
                </button>
                <button className="touch-target flex flex-col items-center space-y-1">
                  <div className="w-6 h-6 bg-muted rounded-full" />
                  <span className="text-xs">Receive</span>
                </button>
                <button className="touch-target flex flex-col items-center space-y-1">
                  <div className="w-6 h-6 bg-muted rounded-full" />
                  <span className="text-xs">History</span>
                </button>
              </div>
            )}
          </div>
        </footer>
      )}
    </div>
  );
}

// Touch-friendly button component
interface TouchButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  loading?: boolean;
}

export function TouchButton({
  children,
  className,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled,
  ...props
}: TouchButtonProps) {
  const variantClasses = {
    primary: 'bg-primary hover:bg-primary-dark text-primary-foreground',
    secondary: 'bg-secondary hover:bg-secondary/80 text-secondary-foreground',
    ghost: 'hover:bg-muted text-foreground',
    destructive: 'bg-destructive hover:bg-destructive/90 text-destructive-foreground',
  };

  const sizeClasses = {
    sm: 'h-10 px-4 text-sm',
    md: 'h-12 px-6 text-base',
    lg: 'h-14 px-8 text-lg',
  };

  return (
    <button
      className={cn(
        'touch-target inline-flex items-center justify-center rounded-xl font-semibold transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && 'w-full',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
          <span>Loading...</span>
        </div>
      ) : (
        children
      )}
    </button>
  );
}

// Touch-friendly input component
interface TouchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function TouchInput({
  label,
  error,
  helperText,
  className,
  ...props
}: TouchInputProps) {
  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm font-medium text-foreground">
          {label}
        </label>
      )}
      <input
        className={cn(
          'touch-target w-full px-4 py-3 bg-background border border-input rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:pointer-events-none',
          error && 'border-destructive focus:ring-destructive',
          className
        )}
        {...props}
      />
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
      {helperText && !error && (
        <p className="text-sm text-muted-foreground">{helperText}</p>
      )}
    </div>
  );
}

// Mobile-optimized card component
interface MobileCardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  clickable?: boolean;
  onClick?: () => void;
}

export function MobileCard({
  children,
  className,
  padding = 'md',
  clickable = false,
  onClick,
}: MobileCardProps) {
  const paddingClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  return (
    <div
      className={cn(
        'bg-card border border-border rounded-xl transition-all duration-200',
        paddingClasses[padding],
        clickable && 'hover:shadow-md active:scale-[0.98] cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

// Mobile-optimized list component
interface MobileListProps {
  children: React.ReactNode;
  className?: string;
  dividers?: boolean;
}

export function MobileList({
  children,
  className,
  dividers = true,
}: MobileListProps) {
  return (
    <div className={cn(
      'bg-card border border-border rounded-xl overflow-hidden',
      className
    )}>
      {React.Children.map(children, (child, index) => (
        <div key={index}>
          {child}
          {dividers && index < React.Children.count(children) - 1 && (
            <div className="border-b border-border mx-4" />
          )}
        </div>
      ))}
    </div>
  );
}

// Mobile-optimized list item component
interface MobileListItemProps {
  children: React.ReactNode;
  className?: string;
  clickable?: boolean;
  onClick?: () => void;
}

export function MobileListItem({
  children,
  className,
  clickable = false,
  onClick,
}: MobileListItemProps) {
  return (
    <div
      className={cn(
        'px-4 py-3 transition-colors duration-200',
        clickable && 'hover:bg-muted active:bg-muted/80 cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
