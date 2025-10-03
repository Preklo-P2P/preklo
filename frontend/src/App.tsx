import React, { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { pwaManager } from "@/lib/pwa";
import { usePerformance, useAccessibility, useMobile, usePWA } from "@/hooks/usePerformance";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

// Import components directly to avoid lazy loading issues
import { LandingPage } from "@/components/LandingPage";
import { RegistrationPage } from "@/components/RegistrationPage";
import { LoginPage } from "@/components/LoginPage";
import { Dashboard } from "@/components/Dashboard";
import { SendMoneyFlow } from "@/components/SendMoneyFlow";
import { ReceiveMoney } from "@/components/ReceiveMoney";
import { TransactionHistory } from "@/components/TransactionHistory";
import { ProfileSettings } from "@/components/ProfileSettings";
import { Notifications } from "@/components/Notifications";
import { HelpAndSupport } from "@/components/HelpAndSupport";

// Configure React Query for mobile optimization
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && 'status' in error && typeof error.status === 'number') {
          return error.status >= 400 && error.status < 500 ? false : failureCount < 3;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false, // Disable refetch on window focus for mobile
      refetchOnReconnect: true, // Refetch when reconnecting to network
    },
  },
});


// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('App Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-destructive mb-4">
              Something went wrong
            </h1>
            <p className="text-muted-foreground mb-4">
              We're sorry, but something unexpected happened.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-primary text-primary-foreground px-6 py-3 rounded-xl font-semibold"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Main App component with mobile-first features
const App = () => {
  // Temporarily disable PWA hooks to fix rendering issues
  // const { measurePerformance } = usePerformance();
  // const { announceToScreenReader } = useAccessibility();
  // const { isMobile, isTouch } = useMobile();
  // const { isOnline, hasUpdate } = usePWA();

  useEffect(() => {
    // Initialize PWA only in production
    if (import.meta.env.PROD) {
      try {
        pwaManager.registerServiceWorker();
      } catch (error) {
        console.log('PWA initialization skipped:', error);
      }
    }

    // Add mobile-specific classes to body
    if (window.innerWidth < 768) {
      document.body.classList.add('mobile-device');
    }
    if ('ontouchstart' in window) {
      document.body.classList.add('touch-device');
    }

    return () => {
      document.body.classList.remove('mobile-device', 'touch-device');
    };
  }, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <div className="min-h-screen bg-background text-foreground">
            {/* PWA Update Notification - Temporarily disabled */}
            {/* {hasUpdate && (
              <div className="bg-primary text-primary-foreground p-3 text-center">
                <p className="text-sm">New version available!</p>
                <button
                  onClick={() => pwaManager.skipWaiting()}
                  className="underline text-sm mt-1 touch-target"
                  aria-label="Update to new version"
                >
                  Update now
                </button>
              </div>
            )} */}

            {/* Offline Indicator - Temporarily disabled */}
            {/* {!isOnline && (
              <div className="bg-warning text-warning-foreground p-2 text-center text-sm">
                You're offline. Some features may be limited.
              </div>
            )} */}

            <BrowserRouter>
                        <Routes>
                          <Route path="/" element={<Index />} />
                          <Route path="/landing" element={<LandingPage onNavigate={() => {}} />} />
                          <Route path="/register" element={<RegistrationPage onNavigate={() => {}} />} />
                          <Route path="/login" element={<LoginPage onNavigate={() => {}} />} />
                          <Route path="/dashboard" element={<Dashboard />} />
                          <Route path="/send" element={<SendMoneyFlow />} />
                          <Route path="/receive" element={<ReceiveMoney />} />
                          <Route path="/history" element={<TransactionHistory />} />
                          <Route path="/profile" element={<ProfileSettings />} />
                          <Route path="/notifications" element={<Notifications />} />
                          <Route path="/help" element={<HelpAndSupport />} />
                          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                          <Route path="*" element={<NotFound />} />
                        </Routes>
            </BrowserRouter>

            {/* Toast notifications */}
            <Toaster />
            <Sonner />
          </div>
        </TooltipProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
