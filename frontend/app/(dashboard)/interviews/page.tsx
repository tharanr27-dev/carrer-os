"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { InterviewStudio } from "@/features/platform/module-screens";

export default function InterviewsPage() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=interviews");
    }
  }, [pathname, router]);

  return <InterviewStudio />;
}
