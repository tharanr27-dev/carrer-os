"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { CareerJourneyView } from "@/features/student/career-journey";

export default function CareerDashboard() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=careers");
    }
  }, [pathname, router]);

  return <CareerJourneyView />;
}
