"use client";

import React, { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { InterviewPreparationView, PREP_TABS } from "@/features/student/interview-prep";

function InterviewPrepContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const raw = searchParams.get("tab") || "roadmap";
  const tab = PREP_TABS.some((t) => t.value === raw) ? raw : "roadmap";

  return (
    <div className="text-left">
      <InterviewPreparationView tab={tab} onTabChange={(value) => router.push(`/interview-prep?tab=${value}`)} />
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={null}>
      <InterviewPrepContent />
    </Suspense>
  );
}
