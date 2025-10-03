import { ArrowUpRight, ArrowDownLeft, Clock, CheckCircle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Transaction {
  id: string;
  type: 'sent' | 'received' | 'request';
  amount: number;
  currency: 'USDC' | 'APT';
  recipient_username?: string;
  sender_username?: string;
  description?: string;
  status: 'pending' | 'confirmed' | 'failed' | 'cancelled';
  timestamp: string;
  blockchain_hash?: string;
}

interface TransactionCardProps {
  transaction: Transaction;
  onClick?: (transaction: Transaction) => void;
  className?: string;
}

export function TransactionCard({ transaction, onClick, className }: TransactionCardProps) {
  const formatAmount = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInHours = diffInMs / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getStatusIcon = () => {
    switch (transaction.status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-warning" />;
      case 'confirmed':
        return <CheckCircle className="h-4 w-4 text-success" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-destructive" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-muted-foreground" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (transaction.status) {
      case 'pending':
        return 'text-warning';
      case 'confirmed':
        return 'text-success';
      case 'failed':
        return 'text-destructive';
      case 'cancelled':
        return 'text-muted-foreground';
      default:
        return 'text-muted-foreground';
    }
  };

  const otherUser = transaction.type === 'sent' ? transaction.recipient_username : transaction.sender_username;
  const isReceived = transaction.type === 'received';
  const isRequest = transaction.type === 'request';

  return (
    <div
      className={cn(
        "transaction-card cursor-pointer",
        onClick && "hover:bg-muted/50 active:scale-[0.99]",
        className
      )}
      onClick={() => onClick?.(transaction)}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick(transaction);
        }
      }}
    >
      <div className="flex items-center gap-4">
        {/* Transaction Icon */}
        <div className={cn(
          "w-12 h-12 rounded-full flex items-center justify-center",
          isReceived 
            ? "bg-success/10 text-success" 
            : "bg-primary/10 text-primary"
        )}>
          {isReceived ? (
            <ArrowDownLeft className="h-6 w-6" />
          ) : isRequest ? (
            <ArrowUpRight className="h-6 w-6" />
          ) : (
            <ArrowUpRight className="h-6 w-6" />
          )}
        </div>

        {/* Transaction Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-foreground truncate">
                {isReceived ? 'Received from' : isRequest ? 'Request to' : 'Sent to'} {otherUser || 'Unknown'}
              </h3>
              {getStatusIcon()}
            </div>
            <div className="text-right">
              <p className={cn(
                "font-semibold text-lg",
                isReceived ? "text-success" : "text-foreground"
              )}>
                {isReceived ? '+' : '-'}${formatAmount(transaction.amount)}
              </p>
              <p className="text-xs text-muted-foreground">
                {transaction.currency}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {transaction.description && (
                <p className="text-sm text-muted-foreground truncate max-w-[200px]">
                  {transaction.description}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className={getStatusColor()}>
                {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
              </span>
              <span className="text-muted-foreground">
                {formatTimestamp(transaction.timestamp)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}