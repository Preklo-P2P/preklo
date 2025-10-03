import { useState } from "react";
import { Home, Send, Download, History, Settings, HelpCircle } from "lucide-react";
import { NavigationTab } from "@/components/ui/NavigationTab";

interface LayoutProps {
  children: React.ReactNode;
  currentPage: string;
  onNavigate: (page: string) => void;
}

export function Layout({ children, currentPage, onNavigate }: LayoutProps) {
  const [notificationCount] = useState(3); // Mock notification count

  const navigationTabs = [
    {
      id: "dashboard",
      label: "Home",
      icon: <Home className="h-6 w-6" />,
    },
    {
      id: "send",
      label: "Send",
      icon: <Send className="h-6 w-6" />,
    },
    {
      id: "receive",
      label: "Request",
      icon: <Download className="h-6 w-6" />,
    },
    {
      id: "history",
      label: "History",
      icon: <History className="h-6 w-6" />,
    },
    {
      id: "account",
      label: "Account",
      icon: <Settings className="h-6 w-6" />,
      badge: currentPage === "account" ? undefined : notificationCount,
    },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {children}
      </div>

      {/* Bottom Navigation */}
      <nav className="bg-background border-t border-border px-2 py-1 sticky bottom-0 z-50">
        <div className="flex items-center justify-around max-w-md mx-auto">
          {navigationTabs.map((tab) => (
            <NavigationTab
              key={tab.id}
              icon={tab.icon}
              label={tab.label}
              isActive={currentPage === tab.id}
              badge={tab.badge}
              onClick={() => onNavigate(tab.id)}
              className="flex-1"
            />
          ))}
        </div>
      </nav>

      {/* Floating Help Button */}
      {currentPage !== "help" && (
        <button
          onClick={() => onNavigate("help")}
          className="fixed bottom-20 right-4 w-14 h-14 bg-primary text-primary-foreground rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center z-40 touch-target"
          aria-label="Get help and support"
        >
          <HelpCircle className="h-6 w-6" />
        </button>
      )}
    </div>
  );
}