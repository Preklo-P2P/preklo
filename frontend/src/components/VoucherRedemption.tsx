import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { 
  Gift, 
  Key, 
  Eye, 
  EyeOff, 
  CheckCircle, 
  AlertCircle,
  Clock,
  User,
  DollarSign,
  Shield,
  MapPin,
  Phone
} from "lucide-react";

interface VoucherRedemptionProps {
  onVoucherRedeemed?: (voucher: any) => void;
  onClose?: () => void;
}

export function VoucherRedemption({ onVoucherRedeemed, onClose }: VoucherRedemptionProps) {
  const { toast } = useToast();
  const [step, setStep] = useState(1);
  const [voucherCode, setVoucherCode] = useState("");
  const [pin, setPin] = useState("");
  const [showPin, setShowPin] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isRedeeming, setIsRedeeming] = useState(false);
  const [voucher, setVoucher] = useState<any>(null);
  const [redeemedVoucher, setRedeemedVoucher] = useState<any>(null);

  const mockVoucher = {
    id: "voucher-123",
    voucher_code: "ABC123DEF456GHI789",
    amount: 100,
    currency: "USDC",
    status: "active",
    has_pin: true,
    expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000),
    creator_username: "john_doe",
    time_remaining: "23h 45m"
  };

  const mockAgents = [
    {
      id: "agent-1",
      name: "QuickCash Store",
      address: "123 Main Street",
      city: "New York",
      phone: "+1-555-0123",
      distance: "0.5 km"
    },
    {
      id: "agent-2",
      name: "MoneyMart",
      address: "456 Oak Avenue",
      city: "New York",
      phone: "+1-555-0456",
      distance: "1.2 km"
    }
  ];

  const handleValidateVoucher = async () => {
    if (!voucherCode || voucherCode.length !== 20) {
      toast({
        title: "Invalid Code",
        description: "Please enter a valid 20-character voucher code",
        variant: "destructive"
      });
      return;
    }

    setIsValidating(true);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock validation - in real app, this would be an API call
      if (voucherCode.toUpperCase() === "ABC123DEF456GHI789") {
        setVoucher(mockVoucher);
        setStep(2);
      } else {
        toast({
          title: "Voucher Not Found",
          description: "The voucher code you entered is invalid or expired",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Validation Failed",
        description: "Failed to validate voucher. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleRedeemVoucher = async () => {
    if (voucher.has_pin && !pin) {
      toast({
        title: "PIN Required",
        description: "This voucher requires a PIN for redemption",
        variant: "destructive"
      });
      return;
    }

    setIsRedeeming(true);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      const redeemed = {
        ...voucher,
        status: "redeemed",
        redeemed_at: new Date(),
        redeemed_by: "current_user"
      };

      setRedeemedVoucher(redeemed);
      setStep(3);

      toast({
        title: "Voucher Redeemed!",
        description: `Successfully redeemed $${voucher.amount} ${voucher.currency}`,
      });

      if (onVoucherRedeemed) {
        onVoucherRedeemed(redeemed);
      }
    } catch (error) {
      toast({
        title: "Redemption Failed",
        description: "Failed to redeem voucher. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsRedeeming(false);
    }
  };

  const formatTimeRemaining = (timeStr: string) => {
    return timeStr;
  };

  if (step === 3 && redeemedVoucher) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-foreground mb-2">Voucher Redeemed!</h2>
          <p className="text-muted-foreground">
            You have successfully redeemed the voucher
          </p>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Gift className="h-5 w-5 text-primary" />
              Redemption Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-muted-foreground">Amount</Label>
                <p className="text-lg font-semibold">${redeemedVoucher.amount} {redeemedVoucher.currency}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Code</Label>
                <p className="text-lg font-mono font-semibold">{redeemedVoucher.voucher_code}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-muted-foreground">Redeemed At</Label>
                <p className="text-sm">{redeemedVoucher.redeemed_at.toLocaleString()}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Status</Label>
                <Badge variant="default" className="bg-green-100 text-green-800">
                  Redeemed
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <MapPin className="h-5 w-5 text-blue-600 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-medium text-blue-900">Next Steps</h4>
                <p className="text-sm text-blue-800">
                  Visit any authorized voucher agent to collect your cash. 
                  Bring a valid ID and this redemption confirmation.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Button onClick={onClose} className="w-full">
          Done
        </Button>
      </div>
    );
  }

  if (step === 2 && voucher) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Gift className="h-8 w-8 text-blue-600" />
          </div>
          <h2 className="text-xl font-bold text-foreground mb-2">Voucher Found!</h2>
          <p className="text-muted-foreground">
            Review the details and redeem your voucher
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
                <p className="text-2xl font-bold text-green-600">${voucher.amount} {voucher.currency}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Code</Label>
                <p className="text-lg font-mono font-semibold">{voucher.voucher_code}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-muted-foreground">From</Label>
                <p className="text-sm flex items-center gap-2">
                  <User className="h-4 w-4" />
                  {voucher.creator_username}
                </p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Expires</Label>
                <p className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  {formatTimeRemaining(voucher.time_remaining)}
                </p>
              </div>
            </div>

            <div>
              <Label className="text-sm text-muted-foreground">Status</Label>
              <Badge variant="default" className="bg-green-100 text-green-800">
                Active
              </Badge>
            </div>

            {voucher.has_pin && (
              <div>
                <Label htmlFor="pin">Enter PIN</Label>
                <div className="relative">
                  <Shield className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="pin"
                    type={showPin ? "text" : "password"}
                    placeholder="Enter PIN"
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
                  This voucher is PIN protected
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <MapPin className="h-5 w-5 text-primary" />
              Nearby Agents
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {mockAgents.map((agent) => (
              <div key={agent.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <h4 className="font-medium">{agent.name}</h4>
                  <p className="text-sm text-muted-foreground">{agent.address}</p>
                  <p className="text-sm text-muted-foreground">{agent.city}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{agent.distance}</p>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <Phone className="h-3 w-3" />
                    {agent.phone}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => {
              setStep(1);
              setVoucher(null);
              setPin("");
            }}
            className="flex-1"
          >
            Back
          </Button>
          <Button
            onClick={handleRedeemVoucher}
            disabled={isRedeeming || (voucher.has_pin && !pin)}
            className="flex-1"
          >
            {isRedeeming ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Redeeming...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4 mr-2" />
                Redeem Voucher
              </>
            )}
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
            <Key className="h-5 w-5 text-primary" />
            Voucher Code
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="voucherCode">Voucher Code</Label>
            <Input
              id="voucherCode"
              type="text"
              placeholder="Enter 20-character voucher code"
              value={voucherCode}
              onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
              className="font-mono text-center"
              maxLength={20}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Enter the 20-character code from your voucher
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="space-y-1">
              <h4 className="font-medium text-blue-900">How to Redeem</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Enter your 20-character voucher code</li>
                <li>• Provide PIN if required</li>
                <li>• Visit any authorized agent to collect cash</li>
                <li>• Bring valid ID for verification</li>
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
          onClick={handleValidateVoucher}
          disabled={!voucherCode || voucherCode.length !== 20 || isValidating}
          className="flex-1"
        >
          {isValidating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              Validating...
            </>
          ) : (
            <>
              <Key className="h-4 w-4 mr-2" />
              Validate Code
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
