"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { ResumeCenterView } from "@/features/student/resume-center";

export default function ResumeCenter() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=resume");
    }
  }, [pathname, router]);

  return <ResumeCenterView />;
}
