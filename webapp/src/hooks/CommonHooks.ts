import {type RefObject, useEffect, useState, useSyncExternalStore} from "react";

/** Calls `onVisible` whenever the element scrolls into view, while `enabled`. */
export const useOnVisible = (ref: RefObject<Element | null>, onVisible: () => void, enabled = true) => {
    useEffect(() => {
        const element = ref.current;
        if (!element || !enabled) return;
        const observer = new IntersectionObserver((entries) => {
            if (entries.some((entry) => entry.isIntersecting)) onVisible();
        }, {rootMargin: "200px"});
        observer.observe(element);
        return () => observer.disconnect();
    }, [ref, onVisible, enabled]);
};

/** Returns `value` once it has stopped changing for `delay` milliseconds. */
export const useDebouncedValue = <T, >(value: T, delay = 300): T => {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const timer = setTimeout(() => setDebounced(value), delay);
        return () => clearTimeout(timer);
    }, [value, delay]);
    return debounced;
};

/** Whether the media query currently matches, updating as it changes. */
export const useMediaQuery = (query: string): boolean =>
    useSyncExternalStore(
        (onChange) => {
            const list = window.matchMedia(query);
            list.addEventListener("change", onChange);
            return () => list.removeEventListener("change", onChange);
        },
        () => window.matchMedia(query).matches,
    );
