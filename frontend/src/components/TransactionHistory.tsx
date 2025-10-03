import { useState, useEffect } from "react";
import { ArrowLeft, Search, Filter, Download, Calendar, ArrowUpRight, ArrowDownLeft, X, Eye, Share2, Copy, ChevronDown, ChevronUp, RefreshCw, FileText, FileSpreadsheet } from "lucide-react";
import { TransactionCard } from "@/components/ui/TransactionCard";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TransactionDetailsModal } from "@/components/TransactionDetailsModal";
import { TransactionFilters } from "@/components/TransactionFilters";
import { useToast } from "@/hooks/use-toast";
import { userService } from "@/services/userService";

interface TransactionHistoryProps {
  onNavigate: (page: string) => void;
  onGoBack?: () => void;
}

// Enhanced transaction data structure
interface Transaction {
  id: string;
  type: "sent" | "received" | "request";
  amount: number;
  currency: "USDC" | "APT";
  sender_username?: string;
  recipient_username?: string;
  description: string;
  status: "pending" | "confirmed" | "failed" | "cancelled";
  timestamp: string;
  blockchain_hash?: string;
  fee?: number;
  notes?: string;
  tags?: string[];
  isNew?: boolean;
}

// Transactions are now loaded from the backend API

type FilterType = "all" | "sent" | "received" | "request" | "pending" | "confirmed" | "failed";

interface DateRange {
  start: Date | null;
  end: Date | null;
}

interface AmountRange {
  min: number | null;
  max: number | null;
}

