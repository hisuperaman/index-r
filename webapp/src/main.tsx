import {createRoot} from 'react-dom/client'
import '@/index.css'
import App from '@/App.tsx'
import {BrowserRouter} from "react-router";
import {QueryClient, QueryClientProvider} from "@tanstack/react-query";
import {ThemeProvider, UserProvider} from "@/contexts";
import {Toaster} from "@/components/ui/toast.tsx";

const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
    <ThemeProvider storageKey="indexr-ui-theme">
        <QueryClientProvider client={queryClient}>
            <UserProvider>
                <BrowserRouter>
                    <App/>
                    <Toaster/>
                </BrowserRouter>
            </UserProvider>
        </QueryClientProvider>
    </ThemeProvider>
)