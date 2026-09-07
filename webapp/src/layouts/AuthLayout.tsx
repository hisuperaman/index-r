import {useEffect, useRef} from "react";
import {useNavigate} from "react-router";
import {Button} from "@/components/ui/button";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";

type AuthLayoutProps = {
    children: React.ReactNode;
};

export function AuthLayout({children}: AuthLayoutProps) {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const navigate = useNavigate();

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

        type GraphNode = {
            x: number;
            y: number;
            vx: number;
            vy: number;
            r: number;
            pulse: number;
        };

        let nodes: GraphNode[] = [];
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

            for (const node of nodes) {
                node.x += node.vx;
                node.y += node.vy;

                if (node.x < -20) node.x = W + 20;
                if (node.x > W + 20) node.x = -20;

                if (node.y < -20) node.y = H + 20;
                if (node.y > H + 20) node.y = -20;

                node.pulse += 0.015;
            }

            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const a = nodes[i];
                    const b = nodes[j];

                    const dx = a.x - b.x;
                    const dy = a.y - b.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < LINK_DIST) {
                        const alpha =
                            (1 - distance / LINK_DIST) * 0.18;

                        canvasContext.strokeStyle =
                            `rgba(255,255,255,${alpha})`;

                        canvasContext.lineWidth = 0.6;
                        canvasContext.beginPath();
                        canvasContext.moveTo(a.x, a.y);
                        canvasContext.lineTo(b.x, b.y);
                        canvasContext.stroke();
                    }
                }
            }

            for (const node of nodes) {
                const glow =
                    0.35 + Math.sin(node.pulse) * 0.2;

                canvasContext.beginPath();
                canvasContext.fillStyle =
                    `rgba(244,244,242,${glow})`;

                canvasContext.arc(
                    node.x,
                    node.y,
                    node.r,
                    0,
                    Math.PI * 2
                );

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

            if (raf !== undefined) {
                cancelAnimationFrame(raf);
            }
        };
    }, []);

    const goToLogin = () => {
        navigate(
            Path.getExactRoutePath(RoutePaths.login)
        );
    };

    return (
        <div
            className="
                relative min-h-screen overflow-hidden
                bg-[#08090a] text-[#f4f4f2]
                font-[Inter,sans-serif]
            "
        >
            {/* Animated research graph */}
            <canvas
                ref={canvasRef}
                className="
                    pointer-events-none fixed inset-0
                    h-full w-full
                    motion-reduce:hidden
                "
            />

            {/* Background scrim */}
            <div
                className="
                    pointer-events-none fixed inset-0
                    bg-[radial-gradient(ellipse_900px_700px_at_78%_45%,rgba(255,255,255,0.045),transparent_65%),linear-gradient(180deg,rgba(8,9,10,0.25),rgba(8,9,10,0.72))]
                "
            />

            <div className="relative z-10 flex min-h-screen flex-col">
                {/* Header */}
                <header
                    className="
                        flex h-[92px] shrink-0
                        items-center justify-between
                        px-7 sm:px-12
                    "
                >
                    <Button
                        type="button"
                        variant="ghost"
                        onClick={goToLogin}
                        className="
                            h-auto gap-0 rounded-none p-0
                            font-[Space_Grotesk,sans-serif]
                            text-[22px] font-semibold
                            tracking-[-0.04em]
                            text-[#f4f4f2]
                            hover:bg-transparent
                            hover:text-[#f4f4f2]
                        "
                    >
                        <span
                            className="
                                mr-2 inline-block
                                h-[8px] w-[8px]
                                rounded-full
                                bg-[#f4f4f2]
                            "
                        />

                        Index
                        <span className="text-[#9a9b98]">
                            R
                        </span>
                    </Button>

                    <nav>
                        <Button
                            type="button"
                            variant="ghost"
                            onClick={goToLogin}
                            className="
                                h-auto rounded-none p-0
                                font-[Inter,sans-serif]
                                text-[12px] font-medium
                                text-[#9a9b98]
                                hover:bg-transparent
                                hover:text-[#f4f4f2]
                            "
                        >
                            Already tracking research? Log in →
                        </Button>
                    </nav>
                </header>

                {/* Page content */}
                <main className="flex flex-1 items-center">
                    {children}
                </main>
            </div>
        </div>
    );
}