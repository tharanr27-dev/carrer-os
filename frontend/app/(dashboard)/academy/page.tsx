"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { TrainingAcademyView } from "@/features/student/learning";

export default function Page() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=academy");
    }
  }, [pathname, router]);

  return <TrainingAcademyView />;
}
