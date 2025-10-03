import { useEffect, useRef } from "react";
import { X, Copy, Share2, Eye } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Transaction {
  id: string;
  type: "sent" | "received" | "request";
  amount: number;
  currency: "USDC" | "APT";
  sender_username?: string;
  recipient_username?: string;
  description: string;
  status: "pending" | "confirmed" | "failed" | "cancelled";
  timestamp: string;
  blockchain_hash?: string;
  fee?: number;
  notes?: string;
  tags?: string[];
  isNew?: boolean;
}

interface TransactionDetailsModalProps {
  transaction: Transaction | null;
  isOpen: boolean;
  onClose: () => void;
  onShare: (transaction: Transaction) => void;
  onCopyId: (transaction: Transaction) => void;
}

export function TransactionDetailsModal({ 
  transaction, 
  isOpen, 
  onClose, 
  onShare, 
  onCopyId 
}: TransactionDetailsModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen || !transaction) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <Card 
        ref={modalRef}
        className="w-full max-w-lg max-h-[85vh] overflow-y-auto shadow-2xl animate-in fade-in-0 zoom-in-95 duration-200"
      >
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg">Transaction Details</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
          >
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-6 p-6">
          {/* Transaction Amount - Prominent Display */}
          <div className="text-center py-4 border-b border-border">
            <div className="text-3xl font-bold text-foreground mb-1">
              ${transaction.amount} {transaction.currency}
            </div>
            <div className="flex items-center justify-center gap-2">
              <Badge variant={transaction.type === "sent" ? "destructive" : "default"}>
                {transaction.type.toUpperCase()}
              </Badge>
              <Badge variant={
                transaction.status === "confirmed" ? "default" :
                transaction.status === "pending" ? "secondary" : "destructive"
              }>
                {transaction.status.toUpperCase()}
              </Badge>
            </div>
          </div>

          {/* Transaction Info */}
          <div className="space-y-4">
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {transaction.type === "sent" ? "To" : "From"}
              </span>
              <span className="text-sm font-medium">
                {transaction.type === "sent" 
                  ? transaction.recipient_username 
                  : transaction.sender_username}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Date</span>
              <span className="text-sm">
                {new Date(transaction.timestamp).toLocaleDateString()}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Time</span>
              <span className="text-sm">
                {new Date(transaction.timestamp).toLocaleTimeString()}
              </span>
            </div>
            
            {transaction.fee && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Fee</span>
                <span className="text-sm">${transaction.fee}</span>
              </div>
            )}
          </div>

          {/* Description */}
          <div>
            <span className="text-sm text-muted-foreground">Description</span>
            <p className="text-sm mt-1">{transaction.description}</p>
          </div>

          {/* Notes */}
          {transaction.notes && (
            <div>
              <span className="text-sm text-muted-foreground">Notes</span>
              <p className="text-sm mt-1">{transaction.notes}</p>
            </div>
          )}

          {/* Tags */}
          {transaction.tags && transaction.tags.length > 0 && (
            <div>
              <span className="text-sm text-muted-foreground">Tags</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {transaction.tags.map((tag, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Blockchain Hash */}
          {transaction.blockchain_hash && (
            <div>
              <span className="text-sm text-muted-foreground">Transaction Hash</span>
              <div className="flex items-center gap-2 mt-1">
                <code className="text-xs bg-muted px-2 py-1 rounded flex-1 break-all">
                  {transaction.blockchain_hash}
                </code>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onCopyId(transaction)}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => onShare(transaction)}
              className="flex-1"
            >
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </Button>
            {transaction.blockchain_hash && (
              <Button
                variant="outline"
                onClick={() => {
                  window.open(`https://explorer.aptoslabs.com/txn/${transaction.blockchain_hash}`, '_blank');
                }}
                className="flex-1"
              >
                <Eye className="h-4 w-4 mr-2" />
                View on Explorer
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
