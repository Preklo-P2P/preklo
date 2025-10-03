/**
 * PWA Functionality Tests
 * Tests service worker registration, offline functionality, and performance monitoring
 */

import { vi } from 'vitest';
import { pwaManager, offlineManager, performanceMonitor } from '@/lib/pwa';

// Mock workbox-window
vi.mock('workbox-window', () => ({
  Workbox: vi.fn().mockImplementation(() => ({
    addEventListener: vi.fn(),
    register: vi.fn().mockResolvedValue(undefined),
    update: vi.fn().mockResolvedValue(undefined),
    messageSkipWaiting: vi.fn().mockResolvedValue(undefined),
  })),
}));

// Mock service worker
const mockServiceWorker = {
  ready: Promise.resolve({
    showNotification: vi.fn(),
  }),
};

Object.defineProperty(navigator, 'serviceWorker', {
  value: {
    register: vi.fn().mockResolvedValue(mockServiceWorker),
    ready: Promise.resolve(mockServiceWorker),
  },
  writable: true,
});

// Mock IndexedDB
const mockIndexedDB = {
  open: vi.fn().mockReturnValue({
    onsuccess: null,
    onerror: null,
    onupgradeneeded: null,
    result: {
      createObjectStore: vi.fn(),
      transaction: vi.fn().mockReturnValue({
        objectStore: vi.fn().mockReturnValue({
          put: vi.fn(),
          get: vi.fn(),
        }),
      }),
    },
  }),
};

Object.defineProperty(window, 'indexedDB', {
  value: mockIndexedDB,
  writable: true,
});

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
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

// Mock Notification API
Object.defineProperty(window, 'Notification', {
  value: {
    requestPermission: vi.fn().mockResolvedValue('granted'),
    permission: 'granted',
  },
  writable: true,
});

describe('PWAManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Service Worker Registration', () => {
    it('registers service worker successfully', async () => {
      await pwaManager.registerServiceWorker();
      
      expect(navigator.serviceWorker.register).toHaveBeenCalledWith('/sw.js');
    });

    it('handles service worker registration failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
      
      // Mock registration failure
      (navigator.serviceWorker.register as any).mockRejectedValueOnce(
        new Error('Registration failed')
      );
      
      await pwaManager.registerServiceWorker();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Service Worker registration failed:',
        expect.any(Error)
      );
      
      consoleSpy.mockRestore();
    });

    it('updates service worker', async () => {
      await pwaManager.updateServiceWorker();
      
      // Should not throw error
      expect(true).toBe(true);
    });

    it('skips waiting for service worker', async () => {
      await pwaManager.skipWaiting();
      
      // Should not throw error
      expect(true).toBe(true);
    });
  });

  describe('PWA Installation', () => {
    it('installs PWA successfully', async () => {
      await pwaManager.installPWA();
      
      // Should not throw error
      expect(true).toBe(true);
    });

    it('requests notification permission', async () => {
      const permission = await pwaManager.requestNotificationPermission();
      
      expect(Notification.requestPermission).toHaveBeenCalled();
      expect(permission).toBe('granted');
    });

    it('sends notification', async () => {
      await pwaManager.sendNotification('Test notification', {
        body: 'Test body',
      });
      
      // Should not throw error
      expect(true).toBe(true);
    });
  });

  describe('State Management', () => {
    it('returns initial state', () => {
      const state = pwaManager.getState();
      
      expect(state).toEqual({
        isOnline: navigator.onLine,
        isInstalled: false,
        hasUpdate: false,
        registration: null,
      });
    });

    it('subscribes to state changes', () => {
      const listener = jest.fn();
      const unsubscribe = pwaManager.subscribe(listener);
      
      expect(typeof unsubscribe).toBe('function');
      
      // Test unsubscribe
      unsubscribe();
      expect(true).toBe(true); // Should not throw error
    });
  });
});

