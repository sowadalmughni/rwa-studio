/**
 * Checkout Button Component
 * Handles Stripe checkout flow
 */

import { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

// Initialize Stripe (use environment variable in production)
// TODO: Use stripePromise when implementing full Stripe Elements checkout
const _stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || "");

export function CheckoutButton({
  plan,
  className,
  variant = "default",
  loading: externalLoading,
  onLoadingChange,
  children,
}) {
  const [internalLoading, setInternalLoading] = useState(false);
  const loading = externalLoading ?? internalLoading;

  const handleCheckout = async () => {
    const setLoading = (value) => {
      setInternalLoading(value);
      onLoadingChange?.(value);
    };

    setLoading(true);

    try {
      // Create checkout session
      const response = await fetch("/api/billing/checkout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          plan,
          success_url: `${window.location.origin}/billing/success`,
          cancel_url: `${window.location.origin}/billing`,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to create checkout session");
      }

      const { checkout_url } = await response.json();

      // Redirect to Stripe Checkout
      if (checkout_url) {
        window.location.href = checkout_url;
      } else {
        throw new Error("No checkout URL returned");
      }
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error(error.message || "Failed to start checkout");
      setLoading(false);
    }
  };

  return (
    <Button onClick={handleCheckout} disabled={loading} className={className} variant={variant}>
      {loading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Processing...
        </>
      ) : (
        children || "Subscribe"
      )}
    </Button>
  );
}
