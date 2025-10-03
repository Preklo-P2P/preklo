import { useState, useEffect } from "react";
import { History, Plus } from "lucide-react";
import { BalanceDisplay } from "@/components/ui/BalanceDisplay";
import { TransactionCard } from "@/components/ui/TransactionCard";
import { ActionButton } from "@/components/ui/ActionButton";
import { SearchBar } from "@/components/SearchBar";
import { DashboardHeader } from "@/components/DashboardHeader";
import { QuickActions } from "@/components/QuickActions";
import { useToast } from "@/hooks/use-toast";
import { userService, User, Balance } from "@/services/userService";
import { authService } from "@/services/authService";
import { notificationService } from "@/services/notificationService";

// User data interface for dashboard
interface DashboardUser {
  id: string;
  username: string;
  email: string;
  balance: { usdc: number; apt: number };
}

// Transaction interface for dashboard
interface Transaction {
  id: string;
  type: 'sent' | 'received' | 'request';
  amount: number;
  currency: 'USDC' | 'APT';
  recipient_username?: string;
  sender_username?: string;
  description?: string;
  status: 'pending' | 'confirmed' | 'failed' | 'cancelled';
  timestamp: string;
  blockchain_hash?: string;
}

interface DashboardProps {
  onNavigate: (page: string) => void;
  currentPage?: string;
}

