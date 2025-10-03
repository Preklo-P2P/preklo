import { Bell, Search, Copy, Share2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface DashboardHeaderProps {
  username: string;
  notificationCount: number;
  onSearchToggle: () => void;
  onNotificationsClick: () => void;
}

export function DashboardHeader({ username, notificationCount, onSearchToggle, onNotificationsClick }: DashboardHeaderProps) {
  const { toast } = useToast();

  const handleCopyUsername = () => {
    navigator.clipboard.writeText(username);
    toast({
      title: "Username Copied",
      description: `${username} copied to clipboard`,
    });
  };

  const handleShareUsername = () => {
    if (navigator.share) {
      navigator.share({
        title: "My Preklo Username",
        text: `Send me money on Preklo: ${username}`,
        url: window.location.origin,
      });
    } else {
      navigator.clipboard.writeText(`Send me money on Preklo: ${username}`);
      toast({
        title: "Username Shared",
        description: "Username copied to clipboard for sharing",
      });
    }
  };

  return (
    <header className="bg-background border-b border-border px-4 py-4">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-foreground">Welcome back! 👋</h1>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-sm text-muted-foreground font-mono">{username}</p>
            <button
              onClick={handleCopyUsername}
              className="p-1 rounded hover:bg-muted transition-colors duration-200"
              aria-label="Copy username"
            >
              <Copy className="h-3 w-3 text-muted-foreground" />
            </button>
            <button
              onClick={handleShareUsername}
              className="p-1 rounded hover:bg-muted transition-colors duration-200"
              aria-label="Share username"
            >
              <Share2 className="h-3 w-3 text-muted-foreground" />
            </button>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={onSearchToggle}
            className="p-2 rounded-full bg-muted hover:bg-muted/80 transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Search"
          >
            <Search className="h-5 w-5 text-muted-foreground" />
          </button>
          <button 
            onClick={onNotificationsClick}
            className="p-2 rounded-full bg-muted hover:bg-muted/80 transition-colors duration-200 relative min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5 text-muted-foreground" />
            {notificationCount > 0 && (
              <div className="absolute top-1 right-1 w-3 h-3 bg-destructive rounded-full flex items-center justify-center">
                <span className="text-xs text-destructive-foreground font-bold">
                  {notificationCount > 9 ? "9+" : notificationCount}
                </span>
              </div>
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
