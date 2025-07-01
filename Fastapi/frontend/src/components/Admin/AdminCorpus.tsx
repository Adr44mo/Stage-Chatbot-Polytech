// =====================================================================
// Composant AdminCorpus
// Gestion du corpus PDF : consultation, suppression et ajout de fichiers
// =====================================================================

import { useRef } from "react";
import AdminCorpusFileTree from "./AdminCorpusFileTree";
import type { AdminCorpusFileTreeRef } from "./AdminCorpusFileTree";

export default function AdminCorpus() {
  const fileTreeRef = useRef<AdminCorpusFileTreeRef>(null);

  const handleFileDeleted = (fileId: string) => {
    console.log(`Fichier supprimé: ${fileId}`);
  };

  const handleFileUploaded = (fileName: string) => {
    console.log(`Fichier uploadé: ${fileName}`);
    // Refresh l'arborescence après un upload réussi
    fileTreeRef.current?.refreshTree();
  };

  return (
    <div className="admin-corpus-container">
      <h2 className="admin-page-subtitle">Gestion du Corpus PDF</h2>

      {/* Arborescence des fichiers */}
      <div className="admin-corpus-tree-section">
        <h3 className="admin-corpus-section-title">Structure du corpus</h3>

        <AdminCorpusFileTree
          ref={fileTreeRef}
          onFileDeleted={handleFileDeleted}
          onFileUploaded={handleFileUploaded}
        />
      </div>
    </div>
  );
}
