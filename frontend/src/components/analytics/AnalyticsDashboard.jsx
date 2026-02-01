/**
 * Analytics Dashboard Component
 * Main dashboard view with all analytics components
 */

import { useState, useEffect, useCallback } from "react";
import {
  Coins,
  Users,
  Shield,
  TrendingUp,
  Activity,
  FileCheck,
  Download,
  RefreshCw,
  Eye,
  Share2,
} from "lucide-react";
import { StatCard } from "./StatCard";
import { TokenMetricsChart } from "./TokenMetricsChart";
import { ComplianceOverview } from "./ComplianceOverview";
import { InvestorDistribution } from "./InvestorDistribution";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function AnalyticsDashboard({ tokenAddress }) {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [timeRange, setTimeRange] = useState("30d");
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadAnalytics = useCallback(async () => {
    setLoading(true);

    try {
      // In production, this would fetch from API
      // const response = await fetch(`/api/transfer-agent/tokens/${tokenAddress}/metrics?period=${timeRange}`);
      // const data = await response.json();

      await new Promise((resolve) => setTimeout(resolve, 1000));

      setStats({
        totalTokens: 5,
        totalTokensTrend: "up",
        totalTokensTrendValue: "+2 this month",

        verifiedInvestors: 127,
        verifiedInvestorsTrend: "up",
        verifiedInvestorsTrendValue: "+12.5%",

        complianceRate: "98.5%",
        complianceRateTrend: "up",
        complianceRateTrendValue: "+0.5%",

        totalVolume: "$2.4M",
        totalVolumeTrend: "up",
        totalVolumeTrendValue: "+15.3%",

        activeTransfers: 42,
        activeTransfersTrend: "neutral",
        activeTransfersTrendValue: "",

        pendingVerifications: 8,
        pendingVerificationsTrend: "down",
        pendingVerificationsTrendValue: "-3",

        // Growth KPIs
        pageViews: 1247,
        pageViewsTrend: "up",
        pageViewsTrendValue: "+23.4%",

        shareCount: 89,
        shareCountTrend: "up",
        shareCountTrendValue: "+15 this week",

        badgeImpressions: 3420,
        badgeImpressionsTrend: "up",
        badgeImpressionsTrendValue: "+8.2%",

        referralConversions: 12,
        referralConversionsTrend: "up",
        referralConversionsTrendValue: "+3",
      });

      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to load analytics:", error);
    } finally {
      setLoading(false);
    }
  }, [tokenAddress, timeRange]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  // Polling for real-time updates (every 5 minutes)
  useEffect(() => {
    const interval = setInterval(
      () => {
        loadAnalytics();
      },
      5 * 60 * 1000
    );

    return () => clearInterval(interval);
  }, [loadAnalytics]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAnalytics();
    setRefreshing(false);
  };

  const handleExport = async (format) => {
    try {
      const response = await fetch(
        `/api/analytics/export/${tokenAddress}?format=${format}&days=${timeRange.replace("d", "")}&type=all`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (format === "json") {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        downloadBlob(blob, `analytics-${tokenAddress}-${format}.json`);
      } else {
        const blob = await response.blob();
        const extension = format === "pdf" ? "md" : format;
        downloadBlob(blob, `analytics-${tokenAddress}.${extension}`);
      }
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-[120px]" />
          ))}
        </div>
        <Skeleton className="h-[400px]" />
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-[350px]" />
          <Skeleton className="h-[350px]" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold">Analytics Dashboard</h2>
          {lastUpdated && (
            <p className="text-sm text-muted-foreground">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Export Format</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => handleExport("csv")}>
                📊 Export as CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport("json")}>
                📋 Export as JSON
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport("pdf")}>
                📄 Export as Report (MD)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <StatCard
          title="Total Tokens"
          value={stats.totalTokens}
          icon={Coins}
          trend={stats.totalTokensTrend}
          trendValue={stats.totalTokensTrendValue}
        />
        <StatCard
          title="Verified Investors"
          value={stats.verifiedInvestors}
          icon={Users}
          trend={stats.verifiedInvestorsTrend}
          trendValue={stats.verifiedInvestorsTrendValue}
        />
        <StatCard
          title="Compliance Rate"
          value={stats.complianceRate}
          icon={Shield}
          trend={stats.complianceRateTrend}
          trendValue={stats.complianceRateTrendValue}
        />
        <StatCard
          title="Total Volume"
          value={stats.totalVolume}
          icon={TrendingUp}
          trend={stats.totalVolumeTrend}
          trendValue={stats.totalVolumeTrendValue}
        />
        <StatCard
          title="Active Transfers"
          value={stats.activeTransfers}
          icon={Activity}
          description="Last 24 hours"
        />
        <StatCard
          title="Pending Verifications"
          value={stats.pendingVerifications}
          icon={FileCheck}
          trend={stats.pendingVerificationsTrend}
          trendValue={stats.pendingVerificationsTrendValue}
        />
        {/* Growth KPIs */}
        <StatCard
          title="Page Views"
          value={stats.pageViews}
          icon={Eye}
          trend={stats.pageViewsTrend}
          trendValue={stats.pageViewsTrendValue}
        />
        <StatCard
          title="Shares"
          value={stats.shareCount}
          icon={Share2}
          trend={stats.shareCountTrend}
          trendValue={stats.shareCountTrendValue}
        />
      </div>

      {/* Growth Metrics Card */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Growth Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
              <div className="text-sm text-blue-600 font-medium">Badge Impressions</div>
              <div className="text-2xl font-bold text-blue-900">
                {stats.badgeImpressions?.toLocaleString()}
              </div>
              <div className="text-xs text-blue-600">{stats.badgeImpressionsTrendValue}</div>
            </div>
            <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
              <div className="text-sm text-green-600 font-medium">Referral Conversions</div>
              <div className="text-2xl font-bold text-green-900">{stats.referralConversions}</div>
              <div className="text-xs text-green-600">{stats.referralConversionsTrendValue}</div>
            </div>
            <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
              <div className="text-sm text-purple-600 font-medium">Viral Coefficient</div>
              <div className="text-2xl font-bold text-purple-900">1.2x</div>
              <div className="text-xs text-purple-600">Above target (1.0x)</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Token Metrics Chart */}
      <TokenMetricsChart timeRange={timeRange} onTimeRangeChange={setTimeRange} />

      {/* Bottom Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Investor Distribution */}
        <InvestorDistribution />

        {/* Compliance Overview */}
        <div className="lg:col-span-1">
          <ComplianceOverview />
        </div>
      </div>
    </div>
  );
}
