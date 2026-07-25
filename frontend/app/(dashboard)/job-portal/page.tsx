"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { JobPortal } from "@/features/platform/module-screens";

export default function JobPortalPage() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/jobs") {
      router.replace("/jobs?tab=portal");
    }
  }, [pathname, router]);

  return <JobPortal />;
}
