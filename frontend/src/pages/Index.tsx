import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Dashboard } from "@/components/Dashboard";
import { SendMoneyFlow } from "@/components/SendMoneyFlow";
import { ReceiveMoney } from "@/components/ReceiveMoney";
import { TransactionHistory } from "@/components/TransactionHistory";
import { Notifications } from "@/components/Notifications";
import { HelpAndSupport } from "@/components/HelpAndSupport";
import { Account } from "@/components/Account";
import { ProfileSettings } from "@/components/ProfileSettings";
import { SecuritySettings } from "@/components/SecuritySettings";
import { DeviceManagement } from "@/components/DeviceManagement";
import { BiometricAuth } from "@/components/BiometricAuth";
import { authService } from "@/services/authService";

const Index = () => {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [navigationHistory, setNavigationHistory] = useState<string[]>(["dashboard"]);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is authenticated using the auth service
    const checkAuth = () => {
      console.log('Checking authentication...');
      
      if (authService.isAuthenticated()) {
        console.log('User authenticated, setting isAuthenticated to true');
        setIsAuthenticated(true);
      } else {
        console.log('User not authenticated, redirecting to landing');
        // Redirect to landing page if not authenticated
        navigate('/landing');
      }
    };

    checkAuth();
  }, [navigate]);

  const handleNavigate = (page: string) => {
    if (page === "logout") {
      // Handle logout using auth service
      authService.logout();
      setIsAuthenticated(false);
      navigate('/landing#top');
      return;
    }
    
    // Don't add to history if it's the same page
    if (page !== currentPage) {
      setNavigationHistory(prev => [...prev, page]);
    }
    setCurrentPage(page);
  };

  const handleGoBack = () => {
    if (navigationHistory.length > 1) {
      const newHistory = [...navigationHistory];
      newHistory.pop(); // Remove current page
      const previousPage = newHistory[newHistory.length - 1];
      setNavigationHistory(newHistory);
      setCurrentPage(previousPage);
    } else {
      // If no history, go to dashboard
      setCurrentPage("dashboard");
    }
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard onNavigate={handleNavigate} currentPage={currentPage} />;
      case "send":
        return <SendMoneyFlow onNavigate={handleNavigate} onGoBack={handleGoBack} />;
      case "receive":
        return <ReceiveMoney onNavigate={handleNavigate} />;
      case "history":
        return <TransactionHistory onNavigate={handleNavigate} onGoBack={handleGoBack} />;
      case "notifications":
        return <Notifications onNavigate={handleNavigate} onNotificationRead={() => {
          // Refresh notification count when a notification is read
          // This will be handled by the Dashboard component when user navigates back
        }} />;
      case "help":
        return <HelpAndSupport onNavigate={handleNavigate} />;
      case "account":
        return <Account onNavigate={handleNavigate} onGoBack={handleGoBack} />;
      case "profile":
        return <ProfileSettings onNavigate={handleNavigate} onGoBack={handleGoBack} />;
      case "security":
        return <SecuritySettings onNavigate={handleNavigate} />;
      case "devices":
        return <DeviceManagement onNavigate={handleNavigate} />;
      case "biometric":
        return <BiometricAuth onNavigate={handleNavigate} />;
      default:
        return <Dashboard onNavigate={handleNavigate} />;
    }
  };

  // Show loading while checking authentication
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <Layout currentPage={currentPage} onNavigate={handleNavigate}>
      {renderCurrentPage()}
    </Layout>
  );
};

export default Index;