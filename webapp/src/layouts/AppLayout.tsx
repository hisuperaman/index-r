import {Outlet} from "react-router";

export const AppLayout = () => (
    <div className="flex min-h-svh flex-col bg-background">
        <Outlet/>
    </div>
);