export function Dashboard({ onNavigate, currentPage }: DashboardProps) {
  const [isBalanceLoading, setIsBalanceLoading] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [user, setUser] = useState<DashboardUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);
  const { toast } = useToast();

  // Map backend transaction data to frontend format
  const mapBackendTransaction = (backendTx: any): Transaction => {
    const currentUserId = localStorage.getItem('preklo_user_id');
    const isSent = backendTx.sender_id === currentUserId;
    const isReceived = backendTx.recipient_id === currentUserId;
    
    return {
      id: backendTx.id,
      type: isSent ? "sent" : isReceived ? "received" : "request",
      amount: parseFloat(backendTx.amount),
      currency: backendTx.currency_type as "USDC" | "APT",
      sender_username: backendTx.sender?.username,
      recipient_username: backendTx.recipient?.username,
      description: backendTx.description || `${isSent ? 'Sent to' : 'Received from'} ${isSent ? backendTx.recipient?.username : backendTx.sender?.username}`,
      status: backendTx.status as "pending" | "confirmed" | "failed" | "cancelled",
      timestamp: backendTx.created_at,
      blockchain_hash: backendTx.transaction_hash,
    };
  };

  // Load recent transactions
  const loadRecentTransactions = async () => {
    try {
      setIsLoadingTransactions(true);
      const transactionsData = await userService.getTransactions(5, 0); // Get only 5 recent transactions
      const mappedTransactions = transactionsData.map(mapBackendTransaction);
      setTransactions(mappedTransactions);
    } catch (error) {
      console.error('Failed to load recent transactions:', error);
      // Don't show error toast for dashboard - it's not critical
    } finally {
      setIsLoadingTransactions(false);
    }
  };

  // Load user data from API
  useEffect(() => {
    const loadUserData = async () => {
      try {
        setIsLoading(true);
        
        // Check if user is authenticated
        if (!authService.isAuthenticated()) {
          // Fallback to localStorage for demo
          const storedData = authService.getStoredUserData();
          if (storedData) {
            setUser({
              id: storedData.id || "1",
              username: storedData.username || "",
              email: storedData.email || "",
              balance: { usdc: 0, apt: 0 } // Will be loaded separately
            });
          }
          return;
        }

        // Load user data from API
        const [userData, balanceData] = await Promise.all([
          userService.getCurrentUser(),
          userService.getBalance().catch((error) => {
            console.error('Balance loading failed:', error);
            return []; // Fallback to empty array if balance fails
          })
        ]);

        // Convert balance data to the format expected by DashboardUser
        const usdcBalance = balanceData.find(b => b.currency === 'USDC')?.balance || 0;
        const aptBalance = balanceData.find(b => b.currency === 'APT')?.balance || 0;

        setUser({
          id: userData.id,
          username: userData.username.startsWith('@') ? userData.username : `@${userData.username}`,
          email: userData.email,
          balance: { usdc: usdcBalance, apt: aptBalance }
        });

      } catch (error) {
        console.error('Error loading user data:', error);
        
        // Fallback to localStorage data
        const storedData = authService.getStoredUserData();
        if (storedData) {
          setUser({
            id: storedData.id || "1",
            username: storedData.username || "",
            email: storedData.email || "",
            balance: { usdc: 0, apt: 0 }
          });
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadUserData();
  }, []);

  // Load recent transactions when component mounts
  useEffect(() => {
    loadRecentTransactions();
  }, []);

  // Load notification count
  const loadNotificationCount = async () => {
    try {
      const count = await notificationService.getUnreadCount();
      setNotificationCount(count);
    } catch (error) {
      console.error('Failed to load notification count:', error);
      // Don't show error toast for notification count - it's not critical
    }
  };

  // Load notification count when component mounts
  useEffect(() => {
    loadNotificationCount();
  }, []);

  // Refresh notification count when returning to dashboard
  useEffect(() => {
    if (currentPage === "dashboard") {
      loadNotificationCount();
    }
  }, [currentPage]);

  const handleRefreshBalance = async () => {
    setIsBalanceLoading(true);
    try {
      // Refresh balance, transactions, and notification count
      await Promise.all([
        userService.getBalance().then(balanceData => {
          const usdcBalance = balanceData.find(b => b.currency === 'USDC')?.balance || 0;
          const aptBalance = balanceData.find(b => b.currency === 'APT')?.balance || 0;
          setUser(prev => prev ? { ...prev, balance: { usdc: usdcBalance, apt: aptBalance } } : null);
        }),
        loadRecentTransactions(),
        loadNotificationCount()
      ]);
      
      toast({
        title: "Data Updated",
        description: "Your balance and recent activity have been refreshed.",
      });
    } catch (error) {
      console.error('Failed to refresh data:', error);
      toast({
        title: "Refresh Failed",
        description: "Failed to refresh data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsBalanceLoading(false);
    }
  };




  // Show loading if user data is not loaded yet
  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <DashboardHeader
        username={user.username}
        notificationCount={notificationCount}
        onSearchToggle={() => setShowSearch(!showSearch)}
        onNotificationsClick={() => onNavigate("notifications")}
      />

      {/* Search Bar */}
      <SearchBar
        isOpen={showSearch}
        onClose={() => setShowSearch(false)}
        onNavigate={onNavigate}
      />

      {/* Main Content */}
      <main className="px-4 py-6 space-y-6">
        {/* Balance Card */}
        <section>
          <BalanceDisplay
            usdcBalance={user.balance.usdc}
            aptBalance={user.balance.apt}
            isLoading={isBalanceLoading}
          />
          <button
            onClick={handleRefreshBalance}
            className="mt-3 text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
            disabled={isBalanceLoading}
          >
            {isBalanceLoading ? "Refreshing..." : "Pull to refresh"}
          </button>
        </section>

        {/* Quick Actions */}
        <QuickActions onNavigate={onNavigate} />


        {/* Recent Transactions */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">Recent Activity</h2>
            <button
              onClick={() => onNavigate("history")}
              className="text-sm text-primary hover:text-primary-dark transition-colors duration-200 font-medium"
            >
              View All
            </button>
          </div>
          
          <div className="space-y-3">
            {isLoadingTransactions ? (
              <div className="text-center py-8">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground">Loading recent activity...</p>
              </div>
            ) : transactions.length > 0 ? (
              transactions.map((transaction) => (
                <TransactionCard
                  key={transaction.id}
                  transaction={transaction}
                  onClick={(tx) => onNavigate("history")}
                />
              ))
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                  <History className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">No transactions yet</h3>
                <p className="text-muted-foreground mb-6">Start by sending or requesting money</p>
                <ActionButton
                  onClick={() => onNavigate("send")}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Send Money
                </ActionButton>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}