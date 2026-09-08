import { Link } from "react-router-dom";

export const Home = () => {
    return (
        <div>
            <Link
                to="/login"
                className="inline-block bg-blue-600 px-6 py-3 text-white"
            >
                LOGIN
            </Link>
        </div>
    );
};