/**
 * Subscription Status Component
 * Displays current subscription details and management options
 */

import { useState } from 'react';
import { format } from 'date-fns';
import { CreditCard, Calendar, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { toast } from 'sonner';

const statusColors = {
  active: 'bg-green-500',
  trialing: 'bg-blue-500',
  past_due: 'bg-yellow-500',
  canceled: 'bg-red-500',
  incomplete: 'bg-gray-500',
};

const statusLabels = {
  active: 'Active',
  trialing: 'Trial',
  past_due: 'Past Due',
  canceled: 'Canceled',
  incomplete: 'Incomplete',
};

export function SubscriptionStatus({ subscription, onRefresh }) {
  const [canceling, setCanceling] = useState(false);

  const handleCancelSubscription = async () => {
    setCanceling(true);
    try {
      const response = await fetch('/api/billing/cancel', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ at_period_end: true }),
      });

      if (!response.ok) {
        throw new Error('Failed to cancel subscription');
      }

      toast.success('Subscription will be canceled at the end of the billing period');
      onRefresh?.();
    } catch (error) {
      toast.error('Failed to cancel subscription');
    } finally {
      setCanceling(false);
    }
  };

  if (!subscription) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            No Active Subscription
          </CardTitle>
          <CardDescription>
            Choose a plan to start tokenizing your assets
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const usagePercent = (subscription.tokens_used / subscription.tokens_limit) * 100;
  const isActive = subscription.status === 'active' || subscription.status === 'trialing';

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            {subscription.plan.charAt(0).toUpperCase() + subscription.plan.slice(1)} Plan
          </CardTitle>
          <Badge
            variant="outline"
            className={`${statusColors[subscription.status]} text-white`}
          >
            {statusLabels[subscription.status]}
          </Badge>
        </div>
        <CardDescription>
          {subscription.cancel_at_period_end
            ? 'Your subscription will end at the end of the current billing period'
            : `Your subscription renews on ${
                subscription.current_period_end
                  ? format(new Date(subscription.current_period_end), 'MMMM d, yyyy')
                  : 'N/A'
              }`}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Usage Stats */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Token Usage
            </span>
            <span>
              {subscription.tokens_used} / {subscription.tokens_limit} tokens
            </span>
          </div>
          <Progress value={usagePercent} className="h-2" />
          <p className="text-xs text-muted-foreground">
            {subscription.tokens_limit - subscription.tokens_used} tokens remaining
          </p>
        </div>

        {/* Billing Period */}
        <div className="flex items-center justify-between rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <Calendar className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Current Period</p>
              <p className="text-sm text-muted-foreground">
                {subscription.current_period_start
                  ? format(new Date(subscription.current_period_start), 'MMM d')
                  : 'N/A'}{' '}
                -{' '}
                {subscription.current_period_end
                  ? format(new Date(subscription.current_period_end), 'MMM d, yyyy')
                  : 'N/A'}
              </p>
            </div>
          </div>
          {isActive && !subscription.cancel_at_period_end && (
            <CheckCircle className="h-5 w-5 text-green-500" />
          )}
          {subscription.cancel_at_period_end && (
            <AlertCircle className="h-5 w-5 text-yellow-500" />
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          {isActive && !subscription.cancel_at_period_end && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" className="text-destructive">
                  Cancel Subscription
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Cancel Subscription?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Your subscription will remain active until the end of the current
                    billing period. You won't be charged again.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Keep Subscription</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleCancelSubscription}
                    disabled={canceling}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {canceling ? 'Canceling...' : 'Cancel Subscription'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}

          {subscription.cancel_at_period_end && (
            <Button variant="default" onClick={() => {/* Reactivate logic */}}>
              Reactivate Subscription
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
