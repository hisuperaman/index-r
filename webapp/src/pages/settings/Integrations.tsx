import {type FormEvent, useState} from "react";
import {KeyRoundIcon, PlusIcon, TriangleAlertIcon} from "lucide-react";
import {ConfirmDialog, CopyButton} from "@/components";
import {Button} from "@/components/ui/button";
import {Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle} from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {Field, FieldError, FieldLabel} from "@/components/ui/field";
import {Input} from "@/components/ui/input";
import {Skeleton} from "@/components/ui/skeleton";
import {Spinner} from "@/components/ui/spinner";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs";
import {toast} from "@/components/ui/toast";
import type {ApiToken} from "@/models";
import {useApiTokens, useCreateApiToken, useMcpServer, useRevokeApiToken} from "@/queries";
import {formatRelativeTime} from "@/utils";

const TOOLS = [
    "Search papers, including your private uploads",
    "Ask questions in a workspace and get cited answers",
    "List, create and organise workspaces and their papers",
];

const Snippet = ({code}: { code: string }) => (
    <div className="relative min-w-0">
        <pre className="max-h-48 overflow-auto rounded-xl border bg-muted/50 p-3 pr-10 font-mono text-xs leading-relaxed whitespace-pre-wrap break-all">
            {code}
        </pre>
        <div className="absolute top-1.5 right-1.5">
            <CopyButton text={code} label="Copy setup"/>
        </div>
    </div>
);

const setupFor = (url: string, token: string) => ({
    claudeCode: `claude mcp add --transport http indexr ${url} --header "Authorization: Bearer ${token}"`,
    claudeDesktop: JSON.stringify({
        mcpServers: {
            indexr: {command: "npx", args: ["-y", "mcp-remote", url, "--header", `Authorization: Bearer ${token}`]},
        },
    }, null, 2),
    other: JSON.stringify({mcpServers: {indexr: {url, headers: {Authorization: `Bearer ${token}`}}}}, null, 2),
});

const NewTokenView = ({token, url, onDone}: { token: ApiToken; url: string; onDone: () => void }) => {
    const setup = setupFor(url, token.token ?? "");

    return (
        <>
            <DialogHeader>
                <DialogTitle>“{token.name}” is ready</DialogTitle>
                <DialogDescription>Copy your token now. For your security, you won't be able to see it again.</DialogDescription>
            </DialogHeader>
            <div className="min-w-0 space-y-4">
                <div className="flex items-center gap-2 rounded-xl border bg-muted/50 p-2 pl-3">
                    <code className="min-w-0 flex-1 truncate font-mono text-sm">{token.token}</code>
                    <CopyButton text={token.token ?? ""} label="Copy token" size="icon-sm"/>
                </div>
                <div className="flex items-start gap-2 text-xs text-muted-foreground">
                    <TriangleAlertIcon className="mt-0.5 size-3.5 shrink-0"/>
                    Anyone with this token can read your workspaces and private papers. Keep it secret.
                </div>
                <div className="min-w-0 space-y-2">
                    <p className="text-sm font-medium">Set up your assistant</p>
                    <Tabs defaultValue="claude-code" className="min-w-0 gap-3">
                        <TabsList className="w-full">
                            <TabsTrigger value="claude-code" className="flex-1">Claude Code</TabsTrigger>
                            <TabsTrigger value="claude-desktop" className="flex-1">Claude Desktop</TabsTrigger>
                            <TabsTrigger value="other" className="flex-1">Other</TabsTrigger>
                        </TabsList>
                        <TabsContent value="claude-code" className="space-y-2">
                            <p className="text-xs text-muted-foreground">Run this in your terminal.</p>
                            <Snippet code={setup.claudeCode}/>
                        </TabsContent>
                        <TabsContent value="claude-desktop" className="space-y-2">
                            <p className="text-xs text-muted-foreground">
                                Add this to Claude Desktop's config (Settings → Developer → Edit config), then restart it.
                            </p>
                            <Snippet code={setup.claudeDesktop}/>
                        </TabsContent>
                        <TabsContent value="other" className="space-y-2">
                            <p className="text-xs text-muted-foreground">For apps that connect to MCP servers by URL.</p>
                            <Snippet code={setup.other}/>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
            <DialogFooter>
                <Button onClick={onDone}>Done</Button>
            </DialogFooter>
        </>
    );
};

