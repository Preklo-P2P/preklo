/**
 * Mobile Layout Component Tests
 * Tests mobile-first layout, touch interactions, and responsive behavior
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MobileLayout, TouchButton, TouchInput, MobileCard, MobileList, MobileListItem } from '@/components/MobileLayout';

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
}));

// Mock performance hooks
vi.mock('@/hooks/usePerformance', () => ({
  usePerformance: () => ({
    metrics: { custom: new Map() },
    measurePerformance: vi.fn(),
  }),
  useAccessibility: () => ({
    isKeyboardUser: false,
    focusVisible: false,
    announceToScreenReader: vi.fn(),
  }),
  useMobile: () => ({
    isMobile: true,
    isTouch: true,
    orientation: 'portrait',
  }),
  usePWA: () => ({
    isOnline: true,
    isInstalled: false,
    hasUpdate: false,
    installPWA: vi.fn(),
    updateServiceWorker: vi.fn(),
    skipWaiting: vi.fn(),
    requestNotificationPermission: vi.fn(),
    sendNotification: vi.fn(),
  }),
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('MobileLayout', () => {
  it('renders with default props', () => {
    renderWithRouter(
      <MobileLayout>
        <div>Test content</div>
      </MobileLayout>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
    expect(screen.getByText('Preklo')).toBeInTheDocument();
  });

  it('renders with custom header content', () => {
    renderWithRouter(
      <MobileLayout headerContent={<div>Custom Header</div>}>
        <div>Test content</div>
      </MobileLayout>
    );

    expect(screen.getByText('Custom Header')).toBeInTheDocument();
  });

  it('renders with custom footer content', () => {
    renderWithRouter(
      <MobileLayout footerContent={<div>Custom Footer</div>}>
        <div>Test content</div>
      </MobileLayout>
    );

    expect(screen.getByText('Custom Footer')).toBeInTheDocument();
  });

  it('applies mobile max width constraint', () => {
    renderWithRouter(
      <MobileLayout maxWidth="mobile">
        <div>Test content</div>
      </MobileLayout>
    );

    const main = screen.getByRole('main');
    expect(main).toHaveClass('max-w-mobile');
  });

  it('applies safe area padding when enabled', () => {
    renderWithRouter(
      <MobileLayout safeArea={true}>
        <div>Test content</div>
      </MobileLayout>
    );

    const container = screen.getByText('Test content').closest('.min-h-screen');
    expect(container).toHaveClass('safe-area-padding');
  });

  it('shows PWA update banner when update is available', () => {
    // Mock PWA state with update available
    vi.doMock('@/lib/pwa', () => ({
      pwaManager: {
        getState: () => ({
          isOnline: true,
          isInstalled: false,
          hasUpdate: true,
          registration: null,
        }),
        subscribe: vi.fn(() => vi.fn()),
        skipWaiting: vi.fn(),
      },
    }));

    renderWithRouter(
      <MobileLayout>
        <div>Test content</div>
      </MobileLayout>
    );

    expect(screen.getByText('New version available!')).toBeInTheDocument();
    expect(screen.getByText('Update now')).toBeInTheDocument();
  });

  it('shows offline indicator when offline', () => {
    // Mock offline state
    vi.doMock('@/hooks/usePerformance', () => ({
      usePerformance: () => ({
        metrics: { custom: new Map() },
        measurePerformance: vi.fn(),
      }),
      useAccessibility: () => ({
        isKeyboardUser: false,
        focusVisible: false,
        announceToScreenReader: vi.fn(),
      }),
      useMobile: () => ({
        isMobile: true,
        isTouch: true,
        orientation: 'portrait',
      }),
      usePWA: () => ({
        isOnline: false,
        isInstalled: false,
        hasUpdate: false,
        installPWA: vi.fn(),
        updateServiceWorker: vi.fn(),
        skipWaiting: vi.fn(),
        requestNotificationPermission: vi.fn(),
        sendNotification: vi.fn(),
      }),
    }));

    renderWithRouter(
      <MobileLayout>
        <div>Test content</div>
      </MobileLayout>
    );

    expect(screen.getByText(/You're offline/)).toBeInTheDocument();
  });
});

describe('TouchButton', () => {
  it('renders with default props', () => {
    render(<TouchButton>Click me</TouchButton>);
    
    const button = screen.getByRole('button', { name: 'Click me' });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('touch-target');
  });

  it('renders with primary variant', () => {
    render(<TouchButton variant="primary">Primary Button</TouchButton>);
    
    const button = screen.getByRole('button', { name: 'Primary Button' });
    expect(button).toHaveClass('bg-primary');
  });

  it('renders with secondary variant', () => {
    render(<TouchButton variant="secondary">Secondary Button</TouchButton>);
    
    const button = screen.getByRole('button', { name: 'Secondary Button' });
    expect(button).toHaveClass('bg-secondary');
  });

  it('renders with full width', () => {
    render(<TouchButton fullWidth>Full Width Button</TouchButton>);
    
    const button = screen.getByRole('button', { name: 'Full Width Button' });
    expect(button).toHaveClass('w-full');
  });

  it('shows loading state', () => {
    render(<TouchButton loading>Loading Button</TouchButton>);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<TouchButton onClick={handleClick}>Click me</TouchButton>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<TouchButton disabled>Disabled Button</TouchButton>);
    
    const button = screen.getByRole('button', { name: 'Disabled Button' });
    expect(button).toBeDisabled();
  });
});

describe('TouchInput', () => {
  it('renders with label', () => {
    render(<TouchInput label="Test Label" />);
    
    expect(screen.getByLabelText('Test Label')).toBeInTheDocument();
    expect(screen.getByText('Test Label')).toBeInTheDocument();
  });

  it('renders with error message', () => {
    render(<TouchInput label="Test Input" error="This field is required" />);
    
    expect(screen.getByText('This field is required')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveClass('border-destructive');
  });

  it('renders with helper text', () => {
    render(<TouchInput label="Test Input" helperText="This is helper text" />);
    
    expect(screen.getByText('This is helper text')).toBeInTheDocument();
  });

  it('has touch target class', () => {
    render(<TouchInput label="Test Input" />);
    
    expect(screen.getByRole('textbox')).toHaveClass('touch-target');
  });

  it('handles input changes', () => {
    const handleChange = vi.fn();
    render(<TouchInput label="Test Input" onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test value' } });
    
    expect(handleChange).toHaveBeenCalled();
    expect(input).toHaveValue('test value');
  });
});

describe('MobileCard', () => {
  it('renders with default props', () => {
    render(<MobileCard>Card content</MobileCard>);
    
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders with clickable prop', () => {
    const handleClick = vi.fn();
    render(<MobileCard clickable onClick={handleClick}>Clickable card</MobileCard>);
    
    const card = screen.getByText('Clickable card').closest('div');
    expect(card).toHaveClass('cursor-pointer');
    
    fireEvent.click(card!);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies different padding sizes', () => {
    render(<MobileCard padding="sm">Small padding</MobileCard>);
    expect(screen.getByText('Small padding').closest('div')).toHaveClass('p-3');
    
    render(<MobileCard padding="lg">Large padding</MobileCard>);
    expect(screen.getByText('Large padding').closest('div')).toHaveClass('p-6');
  });
});

describe('MobileList', () => {
  it('renders list items', () => {
    render(
      <MobileList>
        <MobileListItem>Item 1</MobileListItem>
        <MobileListItem>Item 2</MobileListItem>
      </MobileList>
    );
    
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('renders with dividers', () => {
    render(
      <MobileList dividers>
        <MobileListItem>Item 1</MobileListItem>
        <MobileListItem>Item 2</MobileListItem>
      </MobileList>
    );
    
    // Check for divider elements
    const dividers = screen.getByText('Item 1').closest('div')?.querySelectorAll('.border-b');
    expect(dividers).toHaveLength(1); // One divider between two items
  });

  it('renders without dividers', () => {
    render(
      <MobileList dividers={false}>
        <MobileListItem>Item 1</MobileListItem>
        <MobileListItem>Item 2</MobileListItem>
      </MobileList>
    );
    
    const dividers = screen.getByText('Item 1').closest('div')?.querySelectorAll('.border-b');
    expect(dividers).toHaveLength(0);
  });
});

describe('MobileListItem', () => {
  it('renders with clickable prop', () => {
    const handleClick = vi.fn();
    render(<MobileListItem clickable onClick={handleClick}>Clickable item</MobileListItem>);
    
    const item = screen.getByText('Clickable item').closest('div');
    expect(item).toHaveClass('cursor-pointer');
    
    fireEvent.click(item!);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies hover styles when clickable', () => {
    render(<MobileListItem clickable>Clickable item</MobileListItem>);
    
    const item = screen.getByText('Clickable item').closest('div');
    expect(item).toHaveClass('hover:bg-muted');
  });
});

describe('Responsive Behavior', () => {
  it('applies mobile-first classes', () => {
    renderWithRouter(
      <MobileLayout maxWidth="mobile">
        <div>Mobile content</div>
      </MobileLayout>
    );
    
    const main = screen.getByRole('main');
    expect(main).toHaveClass('max-w-mobile');
  });

  it('applies tablet max width', () => {
    renderWithRouter(
      <MobileLayout maxWidth="tablet">
        <div>Tablet content</div>
      </MobileLayout>
    );
    
    const main = screen.getByRole('main');
    expect(main).toHaveClass('max-w-tablet');
  });

  it('applies desktop max width', () => {
    renderWithRouter(
      <MobileLayout maxWidth="desktop">
        <div>Desktop content</div>
      </MobileLayout>
    );
    
    const main = screen.getByRole('main');
    expect(main).toHaveClass('max-w-4xl');
  });
});

describe('Accessibility', () => {
  it('has proper ARIA labels', () => {
    render(<TouchButton aria-label="Custom label">Button</TouchButton>);
    
    expect(screen.getByRole('button', { name: 'Custom label' })).toBeInTheDocument();
  });

  it('supports keyboard navigation', () => {
    render(<TouchButton>Keyboard accessible</TouchButton>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('focus:ring-2');
  });

  it('has proper focus management', () => {
    render(<TouchInput label="Accessible input" />);
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('focus:ring-2');
  });
});
