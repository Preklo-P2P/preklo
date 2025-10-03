import { Send, Download, Plus } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  variant: "primary" | "secondary" | "outline" | "ghost";
}

interface QuickActionsProps {
  onNavigate: (page: string) => void;
}

export function QuickActions({ onNavigate }: QuickActionsProps) {
  const quickActions: QuickAction[] = [
    {
      id: "send",
      label: "Send Money",
      icon: <Send className="h-6 w-6" />,
      onClick: () => onNavigate("send"),
      variant: "primary",
    },
    {
      id: "receive",
      label: "Receive",
      icon: <Download className="h-6 w-6" />,
      onClick: () => onNavigate("receive"),
      variant: "secondary",
    },
    {
      id: "request",
      label: "Request",
      icon: <Plus className="h-6 w-6" />,
      onClick: () => onNavigate("request"),
      variant: "outline",
    },
  ];

  return (
    <section>
      <h2 className="text-lg font-semibold text-foreground mb-4">Quick Actions</h2>
      <div className="grid grid-cols-3 gap-3">
        {quickActions.map((action) => (
          <ActionButton
            key={action.id}
            variant={action.variant}
            onClick={action.onClick}
            icon={action.icon}
            className="flex-col gap-2 h-20"
            size="sm"
          >
            <span className="text-xs font-medium">{action.label}</span>
          </ActionButton>
        ))}
      </div>
    </section>
  );
}
