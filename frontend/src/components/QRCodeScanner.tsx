import { useState, useEffect, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Camera, 
  CameraOff, 
  Flashlight, 
  FlashlightOff, 
  RotateCcw, 
  X, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Maximize2,
  Minimize2
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface QRCodeScannerProps {
  isOpen: boolean;
  onClose: () => void;
  onScan: (data: string) => void;
  onError?: (error: string) => void;
  title?: string;
  description?: string;
}

interface CameraState {
  hasPermission: boolean;
  isActive: boolean;
  isFlashOn: boolean;
  error: string | null;
}

export function QRCodeScanner({ 
  isOpen, 
  onClose, 
  onScan, 
  onError,
  title = "Scan QR Code",
  description = "Position the QR code within the frame to scan"
}: QRCodeScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const scanIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const [cameraState, setCameraState] = useState<CameraState>({
    hasPermission: false,
    isActive: false,
    isFlashOn: false,
    error: null
  });
  
  const [isScanning, setIsScanning] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [lastScanTime, setLastScanTime] = useState(0);
  const { toast } = useToast();

  // Request camera permission and start stream
  const startCamera = useCallback(async () => {
    try {
      setCameraState(prev => ({ ...prev, error: null }));
      
      // Check if camera is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Camera not supported on this device");
      }

      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        
        setCameraState(prev => ({
          ...prev,
          hasPermission: true,
          isActive: true,
          error: null
        }));

        // Start scanning when video is ready
        videoRef.current.onloadedmetadata = () => {
          if (videoRef.current) {
            videoRef.current.play();
            startScanning();
          }
        };
      }
    } catch (error: any) {
      const errorMessage = error.name === 'NotAllowedError' 
        ? "Camera permission denied. Please allow camera access to scan QR codes."
        : error.name === 'NotFoundError'
        ? "No camera found on this device."
        : "Failed to access camera. Please try again.";
      
      setCameraState(prev => ({
        ...prev,
        hasPermission: false,
        isActive: false,
        error: errorMessage
      }));
      
      onError?.(errorMessage);
      toast({
        title: "Camera Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  }, [onError, toast]);

  // Stop camera stream
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    
    setCameraState(prev => ({
      ...prev,
      isActive: false,
      isFlashOn: false
    }));
    setIsScanning(false);
  }, []);

  // Start QR code scanning
  const startScanning = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;
    
    setIsScanning(true);
    
    const scan = () => {
      if (!videoRef.current || !canvasRef.current) return;
      
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      if (!context) return;
      
      // Set canvas size to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      // Draw current video frame to canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Get image data for QR code detection
      const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
      
      // Simple QR code detection (in real app, use a proper QR library)
      // For now, we'll simulate detection
      const now = Date.now();
      if (now - lastScanTime > 2000) { // Throttle scans to every 2 seconds
        // Simulate QR code detection
        const mockQRData = "https://preklo.app/pay/sarah_m?amount=50&currency=USDC";
        if (Math.random() > 0.95) { // 5% chance of "detecting" a QR code
          handleQRDetected(mockQRData);
        }
      }
    };
    
    // Scan every 100ms
    scanIntervalRef.current = setInterval(scan, 100);
  }, [lastScanTime]);

  // Handle QR code detection
  const handleQRDetected = useCallback((data: string) => {
    setLastScanTime(Date.now());
    setIsScanning(false);
    stopCamera();
    
    // Validate QR code data
    if (validateQRCode(data)) {
      onScan(data);
      toast({
        title: "QR Code Scanned",
        description: "Successfully scanned QR code",
      });
    } else {
      onError?.("Invalid QR code format");
      toast({
        title: "Invalid QR Code",
        description: "The scanned QR code is not valid",
        variant: "destructive",
      });
    }
  }, [onScan, onError, stopCamera, toast]);

  // Validate QR code data
  const validateQRCode = (data: string): boolean => {
    // Basic validation - check if it's a valid URL or payment data
    try {
      if (data.startsWith('https://preklo.app/') || 
          data.startsWith('preklo://') ||
          data.includes('amount=') ||
          data.includes('@')) {
        return true;
      }
      return false;
    } catch {
      return false;
    }
  };

  // Toggle flashlight
  const toggleFlashlight = useCallback(async () => {
    if (!streamRef.current) return;
    
    try {
      const track = streamRef.current.getVideoTracks()[0];
      if (track && track.getCapabilities().torch) {
        await track.applyConstraints({
          advanced: [{ torch: !cameraState.isFlashOn }]
        });
        setCameraState(prev => ({ ...prev, isFlashOn: !prev.isFlashOn }));
      }
    } catch (error) {
      console.warn("Flashlight not supported on this device");
    }
  }, [cameraState.isFlashOn]);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  // Handle component mount/unmount
  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }
    
    return () => {
      stopCamera();
    };
  }, [isOpen, startCamera, stopCamera]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4">
      <Card className={`w-full max-w-md ${isFullscreen ? 'max-w-none h-full' : 'max-h-[90vh]'} transition-all duration-300`}>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleFullscreen}
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Camera View */}
          <div className="relative bg-black rounded-lg overflow-hidden aspect-square">
            {cameraState.isActive ? (
              <>
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  playsInline
                  muted
                />
                
                {/* Scanning Overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative">
                    {/* Scanning Frame */}
                    <div className="w-64 h-64 border-2 border-primary rounded-lg relative">
                      <div className="absolute top-0 left-0 w-6 h-6 border-t-4 border-l-4 border-primary rounded-tl-lg"></div>
                      <div className="absolute top-0 right-0 w-6 h-6 border-t-4 border-r-4 border-primary rounded-tr-lg"></div>
                      <div className="absolute bottom-0 left-0 w-6 h-6 border-b-4 border-l-4 border-primary rounded-bl-lg"></div>
                      <div className="absolute bottom-0 right-0 w-6 h-6 border-b-4 border-r-4 border-primary rounded-br-lg"></div>
                      
                      {/* Scanning Line */}
                      {isScanning && (
                        <div className="absolute top-0 left-0 w-full h-1 bg-primary animate-pulse"></div>
                      )}
                    </div>
                    
                    {/* Scanning Status */}
                    <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
                      {isScanning ? (
                        <Badge variant="secondary" className="flex items-center gap-1">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          Scanning...
                        </Badge>
                      ) : (
                        <Badge variant="outline">
                          Position QR code in frame
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-white">
                {cameraState.error ? (
                  <>
                    <AlertCircle className="h-12 w-12 mb-4 text-red-400" />
                    <p className="text-center text-sm mb-4">{cameraState.error}</p>
                    <Button onClick={startCamera} variant="outline" className="text-white border-white hover:bg-white/20">
                      <Camera className="h-4 w-4 mr-2" />
                      Try Again
                    </Button>
                  </>
                ) : (
                  <>
                    <Camera className="h-12 w-12 mb-4 text-gray-400" />
                    <p className="text-center text-sm text-gray-400 mb-4">
                      Starting camera...
                    </p>
                    <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                  </>
                )}
              </div>
            )}
            
            {/* Hidden canvas for QR detection */}
            <canvas ref={canvasRef} className="hidden" />
          </div>

          {/* Camera Controls */}
          {cameraState.isActive && (
            <div className="flex items-center justify-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleFlashlight}
                disabled={!cameraState.isFlashOn && !streamRef.current?.getVideoTracks()[0]?.getCapabilities().torch}
              >
                {cameraState.isFlashOn ? (
                  <FlashlightOff className="h-4 w-4" />
                ) : (
                  <Flashlight className="h-4 w-4" />
                )}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={startCamera}
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Instructions */}
          <div className="text-center text-sm text-muted-foreground">
            <p>Point your camera at a QR code to scan it</p>
            <p className="text-xs mt-1">
              Make sure the QR code is well-lit and clearly visible
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
