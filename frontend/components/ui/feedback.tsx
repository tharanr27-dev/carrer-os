"use client";

import * as React from "react";
import { AlertCircle, CheckCircle2, Inbox, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { errorMessage } from "@/lib/api";

export function LoadingBlock({ label = "Loading…", className }: { label?: string; className?: string }) {
  return (
    <div
      role="status"
      className={cn("flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground", className)}
    >
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

export function ErrorBanner({
  error,
  onRetry,
  className,
}: {
  error: unknown;
  onRetry?: () => void;
  className?: string;
}) {
  if (!error) return null;
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive",
        className
      )}
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <span className="flex-1">{typeof error === "string" ? error : errorMessage(error)}</span>
      {onRetry ? (
        <Button type="button" size="sm" variant="outline" onClick={onRetry} className="h-6 gap-1 px-2 text-[10px]">
          <RefreshCw className="h-3 w-3" />
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function SuccessBanner({ message, className }: { message: string | null; className?: string }) {
  if (!message) return null;
  return (
    <div
      role="status"
      className={cn(
        "flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-500",
        className
      )}
    >
      <CheckCircle2 className="h-4 w-4 shrink-0" />
      {message}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center gap-2 py-10 text-center", className)}>
      <Inbox className="h-8 w-8 text-muted-foreground" />
      <p className="text-sm font-semibold text-foreground">{title}</p>
      {description ? <p className="max-w-sm text-xs text-muted-foreground">{description}</p> : null}
      {action}
    </div>
  );
}

/** Renders loading / error / empty / content for a react-query result. */
export function QueryBoundary<T>({
  query,
  isEmpty,
  empty,
  children,
  loadingLabel,
}: {
  query: { data: T | undefined; isLoading: boolean; error: unknown; refetch: () => unknown };
  isEmpty?: (data: T) => boolean;
  empty?: React.ReactNode;
  children: (data: T) => React.ReactNode;
  loadingLabel?: string;
}) {
  if (query.isLoading) return <LoadingBlock label={loadingLabel} />;
  if (query.error) return <ErrorBanner error={query.error} onRetry={() => void query.refetch()} />;
  if (query.data === undefined || (isEmpty && isEmpty(query.data))) return <>{empty ?? <EmptyState title="Nothing here yet" />}</>;
  return <>{children(query.data)}</>;
}
