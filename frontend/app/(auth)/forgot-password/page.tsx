"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const forgotSchema = z.object({
  email: z.string().email("Invalid email address"),
});

type ForgotFormValues = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const [success, setSuccess] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotFormValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: "" },
  });

  const onSubmit = async () => {
    setLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setLoading(false);
    setSuccess(true);
  };

  if (success) {
    return (
      <div className="flex flex-col text-left">
        <h3 className="text-xl font-bold text-slate-100">Check Your Email</h3>
        <p className="text-xs text-muted-foreground mt-2 mb-6">
          We have sent password recovery instructions and a 6-digit OTP code to your inbox.
        </p>
        <Link href="/otp-verification" className="w-full">
          <Button className="w-full">Enter OTP Code</Button>
        </Link>
        <p className="text-xs text-muted-foreground text-center mt-6">
          Back to{" "}
          <Link href="/login" className="text-primary hover:underline font-semibold">
            Sign In
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col text-left">
      <h3 className="text-xl font-bold text-slate-100">Reset Password</h3>
      <p className="text-xs text-muted-foreground mt-1 mb-6">
        Enter your email to receive recovery instructions.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Email Address</label>
          <Input
            type="email"
            placeholder="alex.morgan@university.edu"
            {...register("email")}
            className={errors.email ? "border-destructive focus-visible:ring-destructive" : ""}
          />
          {errors.email && (
            <p className="text-[10px] text-destructive font-medium">{errors.email.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full mt-2 cursor-pointer" isLoading={loading}>
          Send Reset Instructions
        </Button>
      </form>

      <p className="text-xs text-muted-foreground text-center mt-6">
        Back to{" "}
        <Link href="/login" className="text-primary hover:underline font-semibold">
          Sign In
        </Link>
      </p>
    </div>
  );
}
