import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Gift, 
  Plus, 
  Key, 
  History, 
  TrendingUp,
  DollarSign,
  Clock,
  CheckCircle,
  AlertCircle,
  ArrowLeft
} from "lucide-react";
import { VoucherCreation } from "@/components/VoucherCreation";
import { VoucherRedemption } from "@/components/VoucherRedemption";
import { VoucherHistory } from "@/components/VoucherHistory";

type Tab = "overview" | "create" | "redeem" | "history";

interface VoucherManagementProps {
  onNavigate: (page: string) => void;
}

export function VoucherManagement({ onNavigate }: VoucherManagementProps) {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRedeemModal, setShowRedeemModal] = useState(false);

  // Mock analytics data
  const analytics = {
    totalCreated: 12,
    totalRedeemed: 8,
    totalAmount: 2500,
    successRate: 67,
    activeVouchers: 3,
    expiredVouchers: 1
  };

  const recentVouchers = [
    {
      id: "voucher-1",
      code: "ABC123DEF456GHI789",
      amount: 100,
      currency: "USDC",
      status: "active",
      timeRemaining: "23h 45m"
    },
    {
      id: "voucher-2",
      code: "XYZ789GHI123JKL456",
      amount: 250,
      currency: "USDC",
      status: "redeemed",
      redeemedAt: "2 hours ago"
    }
  ];

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

  const handleVoucherCreated = (voucher: any) => {
    setShowCreateModal(false);
    setActiveTab("history");
  };

  const handleVoucherRedeemed = (voucher: any) => {
    setShowRedeemModal(false);
    setActiveTab("history");
  };

  if (activeTab === "create") {
    return (
      <div className="min-h-screen bg-background pb-20">
        {/* Header */}
        <header className="bg-background border-b border-border px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab("overview")}
              className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label="Go back"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex-1">
              <h1 className="text-xl font-semibold text-foreground">Create Voucher</h1>
              <p className="text-sm text-muted-foreground">Create a new cash-out voucher</p>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="px-4 py-6">
          <VoucherCreation onVoucherCreated={handleVoucherCreated} onClose={() => setActiveTab("overview")} />
        </div>
      </div>
    );
  }

  if (activeTab === "redeem") {
    return (
      <div className="min-h-screen bg-background pb-20">
        {/* Header */}
        <header className="bg-background border-b border-border px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab("overview")}
              className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label="Go back"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex-1">
              <h1 className="text-xl font-semibold text-foreground">Redeem Voucher</h1>
              <p className="text-sm text-muted-foreground">Redeem a voucher code for cash</p>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="px-4 py-6">
          <VoucherRedemption onVoucherRedeemed={handleVoucherRedeemed} onClose={() => setActiveTab("overview")} />
        </div>
      </div>
    );
  }

  if (activeTab === "history") {
    return (
      <div className="min-h-screen bg-background pb-20">
        {/* Header */}
        <header className="bg-background border-b border-border px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab("overview")}
              className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label="Go back"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex-1">
              <h1 className="text-xl font-semibold text-foreground">Voucher History</h1>
              <p className="text-sm text-muted-foreground">View and manage your vouchers</p>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="px-4 py-6">
          <VoucherHistory />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => onNavigate("dashboard")}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-foreground">Vouchers</h1>
            <p className="text-sm text-muted-foreground">
              Create and redeem cash-out vouchers
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setActiveTab("create")}
              size="sm"
              className="flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Create
            </Button>
            <Button
              variant="outline"
              onClick={() => setActiveTab("redeem")}
              size="sm"
              className="flex items-center gap-2"
            >
              <Key className="h-4 w-4" />
              Redeem
            </Button>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="px-4 py-6 space-y-6">

      {/* Analytics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Created</p>
                <p className="text-2xl font-bold">{analytics.totalCreated}</p>
              </div>
              <Gift className="h-8 w-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Redeemed</p>
                <p className="text-2xl font-bold">{analytics.totalRedeemed}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Amount</p>
                <p className="text-2xl font-bold">${analytics.totalAmount}</p>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Success Rate</p>
                <p className="text-2xl font-bold">{analytics.successRate}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab("create")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                <Plus className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">Create Voucher</h3>
                <p className="text-sm text-muted-foreground">
                  Create a new cash-out voucher for easy money access
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setActiveTab("redeem")}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <Key className="h-6 w-6 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">Redeem Voucher</h3>
                <p className="text-sm text-muted-foreground">
                  Redeem a voucher code to get cash from agents
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Vouchers */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <History className="h-5 w-5" />
            Recent Vouchers
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setActiveTab("history")}
          >
            View All
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentVouchers.map((voucher) => (
              <div key={voucher.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                    <Gift className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-mono font-semibold">{voucher.code}</p>
                    <p className="text-sm text-muted-foreground">
                      ${voucher.amount} {voucher.currency}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  {getStatusBadge(voucher.status)}
                  <p className="text-sm text-muted-foreground mt-1">
                    {voucher.status === "active" ? voucher.timeRemaining : voucher.redeemedAt}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div>
                <p className="font-semibold text-green-900">Active Vouchers</p>
                <p className="text-2xl font-bold text-green-800">{analytics.activeVouchers}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Clock className="h-8 w-8 text-blue-600" />
              <div>
                <p className="font-semibold text-blue-900">Pending</p>
                <p className="text-2xl font-bold text-blue-800">{analytics.totalCreated - analytics.totalRedeemed - analytics.expiredVouchers}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-gray-200 bg-gray-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-8 w-8 text-gray-600" />
              <div>
                <p className="font-semibold text-gray-900">Expired</p>
                <p className="text-2xl font-bold text-gray-800">{analytics.expiredVouchers}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      </div>
    </div>
  );
}
