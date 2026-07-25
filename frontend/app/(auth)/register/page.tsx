"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useAuthStore } from "@/store/useAuthStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";

const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  role: z.enum(["student", "recruiter", "officer"] as const),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const { register: signUp, isLoading } = useAuthStore();
  const [success, setSuccess] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      name: "",
      email: "",
      role: "student",
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (data: RegisterFormValues) => {
    try {
      const isOk = await signUp(data.name, data.email, data.password, data.role);
      if (isOk) {
        setSuccess(true);
        setTimeout(() => {
          window.location.href = "/otp-verification";
        }, 1500);
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (success) {
    return (
      <div className="flex flex-col text-center py-6">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400 mb-4 animate-bounce">
          ✓
        </div>
        <h3 className="text-xl font-bold text-slate-100">Account Created</h3>
        <p className="text-xs text-muted-foreground mt-2">
          Sending OTP code to verify your email. Redirecting...
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col text-left">
      <h3 className="text-xl font-bold text-slate-100">Create Account</h3>
      <p className="text-xs text-muted-foreground mt-1 mb-6">
        Get started with CareerOS AI today.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Name */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Full Name</label>
          <Input
            type="text"
            placeholder="Alex Morgan"
            {...register("name")}
            className={errors.name ? "border-destructive focus-visible:ring-destructive" : ""}
          />
          {errors.name && (
            <p className="text-[10px] text-destructive font-medium">{errors.name.message}</p>
          )}
        </div>

        {/* Email */}
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

        {/* Role */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">I am a...</label>
          <select
            {...register("role")}
            className="flex h-10 w-full rounded-md border border-slate-800 bg-slate-950/40 px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-hidden focus:ring-2 focus:ring-ring transition-all"
          >
            <option value="student">Student (Job Seeker)</option>
            <option value="recruiter">Recruiter (Talent Partner)</option>
            <option value="officer">Placement Officer (Academic Partner)</option>
          </select>
        </div>

        {/* Password */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Password</label>
          <Input
            type="password"
            placeholder="••••••••"
            {...register("password")}
            className={errors.password ? "border-destructive focus-visible:ring-destructive" : ""}
          />
          {errors.password && (
            <p className="text-[10px] text-destructive font-medium">{errors.password.message}</p>
          )}
        </div>

        {/* Confirm Password */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-300">Confirm Password</label>
          <Input
            type="password"
            placeholder="••••••••"
            {...register("confirmPassword")}
            className={errors.confirmPassword ? "border-destructive focus-visible:ring-destructive" : ""}
          />
          {errors.confirmPassword && (
            <p className="text-[10px] text-destructive font-medium">{errors.confirmPassword.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full mt-2 cursor-pointer" isLoading={isLoading}>
          Create Account
        </Button>
      </form>

      <p className="text-xs text-muted-foreground text-center mt-6">
        Already have an account?{" "}
        <Link href="/login" className="text-primary hover:underline font-semibold">
          Sign In
        </Link>
      </p>
    </div>
  );
}
