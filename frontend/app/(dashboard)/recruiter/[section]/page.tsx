"use client";

import { useParams } from "next/navigation";
import { RecruiterPortal } from "@/features/recruiter/recruiter-portal";

export default function RecruiterPortalSectionPage() {
  const { section } = useParams<{ section: string }>();
  return <RecruiterPortal section={section} />;
}
