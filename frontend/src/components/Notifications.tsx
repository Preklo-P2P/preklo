import { useState, useEffect } from "react";
import { Bell, Check, X, Filter, MoreVertical, Archive, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator 
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/hooks/use-toast";
import { notificationService, Notification as BackendNotification } from "@/services/notificationService";

interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: Date;
  isRead: boolean;
  actionUrl?: string;
  actionLabel?: string;
}

interface NotificationsProps {
  onNavigate: (page: string) => void;
  onNotificationRead?: () => void;
}

export function Notifications({ onNavigate, onNotificationRead }: NotificationsProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unread" | "success" | "warning" | "error" | "info">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const { toast } = useToast();

  // Map backend notification to frontend format
  const mapBackendNotification = (backendNotification: BackendNotification): Notification => {
    // Map backend notification types to frontend types
    let frontendType: "info" | "success" | "warning" | "error" = "info";
    
    switch (backendNotification.type) {
      case "payment_request":
        frontendType = "info";
        break;
      case "payment_received":
        frontendType = "success";
        break;
      case "payment_sent":
        frontendType = "success";
        break;
      case "system":
        frontendType = "info";
        break;
      default:
        frontendType = "info";
    }

    // Determine action based on notification type and data
    let actionUrl: string | undefined;
    let actionLabel: string | undefined;

    if (backendNotification.type === "payment_request") {
      actionUrl = "pay_request";
      actionLabel = "Pay Request";
    } else if (backendNotification.type === "payment_received" || backendNotification.type === "payment_sent") {
      actionUrl = "history";
      actionLabel = "View Transaction";
    }

    return {
      id: backendNotification.id,
      type: frontendType,
      title: backendNotification.title,
      message: backendNotification.message,
      timestamp: new Date(backendNotification.created_at),
      isRead: backendNotification.is_read,
      actionUrl,
      actionLabel
    };
  };

  // Load notifications from backend
  useEffect(() => {
    const loadNotifications = async () => {
      try {
        setIsLoading(true);
        const backendNotifications = await notificationService.getUserNotifications();
        const mappedNotifications = backendNotifications.map(mapBackendNotification);
        setNotifications(mappedNotifications);
      } catch (error) {
        console.error('Failed to load notifications:', error);
        toast({
          title: "Error",
          description: "Failed to load notifications",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadNotifications();
  }, [toast]);

  const filteredNotifications = notifications.filter(notification => {
    const matchesFilter = filter === "all" || 
      (filter === "unread" && !notification.isRead) ||
      notification.type === filter;
    
    const matchesSearch = searchQuery === "" ||
      notification.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      notification.message.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

  const unreadCount = notifications.filter(n => !n.isRead).length;

  const markAsRead = async (id: string) => {
    try {
      await notificationService.markNotificationAsRead(id);
      setNotifications(prev => 
        prev.map(notification => 
          notification.id === id 
            ? { ...notification, isRead: true }
            : notification
        )
      );
      toast({
        title: "Notification marked as read",
      });
      
      // Notify parent component that a notification was read
      onNotificationRead?.();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      toast({
        title: "Error",
        description: "Failed to mark notification as read",
        variant: "destructive",
      });
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationService.markAllNotificationsAsRead();
      setNotifications(prev => 
        prev.map(notification => ({ ...notification, isRead: true }))
      );
      toast({
        title: "All notifications marked as read",
      });
      
      // Notify parent component that notifications were read
      onNotificationRead?.();
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      toast({
        title: "Error",
        description: "Failed to mark all notifications as read",
        variant: "destructive",
      });
    }
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
    toast({
      title: "Notification deleted",
    });
  };

  const clearAllRead = () => {
    setNotifications(prev => prev.filter(notification => !notification.isRead));
    toast({
      title: "Read notifications cleared",
    });
  };

  const handlePayRequest = (notification: Notification) => {
    // Extract payment request data from notification
    // For now, we'll parse the message to get basic info
    // In a real implementation, the notification would include structured data
    
    // Parse notification message to extract payment details
    const message = notification.message;
    const amountMatch = message.match(/(\d+(?:\.\d{2})?)\s+(USDC|APT)/);
    const usernameMatch = message.match(/@(\w+)/);
    
    if (amountMatch && usernameMatch) {
      const amount = amountMatch[1];
      const currency = amountMatch[2] as "USDC" | "APT";
      const username = usernameMatch[1];
      
      // Store payment request data for SendMoneyFlow to use
      const paymentRequestData = {
        recipient: username,
        amount: amount,
        currency: currency,
        description: `Payment request from ${username}`,
        source: 'payment_request',
        timestamp: Date.now()
      };
      
      localStorage.setItem('preklo_payment_request_data', JSON.stringify(paymentRequestData));
      
      // Navigate to send money page
      onNavigate("send");
      
      toast({
        title: "Payment Request Loaded",
        description: `Ready to pay ${amount} ${currency} to ${username}`,
      });
    } else {
      // Fallback: navigate to receive page to view the request
      onNavigate("receive");
      
      toast({
        title: "View Payment Request",
        description: "Navigate to receive page to view payment details",
      });
    }
  };

  const getNotificationStyle = (type: string) => {
    switch (type) {
      case "success":
        return { badgeVariant: "default" as const, icon: "✓" };
      case "warning":
        return { badgeVariant: "destructive" as const, icon: "!" };
      case "error":
        return { badgeVariant: "destructive" as const, icon: "X" };
      default:
        return { badgeVariant: "secondary" as const, icon: "i" };
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 60) {
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else {
      return `${days}d ago`;
    }
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate("dashboard")}
              className="p-2 rounded-full hover:bg-muted transition-colors duration-200"
              aria-label="Back to dashboard"
            >
              ←
            </button>
            <div>
              <h1 className="text-2xl font-bold text-foreground">Notifications</h1>
              <p className="text-sm text-muted-foreground">
                {unreadCount > 0 ? `${unreadCount} unread` : "All caught up!"}
              </p>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={markAllAsRead}>
                <Check className="h-4 w-4 mr-2" />
                Mark all as read
              </DropdownMenuItem>
              <DropdownMenuItem onClick={clearAllRead}>
                <Archive className="h-4 w-4 mr-2" />
                Clear read
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Filters and Search */}
      <div className="px-4 py-4 space-y-4">
        {/* Search */}
        <div className="relative">
          <Input
            type="text"
            placeholder="Search notifications..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {[
            { key: "all", label: "All", count: notifications.length },
            { key: "unread", label: "Unread", count: unreadCount },
            { key: "success", label: "Success", count: notifications.filter(n => n.type === "success").length },
            { key: "warning", label: "Warning", count: notifications.filter(n => n.type === "warning").length },
            { key: "error", label: "Error", count: notifications.filter(n => n.type === "error").length },
            { key: "info", label: "Info", count: notifications.filter(n => n.type === "info").length },
          ].map(({ key, label, count }) => (
            <button
              key={key}
              onClick={() => setFilter(key as any)}
              className={`px-3 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors duration-200 ${
                filter === key
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {label} {count > 0 && `(${count})`}
            </button>
          ))}
        </div>
      </div>

      {/* Notifications List */}
      <main className="px-4 space-y-3">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading notifications...</p>
          </div>
        ) : filteredNotifications.length > 0 ? (
          filteredNotifications.map((notification) => (
            <Card 
              key={notification.id} 
              className={`transition-all duration-200 cursor-pointer ${
                !notification.isRead 
                  ? "border-l-4 border-l-primary bg-primary/5" 
                  : "opacity-75"
              }`}
              onClick={async () => {
                // Auto-mark as read when notification card is clicked
                if (!notification.isRead) {
                  await markAsRead(notification.id);
                }
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="text-2xl">{getNotificationStyle(notification.type).icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground text-sm">
                          {notification.title}
                        </h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          {notification.message}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-muted-foreground">
                            {formatTimestamp(notification.timestamp)}
                          </span>
                          <Badge variant={getNotificationStyle(notification.type).badgeVariant} className="text-xs">
                            {notification.type}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {!notification.isRead && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="p-1 rounded hover:bg-muted transition-colors duration-200"
                            aria-label="Mark as read"
                          >
                            <Check className="h-4 w-4 text-muted-foreground" />
                          </button>
                        )}
                        <button
                          onClick={() => deleteNotification(notification.id)}
                          className="p-1 rounded hover:bg-muted transition-colors duration-200"
                          aria-label="Delete notification"
                        >
                          <Trash2 className="h-4 w-4 text-muted-foreground" />
                        </button>
                      </div>
                    </div>
                    {notification.actionUrl && notification.actionLabel && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="mt-3"
                        onClick={async () => {
                          // Auto-mark as read when action is clicked
                          if (!notification.isRead) {
                            await markAsRead(notification.id);
                          }
                          
                          // Handle payment request action
                          if (notification.actionUrl === "pay_request") {
                            handlePayRequest(notification);
                          } else {
                            onNavigate(notification.actionUrl!);
                          }
                        }}
                      >
                        {notification.actionLabel}
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Bell className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              {searchQuery || filter !== "all" ? "No matching notifications" : "No notifications yet"}
            </h3>
            <p className="text-muted-foreground">
              {searchQuery || filter !== "all" 
                ? "Try adjusting your search or filter" 
                : "You'll see important updates and alerts here"}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
