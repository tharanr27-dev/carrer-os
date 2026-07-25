"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { ReportsCenter } from "@/features/platform/module-screens";

export default function ReportsPage() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/analytics") {
      router.replace("/analytics?tab=reports");
    }
  }, [pathname, router]);

  return <ReportsCenter />;
}
