import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Eye, EyeOff, CheckCircle, X, User, Mail, Lock, AlertCircle, Wallet, Smartphone, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { authService, RegisterData } from "@/services/authService";

interface RegistrationPageProps {
  onNavigate: (page: string) => void;
}

type RegistrationStep = "wallet-type" | "petra-registration" | "simple-registration";

export function RegistrationPage({ onNavigate }: RegistrationPageProps) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<RegistrationStep>("wallet-type");
  const [selectedWalletType, setSelectedWalletType] = useState<"petra" | "simple" | null>(null);
  
  // Form data for simple registration
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    agreeToTerms: false
  });
  
  // Form data for Petra registration
  const [petraFormData, setPetraFormData] = useState({
    username: "",
    email: "",
    walletAddress: "",
    agreeToTerms: false
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isCheckingUsername, setIsCheckingUsername] = useState(false);
  const [usernameAvailable, setUsernameAvailable] = useState<boolean | null>(null);
  const { toast } = useToast();

  // Handle wallet type selection
  const handleWalletTypeSelection = (type: "petra" | "simple") => {
    setSelectedWalletType(type);
    if (type === "petra") {
      setCurrentStep("petra-registration");
    } else {
      setCurrentStep("simple-registration");
    }
  };

  // Handle back navigation
  const handleBack = () => {
    if (currentStep === "wallet-type") {
      navigate("/landing");
    } else {
      setCurrentStep("wallet-type");
      setSelectedWalletType(null);
    }
  };

  // Get Petra wallet following documentation pattern
  const getAptosWallet = () => {
    if ('aptos' in window) {
      return (window as any).aptos;
    } else {
      // Open Petra installation page as per documentation
      window.open('https://petra.app/', '_blank');
      return null;
    }
  };

  // Handle Petra wallet connection following documentation
  const handleConnectPetraWallet = async () => {
    try {
      const wallet = getAptosWallet();
      
      if (!wallet) {
        toast({
          title: "Petra Wallet Not Found",
          description: "Please install Petra Wallet extension to continue",
          variant: "destructive",
        });
        return;
      }

      // Connect to Petra wallet as per documentation
      const response = await wallet.connect();
      console.log('Petra connection response:', response); // { address: string, address: string }
      
      if (response && response.address) {
        setPetraFormData(prev => ({
          ...prev,
          walletAddress: response.address
        }));
        
        toast({
          title: "Wallet Connected!",
          description: "Petra wallet connected successfully",
        });
      } else {
        toast({
          title: "Connection Failed",
          description: "No wallet address received from Petra",
          variant: "destructive",
        });
      }
    } catch (error: any) {
      console.error('Petra wallet connection error:', error);
      
      // Handle specific Petra wallet errors as per documentation
      if (error.code === 4001) {
        toast({
          title: "Connection Cancelled",
          description: "User rejected the connection request",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Connection Failed",
          description: error.message || "Failed to connect to Petra wallet",
          variant: "destructive",
        });
      }
    }
  };

  // Handle Petra registration submission
  const handlePetraRegistration = async () => {
    setIsLoading(true);
    
    try {
      // For now, we'll use the simple registration endpoint
      // In a real implementation, we'd have a separate Petra registration endpoint
      const registrationData: RegisterData = {
        username: petraFormData.username,
        email: petraFormData.email,
        password: "petra_wallet_user", // Temporary password for Petra users
        terms_agreed: petraFormData.agreeToTerms,
      };

      const response = await authService.register(registrationData);

      toast({
        title: "Account created successfully!",
        description: `Welcome to Preklo, @${response.user.username}!`,
      });

      // Navigate to dashboard
      navigate("/");

    } catch (error) {
      console.error('Petra registration error:', error);
      
      let errorMessage = "Registration failed. Please try again.";
      
      if (error instanceof Error) {
        if (error.message.includes("Username already registered")) {
          errorMessage = "Username is already taken. Please choose another.";
        } else if (error.message.includes("Email already registered")) {
          errorMessage = "Email is already registered. Please use a different email.";
        } else {
          errorMessage = error.message;
        }
      }

      toast({
        title: "Registration failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    // Username validation
    if (!formData.username) {
      newErrors.username = "Username is required";
    } else if (formData.username.length < 3) {
      newErrors.username = "Username must be at least 3 characters";
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = "Username can only contain letters, numbers, and underscores";
    }

    // Email validation
    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])/.test(formData.password)) {
      newErrors.password = "Password must contain uppercase, lowercase, number, and special character";
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    // Terms agreement
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = "You must agree to the terms and conditions";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const checkUsernameAvailability = async (username: string) => {
    if (username.length < 3) {
      setUsernameAvailable(null);
      return;
    }

    setIsCheckingUsername(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock availability check - some usernames are taken
    const takenUsernames = ["admin", "test", "user", "john", "sarah", "alex", "maria"];
    const isAvailable = !takenUsernames.includes(username.toLowerCase());
    
    setUsernameAvailable(isAvailable);
    setIsCheckingUsername(false);
  };

  const handleUsernameChange = (value: string) => {
    setFormData(prev => ({ ...prev, username: value }));
    setErrors(prev => ({ ...prev, username: "" }));
    
    // Debounce username check
    const timeoutId = setTimeout(() => {
      checkUsernameAvailability(value);
    }, 500);
    
    return () => clearTimeout(timeoutId);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    if (usernameAvailable === false) {
      setErrors(prev => ({ ...prev, username: "Username is not available" }));
      return;
    }

    setIsLoading(true);

    try {
      // Prepare registration data
      const registrationData: RegisterData = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        terms_agreed: formData.agreeToTerms,
        // full_name: formData.username, // Temporarily remove to test
      };

      // Call the real API
      const response = await authService.register(registrationData);

      toast({
        title: "Account created successfully!",
        description: `Welcome to Preklo, @${response.user.username}!`,
      });

      // Automatically log the user in after registration
      try {
        const loginResponse = await authService.login({
          username: formData.username,
          password: formData.password
        });

        toast({
          title: "Welcome to Preklo!",
          description: `You're now logged in as @${loginResponse.user.username}`,
        });

        // Navigate to dashboard
        navigate("/");
      } catch (loginError) {
        console.error('Auto-login after registration failed:', loginError);
        // If auto-login fails, redirect to login page
        toast({
          title: "Account created!",
          description: "Please log in to continue.",
        });
        navigate("/login");
      }

    } catch (error) {
      console.error('Registration error:', error);
      
      // Handle specific error messages
      let errorMessage = "Registration failed. Please try again.";
      
      if (error instanceof Error) {
        if (error.message.includes("Username already registered")) {
          errorMessage = "Username is already taken. Please choose another.";
          setErrors(prev => ({ ...prev, username: errorMessage }));
        } else if (error.message.includes("Email already registered")) {
          errorMessage = "Email is already registered. Please use a different email.";
          setErrors(prev => ({ ...prev, email: errorMessage }));
        } else {
          errorMessage = error.message;
        }
      }

      toast({
        title: "Registration failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const passwordRequirements = [
    { text: "At least 8 characters", met: formData.password.length >= 8 },
    { text: "One uppercase letter", met: /[A-Z]/.test(formData.password) },
    { text: "One lowercase letter", met: /[a-z]/.test(formData.password) },
    { text: "One number", met: /\d/.test(formData.password) },
    { text: "One special character", met: /[!@#$%^&*(),.?":{}|<>]/.test(formData.password) }
  ];

  // Render wallet type selection step
  const renderWalletTypeSelection = () => (
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
          <div>
            <h1 className="text-xl font-semibold text-foreground">Choose Your Wallet</h1>
            <p className="text-sm text-muted-foreground">How would you like to create your account?</p>
          </div>
        </div>
      </header>

      {/* Wallet Type Selection */}
      <main className="px-4 py-8">
        <div className="max-w-md mx-auto space-y-6">
          {/* Petra Wallet Option */}
          <Card 
            className="cursor-pointer hover:border-primary transition-colors duration-200"
            onClick={() => handleWalletTypeSelection("petra")}
          >
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Wallet className="h-6 w-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-2">I have Petra Wallet</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Connect your existing Petra wallet for full control of your funds
                  </p>
                  <div className="flex items-center gap-2 text-xs text-blue-600">
                    <CheckCircle className="h-3 w-3" />
                    <span>Full wallet control</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-blue-600 mt-1">
                    <CheckCircle className="h-3 w-3" />
                    <span>No password required</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Simple Registration Option */}
          <Card 
            className="cursor-pointer hover:border-primary transition-colors duration-200"
            onClick={() => handleWalletTypeSelection("simple")}
          >
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                  <Smartphone className="h-6 w-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-2">Simple Registration</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Create an account with username, email, and password
                  </p>
                  <div className="flex items-center gap-2 text-xs text-green-600">
                    <CheckCircle className="h-3 w-3" />
                    <span>Auto-generated wallet</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-green-600 mt-1">
                    <CheckCircle className="h-3 w-3" />
                    <span>Easy to get started</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Login Option */}
          <div className="text-center pt-6">
            <p className="text-sm text-muted-foreground mb-4">
              Already have an account?
            </p>
            <Button
              variant="outline"
              onClick={() => navigate("/login")}
              className="w-full"
            >
              <LogIn className="h-4 w-4 mr-2" />
              Sign In Instead
            </Button>
          </div>
        </div>
      </main>
    </div>
  );

  // Render Petra registration step
  const renderPetraRegistration = () => (
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
          <div>
            <h1 className="text-xl font-semibold text-foreground">Connect Petra Wallet</h1>
            <p className="text-sm text-muted-foreground">Link your wallet and create your profile</p>
          </div>
        </div>
      </header>

      {/* Petra Registration Form */}
      <main className="px-4 py-8">
        <div className="max-w-md mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Petra Wallet Registration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Wallet Connection */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Connect Your Wallet
                  </label>
                  <Button
                    onClick={handleConnectPetraWallet}
                    variant={petraFormData.walletAddress ? "outline" : "default"}
                    className="w-full"
                    disabled={!!petraFormData.walletAddress}
                  >
                    <Wallet className="h-4 w-4 mr-2" />
                    {petraFormData.walletAddress ? "Wallet Connected" : "Connect Petra Wallet"}
                  </Button>
                  {petraFormData.walletAddress && (
                    <p className="text-xs text-muted-foreground mt-2 font-mono">
                      {petraFormData.walletAddress.slice(0, 8)}...{petraFormData.walletAddress.slice(-8)}
                    </p>
                  )}
                </div>

                {/* Username Field */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Username
                  </label>
                  <div className="relative">
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <User className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <input
                      type="text"
                      value={petraFormData.username}
                      onChange={(e) => setPetraFormData(prev => ({ ...prev, username: e.target.value }))}
                      placeholder="Choose your @username"
                      className="w-full pl-10 pr-4 py-3 border border-border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Email Field */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <input
                      type="email"
                      value={petraFormData.email}
                      onChange={(e) => setPetraFormData(prev => ({ ...prev, email: e.target.value }))}
                      placeholder="Enter your email"
                      className="w-full pl-10 pr-4 py-3 border border-border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Terms Agreement */}
                <div>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={petraFormData.agreeToTerms}
                      onChange={(e) => setPetraFormData(prev => ({ ...prev, agreeToTerms: e.target.checked }))}
                      className="mt-1 w-4 h-4 text-primary bg-background border-border rounded focus:ring-primary focus:ring-2"
                    />
                    <span className="text-sm text-muted-foreground">
                      I agree to the{" "}
                      <button type="button" className="text-primary hover:underline">
                        Terms of Service
                      </button>{" "}
                      and{" "}
                      <button type="button" className="text-primary hover:underline">
                        Privacy Policy
                      </button>
                    </span>
                  </label>
                </div>

                {/* Submit Button */}
                <Button
                  onClick={handlePetraRegistration}
                  className="w-full"
                  size="lg"
                  disabled={!petraFormData.walletAddress || !petraFormData.username || !petraFormData.email || !petraFormData.agreeToTerms || isLoading}
                >
                  {isLoading ? "Creating Account..." : "Create Account with Petra Wallet"}
                </Button>
              </div>

              {/* Sign In Link */}
              <div className="text-center mt-6">
                <p className="text-sm text-muted-foreground">
                  Already have an account?{" "}
                  <button
                    onClick={() => navigate("/login")}
                    className="text-primary hover:underline font-medium"
                  >
                    Sign In
                  </button>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );

  // Render simple registration step
  const renderSimpleRegistration = () => (
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
          <div>
            <h1 className="text-xl font-semibold text-foreground">Create Account</h1>
            <p className="text-sm text-muted-foreground">Join Preklo and start sending money globally</p>
          </div>
        </div>
      </header>

      {/* Registration Form */}
      <main className="px-4 py-8">
        <div className="max-w-md mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Sign Up</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Username Field */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Username
                  </label>
                  <div className="relative">
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <User className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => handleUsernameChange(e.target.value)}
                      placeholder="Choose your @username"
                      className={`w-full pl-10 pr-10 py-3 border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                        errors.username ? "border-destructive" : "border-border"
                      }`}
                    />
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      {isCheckingUsername ? (
                        <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      ) : usernameAvailable === true ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : usernameAvailable === false ? (
                        <X className="h-4 w-4 text-destructive" />
                      ) : null}
                    </div>
                  </div>
                  {errors.username && (
                    <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.username}
                    </p>
                  )}
                  {usernameAvailable === true && (
                    <p className="text-sm text-green-500 mt-1 flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      Username is available
                    </p>
                  )}
                </div>

                {/* Email Field */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                      placeholder="Enter your email"
                      className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                        errors.email ? "border-destructive" : "border-border"
                      }`}
                    />
                  </div>
                  {errors.email && (
                    <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.email}
                    </p>
                  )}
                </div>

                {/* Password Field */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <Lock className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <input
                      type={showPassword ? "text" : "password"}
                      value={formData.password}
                      onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                      placeholder="Create a strong password"
                      className={`w-full pl-10 pr-10 py-3 border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                        errors.password ? "border-destructive" : "border-border"
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full hover:bg-muted transition-colors duration-200"
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.password}
                    </p>
                  )}
                  
                  {/* Password Requirements */}
                  {formData.password && (
                    <div className="mt-2 space-y-1">
                      {passwordRequirements.map((req, index) => (
                        <div key={index} className="flex items-center gap-2 text-xs">
                          {req.met ? (
                            <CheckCircle className="h-3 w-3 text-green-500" />
                          ) : (
                            <div className="h-3 w-3 rounded-full border border-muted-foreground" />
                          )}
                          <span className={req.met ? "text-green-500" : "text-muted-foreground"}>
                            {req.text}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Confirm Password Field */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                      <Lock className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                      placeholder="Confirm your password"
                      className={`w-full pl-10 pr-10 py-3 border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                        errors.confirmPassword ? "border-destructive" : "border-border"
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full hover:bg-muted transition-colors duration-200"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                  {errors.confirmPassword && (
                    <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.confirmPassword}
                    </p>
                  )}
                </div>

                {/* Terms Agreement */}
                <div>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.agreeToTerms}
                      onChange={(e) => setFormData(prev => ({ ...prev, agreeToTerms: e.target.checked }))}
                      className="mt-1 w-4 h-4 text-primary bg-background border-border rounded focus:ring-primary focus:ring-2"
                    />
                    <span className="text-sm text-muted-foreground">
                      I agree to the{" "}
                      <button type="button" className="text-primary hover:underline">
                        Terms of Service
                      </button>{" "}
                      and{" "}
                      <button type="button" className="text-primary hover:underline">
                        Privacy Policy
                      </button>
                    </span>
                  </label>
                  {errors.agreeToTerms && (
                    <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.agreeToTerms}
                    </p>
                  )}
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={isLoading || usernameAvailable === false}
                >
                  {isLoading ? "Creating Account..." : "Create Account"}
                </Button>
              </form>

              {/* Sign In Link */}
              <div className="text-center mt-6">
                <p className="text-sm text-muted-foreground">
                  Already have an account?{" "}
                  <button
                    onClick={() => navigate("/login")}
                    className="text-primary hover:underline font-medium"
                  >
                    Sign In
                  </button>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );

  // Main render function that switches between steps
  return (
    <>
      {currentStep === "wallet-type" && renderWalletTypeSelection()}
      {currentStep === "petra-registration" && renderPetraRegistration()}
      {currentStep === "simple-registration" && renderSimpleRegistration()}
    </>
  );
}
