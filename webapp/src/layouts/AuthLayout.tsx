import {Link, Outlet} from "react-router";
import {Button} from "@/components/ui/button";
import {AppLogo} from "@/components";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {ArrowRight, RadioIcon} from "lucide-react";
import {Separator} from "@/components/ui/separator.tsx";

export const AuthLayout = () => (
    <div className="flex min-h-screen flex-col">
        <header className="flex h-16 items-center justify-between border-b px-6 lg:px-12">
            <AppLogo/>
            <nav>
                <Button
                    render={<Link to={Path.getExactRoutePath(RoutePaths.login)}/>}
                    nativeButton={false}
                    variant="outline"
                >
                    Already tracking research? Log in <ArrowRight/>
                </Button>
            </nav>
        </header>

        <main className="flex-1 py-12">
            <div className="container mx-auto grid items-center gap-12 px-6 lg:grid-cols-2 lg:px-12">

                <section className="order-2 max-w-xl lg:order-1">
                    <div
                        className="mb-6 flex items-center gap-2 text-xs font-medium uppercase text-muted-foreground">
                        <RadioIcon/>
                        watching your research topics — live
                    </div>

                    <h1 className="text-4xl font-bold tracking-tight lg:text-5xl">
                        Find the right paper.
                        <br/>
                        Never miss the <span className="text-muted-foreground">next</span> one.
                    </h1>

                    <p className="mt-4 leading-relaxed text-muted-foreground">
                        IndexR searches only confirmed sources — published papers, verified datasets,
                        peer-reviewed work — and surfaces what's actually relevant to your research. When
                        something new lands on a topic you're tracking, it tells you first.
                    </p>

                    <Separator className={'my-8'}/>

                    <div className="flex flex-wrap gap-8">
                        <div>
                            <div className="font-mono text-xl font-semibold">{(1042817).toLocaleString()}</div>
                            <div className="text-xs uppercase text-muted-foreground">sources indexed</div>
                        </div>

                        <Separator orientation={'vertical'}/>

                        <div>
                            <div className="font-mono text-xl font-semibold">2.4M+</div>
                            <div className="text-xs uppercase text-muted-foreground">papers tracked</div>
                        </div>

                        <Separator orientation={'vertical'}/>

                        <div>
                            <div className="font-mono text-xl font-semibold">12k+</div>
                            <div className="text-xs uppercase text-muted-foreground">researchers</div>
                        </div>
                    </div>
                </section>

                <section className="order-1 w-full max-w-md justify-self-center lg:order-2 lg:justify-self-end">
                    <Outlet/>
                </section>

            </div>
        </main>
    </div>
)