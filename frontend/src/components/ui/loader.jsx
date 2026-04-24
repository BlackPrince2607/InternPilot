import { motion } from "framer-motion";

const _motion = motion;

export default function GooeyLoader({ phase = "uploading" }) {
  const isParsing = phase === "parsing";
  const label = isParsing ? "Analyzing resume…" : "Uploading resume…";

  return (
    <div className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 px-4 py-4">
      <div className="relative flex h-14 w-14 items-center justify-center">
        <motion.div
          animate={{
            scale: [1, 1.08, 1],
            opacity: [0.85, 1, 0.85],
            backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
          }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-0 rounded-full bg-[linear-gradient(90deg,#ef4444,#f97316,#eab308,#84cc16,#22c55e)] bg-[length:200%_200%] blur-lg"
        />
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "linear" }}
          className="absolute inset-1 rounded-full border border-white/10 border-t-cyan-300"
        />
        <motion.div
          animate={{
            scale: [0.9, 1.1, 0.9],
            boxShadow: [
              "0 0 0 0 rgba(239,68,68,0.28)",
              "0 0 0 10px rgba(34,197,94,0.08)",
              "0 0 0 0 rgba(239,68,68,0.28)",
            ],
          }}
          transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          className="relative h-6 w-6 rounded-full bg-gradient-to-br from-rose-500 via-amber-400 to-emerald-400"
        />
      </div>

      <div className="flex-1">
        <p className="text-sm font-semibold text-white">{label}</p>
        <p className="mt-1 text-sm text-slate-400">
          {isParsing
            ? "Extracting text, skills, and projects from your resume."
            : "Your file is being sent securely before parsing begins."}
        </p>
      </div>
    </div>
  );
}
