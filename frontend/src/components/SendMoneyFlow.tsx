import { useState, useEffect } from "react";
import { ArrowLeft, CheckCircle, Send, AlertCircle, Edit3, Share2, Copy, Clock, DollarSign, QrCode } from "lucide-react";
import { UsernameInput } from "@/components/ui/UsernameInput";
import { AmountInput } from "@/components/ui/AmountInput";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StepIndicator } from "@/components/StepIndicator";
import { useToast } from "@/hooks/use-toast";
import { sendMoneyService, SendMoneyRequest, Balance } from "@/services/sendMoneyService";
import { QRCodeScanner } from "@/components/QRCodeScanner";
import { QRCodeValidator } from "@/components/QRCodeValidator";

interface SendMoneyFlowProps {
  onNavigate: (page: string) => void;
  onGoBack?: () => void;
}

type Step = "recipient" | "amount" | "description" | "confirm" | "success";

interface SendData {
  recipient: string;
  amount: string;
  currency: "USDC" | "APT";
  description: string;
}

interface TransactionResult {
  id: string;
  status: "pending" | "confirmed" | "failed";
  timestamp: Date;
  fee: number;
}

// Mock user suggestions for demo purposes
const mockUserSuggestions = ["@john_doe", "@maria_garcia", "@alex_smith", "@sarah_johnson"];

