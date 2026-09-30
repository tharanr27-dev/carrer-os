"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { CareerDiscoveryView } from "@/features/student/career-discovery";

export default function CareerDiscovery() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=discovery");
    }
  }, [pathname, router]);

  return <CareerDiscoveryView />;
}
