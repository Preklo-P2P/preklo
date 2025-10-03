import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface NavigationTabProps {
  icon: React.ReactNode;
  label: string;
  isActive?: boolean;
  badge?: number;
  onClick?: () => void;
  className?: string;
}

const NavigationTab = forwardRef<HTMLButtonElement, NavigationTabProps>(
  ({ icon, label, isActive = false, badge, onClick, className }, ref) => {
    return (
      <button
        ref={ref}
        onClick={onClick}
        className={cn(
          "flex flex-col items-center justify-center py-2 px-1 min-h-[60px] relative transition-colors duration-200",
          isActive 
            ? "text-primary" 
            : "text-muted-foreground hover:text-foreground",
          className
        )}
        aria-label={label}
        aria-current={isActive ? "page" : undefined}
      >
        <div className="relative mb-1">
          {icon}
          {badge !== undefined && badge > 0 && (
            <div className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
              {badge > 99 ? '99+' : badge}
            </div>
          )}
        </div>
        <span className={cn(
          "text-xs font-medium transition-colors duration-200",
          isActive ? "text-primary" : "text-muted-foreground"
        )}>
          {label}
        </span>
        {isActive && (
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-primary rounded-full" />
        )}
      </button>
    );
  }
);

NavigationTab.displayName = "NavigationTab";

export { NavigationTab };