export function SendMoneyFlow({ onNavigate, onGoBack }: SendMoneyFlowProps) {
  const [currentStep, setCurrentStep] = useState<Step>("recipient");
  const [sendData, setSendData] = useState<SendData>({
    recipient: "",
    amount: "",
    currency: "USDC",
    description: "",
  });
  const [isValidatingUser, setIsValidatingUser] = useState(false);
  const [isUserValid, setIsUserValid] = useState<boolean | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [transactionResult, setTransactionResult] = useState<TransactionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [isLoadingBalances, setIsLoadingBalances] = useState(true);
  const [walletType, setWalletType] = useState<{ isCustodial: boolean; walletAddress: string } | null>(null);
  const [isLoadingWalletType, setIsLoadingWalletType] = useState(true);
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [showQRValidator, setShowQRValidator] = useState(false);
  const [scannedQRData, setScannedQRData] = useState<string>("");
  const { toast } = useToast();

  // Check for QR payment data and payment request data on component mount
  useEffect(() => {
    // Check for QR payment data
    const qrPaymentData = localStorage.getItem('preklo_qr_payment_data');
    if (qrPaymentData) {
      try {
        const data = JSON.parse(qrPaymentData);
        // Check if data is recent (within 5 minutes)
        if (Date.now() - data.timestamp < 5 * 60 * 1000) {
          setSendData(prev => ({
            ...prev,
            recipient: data.recipient || '',
            amount: data.amount ? data.amount.toString() : '',
            currency: data.currency || 'USDC',
            description: data.description || ''
          }));
          
          // Clear the QR data after using it
          localStorage.removeItem('preklo_qr_payment_data');
          
          // If amount is provided, skip to amount step
          if (data.amount) {
            setCurrentStep("amount");
          }
          
          toast({
            title: "QR Code Data Loaded",
            description: data.amount 
              ? `Payment request loaded: ${data.amount} ${data.currency} to ${data.recipient}`
              : `Recipient loaded: ${data.recipient}`,
          });
        } else {
          // Clear expired data
          localStorage.removeItem('preklo_qr_payment_data');
        }
      } catch (error) {
        console.error('Failed to parse QR payment data:', error);
        localStorage.removeItem('preklo_qr_payment_data');
      }
    }

    // Check for payment request data
    const paymentRequestData = localStorage.getItem('preklo_payment_request_data');
    if (paymentRequestData) {
      try {
        const data = JSON.parse(paymentRequestData);
        // Check if data is recent (within 5 minutes)
        if (Date.now() - data.timestamp < 5 * 60 * 1000) {
          setSendData(prev => ({
            ...prev,
            recipient: data.recipient || '',
            amount: data.amount ? data.amount.toString() : '',
            currency: data.currency || 'USDC',
            description: data.description || ''
          }));
          
          // Clear the payment request data after using it
          localStorage.removeItem('preklo_payment_request_data');
          
          // If amount is provided, skip to amount step
          if (data.amount) {
            setCurrentStep("amount");
          }
          
          toast({
            title: "Payment Request Loaded",
            description: data.amount 
              ? `Payment request loaded: ${data.amount} ${data.currency} to ${data.recipient}`
              : `Recipient loaded: ${data.recipient}`,
          });
        } else {
          // Clear expired data
          localStorage.removeItem('preklo_payment_request_data');
        }
      } catch (error) {
        console.error('Failed to parse payment request data:', error);
        localStorage.removeItem('preklo_payment_request_data');
      }
    }
  }, [toast]);

  // Load balances and wallet type on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoadingBalances(true);
        setIsLoadingWalletType(true);
        
        // Load both balances and wallet type in parallel
        const [balanceData, walletTypeData] = await Promise.all([
          sendMoneyService.getBalance(),
          sendMoneyService.getCurrentUserWalletType()
        ]);
        
        setBalances(balanceData);
        setWalletType(walletTypeData);
      } catch (error) {
        console.error('Failed to load data:', error);
        toast({
          title: "Failed to load data",
          description: "Please refresh the page and try again.",
          variant: "destructive",
        });
      } finally {
        setIsLoadingBalances(false);
        setIsLoadingWalletType(false);
      }
    };

    loadData();
  }, [toast]);

  const stepTitles = {
    recipient: "Send to",
    amount: "Enter amount",
    description: "Add note",
    confirm: "Confirm payment",
    success: "Payment sent!",
  };

  const stepNumbers = {
    recipient: 1,
    amount: 2,
    description: 3,
    confirm: 4,
    success: 5,
  };

  const stepDescriptions = {
    recipient: "Who are you sending money to?",
    amount: "How much would you like to send?",
    description: "Add a note to your payment (optional)",
    confirm: "Review your payment details",
    success: "Your payment has been sent successfully!",
  };

  const handleRecipientChange = async (value: string) => {
    setSendData(prev => ({ ...prev, recipient: value }));
    
    if (value.length > 3) {
      setIsValidatingUser(true);
      setIsUserValid(null);
      
      try {
        // Use real API validation
        const isValid = await sendMoneyService.validateUsername(value);
        setIsUserValid(isValid);
      } catch (error) {
        console.error('Username validation error:', error);
        setIsUserValid(false);
      } finally {
        setIsValidatingUser(false);
      }
    } else {
      setIsUserValid(null);
    }
  };

  const validateRecipient = () => {
    if (!sendData.recipient || !isUserValid) {
      setError("Please enter a valid name");
      return false;
    }
    return true;
  };

  const validateAmount = () => {
    if (!sendData.amount || parseFloat(sendData.amount) <= 0) {
      setError("Please enter a valid amount");
      return false;
    }
    
    const userBalance = balances.find(b => b.currency === sendData.currency);
    const maxAmount = userBalance?.balance || 0;
    
    if (parseFloat(sendData.amount) > maxAmount) {
      setError(`Insufficient balance. You have $${maxAmount.toFixed(2)} ${sendData.currency}`);
      return false;
    }
    return true;
  };

  const handleNext = () => {
    setError(null); // Clear any previous errors
    
    switch (currentStep) {
      case "recipient":
        if (validateRecipient()) {
          setCurrentStep("amount");
        }
        break;
      case "amount":
        if (validateAmount()) {
          setCurrentStep("description");
        }
        break;
      case "description":
        setCurrentStep("confirm");
        break;
      case "confirm":
        handleSendMoney();
        break;
    }
  };

  const handleBack = () => {
    setError(null); // Clear any errors when going back
    
    if (currentStep === "amount") {
      setCurrentStep("recipient");
    } else if (currentStep === "description") {
      setCurrentStep("amount");
    } else if (currentStep === "confirm") {
      setCurrentStep("description");
    } else if (currentStep === "success") {
      onGoBack ? onGoBack() : onNavigate("dashboard");
    } else {
      onGoBack ? onGoBack() : onNavigate("dashboard");
    }
  };

  const handleSendMoney = async () => {
    setIsSending(true);
    setError(null);
    
    try {
      if (!walletType) {
        throw new Error("Wallet type not loaded. Please refresh and try again.");
      }

      // Prepare the send money request
      const sendRequest: SendMoneyRequest = {
        recipient_username: sendData.recipient.startsWith('@') ? sendData.recipient.slice(1) : sendData.recipient,
        amount: sendData.amount,
        currency_type: sendData.currency,
        password: "", // Will be set based on wallet type
        description: sendData.description || undefined,
      };

      if (walletType.isCustodial) {
        // Custodial wallet: Get password from prompt
        const password = prompt("Enter your password to confirm the transaction:");
        if (!password) {
          setIsSending(false);
          setError("Password is required to send money");
          return;
        }
        sendRequest.password = password;
      }
      // For non-custodial wallets, no password is needed - the sendMoneyService will handle it

      // Call the real API
      const response = await sendMoneyService.sendMoney(sendRequest, walletType.isCustodial);
      
      // Success
      const result: TransactionResult = {
        id: response.data.transaction_hash,
        status: "confirmed", // Petra transactions are now confirmed after signing
        timestamp: new Date(response.data.created_at),
        fee: parseFloat(response.data.fee_amount),
      };
      
      setTransactionResult(result);
      setIsSending(false);
      setCurrentStep("success");
      setRetryCount(0);
      
      // Refresh balances after successful transaction
      try {
        const updatedBalances = await sendMoneyService.getBalance();
        setBalances(updatedBalances);
      } catch (balanceError) {
        console.error('Failed to refresh balances:', balanceError);
      }
      
      // Show appropriate success message based on wallet type
      if (walletType.isCustodial) {
        toast({
          title: "Payment sent successfully!",
          description: `$${sendData.amount} sent to ${sendData.recipient}`,
        });
      } else {
        toast({
          title: "Payment sent successfully!",
          description: `$${sendData.amount} sent to ${sendData.recipient} via Petra wallet`,
        });
      }
      
    } catch (err) {
      setIsSending(false);
      const errorMessage = err instanceof Error ? err.message : "Payment failed. Please try again.";
      setError(errorMessage);
      
      toast({
        title: "Payment failed",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    handleSendMoney();
  };

  // QR Scanner handlers
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
    if (isValid && data.username) {
      setSendData(prev => ({
        ...prev,
        recipient: data.username,
        amount: data.amount ? data.amount.toString() : prev.amount,
        currency: data.currency || prev.currency,
        description: data.description || prev.description
      }));
      
      // If amount is provided, skip to amount step
      if (data.amount) {
        setCurrentStep("amount");
      }
      
      toast({
        title: "QR Code Processed",
        description: data.amount 
          ? `Payment request loaded: ${data.amount} ${data.currency} to ${data.username}`
          : `Recipient loaded: ${data.username}`,
      });
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

  const canProceed = () => {
    switch (currentStep) {
      case "recipient":
        return sendData.recipient && isUserValid;
      case "amount":
        const userBalance = balances.find(b => b.currency === sendData.currency);
        const maxAmount = userBalance?.balance || 0;
        return sendData.amount && parseFloat(sendData.amount) > 0 && 
               parseFloat(sendData.amount) <= maxAmount;
      case "description":
        return true; // Description is optional
      case "confirm":
        return true;
      default:
        return false;
    }
  };

  const handleEditStep = (step: Step) => {
    setCurrentStep(step);
    setError(null);
  };

  const handleCopyTransactionId = () => {
    if (transactionResult) {
      navigator.clipboard.writeText(transactionResult.id);
      toast({
        title: "Transaction ID copied",
        description: "Transaction ID copied to clipboard",
      });
    }
  };

  const handleShareTransaction = () => {
    if (transactionResult) {
      const shareText = `I sent $${sendData.amount} ${sendData.currency} to ${sendData.recipient} via Preklo. Transaction ID: ${transactionResult.id}`;
      
      if (navigator.share) {
        navigator.share({
          title: "Payment Sent",
          text: shareText,
        });
      } else {
        navigator.clipboard.writeText(shareText);
        toast({
          title: "Transaction shared",
          description: "Transaction details copied to clipboard",
        });
      }
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={handleBack}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-foreground">
              {stepTitles[currentStep]}
            </h1>
            {currentStep !== "success" && (
              <p className="text-sm text-muted-foreground">
                Step {stepNumbers[currentStep]} of 4 • {stepDescriptions[currentStep]}
              </p>
            )}
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      {currentStep !== "success" && (
        <StepIndicator
          currentStep={stepNumbers[currentStep]}
          totalSteps={4}
          stepTitles={["Recipient", "Amount", "Description", "Confirm"]}
        />
      )}

      {/* Error Display */}
      {error && (
        <div className="px-4 py-2">
          <Card className="border-destructive bg-destructive/5">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-destructive font-medium">Error</p>
                  <p className="text-sm text-destructive/80 mt-1">{error}</p>
                  {currentStep === "confirm" && retryCount < 3 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleRetry}
                      className="mt-3 border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground"
                    >
                      Retry Payment
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Wallet Type Indicator */}
      {walletType && (
        <div className="px-4 py-2">
          <Card className="bg-muted/30">
            <CardContent className="p-3">
              <div className="flex items-center gap-2 text-sm">
                <div className={`w-2 h-2 rounded-full ${walletType.isCustodial ? 'bg-green-500' : 'bg-blue-500'}`} />
                <span className="text-muted-foreground">
                  {walletType.isCustodial ? 'Custodial Wallet' : 'Petra Wallet'}
                </span>
                <span className="text-xs text-muted-foreground font-mono">
                  {walletType.walletAddress.slice(0, 8)}...{walletType.walletAddress.slice(-8)}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Content */}
      <main className="px-4 py-6">
        {(isLoadingBalances || isLoadingWalletType) && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center space-y-4">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-sm text-muted-foreground">Loading wallet data...</p>
            </div>
          </div>
        )}
        
        {!isLoadingBalances && !isLoadingWalletType && (
          <>
            {currentStep === "recipient" && (
              <div className="space-y-6">
                <div className="space-y-4">
                  <UsernameInput
                    value={sendData.recipient}
                    onChange={handleRecipientChange}
                    placeholder="Search for name"
                    isValidating={isValidatingUser}
                    isValid={isUserValid}
                    error={isUserValid === false ? "User not found" : undefined}
                    suggestions={mockUserSuggestions.filter(user =>
                      user.toLowerCase().includes(sendData.recipient.toLowerCase().replace('@', ''))
                    )}
                    onSelectSuggestion={(name) => {
                      setSendData(prev => ({ ...prev, recipient: name }));
                      setIsUserValid(true);
                    }}
                  />
                </div>
                
                {/* QR Scanner Button */}
                <div className="text-center">
                  <Button
                    variant="outline"
                    onClick={() => setShowQRScanner(true)}
                    className="w-full"
                  >
                    <QrCode className="h-4 w-4 mr-2" />
                    Scan QR Code
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    Scan someone's QR code to send them money
                  </p>
                </div>
                
                <ActionButton
                  onClick={handleNext}
                  disabled={!canProceed()}
                  fullWidth
                  size="lg"
                >
                  Continue
                </ActionButton>
              </div>
            )}

            {currentStep === "amount" && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <p className="text-muted-foreground">Sending to</p>
                  <p className="text-xl font-semibold text-foreground">{sendData.recipient}</p>
                </div>

                <AmountInput
                  value={sendData.amount}
                  onChange={(value) => setSendData(prev => ({ ...prev, amount: value }))}
                  currency={sendData.currency}
                  onCurrencyChange={(currency) => setSendData(prev => ({ ...prev, currency }))}
                  maxAmount={balances.find(b => b.currency === sendData.currency)?.balance || 0}
                  suggestions={[10, 25, 50, 100]}
                  onSelectSuggestion={(amount) => setSendData(prev => ({ ...prev, amount: amount.toString() }))}
                />

                <ActionButton
                  onClick={handleNext}
                  disabled={!canProceed()}
                  fullWidth
                  size="lg"
                >
                  Continue
                </ActionButton>
              </div>
            )}

            {currentStep === "description" && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <p className="text-muted-foreground">Sending ${sendData.amount} {sendData.currency} to</p>
                  <p className="text-xl font-semibold text-foreground">{sendData.recipient}</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Add a note (optional)
                    </label>
                    <textarea
                      value={sendData.description}
                      onChange={(e) => setSendData(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="What's this payment for?"
                      className="w-full p-4 border border-border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none h-24"
                      maxLength={100}
                    />
                    <div className="flex justify-between items-center mt-2">
                      <p className="text-xs text-muted-foreground">
                        Common: Lunch, Rent, Gift, Services
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {sendData.description.length}/100
                      </p>
                    </div>
                  </div>
                  
                  <ActionButton
                    onClick={handleNext}
                    disabled={!canProceed()}
                    fullWidth
                    size="lg"
                  >
                    Continue
                  </ActionButton>
                </div>
              </div>
            )}

            {currentStep === "confirm" && (
              <div className="space-y-6">
                <div className="bg-card border border-border rounded-2xl p-6 space-y-4">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-2xl font-bold text-primary">
                        {sendData.recipient.replace('@', '').charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex items-center justify-center gap-2 mb-1">
                      <h3 className="text-xl font-semibold text-foreground">
                        {sendData.recipient}
                      </h3>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditStep("recipient")}
                        className="h-6 w-6 p-0"
                      >
                        <Edit3 className="h-3 w-3" />
                      </Button>
                    </div>
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <p className="text-3xl font-bold text-foreground">
                        ${parseFloat(sendData.amount).toFixed(2)}
                      </p>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditStep("amount")}
                        className="h-6 w-6 p-0"
                      >
                        <Edit3 className="h-3 w-3" />
                      </Button>
                    </div>
                    <p className="text-sm text-muted-foreground">{sendData.currency}</p>
                  </div>

                  <div className="pt-4 border-t border-border">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-muted-foreground">Note</p>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditStep("description")}
                        className="h-6 w-6 p-0"
                      >
                        <Edit3 className="h-3 w-3" />
                      </Button>
                    </div>
                    <p className="text-foreground">
                      {sendData.description || "No note added"}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-border space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Amount</span>
                      <span className="text-foreground">${sendData.amount}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Network fee</span>
                      <span className="text-foreground">$0.01</span>
                    </div>
                    <div className="flex justify-between text-base font-semibold pt-2 border-t border-border">
                      <span>Total</span>
                      <span>${(parseFloat(sendData.amount) + 0.01).toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <ActionButton
                  onClick={handleNext}
                  isLoading={isSending}
                  fullWidth
                  size="lg"
                  icon={<Send className="h-5 w-5" />}
                >
                  {isSending ? (walletType?.isCustodial ? "Sending..." : "Confirming payment...") : "Send Money"}
                </ActionButton>
              </div>
            )}

            {currentStep === "success" && transactionResult && (
              <div className="text-center space-y-6 py-12">
                <div className="w-24 h-24 bg-success/10 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle className="h-12 w-12 text-success" />
                </div>
                
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Payment Sent!</h2>
                  <p className="text-muted-foreground">
                    ${sendData.amount} {sendData.currency} has been sent to {sendData.recipient}
                  </p>
                </div>

                <Card className="bg-muted/50">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-muted-foreground">Transaction ID</p>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleCopyTransactionId}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <p className="text-sm font-mono text-foreground break-all">
                      {transactionResult.id}
                    </p>
                    
                    <div className="flex items-center justify-between pt-2 border-t border-border">
                      <p className="text-sm text-muted-foreground">Status</p>
                      <Badge variant="default" className="bg-success text-success-foreground">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Confirmed
                      </Badge>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-muted-foreground">Time</p>
                      <p className="text-sm text-foreground">
                        {transactionResult.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                <div className="space-y-3">
                  <ActionButton
                    onClick={onGoBack || (() => onNavigate("dashboard"))}
                    fullWidth
                    size="lg"
                  >
                    Back to Home
                  </ActionButton>
                  
                  <div className="flex gap-3">
                    <ActionButton
                      onClick={handleShareTransaction}
                      variant="outline"
                      className="flex-1"
                      icon={<Share2 className="h-4 w-4" />}
                    >
                      Share
                    </ActionButton>
                    
                    <ActionButton
                      onClick={() => onNavigate("history")}
                      variant="outline"
                      className="flex-1"
                      icon={<Clock className="h-4 w-4" />}
                    >
                      View History
                    </ActionButton>
                  </div>
                  
                  <ActionButton
                    onClick={() => {
                      setCurrentStep("recipient");
                      setSendData({
                        recipient: "",
                        amount: "",
                        currency: "USDC",
                        description: "",
                      });
                      setIsUserValid(null);
                      setTransactionResult(null);
                      setError(null);
                    }}
                    variant="ghost"
                    fullWidth
                    icon={<DollarSign className="h-4 w-4" />}
                  >
                    Send Another Payment
                  </ActionButton>
                </div>
              </div>
            )}
          </>
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