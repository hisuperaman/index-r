import { createRoot } from "react-dom/client";
import "@/index.css";
import App from "@/App.tsx";
import { BrowserRouter } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, UserProvider } from "@/contexts";
import { GoogleOAuthProvider } from "@react-oauth/google";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
    <ThemeProvider storageKey="indexr-ui-theme">
        <QueryClientProvider client={queryClient}>
            <UserProvider>
				<GoogleOAuthProvider
    clientId="230178151265-44jlrt08ab8m6k53jbhe660l2ujqq5em.apps.googleusercontent.com"
                >
                
            
                    <BrowserRouter>
                        <App />
                    </BrowserRouter>
                </GoogleOAuthProvider>
            </UserProvider>
        </QueryClientProvider>
    </ThemeProvider>
);