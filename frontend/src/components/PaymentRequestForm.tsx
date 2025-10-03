import { useState, useEffect } from "react";
import { AmountInput } from "@/components/ui/AmountInput";
import { ActionButton } from "@/components/ui/ActionButton";
import { QRCodeDisplay } from "@/components/ui/QRCodeDisplay";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Link, Clock, Star, Zap, Copy, Share2, Mail, MessageSquare, Twitter, Facebook, Instagram } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface PaymentRequestFormProps {
  username: string;
  paymentLink: string;
  onSendRequest: (request: {
    amount: number;
    currency: "USDC" | "APT";
    description: string;
    recipient: string;
    expiresAt?: Date;
  }) => void;
}

interface PaymentRequestTemplate {
  name: string;
  amount: number;
  description: string;
  currency: "USDC" | "APT";
}

export function PaymentRequestForm({ username, paymentLink, onSendRequest }: PaymentRequestFormProps) {
  const [requestAmount, setRequestAmount] = useState("");
  const [requestCurrency, setRequestCurrency] = useState<"USDC" | "APT">("USDC");
  const [requestDescription, setRequestDescription] = useState("");
  const [recipient, setRecipient] = useState("");
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [isGeneratingQR, setIsGeneratingQR] = useState(false);
  const { toast } = useToast();

  // Mock templates - in real app, these would come from API
  const templates: PaymentRequestTemplate[] = [
    { name: "Lunch", amount: 15.00, description: "Lunch payment", currency: "USDC" },
    { name: "Rent", amount: 500.00, description: "Monthly rent", currency: "USDC" },
    { name: "Utilities", amount: 75.00, description: "Utility bill split", currency: "USDC" },
    { name: "Groceries", amount: 50.00, description: "Grocery shopping", currency: "USDC" },
    { name: "Gas", amount: 30.00, description: "Gas money", currency: "USDC" },
    { name: "Coffee", amount: 5.00, description: "Coffee run", currency: "USDC" },
  ];

  const getPaymentLink = () => {
    if (requestAmount) {
      return `${paymentLink}?amount=${requestAmount}&currency=${requestCurrency}&description=${encodeURIComponent(requestDescription)}`;
    }
    return paymentLink;
  };

  const getQRTitle = () => {
    if (requestAmount) {
      return `Request $${requestAmount}`;
    }
    return "Scan to Pay Me";
  };

  const getQRSubtitle = () => {
    if (requestAmount) {
      return requestDescription || `Payment request for $${requestAmount} ${requestCurrency}`;
    }
    return `Send money to ${username}`;
  };

  const handleTemplateSelect = (template: PaymentRequestTemplate) => {
    setRequestAmount(template.amount.toString());
    setRequestCurrency(template.currency);
    setRequestDescription(template.description);
    setShowTemplates(false);
  };

  const handleSendRequest = () => {
    if (!recipient || !requestAmount) {
      toast({
        title: "Missing Information",
        description: "Please enter recipient and amount",
        variant: "destructive",
      });
      return;
    }

    onSendRequest({
      amount: parseFloat(requestAmount),
      currency: requestCurrency,
      description: requestDescription,
      recipient,
      expiresAt: expiresAt || undefined,
    });

    // Reset form
    setRequestAmount("");
    setRequestDescription("");
    setRecipient("");
    setExpiresAt(null);
  };

  const handleCopyLink = async () => {
    try {
      const link = getPaymentLink();
      await navigator.clipboard.writeText(link);
      toast({
        title: "Link Copied",
        description: "Payment request link copied to clipboard",
      });
    } catch (error) {
      toast({
        title: "Copy Failed",
        description: "Failed to copy link to clipboard",
        variant: "destructive",
      });
    }
  };

  const handleShare = async () => {
    const link = getPaymentLink();
    const text = `Pay me $${requestAmount} ${requestCurrency}${requestDescription ? ` for ${requestDescription}` : ''} via Preklo: ${link}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: "Payment Request",
          text: text,
          url: link,
        });
      } catch (error) {
        // User cancelled sharing
      }
    } else {
      // Fallback to copying
      await handleCopyLink();
    }
  };

  return (
    <div className="space-y-6">
      {/* Templates Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-foreground">Quick Templates</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowTemplates(!showTemplates)}
            className="text-primary"
          >
            {showTemplates ? "Hide" : "Show"} Templates
          </Button>
        </div>
        
        {showTemplates && (
          <div className="grid grid-cols-2 gap-2 mb-4">
            {templates.map((template, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => handleTemplateSelect(template)}
                className="h-auto p-3 flex flex-col items-start"
              >
                <span className="font-medium">{template.name}</span>
                <span className="text-xs text-muted-foreground">
                  ${template.amount} {template.currency}
                </span>
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Request Form */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Request Amount
          </label>
          <AmountInput
            value={requestAmount}
            onChange={setRequestAmount}
            currency={requestCurrency}
            onCurrencyChange={setRequestCurrency}
            placeholder="0.00"
            suggestions={[25, 50, 100, 200]}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            What's this for? (Optional)
          </label>
          <textarea
            value={requestDescription}
            onChange={(e) => setRequestDescription(e.target.value)}
            placeholder="e.g., Lunch payment, Rent split..."
            className="w-full p-4 border border-border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none h-20"
            maxLength={100}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Send request to (Optional)
          </label>
          <input
            type="text"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            placeholder="@username or email"
            className="w-full p-4 border border-border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Expires (Optional)
          </label>
          <div className="flex gap-2">
            <Button
              variant={expiresAt ? "default" : "outline"}
              size="sm"
              onClick={() => {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                setExpiresAt(tomorrow);
              }}
            >
              1 Day
            </Button>
            <Button
              variant={expiresAt ? "default" : "outline"}
              size="sm"
              onClick={() => {
                const week = new Date();
                week.setDate(week.getDate() + 7);
                setExpiresAt(week);
              }}
            >
              1 Week
            </Button>
            <Button
              variant={expiresAt ? "default" : "outline"}
              size="sm"
              onClick={() => setExpiresAt(null)}
            >
              Never
            </Button>
          </div>
          {expiresAt && (
            <p className="text-xs text-muted-foreground mt-1">
              Expires: {expiresAt.toLocaleDateString()}
            </p>
          )}
        </div>
      </div>

      {/* Preview QR if amount is set */}
      {requestAmount && parseFloat(requestAmount) > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              Payment Request Preview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-center">
              <QRCodeDisplay
                data={getPaymentLink()}
                title={getQRTitle()}
                subtitle={getQRSubtitle()}
                size={180}
                showActions={false}
              />
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyLink}
                className="flex-1"
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy Link
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleShare}
                className="flex-1"
              >
                <Share2 className="h-4 w-4 mr-2" />
                Share
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="space-y-3">
        {recipient && (
          <ActionButton
            onClick={handleSendRequest}
            disabled={!requestAmount || parseFloat(requestAmount) <= 0}
            fullWidth
            size="lg"
          >
            Send Request
          </ActionButton>
        )}
        
        <ActionButton
          variant="ghost"
          onClick={handleCopyLink}
          disabled={!requestAmount || parseFloat(requestAmount) <= 0}
          fullWidth
          icon={<Link className="h-4 w-4" />}
        >
          Copy Request Link
        </ActionButton>
      </div>
    </div>
  );
}
