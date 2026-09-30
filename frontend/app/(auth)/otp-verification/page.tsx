"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

// Accounts are activated at sign-up and the backend exposes no OTP endpoint, so there is nothing to verify here.
export default function OtpPage() {
  return (
    <div className="flex flex-col text-left">
      <h3 className="text-xl font-bold text-foreground">Email verification</h3>
      <p className="text-xs text-muted-foreground mt-2 mb-6">
        Email verification codes are not used yet: your account is active as soon as you register. You can sign in
        directly.
      </p>
      <Link href="/login" className="w-full">
        <Button className="w-full">Go to Sign In</Button>
      </Link>
    </div>
  );
}
