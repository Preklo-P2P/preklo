import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { 
  Fingerprint, 
  Eye, 
  Mic, 
  Smartphone, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  Shield,
  ArrowLeft,
  Plus,
  Trash2
} from "lucide-react";

interface BiometricAuthProps {
  onNavigate: (page: string) => void;
}

interface BiometricCredential {
  id: string;
  credential_type: string;
  credential_id: string;
  is_active: boolean;
  created_at: string;
}

export function BiometricAuth({ onNavigate }: BiometricAuthProps) {
  const { toast } = useToast();
  const [credentials, setCredentials] = useState<BiometricCredential[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegistering, setIsRegistering] = useState(false);
  const [isRemoving, setIsRemoving] = useState<string | null>(null);
  const [availableTypes, setAvailableTypes] = useState<string[]>([]);

  // Mock data - replace with real API calls
  useEffect(() => {
    const loadBiometricData = async () => {
      setIsLoading(true);
      
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setCredentials([
          {
            id: "cred-1",
            credential_type: "fingerprint",
            credential_id: "fp_abc123",
            is_active: true,
            created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()
          },
          {
            id: "cred-2",
            credential_type: "face_id",
            credential_id: "face_xyz789",
            is_active: true,
            created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString()
          }
        ]);
        
        // Check available biometric types
        setAvailableTypes(["fingerprint", "face_id", "voice"]);
      } catch (error) {
        toast({
          title: "Failed to load biometric data",
          description: "Please try again later",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadBiometricData();
  }, [toast]);

  const getBiometricIcon = (type: string) => {
    switch (type) {
      case "fingerprint":
        return <Fingerprint className="h-5 w-5" />;
      case "face_id":
        return <Eye className="h-5 w-5" />;
      case "voice":
        return <Mic className="h-5 w-5" />;
      case "webauthn":
        return <Shield className="h-5 w-5" />;
      default:
        return <Fingerprint className="h-5 w-5" />;
    }
  };

  const getBiometricName = (type: string) => {
    switch (type) {
      case "fingerprint":
        return "Fingerprint";
      case "face_id":
        return "Face ID";
      case "voice":
        return "Voice Recognition";
      case "webauthn":
        return "WebAuthn";
      default:
        return type;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days > 0) {
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else {
      return 'Recently';
    }
  };

  const handleRegisterBiometric = async (type: string) => {
    setIsRegistering(true);
    
    try {
      // Simulate biometric registration process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const newCredential: BiometricCredential = {
        id: `cred-${Date.now()}`,
        credential_type: type,
        credential_id: `${type}_${Math.random().toString(36).substr(2, 9)}`,
        is_active: true,
        created_at: new Date().toISOString()
      };
      
      setCredentials(prev => [...prev, newCredential]);
      
      toast({
        title: `${getBiometricName(type)} registered`,
        description: "You can now use this biometric method for authentication"
      });
    } catch (error) {
      toast({
        title: "Registration failed",
        description: "Failed to register biometric credential. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsRegistering(false);
    }
  };

  const handleRemoveCredential = async (credentialId: string) => {
    setIsRemoving(credentialId);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setCredentials(prev => prev.filter(cred => cred.id !== credentialId));
      
      toast({
        title: "Biometric credential removed",
        description: "This biometric method is no longer available for authentication"
      });
    } catch (error) {
      toast({
        title: "Failed to remove credential",
        description: "Please try again later",
        variant: "destructive"
      });
    } finally {
      setIsRemoving(null);
    }
  };

  const activeCredentials = credentials.filter(cred => cred.is_active);
  const availableToRegister = availableTypes.filter(type => 
    !credentials.some(cred => cred.credential_type === type && cred.is_active)
  );

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
            <h1 className="text-xl font-semibold text-foreground">Biometric Authentication</h1>
            <p className="text-sm text-muted-foreground">Manage your biometric credentials</p>
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
                  <p className="text-sm text-muted-foreground">Active Methods</p>
                  <p className="text-2xl font-bold text-green-600">{activeCredentials.length}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Available</p>
                  <p className="text-2xl font-bold text-blue-600">{availableToRegister.length}</p>
                </div>
                <Plus className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Active Biometric Methods */}
        {activeCredentials.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-600" />
                Active Biometric Methods
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activeCredentials.map((credential) => (
                  <div key={credential.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                        {getBiometricIcon(credential.credential_type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">
                            {getBiometricName(credential.credential_type)}
                          </h3>
                          <Badge variant="outline" className="bg-green-100 text-green-800">
                            Active
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Registered {formatTimeAgo(credential.created_at)}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveCredential(credential.id)}
                      disabled={isRemoving === credential.id}
                    >
                      {isRemoving === credential.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Available Methods */}
        {availableToRegister.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Plus className="h-5 w-5 text-blue-600" />
                Available Methods
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {availableToRegister.map((type) => (
                  <div key={type} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        {getBiometricIcon(type)}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold">
                          {getBiometricName(type)}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          {type === "fingerprint" && "Use your fingerprint for quick and secure access"}
                          {type === "face_id" && "Use facial recognition for hands-free authentication"}
                          {type === "voice" && "Use your voice for secure authentication"}
                          {type === "webauthn" && "Use WebAuthn for cross-platform authentication"}
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => handleRegisterBiometric(type)}
                      disabled={isRegistering}
                    >
                      {isRegistering ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                          Registering...
                        </>
                      ) : (
                        <>
                          <Plus className="h-4 w-4 mr-2" />
                          Register
                        </>
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* No Available Methods */}
        {availableToRegister.length === 0 && activeCredentials.length > 0 && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="text-lg font-medium text-foreground mb-2">All Methods Registered</h3>
                <p className="text-muted-foreground">
                  You have registered all available biometric authentication methods
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* No Biometric Support */}
        {availableTypes.length === 0 && (
          <Card className="border-amber-200 bg-amber-50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="font-medium text-amber-900">Biometric Authentication Not Available</h4>
                  <p className="text-sm text-amber-800">
                    Your device doesn't support biometric authentication or it's not enabled. 
                    You can still use other security methods like two-factor authentication.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Security Information */}
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-medium text-blue-900">How Biometric Authentication Works</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Your biometric data is stored securely on your device</li>
                  <li>• We never have access to your actual biometric data</li>
                  <li>• Biometric authentication is faster and more secure than passwords</li>
                  <li>• You can use multiple biometric methods for redundancy</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

