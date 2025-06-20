// ===============================================================
// Hook pour gérer le défilement automatique d'une zone de contenu
// ===============================================================

import { useEffect, useLayoutEffect, useRef } from "react";
import type { RefObject } from "react";

const SCROLL_THRESHOLD = 10;

function useAutoScroll(dependency: any): RefObject<HTMLDivElement | null> {
  const scrollContentRef = useRef<HTMLDivElement>(null);
  const isDisabled = useRef<boolean>(false);
  const prevScrollTop = useRef<number | null>(null);

  useLayoutEffect(() => {
    const el = scrollContentRef.current;
    if (!el) return;
    if (!isDisabled.current) {
      el.scrollTo({
        top: el.scrollHeight - el.clientHeight,
        behavior: "smooth",
      });
    }
  }, [dependency]);

  useEffect(() => {
    const el = scrollContentRef.current;
    if (!el) return;

    const resizeObserver = new ResizeObserver(() => {
      if (!isDisabled.current) {
        el.scrollTo({
          top: el.scrollHeight - el.clientHeight,
          behavior: "smooth",
        });
      }
    });

    resizeObserver.observe(el);

    return () => resizeObserver.disconnect();
  }, []);

  useLayoutEffect(() => {
    const el = scrollContentRef.current;
    if (!el) return;

    if (!dependency || dependency <= 0) {
      isDisabled.current = true;
      return;
    }

    function onScroll() {
      if (!scrollContentRef.current) return;
      const el = scrollContentRef.current;

      if (
        !isDisabled.current &&
        el.scrollTop < (prevScrollTop.current ?? 0) &&
        el.scrollHeight - el.clientHeight > el.scrollTop + SCROLL_THRESHOLD
      ) {
        isDisabled.current = true;
      } else if (
        isDisabled.current &&
        el.scrollHeight - el.clientHeight <= el.scrollTop + SCROLL_THRESHOLD
      ) {
        isDisabled.current = false;
      }

      prevScrollTop.current = el.scrollTop;
    }

    isDisabled.current = false;
    prevScrollTop.current = el.scrollTop;
    el.addEventListener("scroll", onScroll);

    return () => el.removeEventListener("scroll", onScroll);
  }, [dependency]);
  1;

  return scrollContentRef;
}

export default useAutoScroll;
