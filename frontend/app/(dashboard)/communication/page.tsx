"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { CommunicationCoachView } from "@/features/student/communication";

export default function Page() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=communication");
    }
  }, [pathname, router]);

  return <CommunicationCoachView />;
}
