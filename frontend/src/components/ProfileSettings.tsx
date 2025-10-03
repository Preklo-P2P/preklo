import { useState, useEffect, useMemo } from "react";
import { 
  ArrowLeft, 
  User, 
  Shield, 
  Bell, 
  HelpCircle, 
  LogOut, 
  ChevronRight,
  Edit2,
  Copy,
  ExternalLink,
  Settings
} from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import { useToast } from "@/hooks/use-toast";
import { userService } from "@/services/userService";
import { authService } from "@/services/authService";

interface ProfileSettingsProps {
  onNavigate: (page: string) => void;
  onGoBack?: () => void;
}

// User data interface
interface User {
  id: string;
  username: string;
  email: string;
  wallet_address: string;
  is_custodial: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  terms_agreed: boolean;
  terms_agreed_at: string | null;
}

export function ProfileSettings({ onNavigate, onGoBack }: ProfileSettingsProps) {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    username: '',
    email: ''
  });
  const { toast } = useToast();

  // Load user data from backend
  useEffect(() => {
    const loadUserData = async () => {
      try {
        setIsLoading(true);
        const userData = await userService.getCurrentUser();
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user data:', error);
        toast({
          title: "Error",
          description: "Failed to load profile data",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadUserData();
  }, [toast]);

  const handleCopyUsername = () => {
    if (user) {
      navigator.clipboard.writeText(user.username);
      toast({
        title: "Username copied!",
        description: "Your username has been copied to clipboard",
      });
    }
  };

  const handleEditProfile = () => {
    if (user) {
      setEditForm({
        username: user.username,
        email: user.email
      });
      setIsEditing(true);
    }
  };

  const handleSaveProfile = async () => {
    try {
      if (!user) return;

      const updatedUser = await userService.updateProfile({
        username: editForm.username,
        email: editForm.email
      });

      setUser(updatedUser);
      setIsEditing(false);
      
      // Update localStorage with new data
      localStorage.setItem('preklo_username', editForm.username);
      localStorage.setItem('preklo_email', editForm.email);

      toast({
        title: "Profile updated!",
        description: "Your profile has been successfully updated",
      });
    } catch (error) {
      console.error('Failed to update profile:', error);
      toast({
        title: "Error",
        description: "Failed to update profile. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditForm({ username: '', email: '' });
  };

  const menuSections = useMemo(() => [
    {
      title: "Account",
      items: [
        {
          id: "profile",
          label: "Edit Profile",
          icon: <User className="h-5 w-5" />,
          description: "Update your personal information",
          onClick: handleEditProfile,
        },
        {
          id: "username",
          label: "Username",
          icon: <Edit2 className="h-5 w-5" />,
          description: user?.username || "",
          action: (
            <button
              onClick={handleCopyUsername}
              className="p-2 rounded-full hover:bg-muted transition-colors duration-200"
              aria-label="Copy username"
            >
              <Copy className="h-4 w-4 text-muted-foreground" />
            </button>
          ),
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
          onClick: () => onNavigate("security"),
        },
        {
          id: "privacy",
          label: "Privacy Controls",
          icon: <Settings className="h-5 w-5" />,
          description: "Manage your privacy preferences",
          onClick: () => console.log("Privacy settings"),
        },
      ]
    },
    {
      title: "Preferences",
      items: [
        {
          id: "notifications",
          label: "Notifications",
          icon: <Bell className="h-5 w-5" />,
          description: "Payment alerts and updates",
          action: (
            <button
              onClick={() => setNotificationsEnabled(!notificationsEnabled)}
              className={`w-12 h-6 rounded-full transition-colors duration-200 relative ${
                notificationsEnabled ? "bg-primary" : "bg-muted"
              }`}
              aria-label="Toggle notifications"
            >
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform duration-200 ${
                notificationsEnabled ? "translate-x-6" : "translate-x-0.5"
              }`} />
            </button>
          ),
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
          description: "Get help with your account",
          onClick: () => onNavigate("help"),
        },
        {
          id: "terms",
          label: "Terms & Privacy",
          icon: <ExternalLink className="h-5 w-5" />,
          description: "Legal information",
          onClick: () => console.log("Terms & privacy"),
        },
      ]
    }
  ], [user, handleEditProfile, handleCopyUsername, onNavigate, notificationsEnabled, setNotificationsEnabled]);

  // Show loading if user data is not loaded yet
  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleLogout = async () => {
    try {
      await authService.logout();
      toast({
        title: "Logged out",
        description: "You have been successfully logged out",
      });
      onNavigate("logout");
    } catch (error) {
      console.error('Logout error:', error);
      // Still navigate to logout even if API call fails
      onNavigate("logout");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

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
          <div>
            <h1 className="text-xl font-semibold text-foreground">Profile & Settings</h1>
            <p className="text-sm text-muted-foreground">Manage your account</p>
          </div>
        </div>
      </header>

      {/* Profile Header */}
      <div className="px-4 py-6">
        <div className="bg-card border border-border rounded-2xl p-6">
          {isEditing ? (
            // Edit Form
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold text-primary">
                    {editForm.username.replace('@', '').charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="flex-1">
                  <h2 className="text-xl font-bold text-foreground mb-2">Edit Profile</h2>
                  <p className="text-sm text-muted-foreground">Update your personal information</p>
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Username
                  </label>
                  <input
                    type="text"
                    value={editForm.username}
                    onChange={(e) => setEditForm(prev => ({ ...prev, username: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Enter username"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Enter email"
                  />
                </div>
              </div>
              
              <div className="flex gap-3 pt-4">
                <ActionButton
                  onClick={handleSaveProfile}
                  size="sm"
                  className="flex-1"
                >
                  Save Changes
                </ActionButton>
                <ActionButton
                  onClick={handleCancelEdit}
                  variant="outline"
                  size="sm"
                  className="flex-1"
                >
                  Cancel
                </ActionButton>
              </div>
            </div>
          ) : (
            // Display View
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-primary">
                  {user.username.replace('@', '').charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="text-xl font-bold text-foreground">{user.username}</h2>
                  {user.is_active && (
                    <div className="w-5 h-5 bg-success rounded-full flex items-center justify-center">
                      <div className="w-3 h-3 bg-white rounded-full" />
                    </div>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">{user.email}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Member since {formatDate(user.created_at)}
                </p>
                <p className="text-xs text-muted-foreground">
                  Wallet: {user.is_custodial ? 'Custodial' : 'Petra Wallet'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Settings Menu */}
      <main className="px-4 space-y-6">
        {menuSections.map((section) => (
          <div key={section.title}>
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3 px-2">
              {section.title}
            </h3>
            <div className="space-y-2">
              {section.items.map((item) => (
                <button
                  key={item.id}
                  onClick={item.onClick}
                  className="w-full bg-card border border-border rounded-xl p-4 hover:bg-muted/50 transition-colors duration-200 text-left min-h-[60px]"
                  disabled={!item.onClick}
                >
                  <div className="flex items-center gap-4">
                    <div className="text-muted-foreground">
                      {item.icon}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-foreground">{item.label}</h4>
                      {item.description && (
                        <p className="text-sm text-muted-foreground">{item.description}</p>
                      )}
                    </div>
                    {item.action ? (
                      item.action
                    ) : item.onClick ? (
                      <ChevronRight className="h-5 w-5 text-muted-foreground" />
                    ) : null}
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}

        {/* Logout Button */}
        <div className="pt-6">
          <ActionButton
            onClick={handleLogout}
            variant="destructive"
            fullWidth
            size="lg"
            icon={<LogOut className="h-5 w-5" />}
          >
            Sign Out
          </ActionButton>
        </div>

        {/* App Version */}
        <div className="text-center py-4">
          <p className="text-xs text-muted-foreground">
            Preklo v1.0.0 • Made with love for global payments
          </p>
        </div>
      </main>
    </div>
  );
}