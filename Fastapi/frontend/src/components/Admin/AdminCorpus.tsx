// ===================================================
// Composant AdminCorpus
// Coordinateur principal de la gestion du corpus PDF
// ===================================================

import { useRef, useState, useEffect, useCallback } from "react";
import AdminCorpusFileTree from "./AdminCorpusFileTree";
import type { AdminCorpusFileTreeRef } from "./AdminCorpusFileTree";
import { useScrapingContext } from "../../contexts/ScrapingContext";
import {
  enableEditMode,
  saveChanges,
  cancelChanges,
  getEditStatus,
  runCorpusVectorization,
  resetCorpusVectorizationProgress,
} from "../../api/corpusApi";

export default function AdminCorpus() {
  const fileTreeRef = useRef<AdminCorpusFileTreeRef>(null);
  const [editMode, setEditMode] = useState(false);
  const [snapshotId, setSnapshotId] = useState<string>("");
  const [loading, setLoading] = useState(false);

  // États globaux du contexte
	const {
		isScraping,
		isVectorizing,
    isCorpusVectorizing,
    corpusVectorizationProgress,
    startCorpusVectorization,
    stopCorpusVectorization
	} = useScrapingContext();
  const vectorizationCorpusCompleteRef = useRef(false);

  // On vérifie le statut du mode édition au montage du composant
  useEffect(() => {
    checkEditStatus();
  }, []);

  /**
   * Récupère l'état actuel du mode édition
   */
  const checkEditStatus = async () => {
    try {
      const status = await getEditStatus();
      console.log("Status reçu:", status);
      setEditMode(status.edit_mode);
      // Si on est en mode édition, on récupère le snapshot ID
      if (status.edit_mode && status.snapshot_id) {
        setSnapshotId(status.snapshot_id);
        console.log("Snapshot ID défini:", status.snapshot_id);
      }
    } catch (error) {
      console.error("Erreur lors de la vérification du statut:", error);
      // En cas d'erreur on reste en mode lecture par défaut
    }
  };

  /**
   * Notification de la suppression d'un fichier
   * @param fileId  - l'ID du fichier supprimé
   */
  const handleFileDeleted = (fileId: string) => {
    console.log(`Fichier supprimé: ${fileId}`);
  };

  /**
   * Notification d'upload d'un fichier
   * @param fileName - le nom du fichier uploadé
   */
  const handleFileUploaded = (fileName: string) => {
    console.log(`Fichier uploadé: ${fileName}`);
    // Refresh l'arborescence après un upload réussi
    fileTreeRef.current?.refreshTree();
  };

  /**
   * Active le mode édition du corpus
   */
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

  /**
   * Sauvegarde les changements effectués dans le corpus
   */
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

  /**
   * Annule les changements effectués dans le corpus
   */
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

  /**
   * Lance la vectorisation du corpus (pipeline + vectorisation)
   */
  const handleVectorization = useCallback(async () => {
    try {
      await resetCorpusVectorizationProgress();
      vectorizationCorpusCompleteRef.current = false; // Réinitialiser le flag de complétion

      startCorpusVectorization();
      await runCorpusVectorization();

    } catch (err: any) {
      console.error("Erreur vectorisation corpus :", err.message);
      alert("Erreur pendant la vectorisation corpus : " + err.message);
      stopCorpusVectorization();
    }
  }, [startCorpusVectorization, stopCorpusVectorization]);

  // ===============
  // RENDU PRINCIPAL
  // ===============

  return (
    <div className="admin-corpus-container">
      <div className="admin-corpus-header">
        <h2 className="admin-page-subtitle">Gestion du Corpus PDF</h2>
      </div>

      <div className="admin-corpus-tree-section">
        <h3 className="admin-corpus-section-title">Structure du corpus</h3>

        {/* Barre de contrôle */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1rem",
          }}
        >
          {/* Interface en mode lecture */}
          {!editMode ? (
            <>
              <p style={{ margin: 0, color: "#666" }}>
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
            // Interface en mode édition
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

        {/* Arborescence des fichiers */}
        <AdminCorpusFileTree
          ref={fileTreeRef}
          onFileDeleted={handleFileDeleted}
          onFileUploaded={handleFileUploaded}
          editMode={editMode}
        />

        {/*Vectorisation */}
        {!editMode && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              marginTop: "1rem",
            }}
          >
            <button
              className="admin-corpus-edit-btn"
              onClick={handleVectorization}
              disabled={isVectorizing || isScraping || isCorpusVectorizing}
            >
              {isVectorizing
                ? "Vectorisation en cours..."
                : "Lancer la vectorisation"}
            </button>

            {isCorpusVectorizing && corpusVectorizationProgress && (
              <>
                <progress
                  value={corpusVectorizationProgress.current}
                  max={corpusVectorizationProgress.total}
                  className="admin-vectorization-progress"
                />
                <span>{corpusVectorizationProgress.status}</span>
              </>
            )}            
          </div>
        )}
      </div>
    </div>
  );
}
