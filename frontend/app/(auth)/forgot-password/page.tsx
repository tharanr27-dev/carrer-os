"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

// The backend has no password-reset endpoint yet, so this page says so instead of pretending to email a code.
export default function ForgotPasswordPage() {
  return (
    <div className="flex flex-col text-left">
      <h3 className="text-xl font-bold text-foreground">Reset Password</h3>
      <p className="text-xs text-muted-foreground mt-2 mb-6">
        Self-service password reset is not available yet. Please contact your platform administrator to have your
        password reset.
      </p>
      <Link href="/login" className="w-full">
        <Button className="w-full">Back to Sign In</Button>
      </Link>
    </div>
  );
}
