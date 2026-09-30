"use client";

import React from "react";
import { useRouter } from "next/navigation";

// Reports are exported from the Analytics page (CSV snapshot built from live data).
export default function ReportsPage() {
  const router = useRouter();

  React.useEffect(() => {
    router.replace("/analytics");
  }, [router]);

  return null;
}
