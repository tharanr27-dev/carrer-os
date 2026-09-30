import * as React from "react";

function label(key: string) {
  return key.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

/** Renders arbitrary JSON returned by the backend (AI reports) as readable nested lists. */
export function JsonView({ value }: { value: unknown }): React.ReactElement | null {
  if (value === null || value === undefined) return null;

  if (Array.isArray(value)) {
    if (value.every((v) => typeof v !== "object" || v === null)) {
      return (
        <div className="flex flex-wrap gap-1.5">
          {value.map((v, i) => (
            <span key={i} className="px-2 py-0.5 rounded-md bg-primary/10 text-primary text-[10px] font-semibold">
              {String(v)}
            </span>
          ))}
        </div>
      );
    }
    return (
      <div className="space-y-2">
        {value.map((v, i) => (
          <div key={i} className="pl-3 border-l border-border">
            <JsonView value={v} />
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === "object") {
    return (
      <dl className="space-y-2 text-xs">
        {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
          <div key={k}>
            <dt className="text-[10px] font-semibold uppercase text-muted-foreground">{label(k)}</dt>
            <dd>
              <JsonView value={v} />
            </dd>
          </div>
        ))}
      </dl>
    );
  }

  return <span className="text-xs">{String(value)}</span>;
}
