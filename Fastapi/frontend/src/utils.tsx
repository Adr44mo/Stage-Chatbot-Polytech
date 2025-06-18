// =============================================================
// Fonction utilitaire pour l'affichage des sources dans le chat
// =============================================================

import React from "react";

/* Formate les sources (string[]) en éléments cliquables si ce sont des URLs */
export function renderSources(sources: string[]): React.ReactNode {
  return (
    <>
      {sources.map((src: string, i: number) =>
        /^https?:\/\//i.test(src) ? (
          <div key={i}>
            <a href={src} target="_blank" rel="noopener noreferrer">
              {src}
            </a>
          </div>
        ) : (
          <div key={i}>{src}</div>
        )
      )}
    </>
  );
}
