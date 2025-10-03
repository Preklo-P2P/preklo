import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { 
  User, 
  Shield, 
  Bell, 
  HelpCircle, 
  LogOut, 
  ChevronRight,
  Edit2,
  Copy,
  ExternalLink,
  Settings,
  Gift,
  CreditCard,
  Smartphone,
  Fingerprint,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Clock,
  MapPin,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Plus,
  Trash2,
  ArrowLeft
} from "lucide-react";

interface AccountProps {
  onNavigate: (page: string) => void;
  onGoBack?: () => void;
}

// User data interface
interface User {
  id: string;
  username: string;
  email: string;
  balance: { usdc: number; apt: number };
  profile_picture: string | null;
  verified: boolean;
  created_at: string;
}

export function Account({ onNavigate, onGoBack }: AccountProps) {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [activeTab, setActiveTab] = useState<"profile" | "vouchers" | "security">("profile");
  const [user, setUser] = useState<User | null>(null);
  const { toast } = useToast();

  // Load user data from localStorage
  useEffect(() => {
    const loadUserData = () => {
      const username = localStorage.getItem('preklo_username');
      const email = localStorage.getItem('preklo_email');
      
      if (username && email) {
        setUser({
          id: "1", // In a real app, this would come from the API
          username: username.startsWith('@') ? username : `@${username}`,
          email: email,
          balance: { usdc: 0, apt: 0 }, // In a real app, this would come from the API
          profile_picture: null,
          verified: false, // In a real app, this would come from the API
          created_at: new Date().toISOString()
        });
      }
    };

    loadUserData();
  }, []);

  const handleCopyUsername = () => {
    if (user) {
      navigator.clipboard.writeText(user.username);
      toast({
        title: "Username copied!",
        description: "Your username has been copied to clipboard",
      });
    }
  };

  // Show loading if user data is not loaded yet
  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleLogout = () => {
    toast({
      title: "Logged out",
      description: "You have been successfully logged out",
    });
    onNavigate("logout");
  };

  const profileSections = [
    {
      title: "Account",
      items: [
        {
          id: "edit-profile",
          label: "Edit Profile",
          icon: <Edit2 className="h-5 w-5" />,
          description: "Update your personal information",
          onClick: () => onNavigate("profile"),
        },
        {
          id: "verification",
          label: "Identity Verification",
          icon: <CheckCircle className="h-5 w-5" />,
          description: user.verified ? "Verified" : "Verify your identity",
          onClick: () => console.log("Verification"),
        },
      ]
    },
    {
      title: "Security",
      items: [
        {
          id: "security",
          label: "Security Settings",
          icon: <Shield className="h-5 w-5" />,
          description: "Two-factor authentication, password",
          onClick: () => setActiveTab("security"),
        },
        {
          id: "privacy",
          label: "Privacy Controls",
          icon: <Settings className="h-5 w-5" />,
          description: "Manage your privacy preferences",
          onClick: () => console.log("Privacy controls"),
        },
      ]
    },
    {
      title: "Support",
      items: [
        {
          id: "help",
          label: "Help & Support",
          icon: <HelpCircle className="h-5 w-5" />,
          description: "Get help and contact support",
          onClick: () => onNavigate("help"),
        },
        {
          id: "about",
          label: "About Preklo",
          icon: <ExternalLink className="h-5 w-5" />,
          description: "Version 1.0.0",
          onClick: () => console.log("About"),
        },
      ]
    }
  ];

  const renderProfileTab = () => (
    <div className="space-y-6">
      {/* User Profile Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              <User className="h-8 w-8 text-primary" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-semibold">{user.username}</h2>
                {user.verified && (
                  <Badge variant="outline" className="bg-green-100 text-green-800">
                    Verified
                  </Badge>
                )}
              </div>
              <p className="text-muted-foreground">{user.email}</p>
              <div className="flex items-center gap-4 mt-2">
                <div>
                  <p className="text-sm text-muted-foreground">USDC Balance</p>
                  <p className="font-semibold">${user.balance.usdc.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">APT Balance</p>
                  <p className="font-semibold">{user.balance.apt.toFixed(2)} APT</p>
                </div>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={handleCopyUsername}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Profile Sections */}
      {profileSections.map((section, index) => (
        <Card key={index}>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">{section.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {section.items.map((item) => (
                <button
                  key={item.id}
                  onClick={item.onClick}
                  className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors duration-200"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                      {item.icon}
                    </div>
                    <div className="text-left">
                      <p className="font-medium">{item.label}</p>
                      <p className="text-sm text-muted-foreground">{item.description}</p>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Logout */}
      <Card className="border-red-200">
        <CardContent className="pt-6">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-red-50 transition-colors duration-200"
          >
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <LogOut className="h-5 w-5 text-red-600" />
            </div>
            <div className="text-left">
              <p className="font-medium text-red-600">Logout</p>
              <p className="text-sm text-red-500">Sign out of your account</p>
            </div>
          </button>
        </CardContent>
      </Card>
    </div>
  );

  const renderVouchersTab = () => (
    <div className="space-y-6">
      {/* Voucher Overview */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Vouchers</p>
                <p className="text-2xl font-bold text-green-600">3</p>
              </div>
              <Gift className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Value</p>
                <p className="text-2xl font-bold text-blue-600">$150</p>
              </div>
              <CreditCard className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <Button 
              className="h-16 flex flex-col gap-2"
              onClick={() => console.log("Create voucher")}
            >
              <Plus className="h-5 w-5" />
              <span className="text-sm">Create Voucher</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-16 flex flex-col gap-2"
              onClick={() => console.log("Redeem voucher")}
            >
              <Gift className="h-5 w-5" />
              <span className="text-sm">Redeem Voucher</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Vouchers */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Recent Vouchers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { id: "1", amount: "$50", status: "Active", created: "2 days ago" },
              { id: "2", amount: "$25", status: "Redeemed", created: "1 week ago" },
              { id: "3", amount: "$75", status: "Active", created: "3 days ago" },
            ].map((voucher) => (
              <div key={voucher.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                    <Gift className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium">{voucher.amount}</p>
                    <p className="text-sm text-muted-foreground">{voucher.created}</p>
                  </div>
                </div>
                <Badge 
                  variant="outline" 
                  className={
                    voucher.status === "Active" 
                      ? "bg-green-100 text-green-800" 
                      : "bg-gray-100 text-gray-800"
                  }
                >
                  {voucher.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderSecurityTab = () => (
    <div className="space-y-6">
      {/* Security Status Overview */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Security Status
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <Badge className="bg-green-100 text-green-800">Low</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Trusted Devices</p>
              <p className="text-lg font-semibold">3</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Biometric Auth</p>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm">Enabled</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Two-Factor Auth</p>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm">Enabled</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security Actions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Security Management</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Button 
              variant="outline" 
              className="w-full justify-start h-12"
              onClick={() => console.log("Manage devices")}
            >
              <Smartphone className="h-5 w-5 mr-3" />
              <div className="text-left">
                <p className="font-medium">Device Management</p>
                <p className="text-sm text-muted-foreground">Manage trusted devices</p>
              </div>
            </Button>
            
            <Button 
              variant="outline" 
              className="w-full justify-start h-12"
              onClick={() => console.log("Biometric settings")}
            >
              <Fingerprint className="h-5 w-5 mr-3" />
              <div className="text-left">
                <p className="font-medium">Biometric Authentication</p>
                <p className="text-sm text-muted-foreground">Fingerprint, Face ID, Voice</p>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onGoBack || (() => onNavigate("dashboard"))}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-foreground">Account</h1>
            <p className="text-sm text-muted-foreground">Manage your profile, vouchers, and security</p>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="px-4 py-4">
        <div className="flex bg-muted rounded-lg p-1">
          <button
            onClick={() => setActiveTab("profile")}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors duration-200 ${
              activeTab === "profile"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => setActiveTab("vouchers")}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors duration-200 ${
              activeTab === "vouchers"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Vouchers
          </button>
          <button
            onClick={() => setActiveTab("security")}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors duration-200 ${
              activeTab === "security"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Security
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pb-6">
        {activeTab === "profile" && renderProfileTab()}
        {activeTab === "vouchers" && renderVouchersTab()}
        {activeTab === "security" && renderSecurityTab()}
      </div>
    </div>
  );
}
