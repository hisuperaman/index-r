import '@/App.css';
import {Route, Routes} from "react-router";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {Home} from "@/pages";

function App() {
	return (
		<Routes>
			<Route path={Path.getExactRoutePath(RoutePaths.empty)} element={<Home/>}/>
		</Routes>
	)
}

export default App;
