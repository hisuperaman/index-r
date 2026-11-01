import {Link, Outlet, useLocation} from "react-router";
import {Button} from "@/components/ui/button";
import {Badge} from "@/components/ui/badge";
import {Separator} from "@/components/ui/separator";
import {AppLogo} from "@/components";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {ArrowRight, RadioIcon} from "lucide-react";

export const AuthLayout = () => {
    const location = useLocation();

    const isLoginPath = location.pathname === Path.getExactRoutePath(RoutePaths.login);
    const headerLinkPath = isLoginPath ? Path.getExactRoutePath(RoutePaths.signup) : Path.getExactRoutePath(RoutePaths.login);
    const headerLinkText = isLoginPath ? "New to IndexR? Sign up" : "Already tracking research? Log in";
    const mobileLinkText = isLoginPath ? "Sign up" : "Log in";

    return (
        <div className="flex min-h-screen flex-col bg-background">
            <header
                className="sticky top-0 z-50 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur md:px-8 lg:px-12">
                <AppLogo/>
                <nav>
                    <Button
                        render={<Link to={headerLinkPath}/>}
                        nativeButton={false}
                        variant="outline"
                        className="hidden md:flex"
                    >
                        {headerLinkText} <ArrowRight className="ml-2 size-4"/>
                    </Button>

                    <Button
                        render={<Link to={headerLinkPath}/>}
                        nativeButton={false}
                        variant="outline"
                        size="sm"
                        className="md:hidden"
                    >
                        {mobileLinkText}
                    </Button>
                </nav>
            </header>

            <main className="flex flex-1 items-center py-8 sm:py-12">
                <div
                    className="container mx-auto grid w-full items-center gap-12 px-4 md:px-8 lg:grid-cols-2 lg:gap-16 lg:px-12">

                    <section className="order-2 flex flex-col justify-center space-y-8 lg:order-1 lg:max-w-xl">
                        <div className="space-y-6">
                            <Badge variant="secondary"
                                   className="w-fit text-xs font-medium uppercase tracking-wider py-1.5 px-3">
                                <RadioIcon className="mr-2 size-3.5 animate-pulse text-primary"/>
                                Live Research Tracking
                            </Badge>

                            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl lg:text-5xl lg:leading-[1.1]">
                                Find the right paper.
                                <br className="hidden sm:inline"/>
                                Never miss the <span className="text-primary">next</span> one.
                            </h1>

                            <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
                                IndexR searches only confirmed sources — published papers, verified datasets,
                                and peer-reviewed work. When something new lands on your tracked topics, you'll be the
                                first to know.
                            </p>
                        </div>

                        <Separator/>

                        <div className="grid grid-cols-2 gap-6 sm:flex sm:flex-wrap sm:gap-8">
                            <div className="space-y-1">
                                <div className="font-mono text-2xl font-bold tracking-tighter">
                                    {(1042817).toLocaleString()}
                                </div>
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                    Sources Indexed
                                </div>
                            </div>

                            <Separator orientation="vertical" className="hidden h-12 sm:block"/>

                            <div className="space-y-1">
                                <div className="font-mono text-2xl font-bold tracking-tighter">2.4M+</div>
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                    Papers Tracked
                                </div>
                            </div>

                            <Separator orientation="vertical" className="hidden h-12 sm:block"/>

                            <div className="col-span-2 space-y-1 sm:col-span-1">
                                <div className="font-mono text-2xl font-bold tracking-tighter">12k+</div>
                                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                                    Researchers
                                </div>
                            </div>
                        </div>
                    </section>

                    <section className="order-1 w-full max-w-md justify-self-center lg:order-2 lg:justify-self-end">
                        <Outlet/>
                    </section>

                </div>
            </main>
        </div>
    );
}