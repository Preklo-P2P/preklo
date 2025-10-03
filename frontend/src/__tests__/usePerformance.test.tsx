/**
 * Performance Hooks Tests
 * Tests performance monitoring, accessibility, mobile detection, and PWA hooks
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from '@testing-library/react';
import {
  usePerformance,
  useAccessibility,
  useMobile,
  usePWA,
  useOffline,
} from '@/hooks/usePerformance';

import { vi } from 'vitest';

// Mock PWA manager
vi.mock('@/lib/pwa', () => ({
  pwaManager: {
    getState: () => ({
      isOnline: true,
      isInstalled: false,
      hasUpdate: false,
      registration: null,
    }),
    subscribe: vi.fn(() => vi.fn()),
    registerServiceWorker: vi.fn(),
    updateServiceWorker: vi.fn(),
    skipWaiting: vi.fn(),
    installPWA: vi.fn(),
    requestNotificationPermission: vi.fn(),
    sendNotification: vi.fn(),
  },
  offlineManager: {
    storeOfflineData: vi.fn(),
    getOfflineData: vi.fn(),
    syncOfflineData: vi.fn(),
  },
  performanceMonitor: {
    measurePerformance: vi.fn(),
    getMetrics: vi.fn(() => new Map()),
  },
}));

// Mock Performance Observer
const mockPerformanceObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
}));

Object.defineProperty(window, 'PerformanceObserver', {
  value: mockPerformanceObserver,
  writable: true,
});

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: vi.fn(() => Date.now()),
    mark: vi.fn(),
    measure: vi.fn(),
    getEntriesByType: vi.fn(() => []),
    getEntriesByName: vi.fn(() => []),
  },
  writable: true,
});

// Mock navigator properties
Object.defineProperty(navigator, 'onLine', {
  value: true,
  writable: true,
});

Object.defineProperty(navigator, 'userAgent', {
  value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
  writable: true,
});

Object.defineProperty(navigator, 'maxTouchPoints', {
  value: 5,
  writable: true,
});

// Test components
const PerformanceTestComponent = () => {
  const { metrics, measurePerformance } = usePerformance();

  const handleMeasure = () => {
    measurePerformance('test-operation', () => {
      // Simulate some work
      return 'result';
    });
  };

  return (
    <div>
      <button onClick={handleMeasure}>Measure Performance</button>
      <div data-testid="metrics">
        {metrics.fcp ? `FCP: ${metrics.fcp}ms` : 'No FCP'}
      </div>
    </div>
  );
};

const AccessibilityTestComponent = () => {
  const { isKeyboardUser, focusVisible, announceToScreenReader } = useAccessibility();

  const handleAnnounce = () => {
    announceToScreenReader('Test announcement');
  };

  return (
    <div>
      <div data-testid="keyboard-user">{isKeyboardUser ? 'keyboard' : 'mouse'}</div>
      <div data-testid="focus-visible">{focusVisible ? 'visible' : 'hidden'}</div>
      <button onClick={handleAnnounce}>Announce</button>
    </div>
  );
};

const MobileTestComponent = () => {
  const { isMobile, isTouch, orientation } = useMobile();

  return (
    <div>
      <div data-testid="is-mobile">{isMobile ? 'mobile' : 'desktop'}</div>
      <div data-testid="is-touch">{isTouch ? 'touch' : 'no-touch'}</div>
      <div data-testid="orientation">{orientation}</div>
    </div>
  );
};

const PWATestComponent = () => {
  const { isOnline, isInstalled, hasUpdate, installPWA, updateServiceWorker } = usePWA();

  return (
    <div>
      <div data-testid="is-online">{isOnline ? 'online' : 'offline'}</div>
      <div data-testid="is-installed">{isInstalled ? 'installed' : 'not-installed'}</div>
      <div data-testid="has-update">{hasUpdate ? 'update-available' : 'no-update'}</div>
      <button onClick={installPWA}>Install PWA</button>
      <button onClick={updateServiceWorker}>Update SW</button>
    </div>
  );
};

const OfflineTestComponent = () => {
  const { isOnline, storeOfflineData, getOfflineData, syncOfflineData } = useOffline();

  const handleStore = () => {
    storeOfflineData('test-key', { data: 'test' });
  };

  const handleGet = () => {
    getOfflineData('test-key');
  };

  const handleSync = () => {
    syncOfflineData();
  };

  return (
    <div>
      <div data-testid="offline-status">{isOnline ? 'online' : 'offline'}</div>
      <button onClick={handleStore}>Store Data</button>
      <button onClick={handleGet}>Get Data</button>
      <button onClick={handleSync}>Sync Data</button>
    </div>
  );
};

describe('usePerformance', () => {
  it('provides performance metrics', () => {
    render(<PerformanceTestComponent />);
    
    expect(screen.getByTestId('metrics')).toHaveTextContent('No FCP');
  });

  it('measures performance when called', () => {
    const { performanceMonitor } = require('@/lib/pwa');
    
    render(<PerformanceTestComponent />);
    
    fireEvent.click(screen.getByText('Measure Performance'));
    
    expect(performanceMonitor.measurePerformance).toHaveBeenCalledWith(
      'test-operation',
      expect.any(Function)
    );
  });

  it('handles Performance Observer errors gracefully', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation();
    
    // Mock PerformanceObserver to throw error
    Object.defineProperty(window, 'PerformanceObserver', {
      value: vi.fn().mockImplementation(() => {
        throw new Error('PerformanceObserver not supported');
      }),
      writable: true,
    });
    
    render(<PerformanceTestComponent />);
    
    expect(consoleSpy).toHaveBeenCalledWith(
      'Performance Observer not supported:',
      expect.any(Error)
    );
    
    consoleSpy.mockRestore();
  });
});

describe('useAccessibility', () => {
  it('detects keyboard usage', () => {
    render(<AccessibilityTestComponent />);
    
    expect(screen.getByTestId('keyboard-user')).toHaveTextContent('mouse');
  });

  it('detects keyboard navigation', () => {
    render(<AccessibilityTestComponent />);
    
    // Simulate Tab key press
    act(() => {
      fireEvent.keyDown(document, { key: 'Tab' });
    });
    
    expect(screen.getByTestId('keyboard-user')).toHaveTextContent('keyboard');
  });

  it('announces to screen reader', () => {
    render(<AccessibilityTestComponent />);
    
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation();
    
    fireEvent.click(screen.getByText('Announce'));
    
    // Should create announcement element
    expect(document.querySelector('[aria-live="polite"]')).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });

  it('handles focus events', () => {
    render(<AccessibilityTestComponent />);
    
    // Simulate focus events
    act(() => {
      fireEvent.focusIn(document.body);
      fireEvent.focusOut(document.body);
    });
    
    expect(screen.getByTestId('focus-visible')).toHaveTextContent('hidden');
  });
});

describe('useMobile', () => {
  it('detects mobile device', () => {
    render(<MobileTestComponent />);
    
    expect(screen.getByTestId('is-mobile')).toHaveTextContent('mobile');
  });

  it('detects touch capability', () => {
    render(<MobileTestComponent />);
    
    expect(screen.getByTestId('is-touch')).toHaveTextContent('touch');
  });

  it('detects orientation', () => {
    render(<MobileTestComponent />);
    
    expect(screen.getByTestId('orientation')).toHaveTextContent('portrait');
  });

  it('handles orientation changes', () => {
    render(<MobileTestComponent />);
    
    // Mock window dimensions for landscape
    Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true });
    Object.defineProperty(window, 'innerHeight', { value: 768, writable: true });
    
    act(() => {
      fireEvent.resize(window);
    });
    
    expect(screen.getByTestId('orientation')).toHaveTextContent('landscape');
  });

  it('handles orientation change events', () => {
    render(<MobileTestComponent />);
    
    act(() => {
      fireEvent.orientationchange(window);
    });
    
    // Should not throw error
    expect(true).toBe(true);
  });
});

describe('usePWA', () => {
  it('provides PWA state', () => {
    render(<PWATestComponent />);
    
    expect(screen.getByTestId('is-online')).toHaveTextContent('online');
    expect(screen.getByTestId('is-installed')).toHaveTextContent('not-installed');
    expect(screen.getByTestId('has-update')).toHaveTextContent('no-update');
  });

  it('calls PWA methods', () => {
    const { pwaManager } = require('@/lib/pwa');
    
    render(<PWATestComponent />);
    
    fireEvent.click(screen.getByText('Install PWA'));
    fireEvent.click(screen.getByText('Update SW'));
    
    expect(pwaManager.installPWA).toHaveBeenCalled();
    expect(pwaManager.updateServiceWorker).toHaveBeenCalled();
  });
});

describe('useOffline', () => {
  it('detects online status', () => {
    render(<OfflineTestComponent />);
    
    expect(screen.getByTestId('offline-status')).toHaveTextContent('online');
  });

  it('detects offline status', () => {
    Object.defineProperty(navigator, 'onLine', {
      value: false,
      writable: true,
    });
    
    render(<OfflineTestComponent />);
    
    expect(screen.getByTestId('offline-status')).toHaveTextContent('offline');
  });

  it('calls offline manager methods', () => {
    const { offlineManager } = require('@/lib/pwa');
    
    render(<OfflineTestComponent />);
    
    fireEvent.click(screen.getByText('Store Data'));
    fireEvent.click(screen.getByText('Get Data'));
    fireEvent.click(screen.getByText('Sync Data'));
    
    expect(offlineManager.storeOfflineData).toHaveBeenCalledWith('test-key', { data: 'test' });
    expect(offlineManager.getOfflineData).toHaveBeenCalledWith('test-key');
    expect(offlineManager.syncOfflineData).toHaveBeenCalled();
  });

  it('handles online/offline events', () => {
    render(<OfflineTestComponent />);
    
    // Simulate going offline
    act(() => {
      Object.defineProperty(navigator, 'onLine', {
        value: false,
        writable: true,
      });
      fireEvent(window, new Event('offline'));
    });
    
    expect(screen.getByTestId('offline-status')).toHaveTextContent('offline');
    
    // Simulate going online
    act(() => {
      Object.defineProperty(navigator, 'onLine', {
        value: true,
        writable: true,
      });
      fireEvent(window, new Event('online'));
    });
    
    expect(screen.getByTestId('offline-status')).toHaveTextContent('online');
  });
});

describe('Hook Integration', () => {
  it('works together without conflicts', () => {
    const IntegratedTestComponent = () => {
      const { isMobile } = useMobile();
      const { isOnline } = useOffline();
      const { isKeyboardUser } = useAccessibility();
      
      return (
        <div>
          <div data-testid="mobile-status">{isMobile ? 'mobile' : 'desktop'}</div>
          <div data-testid="online-status">{isOnline ? 'online' : 'offline'}</div>
          <div data-testid="keyboard-status">{isKeyboardUser ? 'keyboard' : 'mouse'}</div>
        </div>
      );
    };
    
    render(<IntegratedTestComponent />);
    
    expect(screen.getByTestId('mobile-status')).toHaveTextContent('mobile');
    expect(screen.getByTestId('online-status')).toHaveTextContent('online');
    expect(screen.getByTestId('keyboard-status')).toHaveTextContent('mouse');
  });
});
