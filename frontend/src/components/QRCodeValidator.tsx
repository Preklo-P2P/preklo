import { useState } from "react";
import { AlertCircle, CheckCircle, Shield, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface QRCodeValidatorProps {
  qrData: string;
  onValidated: (isValid: boolean, data: any) => void;
  onError?: (error: string) => void;
}

interface ValidationResult {
  isValid: boolean;
  type: 'payment_request' | 'user_profile' | 'unknown';
  data: any;
  warnings: string[];
  errors: string[];
}

export function QRCodeValidator({ qrData, onValidated, onError }: QRCodeValidatorProps) {
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);

  const validateQRCode = async (data: string): Promise<ValidationResult> => {
    const result: ValidationResult = {
      isValid: false,
      type: 'unknown',
      data: null,
      warnings: [],
      errors: []
    };

    try {
      // Basic format validation
      if (!data || typeof data !== 'string') {
        result.errors.push('Invalid QR code format');
        return result;
      }

      // Check if it's a URL
      if (data.startsWith('http://') || data.startsWith('https://')) {
        const url = new URL(data);
        
        // Validate Preklo URLs
        if (url.hostname.includes('preklo.app') || url.hostname.includes('preklo.com')) {
          result.type = 'payment_request';
          result.isValid = true;
          
          // Parse payment request data
          const params = new URLSearchParams(url.search);
          const amount = params.get('amount');
          const currency = params.get('currency');
          const description = params.get('description');
          const username = url.pathname.split('/').pop();
          
          result.data = {
            username,
            amount: amount ? parseFloat(amount) : null,
            currency: currency || 'USDC',
            description: description || null,
            url: data
          };

          // Validation checks
          if (amount && (isNaN(parseFloat(amount)) || parseFloat(amount) <= 0)) {
            result.warnings.push('Invalid amount specified');
          }
          
          if (currency && !['USDC', 'APT'].includes(currency)) {
            result.warnings.push('Unsupported currency');
          }
          
          if (!username || username.length < 3) {
            result.errors.push('Invalid username');
            result.isValid = false;
          }
        } else {
          result.errors.push('Not a Preklo payment URL');
        }
      }
      // Check if it's a Preklo protocol URL
      else if (data.startsWith('preklo://')) {
        result.type = 'payment_request';
        result.isValid = true;
        
        // Parse protocol URL
        const protocolData = data.replace('preklo://', '');
        const [action, ...params] = protocolData.split('/');
        
        if (action === 'pay') {
          result.data = {
            action: 'pay',
            username: params[0],
            url: data
          };
        }
      }
      // Check if it's a username format
      else if (data.startsWith('@') && data.length > 3) {
        result.type = 'user_profile';
        result.isValid = true;
        
        result.data = {
          username: data,
          type: 'profile'
        };
      }
      // Check if it's a payment amount format
      else if (data.includes('@') && (data.includes('$') || data.includes('USDC') || data.includes('APT'))) {
        result.type = 'payment_request';
        result.isValid = true;
        
        // Parse payment data from text
        const amountMatch = data.match(/\$?(\d+(?:\.\d{2})?)/);
        const currencyMatch = data.match(/(USDC|APT)/);
        const usernameMatch = data.match(/@(\w+)/);
        
        result.data = {
          amount: amountMatch ? parseFloat(amountMatch[1]) : null,
          currency: currencyMatch ? currencyMatch[1] : 'USDC',
          username: usernameMatch ? usernameMatch[1] : null,
          raw: data
        };
      }
      else {
        result.errors.push('Unrecognized QR code format');
      }

      // Security checks
      if (result.isValid) {
        // Check for suspicious patterns
        if (data.includes('javascript:') || data.includes('data:')) {
          result.errors.push('Potentially malicious QR code detected');
          result.isValid = false;
        }
        
        // Check for extremely long URLs
        if (data.length > 1000) {
          result.warnings.push('QR code contains unusually long data');
        }
        
        // Check for suspicious domains
        const suspiciousDomains = ['bit.ly', 'tinyurl.com', 't.co'];
        if (suspiciousDomains.some(domain => data.includes(domain))) {
          result.warnings.push('QR code contains shortened URL - verify destination');
        }
      }

    } catch (error) {
      result.errors.push('Failed to parse QR code data');
    }

    return result;
  };

  const handleValidate = async () => {
    setIsValidating(true);
    setValidationResult(null);
    
    try {
      const result = await validateQRCode(qrData);
      setValidationResult(result);
      onValidated(result.isValid, result.data);
      
      if (!result.isValid && result.errors.length > 0) {
        onError?.(result.errors[0]);
      }
    } catch (error) {
      const errorMessage = 'Failed to validate QR code';
      onError?.(errorMessage);
    } finally {
      setIsValidating(false);
    }
  };

  const getValidationIcon = () => {
    if (!validationResult) return null;
    
    if (validationResult.isValid) {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    } else {
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getValidationStatus = () => {
    if (!validationResult) return null;
    
    if (validationResult.isValid) {
      return <Badge variant="default" className="bg-green-100 text-green-800">Valid</Badge>;
    } else {
      return <Badge variant="destructive">Invalid</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Validation Button */}
      <Button
        onClick={handleValidate}
        disabled={isValidating || !qrData}
        className="w-full"
        variant="outline"
      >
        {isValidating ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
            Validating...
          </>
        ) : (
          <>
            <Shield className="h-4 w-4 mr-2" />
            Validate QR Code
          </>
        )}
      </Button>

      {/* Validation Result */}
      {validationResult && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              {getValidationIcon()}
              Validation Result
              {getValidationStatus()}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* QR Code Type */}
            <div>
              <span className="text-sm font-medium text-muted-foreground">Type: </span>
              <Badge variant="outline">
                {validationResult.type.replace('_', ' ').toUpperCase()}
              </Badge>
            </div>

            {/* Parsed Data */}
            {validationResult.data && (
              <div>
                <span className="text-sm font-medium text-muted-foreground">Data: </span>
                <div className="mt-2 p-3 bg-muted rounded-lg">
                  <pre className="text-xs text-foreground whitespace-pre-wrap">
                    {JSON.stringify(validationResult.data, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Warnings */}
            {validationResult.warnings.length > 0 && (
              <div>
                <span className="text-sm font-medium text-yellow-600">Warnings: </span>
                <ul className="mt-1 space-y-1">
                  {validationResult.warnings.map((warning, index) => (
                    <li key={index} className="text-sm text-yellow-600 flex items-center gap-2">
                      <AlertCircle className="h-3 w-3" />
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Errors */}
            {validationResult.errors.length > 0 && (
              <div>
                <span className="text-sm font-medium text-red-600">Errors: </span>
                <ul className="mt-1 space-y-1">
                  {validationResult.errors.map((error, index) => (
                    <li key={index} className="text-sm text-red-600 flex items-center gap-2">
                      <AlertCircle className="h-3 w-3" />
                      {error}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Actions */}
            {validationResult.isValid && (
              <div className="flex gap-2 pt-2">
                <Button
                  size="sm"
                  onClick={() => {
                    if (validationResult.data.url) {
                      window.open(validationResult.data.url, '_blank');
                    }
                  }}
                  className="flex-1"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Open Link
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
