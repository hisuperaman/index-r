import {useEffect, useRef, useState} from "react";
import {useNavigate} from "react-router";
import {useForm} from "react-hook-form";
import type {RegisterBody} from "@/definitions/RequestBody";
import {useRegister} from "@/queries/user";
import {Input} from "@/components/ui/input";
import {Button} from "@/components/ui/button";

type SignupFormValues = {
    name: string;
    email: string;
    pass: string;
    pass2: string;
};

export function Signup() {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const navigate = useNavigate();
    const register = useRegister();

    const [filesCount, setFilesCount] = useState(1042817);

    const form = useForm<SignupFormValues>({
        defaultValues: {
            name: "",
            email: "",
            pass: "",
            pass2: "",
        },
    });

    // ---- animated index-graph background ----
    useEffect(() => {
        const canvas = canvasRef.current;

        if (!canvas) return;

        const context = canvas.getContext("2d");

        if (!context) return;
        const canvasElement = canvas;
        const canvasContext = context;

        const LINK_DIST = 130;
        const reduceMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

        let W = 0;
        let H = 0;

        type Node = {
            x: number;
            y: number;
            vx: number;
            vy: number;
            r: number;
            pulse: number;
        };

        let nodes: Node[] = [];
        let raf: number | undefined;

        function resize() {
            W = canvasElement.width = canvasElement.offsetWidth;
            H = canvasElement.height = canvasElement.offsetHeight;

            const count = Math.max(
                35,
                Math.min(110, Math.floor((W * H) / 16000))
            );

            nodes = Array.from({length: count}, () => ({
                x: Math.random() * W,
                y: Math.random() * H,
                vx: (Math.random() - 0.5) * 0.28,
                vy: (Math.random() - 0.5) * 0.28,
                r: Math.random() * 1.4 + 0.6,
                pulse: Math.random() * Math.PI * 2,
            }));
        }

        function step() {
            canvasContext.clearRect(0, 0, W, H);

            for (const n of nodes) {
                n.x += n.vx;
                n.y += n.vy;

                if (n.x < -20) n.x = W + 20;
                if (n.x > W + 20) n.x = -20;
                if (n.y < -20) n.y = H + 20;
                if (n.y > H + 20) n.y = -20;

                n.pulse += 0.015;
            }

            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const a = nodes[i];
                    const b = nodes[j];

                    const dx = a.x - b.x;
                    const dy = a.y - b.y;
                    const d = Math.sqrt(dx * dx + dy * dy);

                    if (d < LINK_DIST) {
                        const alpha = (1 - d / LINK_DIST) * 0.18;

                        canvasContext.strokeStyle = `rgba(255,255,255,${alpha})`;
                        canvasContext.lineWidth = 0.6;
                        canvasContext.beginPath();
                        canvasContext.moveTo(a.x, a.y);
                        canvasContext.lineTo(b.x, b.y);
                        canvasContext.stroke();
                    }
                }
            }

            for (const n of nodes) {
                const glow = 0.35 + Math.sin(n.pulse) * 0.2;

                canvasContext.beginPath();
                canvasContext.fillStyle = `rgba(244,244,242,${glow})`;
                canvasContext.arc(n.x, n.y, n.r, 0, Math.PI * 2);
                canvasContext.fill();
            }

            if (!reduceMotion) {
                raf = requestAnimationFrame(step);
            }
        }

        resize();
        step();

        window.addEventListener("resize", resize);

        return () => {
            window.removeEventListener("resize", resize);

            if (raf) {
                cancelAnimationFrame(raf);
            }
        };
    }, []);

    // ---- live sources counter ----
    useEffect(() => {
        const id = setInterval(() => {
            setFilesCount(
                (c) => c + Math.floor(Math.random() * 9) + 1
            );
        }, 850);

        return () => clearInterval(id);
    }, []);

    const handleSubmit = (values: SignupFormValues) => {
        if (!values.name.trim()) {
            alert("Please enter your full name.");
            return;
        }

        if (!values.email.trim()) {
            alert("Please enter your email.");
            return;
        }

        if (!values.pass) {
            alert("Please enter a password.");
            return;
        }

        if (values.pass !== values.pass2) {
            alert("Passwords do not match.");
            return;
        }

        const nameParts = values.name.trim().split(/\s+/);

        const data: RegisterBody = {
            email: values.email.trim(),
            first_name: nameParts[0] || "",
            last_name: nameParts.slice(1).join(" "),
            password1: values.pass,
            password2: values.pass2,
        };

        register.mutate(data);
    };

    return (
        <div className="ixr-root">
            <style>{`
                .ixr-root{
                  --bg:#08090a;
                  --panel:#111213;
                  --panel-2:#0d0e0f;
                  --border:#2a2b2c;
                  --border-soft:#1c1d1e;
                  --ink:#f4f4f2;
                  --ink-dim:#9a9b98;
                  --ink-faint:#606160;
                  --white:#ffffff;

                  position:relative;
                  min-height:100vh;
                  width:100%;
                  background:var(--bg);
                  color:var(--ink);
                  font-family:'Inter', sans-serif;
                  overflow:hidden;
                }

                .ixr-root *{ box-sizing:border-box; }

                .ixr-canvas{
                  position:absolute;
                  inset:0;
                  width:100%;
                  height:100%;
                  display:block;
                }

                .ixr-scrim{
                  position:absolute;
                  inset:0;
                  background:
                    radial-gradient(
                      ellipse 900px 700px at 78% 45%,
                      rgba(8,9,10,0.55) 0%,
                      rgba(8,9,10,0.15) 45%,
                      transparent 70%
                    ),
                    linear-gradient(
                      180deg,
                      rgba(8,9,10,0.75) 0%,
                      rgba(8,9,10,0.15) 18%,
                      rgba(8,9,10,0.15) 82%,
                      rgba(8,9,10,0.85) 100%
                    );
                  pointer-events:none;
                }

                .ixr-shell{
                  position:relative;
                  z-index:2;
                  min-height:100vh;
                  display:flex;
                  flex-direction:column;
                }

                .ixr-header{
                  display:flex;
                  align-items:center;
                  justify-content:space-between;
                  padding:28px 48px;
                }

                .ixr-brand{
                  display:flex;
                  align-items:baseline;
                  gap:9px;
                  font-family:'Space Grotesk', sans-serif;
                  font-weight:600;
                  font-size:19px;
                  letter-spacing:0.01em;
                  background:none;
                  border:none;
                  color:var(--ink);
                  cursor:pointer;
                  padding:0;
                }

                .ixr-brand .mark{
                  width:9px;
                  height:9px;
                  background:var(--white);
                  display:inline-block;
                  transform:rotate(45deg);
                }

                .ixr-brand .r{
                  color:var(--ink-dim);
                  font-weight:500;
                }

                .ixr-header nav{
                  font-family:'JetBrains Mono', monospace;
                  font-size:12.5px;
                  color:var(--ink-faint);
                }

                .ixr-header nav button{
                  background:none;
                  border:none;
                  font-family:'JetBrains Mono', monospace;
                  font-size:12.5px;
                  color:var(--ink-dim);
                  cursor:pointer;
                  border-bottom:1px solid transparent;
                  transition:border-color .15s ease, color .15s ease;
                  padding:0;
                }

                .ixr-header nav button:hover{
                  color:var(--ink);
                  border-color:var(--ink-dim);
                }

                .ixr-main{
                  flex:1;
                  display:grid;
                  grid-template-columns:1.15fr 0.85fr;
                  align-items:center;
                  gap:40px;
                  padding:20px 48px 56px;
                }

                .ixr-copy{
                  max-width:520px;
                  padding-right:20px;
                }

                .ixr-eyebrow{
                  display:flex;
                  align-items:center;
                  gap:10px;
                  font-family:'JetBrains Mono', monospace;
                  font-size:12px;
                  color:var(--ink-faint);
                  margin-bottom:26px;
                }

                .ixr-live-dot{
                  width:6px;
                  height:6px;
                  border-radius:50%;
                  background:var(--white);
                  animation:ixr-pulse 2.2s ease-out infinite;
                }

                @keyframes ixr-pulse{
                  0%{
                    box-shadow:0 0 0 0 rgba(255,255,255,0.35);
                  }
                  70%{
                    box-shadow:0 0 0 7px rgba(255,255,255,0);
                  }
                  100%{
                    box-shadow:0 0 0 0 rgba(255,255,255,0);
                  }
                }

                .ixr-copy h1{
                  font-family:'Space Grotesk', sans-serif;
                  font-weight:600;
                  font-size:clamp(38px, 4.4vw, 60px);
                  line-height:1.04;
                  letter-spacing:-0.01em;
                  margin:0 0 22px;
                }

                .ixr-copy h1 em{
                  font-style:normal;
                  color:var(--ink-dim);
                }

                .ixr-lede{
                  font-size:16.5px;
                  line-height:1.6;
                  color:var(--ink-dim);
                  max-width:440px;
                  margin:0 0 38px;
                }

                .ixr-stat-row{
                  display:flex;
                  gap:36px;
                  padding-top:26px;
                  border-top:1px solid var(--border-soft);
                }

                .ixr-stat{
                  font-family:'JetBrains Mono', monospace;
                }

                .ixr-stat .num{
                  font-size:20px;
                  color:var(--ink);
                  font-weight:500;
                  letter-spacing:-0.01em;
                }

                .ixr-stat .label{
                  font-size:11.5px;
                  color:var(--ink-faint);
                  margin-top:5px;
                }

                .ixr-card-wrap{
                  display:flex;
                  justify-content:center;
                }

                .ixr-card{
                  width:100%;
                  max-width:392px;
                  background:linear-gradient(
                    180deg,
                    var(--panel) 0%,
                    var(--panel-2) 100%
                  );
                  border:1px solid var(--border);
                  padding:38px 34px 32px;
                  position:relative;
                }

                .ixr-card::before{
                  content:"";
                  position:absolute;
                  top:-1px;
                  left:-1px;
                  width:16px;
                  height:16px;
                  border-top:1px solid var(--white);
                  border-left:1px solid var(--white);
                  opacity:0.55;
                }

                .ixr-card::after{
                  content:"";
                  position:absolute;
                  bottom:-1px;
                  right:-1px;
                  width:16px;
                  height:16px;
                  border-bottom:1px solid var(--white);
                  border-right:1px solid var(--white);
                  opacity:0.55;
                }

                .ixr-card h2{
                  font-family:'Space Grotesk', sans-serif;
                  font-size:23px;
                  font-weight:600;
                  margin:0 0 6px;
                }

                .ixr-card .sub{
                  font-size:13.5px;
                  color:var(--ink-faint);
                  margin:0 0 28px;
                }

                .ixr-field{
                  margin-bottom:18px;
                }

                .ixr-field label{
                  display:block;
                  font-family:'JetBrains Mono', monospace;
                  font-size:11px;
                  color:var(--ink-faint);
                  margin-bottom:8px;
                  letter-spacing:0.01em;
                }

                .ixr-field input{
                  width:100%;
                  background:#0a0b0c;
                  border:1px solid var(--border);
                  color:var(--ink);
                  font-family:'Inter', sans-serif;
                  font-size:14.5px;
                  padding:12px 13px;
                  outline:none;
                  transition:border-color .15s ease, background .15s ease;
                }

                .ixr-field input::placeholder{
                  color:#4c4d4c;
                }

                .ixr-field input:focus{
                  border-color:var(--ink-dim);
                  background:#0d0e0f;
                }

                .ixr-field input:focus-visible{
                  outline:1.5px solid var(--white);
                  outline-offset:1px;
                }

                .ixr-row2{
                  display:flex;
                  gap:12px;
                }

                .ixr-row2 .ixr-field{
                  flex:1;
                }

                .ixr-submit{
                  width:100%;
                  background:var(--white);
                  color:#0a0a0a;
                  border:none;
                  font-family:'Inter', sans-serif;
                  font-weight:600;
                  font-size:14.5px;
                  padding:13px 0;
                  margin-top:8px;
                  cursor:pointer;
                  transition:background .15s ease, transform .1s ease;
                }

                .ixr-submit:hover{
                  background:#e4e4e2;
                }

                .ixr-submit:active{
                  transform:scale(0.995);
                }

                .ixr-submit:focus-visible{
                  outline:2px solid var(--white);
                  outline-offset:2px;
                }

                .ixr-submit:disabled{
                  opacity:0.6;
                  cursor:not-allowed;
                }

                .ixr-fineprint{
                  font-size:11.5px;
                  color:var(--ink-faint);
                  line-height:1.55;
                  margin-top:16px;
                }

                .ixr-fineprint button{
                  background:none;
                  border:none;
                  padding:0;
                  cursor:pointer;
                  color:var(--ink-dim);
                  font-size:11.5px;
                  font-family:'Inter', sans-serif;
                }

                .ixr-divider{
                  display:flex;
                  align-items:center;
                  gap:12px;
                  margin:24px 0 18px;
                }

                .ixr-divider .line{
                  flex:1;
                  height:1px;
                  background:var(--border-soft);
                }

                .ixr-divider span{
                  font-family:'JetBrains Mono', monospace;
                  font-size:10.5px;
                  color:var(--ink-faint);
                }

                .ixr-switch{
                  text-align:center;
                  font-size:13.5px;
                  color:var(--ink-faint);
                }

                .ixr-switch button{
                  background:none;
                  border:none;
                  padding:0;
                  cursor:pointer;
                  color:var(--ink);
                  font-size:13.5px;
                  font-family:'Inter', sans-serif;
                  border-bottom:1px solid var(--ink-dim);
                }

                .ixr-status{
                  margin-top:12px;
                  font-size:12px;
                  line-height:1.4;
                  font-family:'JetBrains Mono', monospace;
                }

                .ixr-error{
                  color:#ff8f8f;
                }

                .ixr-success{
                  color:#a8e6a8;
                }

                @media (max-width: 880px){
                  .ixr-main{
                    grid-template-columns:1fr;
                    padding:10px 24px 40px;
                  }

                  .ixr-header{
                    padding:22px 24px;
                  }

                  .ixr-copy{
                    max-width:100%;
                    padding-right:0;
                    order:2;
                  }

                  .ixr-card-wrap{
                    order:1;
                    margin-bottom:8px;
                  }

                  .ixr-stat-row{
                    display:none;
                  }

                  .ixr-copy h1{
                    font-size:clamp(30px, 8vw, 40px);
                  }
                }

                @media (prefers-reduced-motion: reduce){
                  .ixr-live-dot{
                    animation:none;
                  }

                  .ixr-canvas{
                    display:none;
                  }
                }
            `}</style>

            <link rel="preconnect" href="https://fonts.googleapis.com"/>
            <link
                href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
                rel="stylesheet"
            />

            <canvas
                ref={canvasRef}
                className="ixr-canvas"
            />

            <div className="ixr-scrim"/>

            <div className="ixr-shell">
                <header className="ixr-header">
                    <button
                        className="ixr-brand"
                        onClick={() => navigate("/login")}
                        type="button"
                    >
                        <span className="mark"/>
                        Index<span className="r">R</span>
                    </button>

                    <nav>
                        <button
                            onClick={() => navigate("/login")}
                            type="button"
                        >
                            Already tracking research? Log in →
                        </button>
                    </nav>
                </header>

                <main className="ixr-main">
                    <div className="ixr-copy">
                        <div className="ixr-eyebrow">
                            <span className="ixr-live-dot"/>
                            watching your research topics — live
                        </div>

                        <h1>
                            Find the right paper.
                            <br/>
                            Never miss the <em>next</em> one.
                        </h1>

                        <p className="ixr-lede">
                            IndexR searches only confirmed sources —
                            published papers, verified datasets,
                            peer-reviewed work — and surfaces what's
                            actually relevant to your research. When
                            something new lands on a topic you're tracking,
                            it tells you first.
                        </p>

                        <div className="ixr-stat-row">
                            <div className="ixr-stat">
                                <div className="num">
                                    {filesCount.toLocaleString("en-US")}
                                </div>
                                <div className="label">
                                    sources verified
                                </div>
                            </div>

                            <div className="ixr-stat">
                                <div className="num">18,204</div>
                                <div className="label">
                                    topics tracked live
                                </div>
                            </div>

                            <div className="ixr-stat">
                                <div className="num">0</div>
                                <div className="label">
                                    unverified sources used
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="ixr-card-wrap">
                        <div className="ixr-card">
                            <h2>Create your account</h2>

                            <div className="sub">
                                Start tracking your research in under two minutes.
                            </div>

                            <form
                                onSubmit={form.handleSubmit(handleSubmit)}
                            >
                                <div className="ixr-field">
                                    <label htmlFor="name">
                                        Full name
                                    </label>

                                    <Input
                                        id="name"
                                        type="text"
                                        placeholder="Ava Chen"
                                        autoComplete="name"
                                        {...form.register("name")}
                                    />
                                </div>

                                <div className="ixr-field">
                                    <label htmlFor="email">
                                        Work email
                                    </label>

                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="ava@company.com"
                                        autoComplete="email"
                                        {...form.register("email")}
                                    />
                                </div>

                                <div className="ixr-row2">
                                    <div className="ixr-field">
                                        <label htmlFor="pass">
                                            Password
                                        </label>

                                        <Input
                                            id="pass"
                                            type="password"
                                            placeholder="••••••••"
                                            autoComplete="new-password"
                                            {...form.register("pass")}
                                        />
                                    </div>

                                    <div className="ixr-field">
                                        <label htmlFor="pass2">
                                            Confirm
                                        </label>

                                        <Input
                                            id="pass2"
                                            type="password"
                                            placeholder="••••••••"
                                            autoComplete="new-password"
                                            {...form.register("pass2")}
                                        />
                                    </div>
                                </div>

                                <Button
                                    className="ixr-submit"
                                    type="submit"
                                    disabled={register.isPending}
                                >
                                    {register.isPending
                                        ? "Creating account..."
                                        : "Create account"}
                                </Button>

                                {register.isError && (
                                    <div className="ixr-status ixr-error">
                                        Registration failed. Please check
                                        your details and try again.
                                    </div>
                                )}

                                {register.isSuccess && (
                                    <div className="ixr-status ixr-success">
                                        {register.data.detail}
                                    </div>
                                )}

                                <div className="ixr-fineprint">
                                    By continuing you agree to IndexR's{" "}
                                    <button type="button">
                                        Terms
                                    </button>{" "}
                                    and{" "}
                                    <button type="button">
                                        Privacy Policy
                                    </button>.
                                </div>
                            </form>

                            <div className="ixr-divider">
                                <div className="line"/>
                                <span>OR</span>
                                <div className="line"/>
                            </div>

                            <div className="ixr-switch">
                                Already have an account?{" "}
                                <button
                                    type="button"
                                    onClick={() => navigate("/login")}
                                >
                                    Log in
                                </button>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}