import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { 
  Gift, 
  DollarSign, 
  Clock, 
  Shield, 
  Eye, 
  EyeOff, 
  Copy, 
  Share2,
  QrCode,
  CheckCircle,
  AlertCircle
} from "lucide-react";
import { QRCodeDisplay } from "@/components/ui/QRCodeDisplay";

interface VoucherCreationProps {
  onVoucherCreated?: (voucher: any) => void;
  onClose?: () => void;
}

export function VoucherCreation({ onVoucherCreated, onClose }: VoucherCreationProps) {
  const { toast } = useToast();
  const [step, setStep] = useState(1);
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USDC");
  const [pin, setPin] = useState("");
  const [showPin, setShowPin] = useState(false);
  const [expiresInHours, setExpiresInHours] = useState(24);
  const [isCreating, setIsCreating] = useState(false);
  const [createdVoucher, setCreatedVoucher] = useState<any>(null);

  const expirationOptions = [
    { value: 1, label: "1 Hour" },
    { value: 6, label: "6 Hours" },
    { value: 24, label: "1 Day" },
    { value: 72, label: "3 Days" },
    { value: 168, label: "1 Week" }
  ];

  const handleCreateVoucher = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast({
        title: "Invalid Amount",
        description: "Please enter a valid amount greater than 0",
        variant: "destructive"
      });
      return;
    }

    if (parseFloat(amount) > 10000) {
      toast({
        title: "Amount Too High",
        description: "Maximum voucher amount is $10,000",
        variant: "destructive"
      });
      return;
    }

    setIsCreating(true);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      const voucher = {
        id: `voucher-${Date.now()}`,
        voucher_code: generateVoucherCode(),
        amount: parseFloat(amount),
        currency,
        pin: pin || null,
        expires_at: new Date(Date.now() + expiresInHours * 60 * 60 * 1000),
        status: "active",
        created_at: new Date()
      };

      setCreatedVoucher(voucher);
      setStep(3);

      toast({
        title: "Voucher Created!",
        description: `Voucher ${voucher.voucher_code} created successfully`,
      });

      if (onVoucherCreated) {
        onVoucherCreated(voucher);
      }
    } catch (error) {
      toast({
        title: "Creation Failed",
        description: "Failed to create voucher. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsCreating(false);
    }
  };

  const generateVoucherCode = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 20; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const handleCopyCode = () => {
    if (createdVoucher) {
      navigator.clipboard.writeText(createdVoucher.voucher_code);
      toast({
        title: "Copied!",
        description: "Voucher code copied to clipboard",
      });
    }
  };

  const handleShareVoucher = () => {
    if (createdVoucher) {
      const shareData = {
        title: "Preklo Voucher",
        text: `I've created a voucher for $${createdVoucher.amount} ${createdVoucher.currency}. Code: ${createdVoucher.voucher_code}`,
        url: window.location.origin
      };

      if (navigator.share) {
        navigator.share(shareData);
      } else {
        navigator.clipboard.writeText(shareData.text);
        toast({
          title: "Shared!",
          description: "Voucher details copied to clipboard",
        });
      }
    }
  };

  const getVoucherLink = () => {
    if (createdVoucher) {
      return `${window.location.origin}/redeem/${createdVoucher.voucher_code}`;
    }
    return "";
  };

  const getQRTitle = () => {
    if (createdVoucher) {
      return `$${createdVoucher.amount} ${createdVoucher.currency}`;
    }
    return "";
  };

  const getQRSubtitle = () => {
    if (createdVoucher) {
      return `Code: ${createdVoucher.voucher_code}`;
    }
    return "";
  };

  if (step === 3 && createdVoucher) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-foreground mb-2">Voucher Created!</h2>
          <p className="text-muted-foreground">
            Your voucher is ready to share
          </p>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Gift className="h-5 w-5 text-primary" />
              Voucher Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-muted-foreground">Amount</Label>
                <p className="text-lg font-semibold">${createdVoucher.amount} {createdVoucher.currency}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Code</Label>
                <div className="flex items-center gap-2">
                  <p className="text-lg font-mono font-semibold">{createdVoucher.voucher_code}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopyCode}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-muted-foreground">Expires</Label>
                <p className="text-sm">{createdVoucher.expires_at.toLocaleDateString()}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Status</Label>
                <Badge variant="default" className="bg-green-100 text-green-800">
                  Active
                </Badge>
              </div>
            </div>

            {createdVoucher.pin && (
              <div>
                <Label className="text-sm text-muted-foreground">PIN Protected</Label>
                <p className="text-sm flex items-center gap-2">
                  <Shield className="h-4 w-4 text-blue-600" />
                  This voucher requires a PIN for redemption
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <QrCode className="h-5 w-5 text-primary" />
              Share Voucher
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-center">
              <QRCodeDisplay
                data={getVoucherLink()}
                title={getQRTitle()}
                subtitle={getQRSubtitle()}
                size={200}
                showActions={false}
              />
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleCopyCode}
                className="flex-1"
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy Code
              </Button>
              <Button
                variant="outline"
                onClick={handleShareVoucher}
                className="flex-1"
              >
                <Share2 className="h-4 w-4 mr-2" />
                Share
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => {
              setStep(1);
              setCreatedVoucher(null);
              setAmount("");
              setPin("");
            }}
            className="flex-1"
          >
            Create Another
          </Button>
          <Button
            onClick={onClose}
            className="flex-1"
          >
            Done
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-primary" />
            Voucher Details
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="amount">Amount</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="amount"
                  type="number"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="pl-10"
                  min="0.01"
                  max="10000"
                  step="0.01"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="currency">Currency</Label>
              <Select value={currency} onValueChange={setCurrency}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USDC">USDC</SelectItem>
                  <SelectItem value="APT">APT</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="pin">PIN (Optional)</Label>
            <div className="relative">
              <Shield className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="pin"
                type={showPin ? "text" : "password"}
                placeholder="4-6 digits"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                className="pl-10 pr-10"
                maxLength={6}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => setShowPin(!showPin)}
              >
                {showPin ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              PIN adds extra security for voucher redemption
            </p>
          </div>

          <div>
            <Label htmlFor="expires">Expires In</Label>
            <Select value={expiresInHours.toString()} onValueChange={(value) => setExpiresInHours(parseInt(value))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {expirationOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value.toString()}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
            <div className="space-y-1">
              <h4 className="font-medium text-amber-900">Important</h4>
              <ul className="text-sm text-amber-800 space-y-1">
                <li>• Vouchers expire automatically and cannot be extended</li>
                <li>• Only the creator can cancel an active voucher</li>
                <li>• Keep your voucher code and PIN secure</li>
                <li>• Vouchers can be redeemed at authorized agents</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={onClose}
          className="flex-1"
        >
          Cancel
        </Button>
        <Button
          onClick={handleCreateVoucher}
          disabled={!amount || parseFloat(amount) <= 0 || isCreating}
          className="flex-1"
        >
          {isCreating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              Creating...
            </>
          ) : (
            <>
              <Gift className="h-4 w-4 mr-2" />
              Create Voucher
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
