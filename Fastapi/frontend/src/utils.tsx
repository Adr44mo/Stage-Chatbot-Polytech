// =============================================================
// Fonction utilitaire pour l'affichage des sources dans le chat
// =============================================================

import React from "react";

/* Formate les sources en éléments cliquables (URLs et PDFs) */
export function renderSources(sources: string[]): React.ReactNode {
  return (
    <>
      {sources.map((src: string, i: number) => {
        if (/^https?:\/\//i.test(src)) {
          return (
            <div key={i}>
              <a href={src} target="_blank" rel="noopener noreferrer">
                {src}
              </a>
            </div>
          );
        } else if (src.endsWith(".pdf")) {
          const fileUrl = `/files${encodeURIComponent(src)}`;
          return (
            <div key={i}>
              <a href={fileUrl} target="_blank" rel="noopener noreferrer">
                {src}
              </a>
            </div>
          );
        } else {
          return <div key={i}>{src}</div>;
        }
      })}
    </>
  );
}