export function TransactionHistory({ onNavigate, onGoBack }: TransactionHistoryProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");
  const [showFilters, setShowFilters] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [showTransactionDetails, setShowTransactionDetails] = useState(false);
  const [dateRange, setDateRange] = useState<DateRange>({ start: null, end: null });
  const [amountRange, setAmountRange] = useState<AmountRange>({ min: null, max: null });
  const [isExporting, setIsExporting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [user, setUser] = useState<{ username: string; email: string } | null>(null);
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
      fee: backendTx.gas_fee ? parseFloat(backendTx.gas_fee) : undefined,
      isNew: false
    };
  };

  // Load user data and transactions from backend
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        
        // Load user data from backend
        const userData = await userService.getCurrentUser();
        setUser({
          username: userData.username,
          email: userData.email
        });
        
        // Load transactions from backend
        const transactionsData = await userService.getTransactions(50, 0);
        const mappedTransactions = transactionsData.map(mapBackendTransaction);
        setTransactions(mappedTransactions);
        
      } catch (error) {
        console.error('Failed to load transaction history:', error);
        toast({
          title: "Error",
          description: "Failed to load transaction history",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [toast]);

  const filters = [
    { key: "all" as const, label: "All", count: transactions.length },
    { key: "sent" as const, label: "Sent", count: transactions.filter(t => t.type === "sent").length },
    { key: "received" as const, label: "Received", count: transactions.filter(t => t.type === "received").length },
    { key: "request" as const, label: "Requests", count: transactions.filter(t => t.type === "request").length },
    { key: "pending" as const, label: "Pending", count: transactions.filter(t => t.status === "pending").length },
    { key: "confirmed" as const, label: "Confirmed", count: transactions.filter(t => t.status === "confirmed").length },
    { key: "failed" as const, label: "Failed", count: transactions.filter(t => t.status === "failed").length },
  ];


  const filterTransaction = (transaction: Transaction): boolean => {
    // Filter by type/status
    if (activeFilter === "sent" && transaction.type !== "sent") return false;
    if (activeFilter === "received" && transaction.type !== "received") return false;
    if (activeFilter === "request" && transaction.type !== "request") return false;
    if (activeFilter === "pending" && transaction.status !== "pending") return false;
    if (activeFilter === "confirmed" && transaction.status !== "confirmed") return false;
    if (activeFilter === "failed" && transaction.status !== "failed") return false;

    // Filter by date range
    if (dateRange.start || dateRange.end) {
      const transactionDate = new Date(transaction.timestamp);
      if (dateRange.start && transactionDate < dateRange.start) return false;
      if (dateRange.end && transactionDate > dateRange.end) return false;
    }

    // Filter by amount range
    if (amountRange.min !== null && transaction.amount < amountRange.min) return false;
    if (amountRange.max !== null && transaction.amount > amountRange.max) return false;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const otherUser = transaction.type === "sent" ? transaction.recipient_username : transaction.sender_username;
      const searchableText = [
        otherUser,
        transaction.description,
        transaction.amount.toString(),
        transaction.currency,
        transaction.notes,
        ...(transaction.tags || [])
      ].filter(Boolean).join(" ").toLowerCase();
      
      return searchableText.includes(query);
    }

    return true;
  };

  const filteredTransactions = transactions.filter(filterTransaction);

  // Pagination
  const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedTransactions = filteredTransactions.slice(startIndex, endIndex);

  const handleTransactionClick = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setShowTransactionDetails(true);
  };

  const handleExport = async (format: "csv" | "pdf") => {
    setIsExporting(true);
    
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: "Export completed",
        description: `Transaction data exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      toast({
        title: "Export failed",
        description: "Failed to export transaction data",
        variant: "destructive",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    
    try {
      // Load fresh transactions from backend
      const transactionsData = await userService.getTransactions(50, 0);
      const mappedTransactions = transactionsData.map(mapBackendTransaction);
      setTransactions(mappedTransactions);
      
      toast({
        title: "Transactions refreshed",
        description: "Latest transaction data loaded",
      });
    } catch (error) {
      console.error('Failed to refresh transactions:', error);
      toast({
        title: "Refresh failed",
        description: "Failed to refresh transaction data",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleShareTransaction = (transaction: Transaction) => {
    const shareText = `Transaction: ${transaction.description} - $${transaction.amount} ${transaction.currency}`;
    
    if (navigator.share) {
      navigator.share({
        title: "Transaction Details",
        text: shareText,
      });
    } else {
      navigator.clipboard.writeText(shareText);
      toast({
        title: "Transaction details copied",
        description: "Transaction details copied to clipboard",
      });
    }
  };

  const handleCopyTransactionId = (transaction: Transaction) => {
    const id = transaction.blockchain_hash || transaction.id;
    navigator.clipboard.writeText(id);
    toast({
      title: "Transaction ID copied",
      description: "Transaction ID copied to clipboard",
    });
  };

  const clearFilters = () => {
    setSearchQuery("");
    setActiveFilter("all");
    setDateRange({ start: null, end: null });
    setAmountRange({ min: null, max: null });
    setCurrentPage(1);
  };

  const getTotalAmount = () => {
    const sent = transactions
      .filter(t => t.type === "sent" && t.status === "confirmed")
      .reduce((sum, t) => sum + t.amount, 0);
    
    const received = transactions
      .filter(t => t.type === "received" && t.status === "confirmed")
      .reduce((sum, t) => sum + t.amount, 0);

    return { sent, received, net: received - sent };
  };

  const totals = getTotalAmount();

  // Auto-refresh effect - refresh every 5 minutes to get latest transactions
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const transactionsData = await userService.getTransactions(50, 0);
        const mappedTransactions = transactionsData.map(mapBackendTransaction);
        setTransactions(mappedTransactions);
      } catch (error) {
        console.error('Auto-refresh failed:', error);
      }
    }, 300000); // Check every 5 minutes

    return () => clearInterval(interval);
  }, []);

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
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onGoBack || (() => onNavigate("dashboard"))}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-foreground">Transaction History</h1>
            <p className="text-sm text-muted-foreground">
              {user.username} • {filteredTransactions.length} transaction{filteredTransactions.length !== 1 ? 's' : ''}
              {transactions.filter(t => t.isNew).length > 0 && (
                <span className="ml-2 text-primary font-medium">
                  • {transactions.filter(t => t.isNew).length} new
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center disabled:opacity-50"
              aria-label="Refresh transactions"
            >
              <RefreshCw className={`h-5 w-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
            <div className="relative">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Show filters"
              >
                <Filter className="h-5 w-5" />
              </button>
              {(dateRange.start || dateRange.end || amountRange.min !== null || amountRange.max !== null) && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full"></div>
              )}
            </div>
            <div className="relative">
              <button
                disabled={isExporting}
                className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center disabled:opacity-50"
                aria-label="Export transactions"
              >
                <Download className="h-5 w-5" />
              </button>
              {isExporting && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Summary Cards */}
      <div className="px-4 py-4">
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-card border border-border rounded-xl p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <ArrowUpRight className="h-4 w-4 text-primary mr-1" />
              <span className="text-xs font-medium text-muted-foreground">SENT</span>
            </div>
            <p className="text-lg font-bold text-foreground">${totals.sent.toFixed(2)}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <ArrowDownLeft className="h-4 w-4 text-success mr-1" />
              <span className="text-xs font-medium text-muted-foreground">RECEIVED</span>
            </div>
            <p className="text-lg font-bold text-success">${totals.received.toFixed(2)}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <Calendar className="h-4 w-4 text-muted-foreground mr-1" />
              <span className="text-xs font-medium text-muted-foreground">NET</span>
            </div>
            <p className={`text-lg font-bold ${totals.net >= 0 ? 'text-success' : 'text-destructive'}`}>
              {totals.net >= 0 ? '+' : ''}${totals.net.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Advanced Filters */}
      <TransactionFilters
        isOpen={showFilters}
        dateRange={dateRange}
        amountRange={amountRange}
        onDateRangeChange={setDateRange}
        onAmountRangeChange={setAmountRange}
        onClearFilters={clearFilters}
      />

      {/* Search and Filters */}
      <div className="px-4 pb-4 space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search transactions, usernames, descriptions..."
            className="w-full p-4 pl-10 border border-border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full hover:bg-muted transition-colors duration-200"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          )}
        </div>

        {/* Filter Buttons */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {filters.map((filter) => (
            <button
              key={filter.key}
              onClick={() => setActiveFilter(filter.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 whitespace-nowrap min-h-[44px] ${
                activeFilter === filter.key
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              }`}
            >
              {filter.label}
              <span className={`px-2 py-0.5 rounded-full text-xs ${
                activeFilter === filter.key
                  ? "bg-primary-foreground/20 text-primary-foreground"
                  : "bg-background text-muted-foreground"
              }`}>
                {filter.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Transaction List */}
      <main className="px-4 space-y-3">
        {paginatedTransactions.length > 0 ? (
          <>
            {paginatedTransactions.map((transaction) => (
                <div key={transaction.id} className="relative">
                  {transaction.isNew && (
                    <div className="absolute -left-2 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-primary rounded-full z-10"></div>
                  )}
                  <TransactionCard
                    transaction={transaction}
                    onClick={handleTransactionClick}
                  />
                </div>
            ))}
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 py-6">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronUp className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground px-4">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">No transactions found</h3>
            <p className="text-muted-foreground mb-6">
              {searchQuery ? "Try adjusting your search terms" : "No transactions match the selected filter"}
            </p>
            {(searchQuery || activeFilter !== "all" || dateRange.start || dateRange.end || amountRange.min !== null || amountRange.max !== null) && (
              <ActionButton
                onClick={clearFilters}
                variant="ghost"
              >
                Clear Filters
              </ActionButton>
            )}
          </div>
        )}
      </main>

      {/* Transaction Details Modal */}
      <TransactionDetailsModal
        transaction={selectedTransaction}
        isOpen={showTransactionDetails}
        onClose={() => setShowTransactionDetails(false)}
        onShare={handleShareTransaction}
        onCopyId={handleCopyTransactionId}
      />
    </div>
  );
}