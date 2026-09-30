"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { MentorWorkspaceView } from "@/features/student/mentor";

export default function Page() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=mentor");
    }
  }, [pathname, router]);

  return <MentorWorkspaceView />;
}
