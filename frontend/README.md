# Preklo Frontend

The frontend application for Preklo - Universal Payments Made Simple.

## Overview

Preklo is a mobile-first remittance and P2P payment application built on the Aptos blockchain, enabling instant, low-cost cross-border transfers using Circle USDC and native APT tokens.

## Tech Stack

This frontend is built with:

- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful, accessible UI components
- **React Router** - Client-side routing
- **TanStack Query** - Server state management
- **React Hook Form** - Form handling with validation
- **Lucide React** - Beautiful icons

## Features

- **Dashboard** - Overview of balances and recent transactions
- **Send Money** - Transfer USDC/APT to usernames or addresses
- **Receive Money** - Generate payment requests and QR codes
- **Transaction History** - Complete transaction tracking
- **Profile Settings** - User account management
- **Responsive Design** - Mobile-first, works on all devices

## Prerequisites

- Node.js 18+ 
- npm or yarn package manager

## Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Available Scripts

```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Development

The development server runs on `http://localhost:8080` and includes:

- Hot module replacement (HMR)
- TypeScript type checking
- ESLint integration
- Tailwind CSS with JIT compilation

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn/ui components
│   ├── Dashboard.tsx   # Main dashboard
│   ├── Layout.tsx      # App layout wrapper
│   └── ...
├── pages/              # Route components
│   ├── Index.tsx       # Home page
│   └── NotFound.tsx    # 404 page
├── hooks/              # Custom React hooks
├── lib/                # Utility functions
└── App.tsx             # Main app component
```

## API Integration

The frontend integrates with the Preklo backend API:

- **Base URL**: `http://localhost:8000/api/v1`
- **Authentication**: JWT tokens
- **State Management**: TanStack Query for server state
- **Error Handling**: Global error boundaries and toast notifications

## Styling

- **Tailwind CSS** for utility-first styling
- **CSS Variables** for theming
- **Responsive Design** with mobile-first approach
- **Dark Mode** support (via next-themes)

## Contributing

1. Follow the existing code style and patterns
2. Use TypeScript for all new components
3. Add proper error handling
4. Test on multiple screen sizes
5. Update documentation for new features

## Deployment

The frontend can be deployed to any static hosting service:

```bash
# Build for production
npm run build

# The dist/ folder contains the built application
```

For production deployment, ensure:

1. Environment variables are properly configured
2. API endpoints point to production backend
3. HTTPS is enabled
4. Proper caching headers are set

## Environment Variables

Create a `.env.local` file for local development:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Preklo
VITE_APP_VERSION=1.0.0
```

## Troubleshooting

### Common Issues

1. **Build Errors**: Check TypeScript errors and fix type issues
2. **Styling Issues**: Verify Tailwind classes and CSS imports
3. **API Errors**: Check backend is running and CORS is configured
4. **Hot Reload Not Working**: Restart the dev server

### Performance

- Use React.memo() for expensive components
- Implement proper loading states
- Optimize images and assets
- Use code splitting for large routes

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.