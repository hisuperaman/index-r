import type {FC, ReactNode} from "react";
import {isLoggedIn} from "@/account";
import {Navigate} from "./Navigate.tsx";


interface ProtectedProps {
    children: ReactNode
}

export const Protected: FC<ProtectedProps> = ({children}) =>
    isLoggedIn() ? <>{children}</> : Navigate.toLogin();

export const GuestOnly: FC<ProtectedProps> = ({children}) =>
    !isLoggedIn() ? <>{children}</> : Navigate.toDashboard();