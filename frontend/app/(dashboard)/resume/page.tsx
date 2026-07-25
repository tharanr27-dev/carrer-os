"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  UploadCloud,
  FileText,
  AlertTriangle,
  CheckCircle,
  FileCode,
  TrendingUp,
  History,
  ArrowRight,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { usePathname, useRouter } from "next/navigation";

const mockVersions = [
  { id: "v2", name: "v2.0 - Optimized (Current)", date: "Jul 2, 2026", score: 87, active: true },
  { id: "v1.1", name: "v1.1 - Added System Design", date: "Jun 30, 2026", score: 79, active: false },
  { id: "v1.0", name: "v1.0 - Original Import", date: "Jun 25, 2026", score: 65, active: false },
];

export default function ResumeCenter() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=resume");
    }
  }, [pathname, router]);

  const [hasUploaded, setHasUploaded] = React.useState(true);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadProgress, setUploadProgress] = React.useState(0);
  const [activeVersion, setActiveVersion] = React.useState("v2");
  const [fileName, setFileName] = React.useState("Alex_Morgan_Resume_v2.pdf");

  const startMockUpload = () => {
    setIsUploading(true);
    setUploadProgress(0);
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setIsUploading(false);
            setHasUploaded(true);
            setFileName("New_Uploaded_Resume_Optimized.pdf");
          }, 500);
          return 100;
        }
        return prev + 10;
      });
    }, 150);
  };

  const selectedVersionData = mockVersions.find((v) => v.id === activeVersion) || mockVersions[0];

  return (
    <div className="space-y-8 text-left">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Resume Center</h1>
          <p className="text-sm text-muted-foreground">
            Optimize your resume for applicant tracking systems (ATS) using AI.
          </p>
        </div>
        {hasUploaded && (
          <Button variant="outline" onClick={() => setHasUploaded(false)} className="cursor-pointer">
            Upload New Version
          </Button>
        )}
      </div>

      {/* Main Grid split: Left is Document Preview / Upload, Right is ATS Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Upload or Preview Document */}
        <div className="lg:col-span-7 space-y-6">
          {!hasUploaded ? (
            <Card className="border-dashed border-2 hover:border-primary/50 transition-colors bg-card/20 min-h-[400px] flex items-center justify-center">
              <CardContent className="flex flex-col items-center justify-center p-8 text-center space-y-4">
                {isUploading ? (
                  <div className="w-64 space-y-3">
                    <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 text-primary flex items-center justify-center animate-spin border-2 border-primary border-t-transparent" />
                    <p className="text-xs font-semibold text-slate-200">Analyzing layout elements...</p>
                    <Progress value={uploadProgress} indicatorClassName="bg-primary" />
                    <span className="text-[10px] text-muted-foreground font-mono">{uploadProgress}% uploaded</span>
                  </div>
                ) : (
                  <>
                    <div className="p-4 bg-primary/10 rounded-full text-primary animate-float">
                      <UploadCloud className="h-8 w-8" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-slate-200">Drag and drop your resume here</p>
                      <p className="text-xs text-muted-foreground">Supports PDF, DOCX, or TXT up to 5MB</p>
                    </div>
                    <Button onClick={startMockUpload} className="cursor-pointer">
                      Browse Files
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          ) : (
            /* Document Paper Sheet Preview */
            <Card className="border border-border bg-card text-card-foreground shadow-2xl relative overflow-hidden min-h-[600px] flex flex-col font-serif">
              {/* Paper overlay styling */}
              <div className="p-8 md:p-12 space-y-6 text-left flex-1 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-muted/30 to-card">
                {/* Header */}
                <div className="text-center border-b border-border pb-4 space-y-1.5 font-sans">
                  <h2 className="text-2xl font-bold text-foreground tracking-tight">Alex Morgan</h2>
                  <p className="text-[10px] text-muted-foreground font-medium">
                    San Francisco, CA • alex.morgan@stanford.edu • github.com/alexmorgan • linkedin.com/in/alexmorgan
                  </p>
                </div>

                {/* Section: Education */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold tracking-wider text-foreground border-b border-border pb-0.5 uppercase font-sans">
                    Education
                  </h3>
                  <div className="flex justify-between text-xs font-sans">
                    <div>
                      <span className="font-bold">Stanford University</span> — BS in Computer Science
                    </div>
                    <div className="text-muted-foreground">Expected Jun 2027</div>
                  </div>
                </div>

                {/* Section: Experience */}
                <div className="space-y-4">
                  <h3 className="text-xs font-bold tracking-wider text-foreground border-b border-border pb-0.5 uppercase font-sans">
                    Work Experience
                  </h3>
                  
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-sans">
                      <div>
                        <span className="font-bold">Frontend Engineer Intern</span> — Linear
                      </div>
                      <div className="text-muted-foreground">Jun 2025 – Sep 2025</div>
                    </div>
                    <ul className="list-disc pl-5 text-[11px] text-muted-foreground space-y-1 leading-relaxed">
                      <li>Designed and built responsive settings layout modules using React 19, improving page load speeds by 15%.</li>
                      <li>Collaborated with design leads to refactor component libraries, enforcing strict TypeScript definitions.</li>
                    </ul>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs font-sans">
                      <div>
                        <span className="font-bold">Software Engineering Intern</span> — Local Startup
                      </div>
                      <div className="text-muted-foreground">Jan 2025 – Apr 2025</div>
                    </div>
                    <ul className="list-disc pl-5 text-[11px] text-muted-foreground space-y-1 leading-relaxed">
                      <li>Integrated RESTful APIs using Node.js/Express, accelerating internal administration lookup queries.</li>
                      <li>Managed CI/CD deployment pipelines, decreasing regression fail-rates.</li>
                    </ul>
                  </div>
                </div>

                {/* Section: Projects */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold tracking-wider text-foreground border-b border-border pb-0.5 uppercase font-sans">
                    Key Projects
                  </h3>
                  <div className="space-y-1.5">
                    <p className="text-xs">
                      <span className="font-bold font-sans">CareerOS AI Dashboard</span> (Next.js, TypeScript) — Build complex role-based routing systems.
                    </p>
                    <p className="text-xs">
                      <span className="font-bold font-sans">Collaborative Editor</span> (WebSockets, Rust) — Real-time editor with sync mechanisms.
                    </p>
                  </div>
                </div>
              </div>
              <CardFooter className="bg-muted/50 border-t border-border px-6 py-4 flex items-center justify-between font-sans text-xs text-muted-foreground">
                <div className="flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="font-semibold truncate max-w-[200px]">{fileName}</span>
                </div>
                <span>Size: 1.2 MB</span>
              </CardFooter>
            </Card>
          )}
        </div>

        {/* Right Column: ATS Score & Diagnostics */}
        <div className="lg:col-span-5 space-y-6">
          {/* Diagnostic score panel */}
          <Card className="border border-indigo-500/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <TrendingUp className="h-4.5 w-4.5 text-primary" /> ATS Diagnostics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Radial Score Gauge */}
              <div className="flex items-center space-x-6">
                <div className="relative flex items-center justify-center h-20 w-20 shrink-0">
                  <svg className="w-20 h-20 transform -rotate-90">
                    <circle cx="40" cy="40" r="32" stroke="currentColor" className="text-muted/20" strokeWidth="5" fill="transparent" />
                    <circle
                      cx="40"
                      cy="40"
                      r="32"
                      stroke="currentColor"
                      className="text-primary"
                      strokeWidth="5"
                      fill="transparent"
                      strokeDasharray={`${2 * Math.PI * 32}`}
                      strokeDashoffset={`${2 * Math.PI * 32 * (1 - selectedVersionData.score / 100)}`}
                    />
                  </svg>
                  <span className="absolute text-base font-bold">{selectedVersionData.score}</span>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-200">ATS Match Index</h4>
                  <p className="text-xs text-muted-foreground mt-0.5 leading-normal">
                    Matches 92% of common applicant sorting systems. Add target keywords to break into the top 5%.
                  </p>
                </div>
              </div>

              {/* Missing Keywords Section */}
              <div className="space-y-2 border-t border-border pt-4">
                <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Missing Recruiter Keywords</span>
                <div className="flex flex-wrap gap-1.5">
                  {["Tailwind CSS v4", "Docker", "Server Actions", "Redis", "CDN"].map((word) => (
                    <span
                      key={word}
                      className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-400 font-semibold cursor-help"
                      title={`This keyword appears in 12 matching job descriptions but is missing in your CV`}
                    >
                      <AlertTriangle className="h-3 w-3 shrink-0" /> {word}
                    </span>
                  ))}
                </div>
              </div>

              {/* Improvement Suggestions */}
              <div className="space-y-3 border-t border-border pt-4 text-xs leading-relaxed">
                <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">ATS Improvement Plan</span>
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <Info className="h-4 w-4 text-violet-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold text-slate-200">Quantify Experience Impact</p>
                      <p className="text-muted-foreground mt-0.5">Instead of &quot;refactor component libraries&quot;, use: &quot;refactored component libraries, decreasing rendering lag by 15% across core modules&quot;.</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Info className="h-4 w-4 text-violet-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-bold text-slate-200">Incorporate Cloud Skills</p>
                      <p className="text-muted-foreground mt-0.5">Your project details miss environment keywords. List Docker or AWS alongside your Rust Collaborative Editor description.</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Resume Version History List */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <History className="h-4.5 w-4.5 text-primary" /> Version Control
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {mockVersions.map((v) => (
                <div
                  key={v.id}
                  onClick={() => {
                    setActiveVersion(v.id);
                    if (v.id === "v2") {
                      setFileName("Alex_Morgan_Resume_v2.pdf");
                    } else if (v.id === "v1.1") {
                      setFileName("Alex_Morgan_Resume_SystemDesign.pdf");
                    } else {
                      setFileName("Alex_Morgan_Original_Import.docx");
                    }
                  }}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg border text-xs cursor-pointer transition-all",
                    activeVersion === v.id
                      ? "bg-primary/10 border-primary text-foreground font-semibold"
                      : "bg-muted/40 border-muted text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <div className="flex items-center space-x-2.5">
                    <FileCode className={cn("h-4 w-4 shrink-0", activeVersion === v.id ? "text-primary" : "text-muted-foreground")} />
                    <div className="text-left">
                      <p className={activeVersion === v.id ? "text-slate-100" : ""}>{v.name}</p>
                      <p className="text-[10px] text-muted-foreground">{v.date}</p>
                    </div>
                  </div>
                  <span className={cn("text-xs font-bold px-1.5 py-0.5 rounded-sm", activeVersion === v.id ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground")}>
                    {v.score} pts
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
