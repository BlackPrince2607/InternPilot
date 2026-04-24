import { Component, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Eye, EyeOff, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

function AnimatedPlane() {
  const meshRef = useRef();

  useFrame(({ clock }) => {
    const mesh = meshRef.current;
    if (!mesh) return;

    const t = clock.getElapsedTime();
    mesh.rotation.x = Math.sin(t * 0.35) * 0.28;
    mesh.rotation.y = t * 0.18;
    mesh.rotation.z = Math.sin(t * 0.2) * 0.12;
    mesh.position.y = Math.sin(t * 0.7) * 0.18;
  });

  return (
    <mesh ref={meshRef} scale={[2.8, 2.8, 2.8]}>
      <planeGeometry args={[2.2, 2.2, 24, 24]} />
      <meshStandardMaterial
        color="#38bdf8"
        emissive="#0f172a"
        emissiveIntensity={1.35}
        wireframe
        roughness={0.45}
        metalness={0.2}
      />
    </mesh>
  );
}

class CanvasBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

export default function SignInFlow({ mode = "login", onSubmit }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const MotionCard = motion.div;

  const isSignup = mode === "signup";
  const heading = isSignup ? "Create your account" : "Welcome back";
  const subtext = isSignup
    ? "Set up your workspace in seconds."
    : "Sign in to continue to your workspace.";
  const buttonText = isSignup ? "Create account" : "Sign in";
  const bottomCopy = isSignup ? "Already have an account?" : "Don't have an account?";
  const bottomHref = isSignup ? "/login" : "/signup";
  const bottomLinkText = isSignup ? "Sign in" : "Create account";

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
      <CanvasBoundary
        fallback={
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.18),_transparent_45%),linear-gradient(135deg,#020617_0%,#0f172a_100%)]" />
        }
      >
        <div className="absolute inset-0">
          <Canvas camera={{ position: [0, 0, 4.5], fov: 45 }} dpr={[1, 1.5]}>
            <color attach="background" args={["#020617"]} />
            <ambientLight intensity={0.85} />
            <directionalLight position={[2, 2, 3]} intensity={1.8} color="#93c5fd" />
            <pointLight position={[-2, -1, 2]} intensity={1.1} color="#0ea5e9" />
            <pointLight position={[0, 2.5, 3]} intensity={0.8} color="#67e8f9" />
            <AnimatedPlane />
          </Canvas>
        </div>
      </CanvasBoundary>

      <div className="absolute inset-0 bg-black/60" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.14),_transparent_45%),radial-gradient(circle_at_bottom,_rgba(59,130,246,0.10),_transparent_55%)]" />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-10">
        <MotionCard
          initial={{ opacity: 0, y: 30, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.55, ease: "easeOut" }}
          whileHover={{ scale: 1.01 }}
          className="w-full max-w-md rounded-3xl border border-white/10 bg-white/8 p-8 shadow-[0_24px_90px_rgba(0,0,0,0.48)] backdrop-blur-2xl"
        >
          <div className="mb-8 text-center">
            <p className="text-xs font-medium uppercase tracking-[0.3em] text-cyan-300/80">
              InternPilot
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
              {heading}
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-300">{subtext}</p>
          </div>

          <div className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-200">
                Email
              </span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full rounded-2xl border border-white/10 bg-slate-900/60 px-4 py-3 text-white placeholder:text-slate-500 outline-none transition duration-200 focus:scale-[1.01] focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-400/20"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-200">
                Password
              </span>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full rounded-2xl border border-white/10 bg-slate-900/60 px-4 py-3 pr-12 text-white placeholder:text-slate-500 outline-none transition duration-200 focus:scale-[1.01] focus:border-cyan-400/50 focus:ring-2 focus:ring-cyan-400/20"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute inset-y-0 right-0 flex items-center px-4 text-slate-400 transition hover:text-cyan-300"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </label>

            <button
              type="button"
              onClick={onSubmit}
              className="group mt-2 flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition duration-200 hover:bg-cyan-300 hover:shadow-[0_0_28px_rgba(34,211,238,0.35)] active:scale-[0.99]"
            >
              {buttonText}
              <ArrowRight className="transition-transform group-hover:translate-x-0.5" size={18} />
            </button>
          </div>

          <p className="mt-6 text-center text-sm text-slate-400">
            {bottomCopy}{" "}
            <Link to={bottomHref} className="font-medium text-cyan-300 hover:text-cyan-200">
              {bottomLinkText}
            </Link>
          </p>
        </MotionCard>
      </div>
    </div>
  );
}
