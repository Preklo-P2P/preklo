import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Gift, 
  Search, 
  Filter, 
  Copy, 
  Share2, 
  Eye, 
  X,
  Clock,
  CheckCircle,
  AlertCircle,
  User,
  DollarSign,
  Shield,
  MapPin
} from "lucide-react";

interface Voucher {
  id: string;
  voucher_code: string;
  amount: number;
  currency: string;
  status: "active" | "redeemed" | "expired" | "cancelled";
  has_pin: boolean;
  expires_at: Date;
  redeemed_at?: Date;
  creator_username?: string;
  redeemer_username?: string;
  time_remaining?: string;
  created_at: Date;
}

export function VoucherHistory() {
  const [vouchers, setVouchers] = useState<Voucher[]>([]);
  const [filteredVouchers, setFilteredVouchers] = useState<Voucher[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedVoucher, setSelectedVoucher] = useState<Voucher | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  // Mock data
  useEffect(() => {
    const mockVouchers: Voucher[] = [
      {
        id: "voucher-1",
        voucher_code: "ABC123DEF456GHI789",
        amount: 100,
        currency: "USDC",
        status: "active",
        has_pin: true,
        expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000),
        creator_username: "sarah_wilson",
        time_remaining: "23h 45m",
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000)
      },
      {
        id: "voucher-2",
        voucher_code: "XYZ789GHI123JKL456",
        amount: 250,
        currency: "USDC",
        status: "redeemed",
        has_pin: false,
        expires_at: new Date(Date.now() - 12 * 60 * 60 * 1000),
        redeemed_at: new Date(Date.now() - 6 * 60 * 60 * 1000),
        redeemer_username: "john_doe",
        created_at: new Date(Date.now() - 18 * 60 * 60 * 1000)
      },
      {
        id: "voucher-3",
        voucher_code: "MNO456PQR789STU012",
        amount: 50,
        currency: "USDC",
        status: "expired",
        has_pin: true,
        expires_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
        created_at: new Date(Date.now() - 26 * 60 * 60 * 1000)
      },
      {
        id: "voucher-4",
        voucher_code: "VWX345YZA678BCD901",
        amount: 500,
        currency: "USDC",
        status: "cancelled",
        has_pin: false,
        expires_at: new Date(Date.now() + 48 * 60 * 60 * 1000),
        created_at: new Date(Date.now() - 4 * 60 * 60 * 1000)
      }
    ];
    setVouchers(mockVouchers);
    setFilteredVouchers(mockVouchers);
  }, []);

  // Filter vouchers
  useEffect(() => {
    let filtered = vouchers;

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(voucher =>
        voucher.voucher_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        voucher.creator_username?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        voucher.redeemer_username?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter(voucher => voucher.status === statusFilter);
    }

    setFilteredVouchers(filtered);
  }, [vouchers, searchQuery, statusFilter]);

  const getStatusBadge = (status: string) => {
    const variants = {
      active: "default",
      redeemed: "default",
      expired: "secondary",
      cancelled: "destructive"
    } as const;

    const colors = {
      active: "bg-green-100 text-green-800",
      redeemed: "bg-blue-100 text-blue-800",
      expired: "bg-gray-100 text-gray-800",
      cancelled: "bg-red-100 text-red-800"
    };

    return (
      <Badge variant={variants[status as keyof typeof variants]} className={colors[status as keyof typeof colors]}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  };

  const handleVoucherClick = (voucher: Voucher) => {
    setSelectedVoucher(voucher);
    setShowDetails(true);
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
  };

  const handleShareVoucher = (voucher: Voucher) => {
    const shareData = {
      title: "Preklo Voucher",
      text: `Voucher: ${voucher.voucher_code} - $${voucher.amount} ${voucher.currency}`,
      url: window.location.origin
    };

    if (navigator.share) {
      navigator.share(shareData);
    } else {
      navigator.clipboard.writeText(shareData.text);
    }
  };

  const clearFilters = () => {
    setSearchQuery("");
    setStatusFilter("all");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {filteredVouchers.length} voucher{filteredVouchers.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search vouchers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="redeemed">Redeemed</SelectItem>
                  <SelectItem value="expired">Expired</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              {(searchQuery || statusFilter !== "all") && (
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Voucher List */}
      <div className="space-y-4">
        {filteredVouchers.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Gift className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No vouchers found</h3>
                <p className="text-muted-foreground">
                  {searchQuery || statusFilter !== "all" 
                    ? "Try adjusting your search or filters"
                    : "You haven't created or redeemed any vouchers yet"
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredVouchers.map((voucher) => (
            <Card key={voucher.id} className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-mono font-semibold text-lg">{voucher.voucher_code}</h3>
                      {getStatusBadge(voucher.status)}
                      {voucher.has_pin && (
                        <Shield className="h-4 w-4 text-blue-600" />
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Amount</p>
                        <p className="font-semibold text-green-600">
                          ${voucher.amount} {voucher.currency}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Created</p>
                        <p className="font-medium">{formatTimeAgo(voucher.created_at)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">
                          {voucher.status === "redeemed" ? "Redeemed" : "Expires"}
                        </p>
                        <p className="font-medium">
                          {voucher.status === "redeemed" && voucher.redeemed_at
                            ? formatTimeAgo(voucher.redeemed_at)
                            : voucher.time_remaining || "Expired"
                          }
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">
                          {voucher.creator_username ? "From" : "To"}
                        </p>
                        <p className="font-medium">
                          {voucher.creator_username || voucher.redeemer_username || "Unknown"}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex flex-col gap-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleVoucherClick(voucher)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopyCode(voucher.voucher_code)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleShareVoucher(voucher)}
                    >
                      <Share2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Voucher Details Modal */}
      {showDetails && selectedVoucher && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg max-h-[85vh] overflow-y-auto shadow-2xl">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Gift className="h-5 w-5" />
                Voucher Details
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDetails(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-2">
                  ${selectedVoucher.amount} {selectedVoucher.currency}
                </div>
                <div className="font-mono text-lg font-semibold mb-2">
                  {selectedVoucher.voucher_code}
                </div>
                {getStatusBadge(selectedVoucher.status)}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Created</p>
                  <p className="font-medium">{selectedVoucher.created_at.toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Expires</p>
                  <p className="font-medium">{selectedVoucher.expires_at.toLocaleDateString()}</p>
                </div>
                {selectedVoucher.redeemed_at && (
                  <div>
                    <p className="text-sm text-muted-foreground">Redeemed</p>
                    <p className="font-medium">{selectedVoucher.redeemed_at.toLocaleDateString()}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-muted-foreground">Security</p>
                  <p className="font-medium flex items-center gap-2">
                    {selectedVoucher.has_pin ? (
                      <>
                        <Shield className="h-4 w-4 text-blue-600" />
                        PIN Protected
                      </>
                    ) : (
                      "No PIN"
                    )}
                  </p>
                </div>
              </div>

              {(selectedVoucher.creator_username || selectedVoucher.redeemer_username) && (
                <div>
                  <p className="text-sm text-muted-foreground">
                    {selectedVoucher.creator_username ? "From" : "Redeemed by"}
                  </p>
                  <p className="font-medium flex items-center gap-2">
                    <User className="h-4 w-4" />
                    {selectedVoucher.creator_username || selectedVoucher.redeemer_username}
                  </p>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => handleCopyCode(selectedVoucher.voucher_code)}
                  className="flex-1"
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Code
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleShareVoucher(selectedVoucher)}
                  className="flex-1"
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  Share
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
