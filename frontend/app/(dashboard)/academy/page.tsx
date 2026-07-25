"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { TrainingAcademy } from "@/features/platform/module-screens";

export default function AcademyPage() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=academy");
    }
  }, [pathname, router]);

  return <TrainingAcademy />;
}