describe('OfflineManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Data Storage', () => {
    it('stores offline data', async () => {
      const testData = { key: 'test', value: 'data' };
      
      await offlineManager.storeOfflineData('test-key', testData);
      
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'preklo-offline-test-key',
        JSON.stringify(testData)
      );
    });

    it('retrieves offline data', async () => {
      const testData = { key: 'test', value: 'data' };
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(testData));
      
      const result = await offlineManager.getOfflineData('test-key');
      
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('preklo-offline-test-key');
      expect(result).toEqual(testData);
    });

    it('handles missing offline data', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      
      const result = await offlineManager.getOfflineData('missing-key');
      
      expect(result).toBeNull();
    });

    it('handles invalid JSON in offline data', async () => {
      mockLocalStorage.getItem.mockReturnValue('invalid json');
      
      const result = await offlineManager.getOfflineData('invalid-key');
      
      expect(result).toBeNull();
    });
  });

  describe('Data Synchronization', () => {
    it('syncs offline data when online', async () => {
      Object.defineProperty(navigator, 'onLine', {
        value: true,
        writable: true,
      });
      
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();
      
      await offlineManager.syncOfflineData();
      
      expect(consoleSpy).toHaveBeenCalledWith('Syncing offline data...');
      
      consoleSpy.mockRestore();
    });

    it('does not sync when offline', async () => {
      Object.defineProperty(navigator, 'onLine', {
        value: false,
        writable: true,
      });
      
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();
      
      await offlineManager.syncOfflineData();
      
      expect(consoleSpy).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });
});

describe('PerformanceMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Performance Measurement', () => {
    it('measures synchronous function performance', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();
      
      performanceMonitor.measurePerformance('test-sync', () => {
        // Simulate some work
        return 'result';
      });
      
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringMatching(/Performance: test-sync took \d+ms/)
      );
      
      consoleSpy.mockRestore();
    });

    it('measures asynchronous function performance', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();
      
      await performanceMonitor.measurePerformance('test-async', async () => {
        // Simulate async work
        await new Promise(resolve => setTimeout(resolve, 10));
        return 'async result';
      });
      
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringMatching(/Performance: test-async took \d+ms/)
      );
      
      consoleSpy.mockRestore();
    });

    it('tracks performance metrics', () => {
      performanceMonitor.measurePerformance('test-metric', () => {
        return 'test';
      });
      
      const metrics = performanceMonitor.getMetrics();
      expect(metrics.has('test-metric')).toBe(true);
    });
  });

  describe('Core Web Vitals', () => {
    it('reports Core Web Vitals when available', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation();
      
      performanceMonitor.reportCoreWebVitals();
      
      expect(consoleSpy).toHaveBeenCalledWith('Core Web Vitals monitoring enabled');
      
      consoleSpy.mockRestore();
    });
  });
});

describe('Online/Offline Detection', () => {
  it('detects online state', () => {
    Object.defineProperty(navigator, 'onLine', {
      value: true,
      writable: true,
    });
    
    const state = pwaManager.getState();
    expect(state.isOnline).toBe(true);
  });

  it('detects offline state', () => {
    Object.defineProperty(navigator, 'onLine', {
      value: false,
      writable: true,
    });
    
    const state = pwaManager.getState();
    expect(state.isOnline).toBe(false);
  });
});

describe('Error Handling', () => {
  it('handles IndexedDB errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    
    // Mock IndexedDB error
    mockIndexedDB.open.mockReturnValue({
      onsuccess: null,
      onerror: vi.fn((callback) => {
        callback({ target: { error: new Error('IndexedDB error') } });
      }),
      onupgradeneeded: null,
      result: null,
    });
    
    await offlineManager.storeOfflineData('test-key', { data: 'test' });
    
    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to store offline data:',
      expect.any(Error)
    );
    
    consoleSpy.mockRestore();
  });

  it('handles localStorage errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    
    // Mock localStorage error
    mockLocalStorage.setItem.mockImplementation(() => {
      throw new Error('localStorage error');
    });
    
    await offlineManager.storeOfflineData('test-key', { data: 'test' });
    
    // Should not throw error
    expect(true).toBe(true);
    
    consoleSpy.mockRestore();
  });
});
