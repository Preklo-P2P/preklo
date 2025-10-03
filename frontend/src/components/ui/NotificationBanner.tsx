import { useState } from "react";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface NotificationBannerProps {
  type: "success" | "error" | "warning" | "info";
  title: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
}

export function NotificationBanner({
  type,
  title,
  message,
  action,
  dismissible = true,
  onDismiss,
  className
}: NotificationBannerProps) {
  const [isVisible, setIsVisible] = useState(true);

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.();
  };

  const getIcon = () => {
    switch (type) {
      case "success":
        return <CheckCircle className="h-5 w-5" />;
      case "error":
        return <AlertCircle className="h-5 w-5" />;
      case "warning":
        return <AlertTriangle className="h-5 w-5" />;
      case "info":
        return <Info className="h-5 w-5" />;
    }
  };

  const getStyles = () => {
    switch (type) {
      case "success":
        return "bg-success/10 border-success/20 text-success";
      case "error":
        return "bg-destructive/10 border-destructive/20 text-destructive";
      case "warning":
        return "bg-warning/10 border-warning/20 text-warning";
      case "info":
        return "bg-accent/10 border-accent/20 text-accent";
    }
  };

  if (!isVisible) return null;

  return (
    <div className={cn(
      "flex items-start gap-3 p-4 rounded-xl border transition-all duration-300",
      getStyles(),
      className
    )}>
      {/* Icon */}
      <div className="flex-shrink-0 mt-0.5">
        {getIcon()}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-sm mb-1">{title}</h4>
        {message && (
          <p className="text-sm opacity-90 leading-relaxed">{message}</p>
        )}
        
        {/* Action Button */}
        {action && (
          <button
            onClick={action.onClick}
            className="mt-3 text-sm font-medium underline hover:no-underline transition-all duration-200"
          >
            {action.label}
          </button>
        )}
      </div>

      {/* Dismiss Button */}
      {dismissible && (
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 p-1 rounded-full hover:bg-black/10 transition-colors duration-200 min-h-[32px] min-w-[32px] flex items-center justify-center"
          aria-label="Dismiss notification"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

// Hook for managing notifications
export function useNotification() {
  const [notifications, setNotifications] = useState<Array<{
    id: string;
    type: "success" | "error" | "warning" | "info";
    title: string;
    message?: string;
    action?: {
      label: string;
      onClick: () => void;
    };
    dismissible?: boolean;
    autoClose?: number;
  }>>([]);

  const addNotification = (notification: Omit<typeof notifications[0], 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newNotification = { ...notification, id };
    
    setNotifications(prev => [...prev, newNotification]);

    // Auto close if specified
    if (notification.autoClose) {
      setTimeout(() => {
        removeNotification(id);
      }, notification.autoClose);
    }

    return id;
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  return {
    notifications,
    addNotification,
    removeNotification,
    clearAll,
  };
}