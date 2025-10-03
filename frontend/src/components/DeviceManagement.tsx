import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { 
  Smartphone, 
  Monitor, 
  Tablet, 
  Trash2, 
  Shield, 
  ShieldOff,
  Clock,
  MapPin,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Plus,
  ArrowLeft
} from "lucide-react";

interface DeviceManagementProps {
  onNavigate: (page: string) => void;
}

interface TrustedDevice {
  id: string;
  device_name: string;
  device_fingerprint: string;
  device_type: string;
  is_trusted: boolean;
  last_used_at: string;
  created_at: string;
  ip_address?: string;
  location?: string;
}

export function DeviceManagement({ onNavigate }: DeviceManagementProps) {
  const { toast } = useToast();
  const [devices, setDevices] = useState<TrustedDevice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRemoving, setIsRemoving] = useState<string | null>(null);

  // Mock data - replace with real API calls
  useEffect(() => {
    const loadDevices = async () => {
      setIsLoading(true);
      
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setDevices([
          {
            id: "device-1",
            device_name: "iPhone 15 Pro",
            device_fingerprint: "abc123def456",
            device_type: "mobile",
            is_trusted: true,
            last_used_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
            ip_address: "192.168.1.100",
            location: "New York, NY"
          },
          {
            id: "device-2",
            device_name: "MacBook Pro",
            device_fingerprint: "xyz789ghi012",
            device_type: "desktop",
            is_trusted: true,
            last_used_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
            ip_address: "192.168.1.101",
            location: "New York, NY"
          },
          {
            id: "device-3",
            device_name: "iPad Air",
            device_fingerprint: "mno345pqr678",
            device_type: "tablet",
            is_trusted: false,
            last_used_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
            ip_address: "192.168.1.102",
            location: "New York, NY"
          }
        ]);
      } catch (error) {
        toast({
          title: "Failed to load devices",
          description: "Please try again later",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadDevices();
  }, [toast]);

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType) {
      case "mobile":
        return <Smartphone className="h-5 w-5" />;
      case "desktop":
        return <Monitor className="h-5 w-5" />;
      case "tablet":
        return <Tablet className="h-5 w-5" />;
      default:
        return <Smartphone className="h-5 w-5" />;
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

  const handleTrustDevice = async (deviceId: string, trusted: boolean) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setDevices(prev => prev.map(device => 
        device.id === deviceId 
          ? { ...device, is_trusted: trusted }
          : device
      ));
      
      toast({
        title: trusted ? "Device trusted" : "Device untrusted",
        description: trusted 
          ? "This device is now trusted for your account"
          : "This device is no longer trusted"
      });
    } catch (error) {
      toast({
        title: "Failed to update device trust",
        description: "Please try again later",
        variant: "destructive"
      });
    }
  };

  const handleRemoveDevice = async (deviceId: string) => {
    setIsRemoving(deviceId);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setDevices(prev => prev.filter(device => device.id !== deviceId));
      
      toast({
        title: "Device removed",
        description: "Device has been removed from your account"
      });
    } catch (error) {
      toast({
        title: "Failed to remove device",
        description: "Please try again later",
        variant: "destructive"
      });
    } finally {
      setIsRemoving(null);
    }
  };

  const trustedDevices = devices.filter(device => device.is_trusted);
  const untrustedDevices = devices.filter(device => !device.is_trusted);

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
            onClick={() => onNavigate("security")}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-foreground">Device Management</h1>
            <p className="text-sm text-muted-foreground">Manage your trusted devices</p>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="px-4 py-6 space-y-6">
        {/* Summary */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Trusted Devices</p>
                  <p className="text-2xl font-bold text-green-600">{trustedDevices.length}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Untrusted Devices</p>
                  <p className="text-2xl font-bold text-orange-600">{untrustedDevices.length}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Trusted Devices */}
        {trustedDevices.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-600" />
                Trusted Devices
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trustedDevices.map((device) => (
                  <div key={device.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                        {getDeviceIcon(device.device_type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{device.device_name}</h3>
                          <Badge variant="outline" className="bg-green-100 text-green-800">
                            Trusted
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatTimeAgo(device.last_used_at)}
                          </div>
                          {device.location && (
                            <div className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {device.location}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTrustDevice(device.id, false)}
                      >
                        <ShieldOff className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRemoveDevice(device.id)}
                        disabled={isRemoving === device.id}
                      >
                        {isRemoving === device.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Untrusted Devices */}
        {untrustedDevices.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                Untrusted Devices
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {untrustedDevices.map((device) => (
                  <div key={device.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                        {getDeviceIcon(device.device_type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{device.device_name}</h3>
                          <Badge variant="outline" className="bg-orange-100 text-orange-800">
                            Untrusted
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatTimeAgo(device.last_used_at)}
                          </div>
                          {device.location && (
                            <div className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {device.location}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTrustDevice(device.id, true)}
                      >
                        <Shield className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRemoveDevice(device.id)}
                        disabled={isRemoving === device.id}
                      >
                        {isRemoving === device.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Add New Device */}
        <Card className="border-dashed">
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                <Plus className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">Add New Device</h3>
              <p className="text-muted-foreground mb-4">
                Trust a new device to access your account securely
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  toast({
                    title: "Device Detection",
                    description: "We'll automatically detect and prompt you to trust new devices when you log in from them"
                  });
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Device
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Security Tips */}
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-medium text-blue-900">Security Tips</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Only trust devices you own and control</li>
                  <li>• Remove devices you no longer use</li>
                  <li>• Review your trusted devices regularly</li>
                  <li>• If you lose a device, remove it immediately</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

