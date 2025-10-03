/**
 * Performance Monitoring Hook
 * Tracks Core Web Vitals and custom performance metrics
 */

import { useEffect, useState, useCallback } from 'react';
import { performanceMonitor } from '@/lib/pwa';

interface PerformanceMetrics {
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  ttfb?: number; // Time to First Byte
  custom: Map<string, number>;
}

export function usePerformance() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    custom: new Map(),
  });

  const measurePerformance = useCallback((name: string, fn: () => void | Promise<void>) => {
    performanceMonitor.measurePerformance(name, fn);
    
    // Update custom metrics
    setMetrics(prev => ({
      ...prev,
      custom: performanceMonitor.getMetrics(),
    }));
  }, []);

  useEffect(() => {
    // Monitor Core Web Vitals
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        switch (entry.entryType) {
          case 'paint':
            if (entry.name === 'first-contentful-paint') {
              setMetrics(prev => ({ ...prev, fcp: entry.startTime }));
            }
            break;
          case 'largest-contentful-paint':
            setMetrics(prev => ({ ...prev, lcp: entry.startTime }));
            break;
          case 'first-input':
            setMetrics(prev => ({ ...prev, fid: entry.processingStart - entry.startTime }));
            break;
          case 'layout-shift':
            if (!(entry as any).hadRecentInput) {
              setMetrics(prev => ({ 
                ...prev, 
                cls: (prev.cls || 0) + (entry as any).value 
              }));
            }
            break;
          case 'navigation':
            setMetrics(prev => ({ ...prev, ttfb: entry.responseStart - entry.requestStart }));
            break;
        }
      }
    });

    // Observe all performance entry types
    try {
      observer.observe({ entryTypes: ['paint', 'largest-contentful-paint', 'first-input', 'layout-shift', 'navigation'] });
    } catch (error) {
      console.warn('Performance Observer not supported:', error);
    }

    return () => observer.disconnect();
  }, []);

  return {
    metrics,
    measurePerformance,
  };
}

/**
 * Accessibility Hook
 * Provides accessibility utilities and keyboard navigation
 */

export function useAccessibility() {
  const [isKeyboardUser, setIsKeyboardUser] = useState(false);
  const [focusVisible, setFocusVisible] = useState(false);

  useEffect(() => {
    // Detect keyboard usage
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        setIsKeyboardUser(true);
        setFocusVisible(true);
      }
    };

    const handleMouseDown = () => {
      setIsKeyboardUser(false);
      setFocusVisible(false);
    };

    const handleFocusIn = (e: FocusEvent) => {
      if (isKeyboardUser) {
        setFocusVisible(true);
      }
    };

    const handleFocusOut = () => {
      setFocusVisible(false);
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('focusin', handleFocusIn);
    document.addEventListener('focusout', handleFocusOut);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('focusin', handleFocusIn);
      document.removeEventListener('focusout', handleFocusOut);
    };
  }, [isKeyboardUser]);

  const announceToScreenReader = useCallback((message: string) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  return {
    isKeyboardUser,
    focusVisible,
    announceToScreenReader,
  };
}

/**
 * Mobile Detection Hook
 * Detects mobile devices and touch capabilities
 */

export function useMobile() {
  const [isMobile, setIsMobile] = useState(false);
  const [isTouch, setIsTouch] = useState(false);
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');

  useEffect(() => {
    // Detect mobile device
    const checkMobile = () => {
      const userAgent = navigator.userAgent;
      const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
      setIsMobile(isMobileDevice);
    };

    // Detect touch capability
    const checkTouch = () => {
      setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0);
    };

    // Detect orientation
    const checkOrientation = () => {
      setOrientation(window.innerHeight > window.innerWidth ? 'portrait' : 'landscape');
    };

    checkMobile();
    checkTouch();
    checkOrientation();

    // Listen for orientation changes
    const handleOrientationChange = () => {
      setTimeout(checkOrientation, 100); // Small delay to ensure accurate dimensions
    };

    window.addEventListener('orientationchange', handleOrientationChange);
    window.addEventListener('resize', handleOrientationChange);

    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange);
      window.removeEventListener('resize', handleOrientationChange);
    };
  }, []);

  return {
    isMobile,
    isTouch,
    orientation,
  };
}

/**
 * PWA Hook
 * Manages PWA state and functionality
 */

import { pwaManager, PWAState } from '@/lib/pwa';

export function usePWA() {
  const [pwaState, setPwaState] = useState<PWAState>(pwaManager.getState());

  useEffect(() => {
    const unsubscribe = pwaManager.subscribe(setPwaState);
    return unsubscribe;
  }, []);

  const installPWA = useCallback(async () => {
    await pwaManager.installPWA();
  }, []);

  const updateServiceWorker = useCallback(async () => {
    await pwaManager.updateServiceWorker();
  }, []);

  const skipWaiting = useCallback(async () => {
    await pwaManager.skipWaiting();
  }, []);

  const requestNotificationPermission = useCallback(async () => {
    return await pwaManager.requestNotificationPermission();
  }, []);

  const sendNotification = useCallback(async (title: string, options?: NotificationOptions) => {
    await pwaManager.sendNotification(title, options);
  }, []);

  return {
    ...pwaState,
    installPWA,
    updateServiceWorker,
    skipWaiting,
    requestNotificationPermission,
    sendNotification,
  };
}

/**
 * Offline Hook
 * Manages offline state and data synchronization
 */

import { offlineManager } from '@/lib/pwa';

export function useOffline() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const storeOfflineData = useCallback(async (key: string, data: any) => {
    await offlineManager.storeOfflineData(key, data);
  }, []);

  const getOfflineData = useCallback(async (key: string) => {
    return await offlineManager.getOfflineData(key);
  }, []);

  const syncOfflineData = useCallback(async () => {
    await offlineManager.syncOfflineData();
  }, []);

  return {
    isOnline,
    storeOfflineData,
    getOfflineData,
    syncOfflineData,
  };
}
