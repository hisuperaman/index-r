import {useState} from "react";
import {PlusIcon} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs";
import type {Workspace} from "@/models";
import {useMentionedPapers, useWorkspacePapers} from "@/queries";
import {cn} from "@/lib/utils.ts";
import {AddPaperDialog} from "./AddPaperDialog.tsx";
import {MentionedPapersTab} from "./MentionedPapersTab.tsx";
import {PanelToggle} from "./PanelToggle.tsx";
import {WorkspacePapersTab} from "./WorkspacePapersTab.tsx";

const Count = ({count, more}: { count?: number; more?: boolean }) =>
    count === undefined ? null : (
        <span className="rounded-full bg-background/70 px-1.5 text-[0.7rem] font-medium tabular-nums">
            {count}{more ? "+" : ""}
        </span>
    );

interface PapersPanelProps {
    workspace: Workspace;
    inSheet?: boolean;
    onCollapse?: () => void;
}

export const PapersPanel = ({workspace, inSheet = false, onCollapse}: PapersPanelProps) => {
    const [adding, setAdding] = useState(false);
    const papers = useWorkspacePapers(workspace.id);
    const mentioned = useMentionedPapers(workspace.id);

    const workspaceItems = papers.data?.pages.flatMap((page) => page.results) ?? [];
    const paperIds = new Set(workspaceItems.map(({paper}) => paper.id));
    const mentionedCount = mentioned.data?.pages.reduce((total, page) => total + page.results.length, 0);

    return (
        <Tabs defaultValue="workspace" className="flex h-full min-h-0 flex-col gap-0">
            <div className="shrink-0 space-y-3 border-b px-4 pt-4 pb-3">
                <div className={cn("flex items-center gap-2", inSheet && "pr-10")}>
                    {onCollapse && <PanelToggle open onClick={onCollapse} className="-ml-1.5"/>}
                    <h2 className="text-sm font-semibold">Papers</h2>
                    <Button size="sm" variant="outline" className="ml-auto" onClick={() => setAdding(true)}>
                        <PlusIcon data-icon="inline-start"/> Add
                    </Button>
                </div>
                <TabsList className="w-full">
                    <TabsTrigger value="workspace" className="flex-1 gap-1.5">
                        Workspace <Count count={papers.isSuccess ? workspaceItems.length : undefined} more={papers.hasNextPage}/>
                    </TabsTrigger>
                    <TabsTrigger value="mentioned" className="flex-1 gap-1.5">
                        Mentioned <Count count={mentionedCount} more={mentioned.hasNextPage}/>
                    </TabsTrigger>
                </TabsList>
            </div>

            <TabsContent value="workspace" className="flex min-h-0 flex-1 flex-col">
                <WorkspacePapersTab workspace={workspace} onAdd={() => setAdding(true)}/>
            </TabsContent>
            <TabsContent value="mentioned" className="flex min-h-0 flex-1 flex-col">
                <MentionedPapersTab workspace={workspace}/>
            </TabsContent>

            <AddPaperDialog workspaceId={workspace.id} open={adding} onOpenChange={setAdding} paperIds={paperIds}/>
        </Tabs>
    );
};
