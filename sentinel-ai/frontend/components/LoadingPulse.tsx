"use client";

export function LoadingPulse({ message = "AI Investigating..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div className="relative flex items-center justify-center">
        <div className="absolute w-16 h-16 rounded-full bg-cyan-500/20 animate-ping" />
        <div className="absolute w-12 h-12 rounded-full bg-cyan-500/30 animate-ping [animation-delay:0.2s]" />
        <div className="relative w-8 h-8 rounded-full bg-cyan-500 animate-pulse shadow-lg shadow-cyan-500/50" />
      </div>
      <div className="flex items-center gap-2">
        <span className="text-cyan-400 font-mono text-sm tracking-widest uppercase animate-pulse">
          {message}
        </span>
      </div>
      <div className="flex gap-1">
        {[0, 1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="w-1 bg-cyan-500 rounded-full animate-pulse"
            style={{
              height: `${8 + Math.sin(i) * 8 + 8}px`,
              animationDelay: `${i * 0.15}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="flex gap-4 p-4 animate-pulse">
      <div className="h-4 bg-slate-700 rounded w-32" />
      <div className="h-4 bg-slate-700 rounded w-24" />
      <div className="h-4 bg-slate-700 rounded w-40" />
      <div className="h-4 bg-slate-700 rounded w-20" />
    </div>
  );
}
