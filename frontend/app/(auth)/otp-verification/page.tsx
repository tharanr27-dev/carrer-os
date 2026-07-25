"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const otpSchema = z.object({
  otp: z.string().length(6, "OTP must be exactly 6 digits").regex(/^\d+$/, "OTP must contain only numbers"),
});

type OtpFormValues = z.infer<typeof otpSchema>;

export default function OtpPage() {
  const [loading, setLoading] = React.useState(false);
  const [success, setSuccess] = React.useState(false);
  const [timer, setTimer] = React.useState(59);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setTimer((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OtpFormValues>({
    resolver: zodResolver(otpSchema),
    defaultValues: { otp: "" },
  });

  const onSubmit = async () => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1200));
    setLoading(false);
    setSuccess(true);
    setTimeout(() => {
      // Complete mock login/auth and direct to student dashboard
      window.location.href = "/student";
    }, 1000);
  };

  if (success) {
    return (
      <div className="flex flex-col text-center py-6">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400 mb-4 animate-bounce">
          ✓
        </div>
        <h3 className="text-xl font-bold text-slate-100">Verification Successful</h3>
        <p className="text-xs text-muted-foreground mt-2">
          Your account is verified! Directing to student dashboard...
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col text-left">
      <h3 className="text-xl font-bold text-slate-100">Two-Factor OTP</h3>
      <p className="text-xs text-muted-foreground mt-1 mb-6">
        We sent a 6-digit verification code to your email. Enter it below to proceed.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300">OTP Code</label>
            <span className="text-[10px] text-muted-foreground">
              {timer > 0 ? `Resend in ${timer}s` : "Resend available"}
            </span>
          </div>
          <Input
            type="text"
            placeholder="123456"
            maxLength={6}
            {...register("otp")}
            className={errors.otp ? "border-destructive focus-visible:ring-destructive text-center tracking-widest text-lg font-mono" : "text-center tracking-widest text-lg font-mono"}
          />
          {errors.otp && (
            <p className="text-[10px] text-destructive font-medium">{errors.otp.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full mt-2 cursor-pointer" isLoading={loading}>
          Verify Account
        </Button>
      </form>

      <div className="flex justify-center mt-6 text-xs text-muted-foreground">
        <span>Didn&apos;t receive a code?</span>
        <button
          onClick={() => setTimer(59)}
          disabled={timer > 0}
          className="text-primary hover:underline font-semibold ml-1 cursor-pointer disabled:opacity-50 disabled:pointer-events-none"
        >
          Resend Code
        </button>
      </div>
    </div>
  );
}
