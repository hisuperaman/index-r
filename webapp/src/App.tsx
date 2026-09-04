import '@/App.css';
import {Route, Routes} from "react-router";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {Home} from "@/pages";
import {Signup} from "@/pages/signup/signup";

function App() {
    return (
        <Routes>
            <Route
                path={Path.getExactRoutePath(RoutePaths.empty)}
                element={<Home/>}
            />

            <Route
                path="/signup"
                element={<Signup/>}
            />
        </Routes>
    )
}

export default App;