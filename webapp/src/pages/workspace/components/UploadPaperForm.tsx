import {type DragEvent, useId, useState} from "react";
import {FileTextIcon, LockIcon, UploadIcon, XIcon} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Field, FieldError, FieldLabel} from "@/components/ui/field";
import {Input} from "@/components/ui/input";
import {Spinner} from "@/components/ui/spinner";
import {toast} from "@/components/ui/toast";
import {useUploadPaper} from "@/queries";
import {cn} from "@/lib/utils.ts";

const MAX_MEGABYTES = 50;

const formatSize = (bytes: number) =>
    bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

interface UploadPaperFormProps {
    workspaceId: string;
    onUploaded: () => void;
}

/** Uploads a private PDF and adds it to the workspace. */
export const UploadPaperForm = ({workspaceId, onUploaded}: UploadPaperFormProps) => {
    const inputId = useId();
    const [file, setFile] = useState<File | null>(null);
    const [title, setTitle] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [dragging, setDragging] = useState(false);
    const upload = useUploadPaper(workspaceId);

    const choose = (chosen: File | undefined) => {
        if (!chosen) return;
        if (chosen.type !== "application/pdf" && !chosen.name.toLowerCase().endsWith(".pdf")) {
            setError("Choose a PDF file.");
            return;
        }
        if (chosen.size > MAX_MEGABYTES * 1024 * 1024) {
            setError(`Choose a PDF smaller than ${MAX_MEGABYTES} MB.`);
            return;
        }
        setError(null);
        setFile(chosen);
    };

    const onDrop = (event: DragEvent) => {
        event.preventDefault();
        setDragging(false);
        choose(event.dataTransfer.files[0]);
    };

    const submit = () => {
        if (!file) return;
        upload.mutate({file, title}, {
            onSuccess: (paper) => {
                toast.add({title: "Paper uploaded", description: paper.title, type: "success"});
                onUploaded();
            },
            onError: (failure) => {
                const data = failure.response?.data as { file?: string[]; title?: string[] } | undefined;
                setError(data?.file?.[0] ?? data?.title?.[0] ?? "We couldn't upload this paper. Please try again.");
            },
        });
    };

    return (
        <div className="space-y-4">
            {file ? (
                <div className="flex items-center gap-3 rounded-2xl border p-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
                        <FileTextIcon className="size-5"/>
                    </div>
                    <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">{file.name}</p>
                        <p className="text-xs text-muted-foreground">{formatSize(file.size)}</p>
                    </div>
                    <Button variant="ghost" size="icon-sm" aria-label="Remove file" disabled={upload.isPending}
                            onClick={() => setFile(null)}>
                        <XIcon/>
                    </Button>
                </div>
            ) : (
                <label
                    htmlFor={inputId}
                    onDragOver={(event) => {
                        event.preventDefault();
                        setDragging(true);
                    }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={onDrop}
                    className={cn(
                        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border border-dashed px-6 py-10 text-center transition-colors",
                        dragging ? "border-primary bg-secondary" : "hover:bg-muted/50",
                    )}
                >
                    <div className="flex size-10 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
                        <UploadIcon className="size-5"/>
                    </div>
                    <p className="text-sm font-medium">Drop a PDF here, or click to choose one</p>
                    <p className="text-xs text-muted-foreground">Up to {MAX_MEGABYTES} MB</p>
                </label>
            )}
            <input
                id={inputId}
                type="file"
                accept="application/pdf,.pdf"
                className="sr-only"
                onChange={(event) => {
                    choose(event.target.files?.[0]);
                    event.target.value = "";
                }}
            />

            <Field>
                <FieldLabel htmlFor={`${inputId}-title`}>Title <span className="font-normal text-muted-foreground">(optional)</span></FieldLabel>
                <Input
                    id={`${inputId}-title`}
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="We'll use the title from the PDF"
                    disabled={upload.isPending}
                />
            </Field>

            {error && <FieldError>{error}</FieldError>}

            <div className="flex items-center gap-3">
                <p className="flex flex-1 items-center gap-1.5 text-xs text-muted-foreground">
                    <LockIcon className="size-3.5 shrink-0"/> Only you can see papers you upload.
                </p>
                <Button onClick={submit} disabled={!file || upload.isPending}>
                    {upload.isPending ? <Spinner/> : <UploadIcon data-icon="inline-start"/>}
                    {upload.isPending ? "Reading your PDF…" : "Upload"}
                </Button>
            </div>
        </div>
    );
};
