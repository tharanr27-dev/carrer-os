"use client";

import { useParams } from "next/navigation";
import { AdminPortal } from "@/features/admin/admin-portal";

export default function AdminPortalSectionPage() {
  const { section } = useParams<{ section: string }>();
  return <AdminPortal section={section} />;
}
