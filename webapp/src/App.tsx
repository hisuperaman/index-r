import '@/App.css';
import {Route, Routes} from "react-router";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {Home, NotFound, Signup, VerifyEmail, Login} from "@/pages";
import {AuthLayout} from "@/layouts";
import {GuestOnly} from "@/components";

function App() {
    return (
        <Routes>
            <Route
                path={Path.getExactRoutePath(RoutePaths.empty)}
                element={<Home/>}
            />

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
