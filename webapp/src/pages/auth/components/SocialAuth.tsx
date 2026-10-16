import {useEffect, useRef} from "react";
import {Button} from "@/components/ui/button";
import {FcGoogle} from "react-icons/fc";
import {GoogleUser} from "@/account";
import {toast} from "@/components/ui/toast";

export const SocialAuth = () => {
    const googleUser = useRef(new GoogleUser(
        (message) => toast.add({
            title: "Authentication Error",
            description: message,
            type: "error"
        })
    )).current;

    useEffect(() => {
        googleUser.prompt();
    }, [googleUser]);

    return (
        <div className="space-y-4">
            <Button
                variant="outline"
                className="w-full"
                onClick={googleUser.login}
                type="button"
            >
                <FcGoogle className="mr-2 size-5"/>
                Continue with Google
            </Button>

            <div className="relative">
                <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t"/>
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card px-2 text-muted-foreground">
                        Or continue with email
                    </span>
                </div>
            </div>
        </div>
    );
}