import { useState, useEffect } from "react";
import { ArrowLeft, QrCode, Link, Share2, DollarSign, Bell, Clock, CheckCircle, X, Download, Copy, Mail, MessageSquare, Twitter, Facebook, Instagram } from "lucide-react";
import { QRCodeDisplay } from "@/components/ui/QRCodeDisplay";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PaymentRequestForm } from "@/components/PaymentRequestForm";
import { IncomingPaymentsList } from "@/components/IncomingPaymentsList";
import { PaymentRequestHistory } from "@/components/PaymentRequestHistory";
import { QRCodeScanner } from "@/components/QRCodeScanner";
import { QRCodeValidator } from "@/components/QRCodeValidator";
import { useToast } from "@/hooks/use-toast";
import { userService } from "@/services/userService";
import { paymentRequestService, PaymentRequest } from "@/services/paymentRequestService";

interface ReceiveMoneyProps {
  onNavigate: (page: string) => void;
}

type Tab = "qr" | "request" | "incoming" | "history";

// User interface for receive money
interface User {
  id: string;
  username: string;
  email: string;
  wallet_address: string;
}

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

// For now, we'll use a simplified approach for incoming payments
// In a full implementation, these would come from the backend
const mockIncomingPayments: IncomingPayment[] = [];

export function ReceiveMoney({ onNavigate }: ReceiveMoneyProps) {
  const [activeTab, setActiveTab] = useState<Tab>("qr");
  const [paymentRequests, setPaymentRequests] = useState<PaymentRequest[]>([]);
  const [incomingPayments, setIncomingPayments] = useState<IncomingPayment[]>(mockIncomingPayments);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingRequests, setIsLoadingRequests] = useState(false);
  const [isGeneratingQR, setIsGeneratingQR] = useState(false);
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [scannedQRData, setScannedQRData] = useState<string>("");
  const [showQRValidator, setShowQRValidator] = useState(false);
  const { toast } = useToast();

  // Load user data and payment requests
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        
        // Load user data
        const userData = await userService.getCurrentUser();
        setUser(userData);
        
        // Load payment requests
        await loadPaymentRequests();
        
      } catch (error) {
        console.error('Failed to load receive money data:', error);
        toast({
          title: "Error",
          description: "Failed to load data",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [toast]);

  // Load payment requests
  const loadPaymentRequests = async () => {
    try {
      setIsLoadingRequests(true);
      const requests = await paymentRequestService.getUserPaymentRequests();
      setPaymentRequests(requests);
    } catch (error) {
      console.error('Failed to load payment requests:', error);
      // Don't show error toast here as it's not critical
    } finally {
      setIsLoadingRequests(false);
    }
  };

  const handleSendRequest = async (request: {
    amount: number;
    currency: "USDC" | "APT";
    description: string;
    recipient: string;
    expiresAt?: Date;
  }) => {
    try {
      // For now, we'll need to get the recipient's user ID
      // In a full implementation, we'd have a name lookup service
      // For demo purposes, we'll use a placeholder
      const recipientId = "placeholder-recipient-id"; // This should be looked up from name
      
      const paymentRequestData = {
        recipient_id: recipientId,
        amount: request.amount,
        currency_type: request.currency,
        description: request.description,
        expiry_hours: 24 // Default 24 hours
      };

      const response = await paymentRequestService.createPaymentRequest(paymentRequestData);
      
      if (response.success) {
        // Reload payment requests to show the new one
        await loadPaymentRequests();
        
        toast({
          title: "Payment request sent!",
          description: `Request for ${request.amount} ${request.currency} sent to ${request.recipient}`,
        });
      }
    } catch (error) {
      console.error('Failed to send payment request:', error);
      toast({
        title: "Request failed",
        description: "Failed to send payment request. Please try again.",
        variant: "destructive",
      });
    }
  };

  const updatePaymentStatus = (paymentId: string, status: "received" | "failed", receivedAt?: Date) => {
    setIncomingPayments(prev => 
      prev.map(payment => 
        payment.id === paymentId 
          ? { ...payment, status, ...(receivedAt && { receivedAt }) }
          : payment
      )
    );

    const payment = incomingPayments.find(p => p.id === paymentId);
    if (payment) {
      if (status === "received") {
        toast({
          title: "Payment accepted!",
          description: `Received $${payment.amount} ${payment.currency} from ${payment.from}`,
        });
      } else {
        toast({
          title: "Payment rejected",
          description: `Rejected payment from ${payment.from}`,
          variant: "destructive",
        });
      }
    }
  };

  const handleAcceptPayment = (paymentId: string) => {
    updatePaymentStatus(paymentId, "received", new Date());
  };

  const handleRejectPayment = (paymentId: string) => {
    updatePaymentStatus(paymentId, "failed");
  };

  const handleCancelRequest = async (requestId: string) => {
    try {
      const response = await paymentRequestService.cancelPaymentRequest(requestId);
      
      if (response.success) {
        // Reload payment requests to show updated status
        await loadPaymentRequests();
        
        toast({
          title: "Request cancelled",
          description: "Payment request has been cancelled",
        });
      }
    } catch (error) {
      console.error('Failed to cancel payment request:', error);
      toast({
        title: "Cancel failed",
        description: "Failed to cancel payment request. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handlePayRequest = (requestId: string) => {
    // Find the payment request
    const request = paymentRequests.find(r => r.id === requestId);
    if (!request) {
      toast({
        title: "Error",
        description: "Payment request not found",
        variant: "destructive",
      });
      return;
    }

    // Store payment request data for SendMoneyFlow to use
    const paymentRequestData = {
      recipient: request.recipient || '',
      amount: request.amount.toString(),
      currency: request.currency,
      description: request.description || `Payment request from ${request.recipient}`,
      source: 'payment_request',
      timestamp: Date.now()
    };
    
    localStorage.setItem('preklo_payment_request_data', JSON.stringify(paymentRequestData));
    
    // Navigate to send money page
    onNavigate("send");
    
    toast({
      title: "Payment Request Loaded",
      description: `Ready to pay ${request.amount} ${request.currency} to ${request.recipient}`,
    });
  };

  const handleCopyRequestLink = (requestId: string) => {
    // This would copy the actual payment request link
    toast({
      title: "Link Copied",
      description: "Payment request link copied to clipboard",
    });
  };

  const handleShareRequest = (requestId: string) => {
    // This would share the payment request
    toast({
      title: "Request Shared",
      description: "Payment request has been shared",
    });
  };

  const handleQRScan = (data: string) => {
    setScannedQRData(data);
    setShowQRScanner(false);
    setShowQRValidator(true);
    
    toast({
      title: "QR Code Scanned",
      description: "QR code data captured successfully",
    });
  };

  const handleQRScanError = (error: string) => {
    toast({
      title: "Scan Error",
      description: error,
      variant: "destructive",
    });
  };

  const handleQRValidated = (isValid: boolean, data: any) => {
    if (isValid) {
      // Handle valid QR code - could be a payment request or user profile
      if (data.username) {
        // Store QR data in localStorage for SendMoneyFlow to use
        const qrPaymentData = {
          recipient: data.username,
          amount: data.amount || null,
          currency: data.currency || 'USDC',
          description: data.description || null,
          source: 'qr_scan',
          timestamp: Date.now()
        };
        
        localStorage.setItem('preklo_qr_payment_data', JSON.stringify(qrPaymentData));
        
        // Navigate to send money with pre-filled recipient
        onNavigate("send");
        toast({
          title: "QR Code Processed",
          description: data.amount 
            ? `Found payment request: ${data.amount} ${data.currency} to ${data.username}`
            : `Found user: ${data.username}`,
        });
      }
    }
    setShowQRValidator(false);
  };

  const handleQRValidationError = (error: string) => {
    toast({
      title: "Validation Error",
      description: error,
      variant: "destructive",
    });
  };

  const handleDownloadQR = () => {
    // Simulate QR code download
    setIsGeneratingQR(true);
    setTimeout(() => {
      setIsGeneratingQR(false);
      toast({
        title: "QR Code downloaded",
        description: "QR code saved to your device",
      });
    }, 1000);
  };

  const getPaymentLink = () => {
    if (!user) return "https://preklo.app/pay/loading";
    return `https://preklo.app/pay/${user.username.replace('@', '')}`;
  };

  const getQRTitle = () => {
    return "Scan to Pay Me";
  };

  const getQRSubtitle = () => {
    if (!user) return "Loading...";
    return `Send money to ${user.username}`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
      case "paid":
      case "received":
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Paid</Badge>;
      case "expired":
        return <Badge variant="destructive" className="bg-red-100 text-red-800"><X className="h-3 w-3 mr-1" />Expired</Badge>;
      case "cancelled":
      case "failed":
        return <Badge variant="destructive" className="bg-red-100 text-red-800"><X className="h-3 w-3 mr-1" />Cancelled</Badge>;
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
    return incomingPayments.filter(p => p.status === "pending").length;
  };

  const getPendingRequestsCount = () => {
    return paymentRequests.filter(r => r.status === "pending").length;
  };

  // Show loading if user data is not loaded yet
  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => onNavigate("dashboard")}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-foreground">Receive Money</h1>
            <p className="text-sm text-muted-foreground">{user?.username || "Loading..."}</p>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="px-4 py-4">
        <div className="flex bg-muted rounded-xl p-1 overflow-x-auto">
          <button
            onClick={() => setActiveTab("qr")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-medium transition-colors duration-200 min-h-[44px] whitespace-nowrap ${
              activeTab === "qr"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <QrCode className="h-4 w-4" />
            QR Code
          </button>
          <button
            onClick={() => setActiveTab("request")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-medium transition-colors duration-200 min-h-[44px] whitespace-nowrap ${
              activeTab === "request"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <DollarSign className="h-4 w-4" />
            Request
          </button>
          <button
            onClick={() => setActiveTab("incoming")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-medium transition-colors duration-200 min-h-[44px] whitespace-nowrap relative ${
              activeTab === "incoming"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Bell className="h-4 w-4" />
            Incoming
            {getIncomingCount() > 0 && (
              <div className="absolute -top-1 -right-1 w-5 h-5 bg-destructive rounded-full flex items-center justify-center">
                <span className="text-xs text-destructive-foreground font-bold">
                  {getIncomingCount()}
                </span>
              </div>
            )}
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-medium transition-colors duration-200 min-h-[44px] whitespace-nowrap ${
              activeTab === "history"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Clock className="h-4 w-4" />
            History
          </button>
        </div>
      </div>

      {/* Content */}
      <main className="px-4 pb-6">
        {activeTab === "qr" && (
          <div className="space-y-6">
            {/* User Info */}
            <div className="text-center space-y-2">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                <span className="text-2xl font-bold text-primary">
                  {user ? user.username.replace('@', '').charAt(0).toUpperCase() : "?"}
                </span>
              </div>
              <h2 className="text-xl font-semibold text-foreground">{user?.username || "Loading..."}</h2>
              <p className="text-muted-foreground">Ready to receive payments</p>
            </div>

            {/* QR Code */}
            <QRCodeDisplay
              data={getPaymentLink()}
              title={getQRTitle()}
              subtitle={getQRSubtitle()}
              size={240}
              showCustomization={true}
            />

            {/* Scan QR Code Button */}
            <div className="text-center">
              <ActionButton
                onClick={() => setShowQRScanner(true)}
                size="lg"
                className="w-full max-w-xs"
                icon={<QrCode className="h-5 w-5" />}
              >
                Scan QR Code
              </ActionButton>
              <p className="text-xs text-muted-foreground mt-2">
                Scan someone else's QR code to send them money
              </p>
            </div>

          </div>
        )}

        {activeTab === "request" && (
          <PaymentRequestForm
            username={user?.username || "Loading..."}
            paymentLink={getPaymentLink()}
            onSendRequest={handleSendRequest}
          />
        )}

        {activeTab === "incoming" && (
          <IncomingPaymentsList
            payments={incomingPayments}
            onAcceptPayment={handleAcceptPayment}
            onRejectPayment={handleRejectPayment}
          />
        )}

        {activeTab === "history" && (
          <PaymentRequestHistory
            requests={paymentRequests}
            onCancelRequest={handleCancelRequest}
            onPayRequest={handlePayRequest}
            onCopyLink={handleCopyRequestLink}
            onShareRequest={handleShareRequest}
          />
        )}
      </main>

      {/* QR Code Scanner */}
      <QRCodeScanner
        isOpen={showQRScanner}
        onClose={() => setShowQRScanner(false)}
        onScan={handleQRScan}
        onError={handleQRScanError}
        title="Scan QR Code"
        description="Position the QR code within the frame to scan"
      />

      {/* QR Code Validator */}
      {showQRValidator && scannedQRData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Validate Scanned QR Code</CardTitle>
            </CardHeader>
            <CardContent>
              <QRCodeValidator
                qrData={scannedQRData}
                onValidated={handleQRValidated}
                onError={handleQRValidationError}
              />
              <div className="flex gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowQRValidator(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={() => setShowQRScanner(true)}
                  className="flex-1"
                >
                  Scan Again
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}