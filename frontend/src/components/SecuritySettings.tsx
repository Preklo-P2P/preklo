import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { 
  Shield, 
  Fingerprint, 
  Smartphone, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Settings,
  Bell,
  Clock,
  MapPin,
  Activity
} from "lucide-react";

interface SecuritySettingsProps {
  onNavigate: (page: string) => void;
}

interface SecurityStatus {
  has_biometric_auth: boolean;
  trusted_devices_count: number;
  risk_score: number;
  security_recommendations: string[];
  mfa_enabled: boolean;
  session_timeout_minutes: number;
}

interface SecurityEvent {
  id: string;
  event_type: string;
  risk_score: number;
  created_at: string;
  ip_address?: string;
  device_id?: string;
}

export function SecuritySettings({ onNavigate }: SecuritySettingsProps) {
  const { toast } = useToast();
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus>({
    has_biometric_auth: false,
    trusted_devices_count: 0,
    risk_score: 25,
    security_recommendations: [],
    mfa_enabled: false,
    session_timeout_minutes: 30
  });
  const [recentEvents, setRecentEvents] = useState<SecurityEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Mock data - replace with real API calls
  useEffect(() => {
    const loadSecurityData = async () => {
      setIsLoading(true);
      
      try {
        // Simulate API calls
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setSecurityStatus({
          has_biometric_auth: true,
          trusted_devices_count: 3,
          risk_score: 25,
          security_recommendations: [
            "Enable two-factor authentication",
            "Review trusted devices regularly",
            "Use strong, unique passwords"
          ],
          mfa_enabled: true,
          session_timeout_minutes: 30
        });
        
        setRecentEvents([
          {
            id: "1",
            event_type: "login",
            risk_score: 10,
            created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            ip_address: "192.168.1.100",
            device_id: "device-123"
          },
          {
            id: "2",
            event_type: "transaction",
            risk_score: 15,
            created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            ip_address: "192.168.1.100",
            device_id: "device-123"
          },
          {
            id: "3",
            event_type: "device_trusted",
            risk_score: 5,
            created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            ip_address: "192.168.1.100",
            device_id: "device-456"
          }
        ]);
      } catch (error) {
        toast({
          title: "Failed to load security data",
          description: "Please try again later",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadSecurityData();
  }, [toast]);

  const getRiskLevel = (score: number) => {
    if (score >= 70) return { level: "Critical", color: "bg-red-100 text-red-800" };
    if (score >= 50) return { level: "High", color: "bg-orange-100 text-orange-800" };
    if (score >= 30) return { level: "Medium", color: "bg-yellow-100 text-yellow-800" };
    return { level: "Low", color: "bg-green-100 text-green-800" };
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case "login":
        return <Unlock className="h-4 w-4" />;
      case "transaction":
        return <Activity className="h-4 w-4" />;
      case "device_trusted":
        return <Smartphone className="h-4 w-4" />;
      case "biometric_registered":
        return <Fingerprint className="h-4 w-4" />;
      default:
        return <Shield className="h-4 w-4" />;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  };

  const handleToggleBiometric = async (enabled: boolean) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSecurityStatus(prev => ({
        ...prev,
        has_biometric_auth: enabled
      }));
      
      toast({
        title: enabled ? "Biometric authentication enabled" : "Biometric authentication disabled",
        description: enabled 
          ? "You can now use biometric authentication for secure access"
          : "Biometric authentication has been disabled"
      });
    } catch (error) {
      toast({
        title: "Failed to update biometric settings",
        description: "Please try again later",
        variant: "destructive"
      });
    }
  };

  const handleToggleMFA = async (enabled: boolean) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSecurityStatus(prev => ({
        ...prev,
        mfa_enabled: enabled
      }));
      
      toast({
        title: enabled ? "Two-factor authentication enabled" : "Two-factor authentication disabled",
        description: enabled 
          ? "Additional security layer has been added to your account"
          : "Two-factor authentication has been disabled"
      });
    } catch (error) {
      toast({
        title: "Failed to update MFA settings",
        description: "Please try again later",
        variant: "destructive"
      });
    }
  };

  const riskLevel = getRiskLevel(securityStatus.risk_score);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background pb-20">
        <div className="flex items-center justify-center min-h-screen">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => onNavigate("profile")}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <Settings className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-foreground">Security Settings</h1>
            <p className="text-sm text-muted-foreground">Manage your account security</p>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="px-4 py-6 space-y-6">
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
                <Badge className={riskLevel.color}>
                  {riskLevel.level}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Trusted Devices</p>
                <p className="text-lg font-semibold">{securityStatus.trusted_devices_count}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Biometric Auth</p>
                <div className="flex items-center gap-2">
                  {securityStatus.has_biometric_auth ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600" />
                  )}
                  <span className="text-sm">
                    {securityStatus.has_biometric_auth ? "Enabled" : "Disabled"}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Two-Factor Auth</p>
                <div className="flex items-center gap-2">
                  {securityStatus.mfa_enabled ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600" />
                  )}
                  <span className="text-sm">
                    {securityStatus.mfa_enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Authentication Settings */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Lock className="h-5 w-5 text-primary" />
              Authentication
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Fingerprint className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="font-medium">Biometric Authentication</p>
                  <p className="text-sm text-muted-foreground">
                    Use fingerprint or face recognition
                  </p>
                </div>
              </div>
              <Switch
                checked={securityStatus.has_biometric_auth}
                onCheckedChange={handleToggleBiometric}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="font-medium">Two-Factor Authentication</p>
                  <p className="text-sm text-muted-foreground">
                    Add an extra layer of security
                  </p>
                </div>
              </div>
              <Switch
                checked={securityStatus.mfa_enabled}
                onCheckedChange={handleToggleMFA}
              />
            </div>
          </CardContent>
        </Card>

        {/* Device Management */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Smartphone className="h-5 w-5 text-primary" />
              Device Management
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Trusted Devices</p>
                <p className="text-sm text-muted-foreground">
                  {securityStatus.trusted_devices_count} device{securityStatus.trusted_devices_count !== 1 ? 's' : ''} trusted
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate("devices")}
              >
                Manage
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Security Recommendations */}
        {securityStatus.security_recommendations.length > 0 && (
          <Card className="border-amber-200 bg-amber-50">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                Security Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {securityStatus.security_recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <div className="w-1.5 h-1.5 bg-amber-600 rounded-full mt-2 flex-shrink-0" />
                    <span className="text-amber-800">{recommendation}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Recent Security Events */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              Recent Security Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentEvents.map((event) => (
                <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
                      {getEventIcon(event.event_type)}
                    </div>
                    <div>
                      <p className="font-medium capitalize">
                        {event.event_type.replace('_', ' ')}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {formatTimeAgo(event.created_at)}
                        {event.ip_address && ` • ${event.ip_address}`}
                      </p>
                    </div>
                  </div>
                  <Badge 
                    variant="outline" 
                    className={
                      event.risk_score >= 50 
                        ? "border-red-200 text-red-800" 
                        : event.risk_score >= 30 
                        ? "border-yellow-200 text-yellow-800"
                        : "border-green-200 text-green-800"
                    }
                  >
                    Risk: {event.risk_score}
                  </Badge>
                </div>
              ))}
            </div>
            
            <Button
              variant="outline"
              className="w-full mt-4"
              onClick={() => onNavigate("security-events")}
            >
              View All Events
            </Button>
          </CardContent>
        </Card>

        {/* Advanced Settings */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Settings className="h-5 w-5 text-primary" />
                Advanced Settings
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                {showAdvanced ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </CardHeader>
          {showAdvanced && (
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Clock className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Session Timeout</p>
                    <p className="text-sm text-muted-foreground">
                      {securityStatus.session_timeout_minutes} minutes
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm">
                  Change
                </Button>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Bell className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Security Notifications</p>
                    <p className="text-sm text-muted-foreground">
                      Get alerts for security events
                    </p>
                  </div>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
}

