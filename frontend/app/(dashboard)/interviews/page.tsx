"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { InterviewStudioView } from "@/features/student/interview";

export default function Page() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=interviews");
    }
  }, [pathname, router]);

  return <InterviewStudioView />;
}
