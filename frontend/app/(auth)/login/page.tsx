"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useAuthStore } from "@/store/useAuthStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Chrome, Github, ShieldAlert } from "lucide-react";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  role: z.enum(["student", "recruiter", "officer", "admin"] as const),
  rememberMe: z.boolean().optional(),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login, isLoading } = useAuthStore();
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
      role: "student",
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormValues) => {
    setErrorMessage(null);
    try {
      const success = await login(data.email, data.password, data.role);
      if (success) {
        // Successful login, redirect to dashboard based on role
        window.location.href = `/${data.role}`;
      } else {
        setErrorMessage("Invalid credentials. Try again.");
      }
    } catch {
      setErrorMessage("An error occurred. Please try again.");
    }
  };

  return (
    <div className="flex flex-col text-left">
      <h3 className="text-xl font-bold text-foreground">Sign In</h3>
      <p className="text-xs text-muted-foreground mt-1 mb-6">
        Enter your details to access your dashboard.
      </p>

      {errorMessage && (
        <div className="mb-4 flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 text-destructive text-xs rounded-lg">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Email */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-foreground">Email Address</label>
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

        {/* Password */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-foreground">Password</label>
            <Link
              href="/forgot-password"
              className="text-[10px] text-primary hover:underline font-medium"
            >
              Forgot Password?
            </Link>
          </div>
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

        {/* Persona Select */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-foreground">Sign In Persona (Dashboard Access)</label>
          <select
            {...register("role")}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background placeholder:text-muted-foreground focus:outline-hidden focus:ring-2 focus:ring-ring transition-all"
          >
            <option value="student">Student Dashboard</option>
            <option value="recruiter">Recruiter Dashboard</option>
            <option value="officer">Placement Officer Dashboard</option>
            <option value="admin">Platform Admin Dashboard</option>
          </select>
        </div>

        {/* Remember Me */}
        <div className="flex items-center space-x-2 pt-1">
          <input
            type="checkbox"
            id="rememberMe"
            {...register("rememberMe")}
            className="h-4 w-4 rounded-sm border-input bg-background text-primary focus:ring-ring cursor-pointer"
          />
          <label htmlFor="rememberMe" className="text-xs text-muted-foreground select-none cursor-pointer">
            Remember this device for 30 days
          </label>
        </div>

        {/* Submit */}
        <Button type="submit" className="w-full mt-2 cursor-pointer" isLoading={isLoading}>
          Sign In to CareerOS
        </Button>
      </form>

      {/* Social Login Separator */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-900" />
        </div>
        <div className="relative flex justify-center text-[10px] uppercase">
          <span className="bg-background px-2.5 text-muted-foreground font-semibold">Or continue with</span>
        </div>
      </div>

      {/* Social Logins */}
      <div className="grid grid-cols-3 gap-2">
        <button
          onClick={() => {}}
          className="flex items-center justify-center py-2 px-3 border border-border bg-muted/40 hover:bg-muted rounded-lg text-xs hover:text-foreground transition-all cursor-pointer"
          title="Google Login"
        >
          <Chrome className="h-4 w-4 shrink-0 text-red-400" />
        </button>
        <button
          onClick={() => {}}
          className="flex items-center justify-center py-2 px-3 border border-border bg-muted/40 hover:bg-muted rounded-lg text-xs hover:text-foreground transition-all cursor-pointer"
          title="GitHub Login"
        >
          <Github className="h-4 w-4 shrink-0 text-slate-300" />
        </button>
        <button
          onClick={() => {}}
          className="flex items-center justify-center py-2 px-3 border border-border bg-muted/40 hover:bg-muted rounded-lg text-xs hover:text-foreground transition-all cursor-pointer"
          title="Microsoft Login"
        >
          {/* Simple Windows icon for Microsoft */}
          <span className="font-semibold text-sky-400 text-[10px]">Azure</span>
        </button>
      </div>

      {/* Bottom Link */}
      <p className="text-xs text-muted-foreground text-center mt-6">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="text-primary hover:underline font-semibold">
          Create Account
        </Link>
      </p>
    </div>
  );
}
