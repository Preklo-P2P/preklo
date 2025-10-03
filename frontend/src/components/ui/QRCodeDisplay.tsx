import { useState, useEffect, useRef } from "react";
import { Copy, Share2, Download, Palette, Settings, X } from "lucide-react";
import { ActionButton } from "./ActionButton";
import { Button } from "./button";
import { Card, CardContent, CardHeader, CardTitle } from "./card";
import { useToast } from "@/hooks/use-toast";
import QRCode from "qrcode";

interface QRCodeDisplayProps {
  data: string;
  size?: number;
  title?: string;
  subtitle?: string;
  showActions?: boolean;
  showCustomization?: boolean;
  className?: string;
}

interface QRCodeOptions {
  color: {
    dark: string;
    light: string;
  };
  margin: number;
  errorCorrectionLevel: 'L' | 'M' | 'Q' | 'H';
  width: number;
}

export function QRCodeDisplay({ 
  data, 
  size = 200, 
  title = "Scan to Pay", 
  subtitle,
  showActions = true,
  showCustomization = false,
  className 
}: QRCodeDisplayProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [qrCodeDataURL, setQrCodeDataURL] = useState<string>("");
  const [showCustomizationPanel, setShowCustomizationPanel] = useState(false);
  const [qrOptions, setQrOptions] = useState<QRCodeOptions>({
    color: {
      dark: '#000000',
      light: '#ffffff'
    },
    margin: 2,
    errorCorrectionLevel: 'M',
    width: size
  });
  const modalRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Generate QR code using the qrcode library
  const generateQRCode = async (text: string, options: QRCodeOptions): Promise<string> => {
    try {
      const dataURL = await QRCode.toDataURL(text, {
        color: options.color,
        margin: options.margin,
        errorCorrectionLevel: options.errorCorrectionLevel,
        width: options.width,
        type: 'image/png'
      });
      return dataURL;
    } catch (error) {
      console.error('Error generating QR code:', error);
      throw new Error('Failed to generate QR code');
    }
  };

  // Generate QR code when data or options change
  useEffect(() => {
    const generateQR = async () => {
      if (!data) return;
      
      setIsLoading(true);
      try {
        const dataURL = await generateQRCode(data, qrOptions);
        setQrCodeDataURL(dataURL);
      } catch (error) {
        toast({
          title: "QR Code Error",
          description: "Failed to generate QR code",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    generateQR();
  }, [data, qrOptions, toast]);

  // Handle click outside modal to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      setShowCustomizationPanel(false);
    }
  };

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showCustomizationPanel) {
        setShowCustomizationPanel(false);
      }
    };

    if (showCustomizationPanel) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [showCustomizationPanel]);

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(data);
      toast({
        title: "Link copied!",
        description: "Payment link has been copied to clipboard",
      });
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Please try again",
        variant: "destructive",
      });
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: subtitle || "Send me money with Preklo",
          url: data,
        });
      } catch (error) {
        // User cancelled sharing
      }
    } else {
      // Fallback to copy
      handleCopyLink();
    }
  };

  const handleDownload = async () => {
    setIsLoading(true);
    
    try {
      // Generate high-resolution QR code for download
      const highResOptions = {
        ...qrOptions,
        width: size * 4 // 4x resolution for better quality
      };
      
      const dataURL = await generateQRCode(data, highResOptions);
      
      // Create download link
      const link = document.createElement('a');
      link.download = `preklo-qr-${Date.now()}.png`;
      link.href = dataURL;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({
        title: "QR code downloaded!",
        description: "Saved to your device",
      });
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Failed to download QR code",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`text-center space-y-6 ${className}`}>
      {/* Title and Subtitle */}
      <div>
        <h3 className="text-xl font-semibold text-foreground mb-2">{title}</h3>
        {subtitle && (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>

      {/* QR Code */}
      <div className="flex justify-center">
        <div className="bg-white p-6 rounded-2xl shadow-lg border border-border">
          {isLoading ? (
            <div className="flex items-center justify-center" style={{ width: size, height: size }}>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : qrCodeDataURL ? (
            <img
              src={qrCodeDataURL}
              alt="QR Code for payment"
              width={size}
              height={size}
              className="block"
            />
          ) : (
            <div className="flex items-center justify-center text-muted-foreground" style={{ width: size, height: size }}>
              <span className="text-sm">Generating QR code...</span>
            </div>
          )}
        </div>
      </div>

      {/* Payment Link */}
      <div className="bg-muted rounded-xl p-4">
        <p className="text-xs text-muted-foreground mb-2">Payment Link</p>
        <p className="text-sm font-mono text-foreground break-all">
          {data.length > 50 ? `${data.substring(0, 50)}...` : data}
        </p>
      </div>

      {/* Customization Modal */}
      {showCustomization && showCustomizationPanel && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={handleBackdropClick}
        >
          <Card 
            ref={modalRef}
            className="w-full max-w-md max-h-[85vh] overflow-y-auto shadow-2xl animate-in fade-in-0 zoom-in-95 duration-200"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Customize QR Code
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowCustomizationPanel(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Color Customization */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Foreground Color</label>
                  <input
                    type="color"
                    value={qrOptions.color.dark}
                    onChange={(e) => setQrOptions(prev => ({
                      ...prev,
                      color: { ...prev.color, dark: e.target.value }
                    }))}
                    className="w-full h-10 rounded-lg border border-border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Background Color</label>
                  <input
                    type="color"
                    value={qrOptions.color.light}
                    onChange={(e) => setQrOptions(prev => ({
                      ...prev,
                      color: { ...prev.color, light: e.target.value }
                    }))}
                    className="w-full h-10 rounded-lg border border-border"
                  />
                </div>
              </div>

              {/* Error Correction Level */}
              <div>
                <label className="block text-sm font-medium mb-2">Error Correction</label>
                <select
                  value={qrOptions.errorCorrectionLevel}
                  onChange={(e) => setQrOptions(prev => ({
                    ...prev,
                    errorCorrectionLevel: e.target.value as 'L' | 'M' | 'Q' | 'H'
                  }))}
                  className="w-full p-2 border border-border rounded-lg bg-background"
                >
                  <option value="L">Low (7%)</option>
                  <option value="M">Medium (15%)</option>
                  <option value="Q">Quartile (25%)</option>
                  <option value="H">High (30%)</option>
                </select>
              </div>

              {/* Margin */}
              <div>
                <label className="block text-sm font-medium mb-2">Margin: {qrOptions.margin}</label>
                <input
                  type="range"
                  min="0"
                  max="10"
                  value={qrOptions.margin}
                  onChange={(e) => setQrOptions(prev => ({
                    ...prev,
                    margin: parseInt(e.target.value)
                  }))}
                  className="w-full"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Action Buttons */}
      {showActions && (
        <div className="flex gap-3 justify-center flex-wrap">
          <ActionButton
            variant="ghost"
            size="sm"
            onClick={handleCopyLink}
            icon={<Copy className="h-4 w-4" />}
          >
            Copy Link
          </ActionButton>
          
          <ActionButton
            variant="ghost"
            size="sm"
            onClick={handleShare}
            icon={<Share2 className="h-4 w-4" />}
          >
            Share
          </ActionButton>
          
          <ActionButton
            variant="ghost"
            size="sm"
            onClick={handleDownload}
            icon={<Download className="h-4 w-4" />}
            isLoading={isLoading}
          >
            Download
          </ActionButton>

          {showCustomization && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCustomizationPanel(!showCustomizationPanel)}
              className="flex items-center gap-2"
            >
              <Settings className="h-4 w-4" />
              Customize
            </Button>
          )}
        </div>
      )}
    </div>
  );
}