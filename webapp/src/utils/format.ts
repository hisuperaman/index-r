import type {Chunk, PaperBasic} from "@/models";

const relativeTime = new Intl.RelativeTimeFormat(undefined, {numeric: "auto"});
const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
    ["year", 365 * 24 * 3600],
    ["month", 30 * 24 * 3600],
    ["week", 7 * 24 * 3600],
    ["day", 24 * 3600],
    ["hour", 3600],
    ["minute", 60],
];

/** "3 days ago", "yesterday", "just now". */
export const formatRelativeTime = (iso: string): string => {
    const seconds = (new Date(iso).getTime() - Date.now()) / 1000;
    for (const [unit, size] of UNITS) {
        if (Math.abs(seconds) >= size) return relativeTime.format(Math.round(seconds / size), unit);
    }
    return "just now";
};

/** The publication year, or null for an undated paper. */
export const formatPaperYear = (paper: PaperBasic): string | null =>
    paper.publication_date ? paper.publication_date.slice(0, 4) : null;

/** "Vaswani, Shazeer et al." */
export const formatAuthors = (authors: string[], max = 2): string => {
    if (!authors.length) return "";
    const names = authors.slice(0, max).map((name) => name.split(" ").at(-1));
    return authors.length > max ? `${names.join(", ")} et al.` : names.join(", ");
};

/** "Venue · 2017 · 1,204 citations", skipping what is unknown. */
export const formatPaperMeta = (paper: PaperBasic): string =>
    [
        paper.venue,
        formatPaperYear(paper),
        paper.citation_count != null ? `${paper.citation_count.toLocaleString()} citations` : null,
    ].filter(Boolean).join(" · ");

/** "§3.2 Attention · p.4" for a chunk's location within its paper. */
export const formatChunkLocation = (chunk: Chunk): string => {
    const pages = chunk.start_page === chunk.end_page ? `p.${chunk.start_page}` : `pp.${chunk.start_page}–${chunk.end_page}`;
    return chunk.heading ? `§${chunk.heading} · ${pages}` : pages;
};

/** Up to two initials from a name or, failing that, an email. */
export const getInitials = (name: string, fallback: string): string => {
    const letters = name.trim().split(/\s+/).filter(Boolean).map((part) => part[0]);
    return (letters.length ? letters.slice(0, 2).join("") : fallback.slice(0, 1)).toUpperCase();
};

const DAY_MS = 24 * 3600 * 1000;

/** Splits items into "Today", "Yesterday", "Previous 7 days", "Previous 30 days" and then month groups, keeping their order. */
export const groupByRecency = <T, >(items: T[], dateOf: (item: T) => string): { label: string; items: T[] }[] => {
    const startOfToday = new Date();
    startOfToday.setHours(0, 0, 0, 0);
    const thisYear = startOfToday.getFullYear();

    const labelFor = (iso: string) => {
        const date = new Date(iso);
        const daysAgo = Math.floor((startOfToday.getTime() - date.getTime()) / DAY_MS) + 1;
        if (date >= startOfToday) return "Today";
        if (daysAgo <= 1) return "Yesterday";
        if (daysAgo <= 7) return "Previous 7 days";
        if (daysAgo <= 30) return "Previous 30 days";
        return date.toLocaleDateString(undefined, date.getFullYear() === thisYear ? {month: "long"} : {month: "long", year: "numeric"});
    };

    const groups: { label: string; items: T[] }[] = [];
    for (const item of items) {
        const label = labelFor(dateOf(item));
        if (groups.at(-1)?.label === label) groups.at(-1)!.items.push(item);
        else groups.push({label, items: [item]});
    }
    return groups;
};

/** "1 paper", "3 papers". */
export const pluralize = (count: number, singular: string, plural = `${singular}s`): string =>
    `${count.toLocaleString()} ${count === 1 ? singular : plural}`;
