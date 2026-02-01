/**
 * Analytics Dashboard Component
 * Main dashboard view with all analytics components
 */

import { useState, useEffect } from 'react';
import { Coins, Users, Shield, TrendingUp, Activity, FileCheck } from 'lucide-react';
import { StatCard } from './StatCard';
import { TokenMetricsChart } from './TokenMetricsChart';
import { ComplianceOverview } from './ComplianceOverview';
import { InvestorDistribution } from './InvestorDistribution';
import { Skeleton } from '@/components/ui/skeleton';

export function AnalyticsDashboard({ tokenAddress }) {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [timeRange, setTimeRange] = useState('30d');

  useEffect(() => {
    // Simulate loading analytics data
    const loadAnalytics = async () => {
      setLoading(true);
      
      // In production, this would fetch from API
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      setStats({
        totalTokens: 5,
        totalTokensTrend: 'up',
        totalTokensTrendValue: '+2 this month',
        
        verifiedInvestors: 127,
        verifiedInvestorsTrend: 'up',
        verifiedInvestorsTrendValue: '+12.5%',
        
        complianceRate: '98.5%',
        complianceRateTrend: 'up',
        complianceRateTrendValue: '+0.5%',
        
        totalVolume: '$2.4M',
        totalVolumeTrend: 'up',
        totalVolumeTrendValue: '+15.3%',
        
        activeTransfers: 42,
        activeTransfersTrend: 'neutral',
        activeTransfersTrendValue: '',
        
        pendingVerifications: 8,
        pendingVerificationsTrend: 'down',
        pendingVerificationsTrendValue: '-3',
      });
      
      setLoading(false);
    };

    loadAnalytics();
  }, [tokenAddress, timeRange]);

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
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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
      </div>

      {/* Token Metrics Chart */}
      <TokenMetricsChart
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
      />

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