const CreateTokenDialog = ({open, onOpenChange, url}: { open: boolean; onOpenChange: (open: boolean) => void; url: string }) => {
    const [name, setName] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [created, setCreated] = useState<ApiToken | null>(null);
    const createToken = useCreateApiToken();

    const close = (next: boolean) => {
        if (!next) {
            setName("");
            setError(null);
            setCreated(null);
        }
        onOpenChange(next);
    };

    const submit = (event: FormEvent) => {
        event.preventDefault();
        if (!name.trim()) return setError("Give the token a name, like “Claude Desktop on my laptop”.");
        createToken.mutate(name.trim(), {
            onSuccess: setCreated,
            onError: (failure) => {
                const data = failure.response?.data as { name?: string[] } | undefined;
                setError(data?.name?.[0] ?? "We couldn't create the token. Please try again.");
            },
        });
    };

    return (
        <Dialog open={open} onOpenChange={close}>
            <DialogContent className="sm:max-w-xl" showCloseButton={!created}>
                {created ? <NewTokenView token={created} url={url} onDone={() => close(false)}/> : (
                    <form onSubmit={submit} className="grid gap-6">
                        <DialogHeader>
                            <DialogTitle>Create an access token</DialogTitle>
                            <DialogDescription>Name it after where you'll use it, so you can recognise it later.</DialogDescription>
                        </DialogHeader>
                        <Field data-invalid={!!error}>
                            <FieldLabel htmlFor="token-name">Name</FieldLabel>
                            <Input
                                id="token-name"
                                autoFocus
                                value={name}
                                onChange={(event) => setName(event.target.value)}
                                placeholder="e.g. Claude Desktop on my laptop"
                                maxLength={100}
                                aria-invalid={!!error}
                                disabled={createToken.isPending}
                            />
                            {error && <FieldError>{error}</FieldError>}
                        </Field>
                        <DialogFooter>
                            <Button type="button" variant="outline" disabled={createToken.isPending} onClick={() => close(false)}>
                                Cancel
                            </Button>
                            <Button type="submit" disabled={createToken.isPending}>
                                {createToken.isPending && <Spinner/>}
                                Create token
                            </Button>
                        </DialogFooter>
                    </form>
                )}
            </DialogContent>
        </Dialog>
    );
};

const TokenRow = ({token, onRevoke}: { token: ApiToken; onRevoke: () => void }) => (
    <li className="flex items-center gap-3 rounded-2xl border p-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
            <KeyRoundIcon className="size-4"/>
        </div>
        <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{token.name}</p>
            <p className="truncate text-xs text-muted-foreground">
                <code className="font-mono">{token.prefix}…</code> · Created {formatRelativeTime(token.created_at)} ·{" "}
                {token.last_used_at ? `Last used ${formatRelativeTime(token.last_used_at)}` : "Never used"}
            </p>
        </div>
        <Button size="sm" variant="outline" onClick={onRevoke}>Revoke</Button>
    </li>
);

export const IntegrationsSection = () => {
    const server = useMcpServer();
    const tokens = useApiTokens();
    const revokeToken = useRevokeApiToken();
    const [creating, setCreating] = useState(false);
    const [revoking, setRevoking] = useState<ApiToken | null>(null);
    const url = server.data?.url ?? "";

    const confirmRevoke = () => revoking && revokeToken.mutate(revoking.id, {
        onSuccess: () => {
            toast.add({title: "Token revoked", description: `“${revoking.name}” can no longer connect.`, type: "success"});
            setRevoking(null);
        },
        onError: () => toast.add({title: "Couldn't revoke the token", description: "Please try again.", type: "error"}),
    });

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>MCP server</CardTitle>
                    <CardDescription>
                        Connect AI assistants like Claude to IndexR, so they can search your papers and answer with
                        citations while you work.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {server.isPending ? <Skeleton className="h-11 rounded-xl"/> : (
                        <div className="flex items-center gap-2 rounded-xl border bg-muted/50 p-2 pl-3">
                            <code className="min-w-0 flex-1 truncate font-mono text-sm">{url}</code>
                            <CopyButton text={url} label="Copy server URL" size="icon-sm"/>
                        </div>
                    )}
                    <ul className="grid gap-1.5 text-sm text-muted-foreground">
                        {TOOLS.map((tool) => <li key={tool} className="flex gap-2"><span aria-hidden>•</span>{tool}</li>)}
                    </ul>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Access tokens</CardTitle>
                    <CardDescription>Each assistant connects with its own token. Revoke one to disconnect it.</CardDescription>
                    <CardAction>
                        <Button size="sm" onClick={() => setCreating(true)}>
                            <PlusIcon data-icon="inline-start"/> Create token
                        </Button>
                    </CardAction>
                </CardHeader>
                <CardContent>
                    {tokens.isPending && <Skeleton className="h-16 rounded-2xl"/>}
                    {tokens.isError && (
                        <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
                            Couldn't load your tokens.
                            <Button size="sm" variant="outline" onClick={() => tokens.refetch()}>Retry</Button>
                        </div>
                    )}
                    {tokens.isSuccess && !tokens.data.length && (
                        <p className="rounded-2xl border border-dashed p-6 text-center text-sm text-muted-foreground">
                            No tokens yet. Create one to connect your first assistant.
                        </p>
                    )}
                    {tokens.isSuccess && !!tokens.data.length && (
                        <ul className="space-y-2">
                            {tokens.data.map((token) => (
                                <TokenRow key={token.id} token={token} onRevoke={() => setRevoking(token)}/>
                            ))}
                        </ul>
                    )}
                </CardContent>
            </Card>

            <CreateTokenDialog open={creating} onOpenChange={setCreating} url={url}/>
            <ConfirmDialog
                open={!!revoking}
                onOpenChange={(open) => !open && setRevoking(null)}
                title="Revoke this token?"
                description={<>Anything using “{revoking?.name}” will be disconnected right away. This can't be undone.</>}
                confirmLabel="Revoke token"
                destructive
                pending={revokeToken.isPending}
                onConfirm={confirmRevoke}
            />
        </div>
    );
};
