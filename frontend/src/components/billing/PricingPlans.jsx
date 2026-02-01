/**
 * Pricing Plans Component
 * Displays available subscription plans with features
 */

import { useState } from "react";
import { Check, Sparkles, Building2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckoutButton } from "./CheckoutButton";

const plans = [
  {
    id: "starter",
    name: "Starter",
    price: 99,
    description: "Perfect for getting started with tokenization",
    tokens_limit: 3,
    features: [
      "Up to 3 tokenized assets",
      "Basic compliance rules",
      "Email support",
      "Standard analytics",
      "Community access",
    ],
    icon: Sparkles,
  },
  {
    id: "professional",
    name: "Professional",
    price: 299,
    description: "For growing businesses with multiple assets",
    tokens_limit: 10,
    features: [
      "Up to 10 tokenized assets",
      "All compliance rules",
      "Priority support",
      "Advanced analytics",
      "Custom branding",
      "API access",
      "Investor management tools",
    ],
    recommended: true,
    icon: Sparkles,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: null,
    description: "Custom solutions for large organizations",
    tokens_limit: 100,
    features: [
      "Unlimited tokenized assets",
      "Custom compliance rules",
      "24/7 dedicated support",
      "White-label solution",
      "SLA guarantees",
      "On-premise deployment",
      "Custom integrations",
      "Dedicated account manager",
    ],
    contactSales: true,
    icon: Building2,
  },
];

export function PricingPlans({ currentPlan, onSelectPlan: _onSelectPlan }) {
  const [loading, setLoading] = useState(null);

  const handleContactSales = () => {
    window.open("mailto:sales@rwa-studio.com?subject=Enterprise Plan Inquiry", "_blank");
  };

  return (
    <div className="grid gap-6 md:grid-cols-3">
      {plans.map((plan) => {
        const Icon = plan.icon;
        const isCurrentPlan = currentPlan === plan.id;

        return (
          <Card
            key={plan.id}
            className={`relative flex flex-col ${
              plan.recommended ? "border-primary shadow-lg ring-2 ring-primary/20" : ""
            } ${isCurrentPlan ? "bg-muted/50" : ""}`}
          >
            {plan.recommended && (
              <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">Most Popular</Badge>
            )}

            <CardHeader>
              <div className="flex items-center gap-2">
                <Icon className="h-5 w-5 text-primary" />
                <CardTitle>{plan.name}</CardTitle>
              </div>
              <CardDescription>{plan.description}</CardDescription>
            </CardHeader>

            <CardContent className="flex-1">
              <div className="mb-6">
                {plan.price !== null ? (
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold">${plan.price}</span>
                    <span className="text-muted-foreground">/month</span>
                  </div>
                ) : (
                  <div className="text-4xl font-bold">Custom</div>
                )}
                <p className="mt-1 text-sm text-muted-foreground">
                  Up to {plan.tokens_limit} tokens
                </p>
              </div>

              <ul className="space-y-3">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
            </CardContent>

            <CardFooter>
              {isCurrentPlan ? (
                <Button className="w-full" disabled variant="outline">
                  Current Plan
                </Button>
              ) : plan.contactSales ? (
                <Button className="w-full" variant="outline" onClick={handleContactSales}>
                  Contact Sales
                </Button>
              ) : (
                <CheckoutButton
                  plan={plan.id}
                  className="w-full"
                  variant={plan.recommended ? "default" : "outline"}
                  loading={loading === plan.id}
                  onLoadingChange={(isLoading) => setLoading(isLoading ? plan.id : null)}
                />
              )}
            </CardFooter>
          </Card>
        );
      })}
    </div>
  );
}
