// ======================================================================
// Composant AdminCorpus
// Gestion du corpus PDF : consultation, suppression et ajout de fichiers
// ======================================================================s

import { useRef, useState, useEffect } from "react";
import AdminCorpusFileTree from "./AdminCorpusFileTree";
import type { AdminCorpusFileTreeRef } from "./AdminCorpusFileTree";
import {
  enableEditMode,
  saveChanges,
  cancelChanges,
  getEditStatus,
} from "../../api/corpusApi";

export default function AdminCorpus() {
  const fileTreeRef = useRef<AdminCorpusFileTreeRef>(null);
  const [editMode, setEditMode] = useState(false);
  const [snapshotId, setSnapshotId] = useState<string>("");
  const [loading, setLoading] = useState(false);

  // Charger le statut du mode édition au montage
  useEffect(() => {
    checkEditStatus();
  }, []);

  const checkEditStatus = async () => {
    try {
      const status = await getEditStatus();
      console.log("Status reçu:", status);
      setEditMode(status.edit_mode);
      if (status.edit_mode && status.snapshot_id) {
        setSnapshotId(status.snapshot_id);
        console.log("Snapshot ID défini:", status.snapshot_id);
      }
    } catch (error) {
      console.error("Erreur lors de la vérification du statut:", error);
    }
  };

  const handleFileDeleted = (fileId: string) => {
    console.log(`Fichier supprimé: ${fileId}`);
  };

  const handleFileUploaded = (fileName: string) => {
    console.log(`Fichier uploadé: ${fileName}`);
    // Refresh l'arborescence après un upload réussi
    fileTreeRef.current?.refreshTree();
  };

  const handleEnableEditMode = async () => {
    try {
      setLoading(true);
      const snapshotId = await enableEditMode();
      setSnapshotId(snapshotId);
      setEditMode(true);
    } catch (error) {
      console.error("Erreur lors de l'activation du mode édition:", error);
      alert("Erreur lors de l'activation du mode édition");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveChanges = async () => {
    if (!snapshotId) {
      console.log("Aucun snapshot ID disponible pour la sauvegarde");
      return;
    }

    try {
      setLoading(true);
      console.log("Sauvegarde avec snapshot ID:", snapshotId);
      await saveChanges(snapshotId);
      setEditMode(false);
      setSnapshotId("");
      // Refresh l'arborescence après sauvegarde
      fileTreeRef.current?.refreshTree();
      alert("Changements sauvegardés avec succès.");
    } catch (error) {
      console.error("Erreur lors de la sauvegarde:", error);
      alert("Erreur lors de la sauvegarde des changements");
    } finally {
      setLoading(false);
    }
  };

  const handleCancelChanges = async () => {
    if (!snapshotId) {
      console.log("Aucun snapshot ID disponible pour l'annulation");
      return;
    }

    if (
      !confirm(
        "ATTENTION : Êtes-vous sûr de vouloir annuler tous les changements ?\nCette action ne peut pas être annulée."
      )
    ) {
      return;
    }

    try {
      setLoading(true);
      console.log("Annulation avec snapshot ID:", snapshotId);
      await cancelChanges(snapshotId);
      setEditMode(false);
      setSnapshotId("");
      // Refresh l'arborescence après annulation
      fileTreeRef.current?.refreshTree();
      alert("Changements annulés avec succès.");
    } catch (error) {
      console.error("Erreur lors de l'annulation:", error);
      alert("❌ Erreur lors de l'annulation des changements");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-corpus-container">
      <div className="admin-corpus-header">
        <h2 className="admin-page-subtitle">Gestion du Corpus PDF</h2>
      </div>

      {/* Arborescence des fichiers */}
      <div className="admin-corpus-tree-section">
        <h3 className="admin-corpus-section-title">Structure du corpus</h3>

        {/* Ligne d'état avec boutons alignés */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1rem",
          }}
        >
          {!editMode ? (
            <>
              <p className="admin-corpus-readonly-note" style={{ margin: 0 }}>
                Mode lecture seule - Cliquez sur "Modifier le corpus" pour
                effectuer des changements
              </p>
              <button
                className="admin-corpus-edit-btn"
                onClick={handleEnableEditMode}
                disabled={loading}
              >
                {loading ? "Activation..." : "Modifier le corpus"}
              </button>
            </>
          ) : (
            <>
              <span style={{ margin: 0, color: "#666" }}>
                Mode édition - Vous pouvez modifier le corpus
              </span>
              <div className="admin-corpus-edit-controls">
                <button
                  className="admin-corpus-edit-btn admin-corpus-cancel-variant"
                  onClick={handleCancelChanges}
                  disabled={loading}
                >
                  {loading ? "Annulation..." : "Annuler"}
                </button>
                <button
                  className="admin-corpus-edit-btn"
                  onClick={handleSaveChanges}
                  disabled={loading}
                >
                  {loading ? "Sauvegarde..." : "Sauvegarder"}
                </button>
              </div>
            </>
          )}
        </div>

        <AdminCorpusFileTree
          ref={fileTreeRef}
          onFileDeleted={handleFileDeleted}
          onFileUploaded={handleFileUploaded}
          editMode={editMode}
        />
      </div>
    </div>
  );
}
