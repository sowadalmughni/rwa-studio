/**
 * Investor Distribution Component
 * Pie chart showing investor distribution by jurisdiction/type
 */

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Sample data
const jurisdictionData = [
  { name: "United States", value: 45, color: "#6366f1" },
  { name: "United Kingdom", value: 20, color: "#8b5cf6" },
  { name: "Germany", value: 15, color: "#a855f7" },
  { name: "Singapore", value: 12, color: "#d946ef" },
  { name: "Other", value: 8, color: "#ec4899" },
];

const investorTypeData = [
  { name: "Accredited", value: 55, color: "#22c55e" },
  { name: "Institutional", value: 30, color: "#3b82f6" },
  { name: "Retail", value: 15, color: "#f59e0b" },
];

const verificationLevelData = [
  { name: "Level 3 (Full)", value: 60, color: "#22c55e" },
  { name: "Level 2 (Document)", value: 30, color: "#3b82f6" },
  { name: "Level 1 (Basic)", value: 10, color: "#f59e0b" },
];

const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (percent < 0.05) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      className="text-xs font-medium"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export function InvestorDistribution() {
  const renderPieChart = (data) => (
    <div className="h-[250px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={CustomLabel}
            outerRadius={80}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
            }}
            formatter={(value, name) => [`${value}%`, name]}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => <span className="text-sm text-muted-foreground">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Investor Distribution</CardTitle>
        <CardDescription>Breakdown of verified investors</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="jurisdiction" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="jurisdiction">Jurisdiction</TabsTrigger>
            <TabsTrigger value="type">Investor Type</TabsTrigger>
            <TabsTrigger value="verification">Verification</TabsTrigger>
          </TabsList>

          <TabsContent value="jurisdiction">{renderPieChart(jurisdictionData)}</TabsContent>

          <TabsContent value="type">{renderPieChart(investorTypeData)}</TabsContent>

          <TabsContent value="verification">{renderPieChart(verificationLevelData)}</TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
