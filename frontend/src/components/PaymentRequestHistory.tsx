import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Clock, 
  CheckCircle, 
  X, 
  Copy, 
  Share2, 
  MoreVertical, 
  Filter,
  Search,
  Calendar,
  DollarSign,
  User,
  AlertCircle
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface PaymentRequest {
  id: string;
  amount: number;
  currency: "USDC" | "APT";
  description: string;
  recipient?: string;
  sender?: string;
  status: "pending" | "paid" | "expired" | "cancelled";
  createdAt: Date;
  expiresAt?: Date;
  paidAt?: Date;
  paidBy?: string;
  type: "sent" | "received";
}

interface PaymentRequestHistoryProps {
  requests: PaymentRequest[];
  onCancelRequest?: (requestId: string) => void;
  onPayRequest?: (requestId: string) => void;
  onCopyLink?: (requestId: string) => void;
  onShareRequest?: (requestId: string) => void;
}

export function PaymentRequestHistory({ 
  requests, 
  onCancelRequest, 
  onPayRequest, 
  onCopyLink, 
  onShareRequest 
}: PaymentRequestHistoryProps) {
  const [filteredRequests, setFilteredRequests] = useState<PaymentRequest[]>(requests);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    let filtered = requests;

    // Filter by status
    if (activeFilter !== "all") {
      filtered = filtered.filter(request => request.status === activeFilter);
    }

    // Filter by type
    if (activeFilter === "sent") {
      filtered = filtered.filter(request => request.type === "sent");
    } else if (activeFilter === "received") {
      filtered = filtered.filter(request => request.type === "received");
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(request => 
        request.description.toLowerCase().includes(query) ||
        (request.recipient && request.recipient.toLowerCase().includes(query)) ||
        (request.sender && request.sender.toLowerCase().includes(query)) ||
        request.amount.toString().includes(query)
      );
    }

    setFilteredRequests(filtered);
  }, [requests, activeFilter, searchQuery]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
      case "paid":
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Paid</Badge>;
      case "expired":
        return <Badge variant="destructive" className="bg-red-100 text-red-800"><X className="h-3 w-3 mr-1" />Expired</Badge>;
      case "cancelled":
        return <Badge variant="outline" className="bg-gray-100 text-gray-800"><X className="h-3 w-3 mr-1" />Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return "Just now";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return date.toLocaleDateString();
  };

  const handleCopyLink = async (request: PaymentRequest) => {
    try {
      const link = `https://preklo.app/pay/${request.id}`;
      await navigator.clipboard.writeText(link);
      toast({
        title: "Link Copied",
        description: "Payment request link copied to clipboard",
      });
      onCopyLink?.(request.id);
    } catch (error) {
      toast({
        title: "Copy Failed",
        description: "Failed to copy link to clipboard",
        variant: "destructive",
      });
    }
  };

  const handleShare = async (request: PaymentRequest) => {
    const link = `https://preklo.app/pay/${request.id}`;
    const text = `Pay me $${request.amount} ${request.currency}${request.description ? ` for ${request.description}` : ''} via Preklo: ${link}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: "Payment Request",
          text: text,
          url: link,
        });
        onShareRequest?.(request.id);
      } catch (error) {
        // User cancelled sharing
      }
    } else {
      // Fallback to copying
      await handleCopyLink(request);
    }
  };

  const filters = [
    { id: "all", label: "All", count: requests.length },
    { id: "sent", label: "Sent", count: requests.filter(r => r.type === "sent").length },
    { id: "received", label: "Received", count: requests.filter(r => r.type === "received").length },
    { id: "pending", label: "Pending", count: requests.filter(r => r.status === "pending").length },
    { id: "paid", label: "Paid", count: requests.filter(r => r.status === "paid").length },
    { id: "expired", label: "Expired", count: requests.filter(r => r.status === "expired").length },
  ];

  return (
    <div className="space-y-4">
      {/* Header with Search and Filters */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Payment Requests</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="text-primary"
          >
            <Filter className="h-4 w-4 mr-2" />
            {showFilters ? "Hide" : "Show"} Filters
          </Button>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search requests..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        {/* Filter Tabs */}
        {showFilters && (
          <div className="flex flex-wrap gap-2">
            {filters.map((filter) => (
              <Button
                key={filter.id}
                variant={activeFilter === filter.id ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveFilter(filter.id)}
                className="text-xs"
              >
                {filter.label}
                {filter.count > 0 && (
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {filter.count}
                  </Badge>
                )}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Payment Requests List */}
      <div className="space-y-3">
        {filteredRequests.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-8 text-center">
              <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">No Payment Requests</h3>
              <p className="text-muted-foreground">
                {searchQuery || activeFilter !== "all" 
                  ? "No requests match your current filters"
                  : "You haven't created or received any payment requests yet"
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredRequests.map((request) => (
            <Card key={request.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-2">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg font-semibold text-foreground">
                          ${request.amount} {request.currency}
                        </span>
                        {getStatusBadge(request.status)}
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {formatTimeAgo(request.createdAt)}
                      </span>
                    </div>

                    {/* Description */}
                    {request.description && (
                      <p className="text-sm text-foreground">{request.description}</p>
                    )}

                    {/* Details */}
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        <span>
                          {request.type === "sent" ? "To" : "From"}: {request.type === "sent" ? request.recipient : request.sender}
                        </span>
                      </div>
                      {request.expiresAt && (
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span>Expires: {request.expiresAt.toLocaleDateString()}</span>
                        </div>
                      )}
                      {request.paidAt && (
                        <div className="flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" />
                          <span>Paid: {request.paidAt.toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    {request.status === "pending" && request.type === "sent" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onCancelRequest?.(request.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <X className="h-3 w-3 mr-1" />
                        Cancel
                      </Button>
                    )}
                    
                    {request.status === "pending" && request.type === "received" && (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => onPayRequest?.(request.id)}
                      >
                        <DollarSign className="h-3 w-3 mr-1" />
                        Pay
                      </Button>
                    )}

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopyLink(request)}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleShare(request)}
                    >
                      <Share2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
