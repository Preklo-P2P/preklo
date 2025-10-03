import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Eye, EyeOff, Mail, Lock, AlertCircle, User, Wallet, Smartphone, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { authService, LoginData } from "@/services/authService";

interface LoginPageProps {
  onNavigate: (page: string) => void;
}

type LoginMethod = "password" | "petra" | "detecting";

export function LoginPage({ onNavigate }: LoginPageProps) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    rememberMe: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loginMethod, setLoginMethod] = useState<LoginMethod>("detecting");
  const [isDetectingWalletType, setIsDetectingWalletType] = useState(false);
  const [walletAddress, setWalletAddress] = useState<string>("");
  const { toast } = useToast();

  // Clear wallet error when wallet address is set
  useEffect(() => {
    if (walletAddress && errors.wallet) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.wallet;
        return newErrors;
      });
    }
  }, [walletAddress, errors.wallet]);

  // Detect wallet type when username changes
  useEffect(() => {
    const detectWalletType = async () => {
      if (!formData.username || formData.username.length < 3) {
        setLoginMethod("detecting");
        return;
      }

      setIsDetectingWalletType(true);
      
      try {
        // Check if user exists and get their wallet type
        const cleanUsername = formData.username.startsWith('@') ? formData.username.slice(1) : formData.username;
        
        // Since we're only supporting Petra Wallet, let's check if the user exists
        // and determine their wallet type from the backend
        try {
          // Try to get user info to determine wallet type
          const response = await fetch(`http://localhost:8000/api/v1/users/info/${cleanUsername}`);
          if (response.ok) {
            const userData = await response.json();
            if (userData.exists) {
              // User exists, check if they have a non-custodial wallet (Petra)
              if (userData.is_custodial === false) {
                setLoginMethod("petra");
              } else {
                setLoginMethod("password");
              }
            } else {
              // User doesn't exist, default to Petra since we're only supporting Petra
              setLoginMethod("petra");
            }
          } else {
            // API call failed, use fallback logic
            const knownPetraUsers = ['mom', 'petra', 'wallet'];
            if (knownPetraUsers.includes(cleanUsername.toLowerCase()) || 
                cleanUsername.toLowerCase().includes('petra') || 
                cleanUsername.toLowerCase().includes('wallet')) {
              setLoginMethod("petra");
            } else {
              setLoginMethod("petra"); // Default to Petra since we're only supporting Petra
            }
          }
        } catch (apiError) {
          console.error('API call failed, using fallback:', apiError);
          // Fallback to heuristic
          const knownPetraUsers = ['mom', 'petra', 'wallet'];
          if (knownPetraUsers.includes(cleanUsername.toLowerCase()) || 
              cleanUsername.toLowerCase().includes('petra') || 
              cleanUsername.toLowerCase().includes('wallet')) {
            setLoginMethod("petra");
          } else {
            setLoginMethod("petra"); // Default to Petra since we're only supporting Petra
          }
        }
        
      } catch (error) {
        console.error('Wallet type detection error:', error);
        // Default to Petra wallet since we're only supporting Petra
        setLoginMethod("petra");
      } finally {
        setIsDetectingWalletType(false);
      }
    };

    const timeoutId = setTimeout(detectWalletType, 200); // Faster detection
    return () => clearTimeout(timeoutId);
  }, [formData.username]);

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
        setWalletAddress(response.address);
        
        // Clear any existing wallet errors
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors.wallet;
          return newErrors;
        });
        
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

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.username) {
      newErrors.username = "Username is required";
    }

    // Only require password for custodial wallet users
    if (loginMethod === "password" && !formData.password) {
      newErrors.password = "Password is required";
    }

    // For Petra wallet users, require wallet connection
    if (loginMethod === "petra" && !walletAddress) {
      newErrors.wallet = "Please connect your Petra wallet";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      if (loginMethod === "password") {
        // Traditional password login for custodial wallet users
        const loginData: LoginData = {
          username: formData.username,
          password: formData.password,
          remember_me: formData.rememberMe,
        };

        const response = await authService.login(loginData);

        toast({
          title: "Welcome back!",
          description: `Hello @${response.user.username}!`,
        });

        navigate("/");

      } else if (loginMethod === "petra") {
        // Petra wallet login - use the wallet login endpoint
        if (!walletAddress) {
          toast({
            title: "Wallet Not Connected",
            description: "Please connect your Petra wallet first.",
            variant: "destructive",
          });
          return;
        }

        try {
          // Call the wallet login endpoint
          const response = await fetch('http://localhost:8000/api/v1/auth/login-wallet', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username: formData.username,
              wallet_address: walletAddress
            })
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Wallet login failed');
          }

          const loginData = await response.json();
          
          // Store the authentication data
          localStorage.setItem('preklo_access_token', loginData.data.tokens.access_token);
          localStorage.setItem('preklo_refresh_token', loginData.data.tokens.refresh_token);
          localStorage.setItem('preklo_user_id', loginData.data.user.id);
          localStorage.setItem('preklo_username', loginData.data.user.username);
          localStorage.setItem('preklo_email', loginData.data.user.email);
          localStorage.setItem('preklo_wallet_address', loginData.data.user.wallet_address);

          toast({
            title: "Welcome back!",
            description: `Hello @${loginData.data.user.username}!`,
          });

          navigate("/");

        } catch (error) {
          console.error('Petra wallet login error:', error);
          toast({
            title: "Login failed",
            description: error instanceof Error ? error.message : "Failed to login with Petra wallet",
            variant: "destructive",
          });
        }
      }

    } catch (error) {
      console.error('Login error:', error);
      
      // Handle specific error messages
      let errorMessage = "Login failed. Please try again.";
      
      if (error instanceof Error) {
        if (error.message.includes("Invalid username or password")) {
          errorMessage = "Invalid username or password. Please check your credentials.";
        } else if (error.message.includes("User not found")) {
          errorMessage = "User not found. Please check your username.";
        } else {
          errorMessage = error.message;
        }
      }

      toast({
        title: "Login failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = () => {
    toast({
      title: "Password Reset",
      description: "Password reset instructions sent to your email",
    });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/landing")}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-foreground">Sign In</h1>
            <p className="text-sm text-muted-foreground">
              {loginMethod === "password" && "Welcome back to Preklo"}
              {loginMethod === "petra" && "Connect your Petra wallet"}
            </p>
          </div>
        </div>
      </header>

      {/* Login Form */}
      <main className="px-4 py-8">
        <div className="max-w-md mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Welcome Back</CardTitle>
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
                      onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                      placeholder="Enter your @username"
                      className={`w-full pl-10 pr-4 py-3 border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                        errors.username ? "border-destructive" : "border-border"
                      }`}
                    />
                  </div>
                  {errors.username && (
                    <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      {errors.username}
                    </p>
                  )}
                </div>


                {/* Password Field - Only for custodial wallet users */}
                {loginMethod === "password" && (
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
                        placeholder="Enter your password"
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
                  </div>
                )}

                {/* Petra Wallet Connection - Only for Petra wallet users */}
                {loginMethod === "petra" && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Connect Your Wallet
                    </label>
                    <Button
                      onClick={handleConnectPetraWallet}
                      variant={walletAddress ? "outline" : "default"}
                      className="w-full"
                      disabled={!!walletAddress}
                    >
                      <Wallet className="h-4 w-4 mr-2" />
                      {walletAddress ? "Wallet Connected" : "Connect Petra Wallet"}
                    </Button>
                    {walletAddress && (
                      <p className="text-xs text-muted-foreground mt-2 font-mono">
                        {walletAddress.slice(0, 8)}...{walletAddress.slice(-8)}
                      </p>
                    )}
                    {errors.wallet && (
                      <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" />
                        {errors.wallet}
                      </p>
                    )}
                  </div>
                )}

                {/* Remember Me & Forgot Password - Only for password login */}
                {loginMethod === "password" && (
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.rememberMe}
                        onChange={(e) => setFormData(prev => ({ ...prev, rememberMe: e.target.checked }))}
                        className="w-4 h-4 text-primary bg-background border-border rounded focus:ring-primary focus:ring-2"
                      />
                      <span className="text-sm text-muted-foreground">Remember me</span>
                    </label>
                    <button
                      type="button"
                      onClick={handleForgotPassword}
                      className="text-sm text-primary hover:underline"
                    >
                      Forgot password?
                    </button>
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={isLoading}
                >
                  {isLoading ? "Signing In..." : 
                   loginMethod === "petra" ? "Sign In with Petra" : "Sign In"}
                </Button>
              </form>

              {/* Sign Up Link */}
              <div className="text-center mt-6">
                <p className="text-sm text-muted-foreground">
                  Don't have an account?{" "}
                  <button
                    onClick={() => navigate("/register")}
                    className="text-primary hover:underline font-medium"
                  >
                    Sign Up
                  </button>
                </p>
              </div>
            </CardContent>
          </Card>

        </div>
      </main>
    </div>
  );
}
