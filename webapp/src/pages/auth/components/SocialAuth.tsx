import {useEffect, useState} from "react";
import {Button} from "@/components/ui/button";
import {FcGoogle} from "react-icons/fc";
import {GoogleUser, isGoogleLoaded} from "@/account";
import {toast} from "@/components/ui/toast";

const showError = (message: string) => toast.add({title: "Authentication Error", description: message, type: "error"});

export const SocialAuth = () => {
    const [googleUser, setGoogleUser] = useState<GoogleUser | null>(null);

    useEffect(() => {
        const script = document.getElementById("google-gsi");
        const init = () => {
            if (!isGoogleLoaded()) return;
            const user = new GoogleUser(showError);
            setGoogleUser(user);
            user.prompt();
        };

        if (isGoogleLoaded()) {
            init();
            return;
        }
        script?.addEventListener("load", init);
        return () => script?.removeEventListener("load", init);
    }, []);

    return (
        <div className="space-y-4">
            <Button
                variant="outline"
                className="w-full"
                onClick={() => googleUser?.login()}
                disabled={!googleUser}
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
                    <span className="bg-background px-2 text-muted-foreground">
                        Or continue with email
                    </span>
                </div>
            </div>
        </div>
    );
}
