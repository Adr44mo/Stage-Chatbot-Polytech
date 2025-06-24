// ==============================================================================
// Composant AdminUploadPDF
// Permet aux administrateurs d'ajouter des fichiers PDF au corpus du chatbot RAG
// ==============================================================================

import React, { useRef } from "react";

export default function AdminUploadPDF() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fonction pour gérer le drop de fichiers
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    handleFiles(files);
  };

  // Fonction pour traiter les fichiers sélectionnés
  const handleFiles = (files: FileList) => {
    // Pour l'instant on log juste les fichiers
    for (let i = 0; i < files.length; i++) {
      if (files[i].type === "application/pdf") {
        console.log("PDF à uploader:", files[i]);

        // TODO: envoyer au backend (adminApi)
      }
    }
  };

  return (
    <div className="admin-upload-section">
      <h2 className="admin-page-subtitle">Ajouter des PDF au corpus</h2>
      <div
        className="admin-upload-dropzone"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => fileInputRef.current?.click()}
      >
        Glissez-déposez vos PDF ici ou cliquez pour sélectionner
        <input
          type="file"
          accept="application/pdf"
          multiple
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>
    </div>
  );
}
