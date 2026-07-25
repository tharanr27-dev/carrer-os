"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { MentorWorkspace } from "@/features/platform/module-screens";

export default function MentorPage() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=mentor");
    }
  }, [pathname, router]);

  return <MentorWorkspace />;
}
