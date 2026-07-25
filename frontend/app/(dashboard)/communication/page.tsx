"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { CommunicationCoach } from "@/features/platform/module-screens";

export default function CommunicationPage() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=communication");
    }
  }, [pathname, router]);

  return <CommunicationCoach />;
}
