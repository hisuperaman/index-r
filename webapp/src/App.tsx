import '@/App.css';
import {lazy, Suspense} from "react";
import {Route, Routes} from "react-router";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {Home, Login, NotFound, Signup, VerifyEmail} from "@/pages";
import {AppLayout, AuthLayout} from "@/layouts";
import {GuestOnly, Protected} from "@/components";
import {Spinner} from "@/components/ui/spinner";

const WorkspacePage = lazy(() => import("@/pages/workspace").then((module) => ({default: module.WorkspacePage})));
const Settings = lazy(() => import("@/pages/settings").then((module) => ({default: module.Settings})));

const PageFallback = () => (
    <div className="flex flex-1 items-center justify-center">
        <Spinner className="size-5 text-muted-foreground"/>
    </div>
);

function App() {
    return (
        <Routes>
            <Route element={<Protected><AppLayout/></Protected>}>
                <Route path={Path.getExactRoutePath(RoutePaths.empty)} element={<Home/>}/>
                <Route
                    path={Path.getExactRoutePath(RoutePaths.workspace)}
                    element={<Suspense fallback={<PageFallback/>}><WorkspacePage/></Suspense>}
                />
                {[RoutePaths.settings, RoutePaths.settingsSection].map((path) => (
                    <Route
                        key={path}
                        path={Path.getExactRoutePath(path)}
                        element={<Suspense fallback={<PageFallback/>}><Settings/></Suspense>}
                    />
                ))}
            </Route>

            <Route element={<GuestOnly><AuthLayout/></GuestOnly>}>
                <Route
                    path={Path.getExactRoutePath(RoutePaths.signup)}
                    element={<Signup/>}
                />
                <Route
                    path={Path.getExactRoutePath(RoutePaths.login)}
                    element={<Login/>}
                />
            </Route>

            <Route path={Path.getRoutePath(RoutePaths.verifyEmail)} element={<VerifyEmail/>}/>

            <Route path="*" element={<NotFound/>}/>
        </Routes>
    )
}

export default App;
