/**
 * Public Asset Page Component for RWA-Studio
 *
 * Displays token information publicly with sharing and referral support
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ShareWidget } from "@/components/share/ShareWidget";
import {
  Shield,
  Globe,
  Building,
  FileText,
  ExternalLink,
  Users,
  TrendingUp,
  Lock,
  CheckCircle,
} from "lucide-react";

// Framework badge colors
const FRAMEWORK_COLORS = {
  "reg-d": { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  "reg-s": { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
  "reg-cf": { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  "reg-a": { bg: "bg-green-50", text: "text-green-700", border: "border-green-200" },
  custom: { bg: "bg-gray-50", text: "text-gray-700", border: "border-gray-200" },
};

// Asset type icons
const ASSET_ICONS = {
  "real-estate": Building,
  "private-equity": TrendingUp,
  debt: FileText,
  commodities: Globe,
  ip: FileText,
};

export function AssetPage() {
  const { tokenAddress } = useParams();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pageData, setPageData] = useState(null);

  const refCode = searchParams.get("ref");
  const utmSource = searchParams.get("utm_source");

  const loadAssetData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Build URL with tracking params
      let url = `/api/assets/${tokenAddress}`;
      const params = new URLSearchParams();
      if (refCode) params.append("ref", refCode);
      if (utmSource) params.append("utm_source", utmSource);
      if (params.toString()) url += `?${params.toString()}`;

      const response = await fetch(url);
      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Failed to load asset data");
      }

      setPageData(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [tokenAddress, refCode, utmSource]);

  useEffect(() => {
    loadAssetData();
  }, [loadAssetData]);

  if (loading) {
    return <AssetPageSkeleton />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <div className="text-red-500 mb-4">
              <Shield className="h-12 w-12 mx-auto" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Asset Not Found</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button variant="outline" onClick={() => window.history.back()}>
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { token, stats, badges, share_urls: _share_urls, embed_codes: _embed_codes } = pageData;
  const framework = token.regulatory_framework?.toLowerCase().replace(" ", "-") || "custom";
  const frameworkColors = FRAMEWORK_COLORS[framework] || FRAMEWORK_COLORS.custom;
  const AssetIcon = ASSET_ICONS[token.asset_type] || Building;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-primary" />
            <span className="font-semibold text-gray-900">RWA-Studio</span>
          </div>
          <ShareWidget
            tokenAddress={token.token_address}
            tokenName={token.token_name}
            tokenSymbol={token.token_symbol}
          />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <Card className="mb-6 overflow-hidden">
          <div className="bg-gradient-to-r from-primary/10 to-primary/5 p-6 border-b">
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-white rounded-lg shadow-sm">
                  <AssetIcon className="h-8 w-8 text-primary" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{token.token_name}</h1>
                  <p className="text-lg text-primary font-semibold">${token.token_symbol}</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {badges?.map((badge, index) => (
                  <Badge
                    key={index}
                    variant="outline"
                    className={`${frameworkColors.bg} ${frameworkColors.text} ${frameworkColors.border}`}
                  >
                    {badge.icon} {badge.name}
                  </Badge>
                ))}
              </div>
            </div>

            {token.description && <p className="mt-4 text-gray-600">{token.description}</p>}
          </div>

          {/* Stats Grid */}
          <CardContent className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatItem
                label="Asset Type"
                value={token.asset_type?.replace("-", " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                icon={AssetIcon}
              />
              <StatItem
                label="Framework"
                value={token.regulatory_framework?.toUpperCase()}
                icon={FileText}
              />
              <StatItem label="Jurisdiction" value={token.jurisdiction} icon={Globe} />
              <StatItem
                label="Verified Investors"
                value={stats?.verified_investors || 0}
                icon={Users}
              />
            </div>
          </CardContent>
        </Card>

        {/* Token Details */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Token Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <DetailRow label="Token Address" value={token.token_address} isAddress />
              <DetailRow label="Max Supply" value={formatNumber(token.max_supply)} />
              <DetailRow label="Compliance Module" value={token.compliance_address} isAddress />
              <DetailRow
                label="Identity Registry"
                value={token.identity_registry_address}
                isAddress
              />
              {token.deployment_date && (
                <DetailRow
                  label="Deployed"
                  value={new Date(token.deployment_date).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                />
              )}
            </div>
          </CardContent>
        </Card>

        {/* Compliance Badges */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Compliance Verification
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <ComplianceBadge
                title="ERC-3643 Compliant"
                description="Token implements the ERC-3643 security token standard"
                verified
              />
              <ComplianceBadge
                title={`${token.regulatory_framework} Compliant`}
                description={`Structured for ${token.regulatory_framework} exemption`}
                verified
              />
              <ComplianceBadge
                title="Identity Verification"
                description="On-chain identity registry for investor verification"
                verified={!!token.identity_registry_address}
              />
              <ComplianceBadge
                title="Transfer Restrictions"
                description="Automated compliance rules enforced on transfers"
                verified={!!token.compliance_address}
              />
            </div>
          </CardContent>
        </Card>

        {/* CTA Section */}
        <Card className="bg-gradient-to-r from-primary to-primary/80 text-white">
          <CardContent className="p-8 text-center">
            <h2 className="text-xl font-bold mb-2">Interested in This Offering?</h2>
            <p className="text-white/80 mb-6">
              Contact the issuer for more information about participating.
            </p>
            <div className="flex justify-center gap-4 flex-wrap">
              <Button variant="secondary" size="lg">
                <Mail className="h-4 w-4 mr-2" />
                Contact Issuer
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="bg-white/10 border-white/30 text-white hover:bg-white/20"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View Documents
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <footer className="mt-8 text-center text-sm text-gray-500">
          <p className="flex items-center justify-center gap-2">
            <Lock className="h-4 w-4" />
            Verified by{" "}
            <a href="/" className="text-primary hover:underline">
              RWA-Studio
            </a>
          </p>
          <p className="mt-2 text-xs">
            ⚠️ This is an informational page. Conduct your own due diligence before investing.
          </p>
        </footer>
      </main>
    </div>
  );
}

// Sub-components
function StatItem({ label, value, icon: Icon }) {
  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        <Icon className="h-4 w-4" />
        <span className="text-xs uppercase tracking-wide">{label}</span>
      </div>
      <p className="font-semibold text-gray-900">{value}</p>
    </div>
  );
}

function DetailRow({ label, value, isAddress }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between py-2 border-b last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={`font-mono text-sm ${isAddress ? "truncate max-w-[300px]" : ""}`}>
        {value}
      </span>
    </div>
  );
}

function ComplianceBadge({ title, description, verified }) {
  return (
    <div
      className={`p-4 rounded-lg border ${verified ? "bg-green-50 border-green-200" : "bg-gray-50 border-gray-200"}`}
    >
      <div className="flex items-start gap-3">
        <div className={`p-1 rounded-full ${verified ? "bg-green-100" : "bg-gray-100"}`}>
          {verified ? (
            <CheckCircle className="h-5 w-5 text-green-600" />
          ) : (
            <Shield className="h-5 w-5 text-gray-400" />
          )}
        </div>
        <div>
          <h4 className="font-medium text-gray-900">{title}</h4>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
    </div>
  );
}

function AssetPageSkeleton() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-64 w-full mb-6" />
        <Skeleton className="h-48 w-full mb-6" />
        <Skeleton className="h-48 w-full" />
      </div>
    </div>
  );
}

function formatNumber(value) {
  if (!value) return "0";
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return num.toLocaleString();
}

// Import Mail icon that we're using
import { Mail } from "lucide-react";

export default AssetPage;
