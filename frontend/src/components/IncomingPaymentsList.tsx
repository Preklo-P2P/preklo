import { Bell, CheckCircle, X, Clock } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface IncomingPayment {
  id: string;
  amount: number;
  currency: "USDC" | "APT";
  description: string;
  from: string;
  status: "pending" | "received" | "failed";
  createdAt: Date;
  receivedAt?: Date;
}

interface IncomingPaymentsListProps {
  payments: IncomingPayment[];
  onAcceptPayment: (paymentId: string) => void;
  onRejectPayment: (paymentId: string) => void;
}

export function IncomingPaymentsList({ payments, onAcceptPayment, onRejectPayment }: IncomingPaymentsListProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
      case "received":
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Paid</Badge>;
      case "failed":
        return <Badge variant="destructive" className="bg-red-100 text-red-800"><X className="h-3 w-3 mr-1" />Failed</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
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

  const getIncomingCount = () => {
    return payments.filter(p => p.status === "pending").length;
  };

  if (payments.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
          <Bell className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">No incoming payments</h3>
        <p className="text-muted-foreground">
          You'll see incoming payments here when someone sends you money
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Incoming Payments</h2>
        <Badge variant="secondary">
          {getIncomingCount()} pending
        </Badge>
      </div>

      <div className="space-y-3">
        {payments.map((payment) => (
          <Card key={payment.id} className={`${payment.status === "pending" ? "border-l-4 border-l-primary bg-primary/5" : ""}`}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-foreground">
                      ${payment.amount} {payment.currency}
                    </h3>
                    {getStatusBadge(payment.status)}
                  </div>
                  <p className="text-sm text-muted-foreground mb-1">
                    From: {payment.from}
                  </p>
                  {payment.description && (
                    <p className="text-sm text-foreground mb-2">
                      {payment.description}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {formatTimeAgo(payment.createdAt)}
                  </p>
                </div>
                
                {payment.status === "pending" && (
                  <div className="flex gap-2 ml-4">
                    <Button
                      size="sm"
                      onClick={() => onAcceptPayment(payment.id)}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Accept
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onRejectPayment(payment.id)}
                      className="border-red-300 text-red-600 hover:bg-red-50"
                    >
                      <X className="h-4 w-4 mr-1" />
                      Reject
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
