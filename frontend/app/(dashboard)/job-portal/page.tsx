"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { JobBoard } from "@/features/student/jobs";

export default function Page() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/jobs") {
      router.replace("/jobs?tab=portal");
    }
  }, [pathname, router]);

  return <JobBoard />;
}
