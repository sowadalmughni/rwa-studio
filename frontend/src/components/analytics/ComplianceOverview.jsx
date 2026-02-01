/**
 * Compliance Overview Component
 * Bar chart showing compliance events
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, CheckCircle, XCircle, AlertCircle } from "lucide-react";

// Sample data
const sampleData = [
  { name: "Transfer Blocked", count: 12, severity: "high" },
  { name: "Verification Expired", count: 8, severity: "medium" },
  { name: "Limit Exceeded", count: 5, severity: "medium" },
  { name: "Jurisdiction Mismatch", count: 3, severity: "high" },
  { name: "Holding Period", count: 2, severity: "low" },
];

const severityColors = {
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#22c55e",
};

const recentEvents = [
  {
    id: 1,
    type: "Transfer Blocked",
    address: "0x1234...5678",
    reason: "Investor limit exceeded",
    severity: "high",
    time: "2 hours ago",
  },
  {
    id: 2,
    type: "Verification Expired",
    address: "0xabcd...efgh",
    reason: "KYC expired",
    severity: "medium",
    time: "5 hours ago",
  },
  {
    id: 3,
    type: "Transfer Approved",
    address: "0x9876...5432",
    reason: "All checks passed",
    severity: "success",
    time: "1 day ago",
  },
];

export function ComplianceOverview({ data = sampleData, events = recentEvents }) {
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case "high":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "medium":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case "low":
        return <AlertCircle className="h-4 w-4 text-blue-500" />;
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance Events</CardTitle>
          <CardDescription>Events by type (last 30 days)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  className="stroke-muted"
                  horizontal={true}
                  vertical={false}
                />
                <XAxis
                  type="number"
                  className="text-xs"
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  className="text-xs"
                  tick={{ fill: "hsl(var(--muted-foreground))" }}
                  width={75}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={severityColors[entry.severity]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Recent Events List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Events</CardTitle>
          <CardDescription>Latest compliance activity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {events.map((event) => (
              <div key={event.id} className="flex items-start gap-3 rounded-lg border p-3">
                {getSeverityIcon(event.severity)}
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{event.type}</p>
                    <span className="text-xs text-muted-foreground">{event.time}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{event.address}</p>
                  <p className="text-xs">{event.reason}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
