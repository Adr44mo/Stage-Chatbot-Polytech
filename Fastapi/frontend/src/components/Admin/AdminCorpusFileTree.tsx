// ====================================================
// Composant AdminCorpusFileTree
// Gestion de l'arborescence des fichiers PDF du corpus
// ====================================================

import { useState, useEffect, forwardRef, useImperativeHandle } from "react";
import type { FileNode } from "../../api/corpusApi";
import { fetchCorpusTree } from "../../api/corpusApi";
import {
  updateFolderExpansion,
  isDescendant,
  createFileInput,
  handleFileDelete,
  handleFileMove,
  handleFolderMove,
  handleFileUpload,
  handleFileOpen,
} from "../../utils/corpusUtils";
import AdminCorpusTreeNode from "./AdminCorpusTreeNode";

interface AdminCorpusFileTreeProps {
  // Callbacks vers le composant parent (AdminCorpus)
  onFileDeleted?: (fileId: string) => void; // notifie qu'un fichier a été supprimé
  onFileUploaded?: (fileName: string) => void; // notifie qu'un fichier a été uploadé
  editMode?: boolean; // active ou désactive les interactions (mode édition)
}

export interface AdminCorpusFileTreeRef {
  refreshTree: () => void; // permet au parent de forcer le refresh
}

const AdminCorpusFileTree = forwardRef<
  AdminCorpusFileTreeRef,
  AdminCorpusFileTreeProps
>(({ onFileDeleted, onFileUploaded, editMode = false }, ref) => {
  // État local du composant
  const [corpusTree, setCorpusTree] = useState<FileNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [draggedItem, setDraggedItem] = useState<FileNode | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);
  const [isDragOverExternal, setIsDragOverExternal] = useState(false);
  const [uploading, setUploading] = useState(false);

  // On charge l'arborescence au montage du composant
  useEffect(() => {
    loadCorpusTree();
  }, []);

  /**
   * Charge l'arborescence du corpus depuis l'API
   */
  const loadCorpusTree = async () => {
    try {
      setLoading(true);
      const tree = await fetchCorpusTree();
      setCorpusTree(tree);
    } catch (error) {
      console.error("Erreur lors du chargement du corpus:", error);
    } finally {
      setLoading(false);
    }
  };

  // Exposer l'API au composant parent
  useImperativeHandle(ref, () => ({
    refreshTree: loadCorpusTree,
  }));

  /**
   * Fonction pour ouvrir/fermer un dossier
   */
  const toggleFolder = (nodeId: string) => {
    if (corpusTree) {
      const updatedTree = updateFolderExpansion(corpusTree, nodeId);
      setCorpusTree(updatedTree);
    }
  };

  /**
   * Supprime un fichier du corpus
   * @param fileId - l'ID du fichier à supprimer
   */
  const handleDeleteFile = async (fileId: string) => {
    try {
      const updatedTree = await handleFileDelete(
        fileId,
        corpusTree!,
        onFileDeleted
      );
      setCorpusTree(updatedTree);
    } catch (error) {
      // Erreur déjà gérée dans handleFileDelete
    }
  };

  // =============================
  // FONCTIONS POUR LE DRAG & DROP
  // =============================

  /**
   * Début du drag - Marque un fichier/dossier comme étant glissé
   * @param e - l'événement de drag & drop
   * @param node - le nœud qu'on commence à drag
   */
  const handleDragStart = (e: React.DragEvent, node: FileNode) => {
    // On peut glisser les fichiers et les dossiers (sauf la racine)
    const isRootCorpus = node.id === "root" || node.path === "";
    if (isRootCorpus) {
      e.preventDefault();
      return;
    }
    
    setDraggedItem(node);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", node.id);
  };

  /**
   * Survol d'un dossier pendant un drag - Valide la cible
   * @param e - l'événement de drag & drop
   * @param targetNode - le nœud cible (dossier) du drag
   */
  const handleDragOver = (e: React.DragEvent, targetNode: FileNode) => {
    e.preventDefault();

    // Drag & drop interne (fichiers ou dossiers du corpus)
    if (draggedItem) {
      if (
        targetNode.type === "folder" &&
        draggedItem?.id !== targetNode.id &&
        corpusTree &&
        !isDescendant(corpusTree, draggedItem?.id || "", targetNode.id)
      ) {
        setDropTarget(targetNode.id);
        e.dataTransfer.dropEffect = "move";
      } else {
        setDropTarget(null);
        e.dataTransfer.dropEffect = "none";
      }
    }
    // Drag & drop externe (fichiers depuis l'OS)
    else if (
      e.dataTransfer.types.includes("Files") &&
      targetNode.type === "folder"
    ) {
      setDropTarget(targetNode.id);
      e.dataTransfer.dropEffect = "copy";
    }
  };

  /**
   * Quitter la zone de drop
   */
  const handleDragLeave = () => {
    setDropTarget(null);
  };

  /**
   * Execute l'action de drop (déplacement ou upload)
   * @param e - l'événement de drag & drop
   * @param targetNode - le nœud cible (dossier) du drop
   */
  const handleDrop = async (e: React.DragEvent, targetNode: FileNode) => {
    e.preventDefault();

    // Drop de fichiers ou dossiers internes (déplacement)
    if (
      draggedItem &&
      targetNode.type === "folder" &&
      draggedItem.id !== targetNode.id
    ) {
      try {
        let updatedTree: FileNode;
        
        // Si c'est un fichier
        if (draggedItem.type === "file") {
          updatedTree = await handleFileMove(
            draggedItem,
            targetNode,
            corpusTree!
          );
        } 
        // Si c'est un dossier
        else {
          updatedTree = await handleFolderMove(
            draggedItem,
            targetNode,
            corpusTree!
          );
        }
        
        setCorpusTree(updatedTree);
      } catch (error) {
        await loadCorpusTree();
      }
    }
    // Drop de fichiers externes (upload)
    else if (e.dataTransfer.files.length > 0 && targetNode.type === "folder") {
      await handleExternalDrop(e, targetNode);
    }

    setDraggedItem(null);
    setDropTarget(null);
  };

  /**
   * Détecte les fichiers externes glissés depuis l'OS
   * @param e - l'événement de drag & drop
   * @param targetNode - le nœud cible (dossier) du drop
   */
  const handleExternalDragOver = (e: React.DragEvent) => {
    if (!editMode) return;

    e.preventDefault();
    e.stopPropagation();

    // Vérifier si ce sont des fichiers depuis l'extérieur
    if (e.dataTransfer.types.includes("Files")) {
      setIsDragOverExternal(true);
      e.dataTransfer.dropEffect = "copy";
    }
  };

  /**
   * Vérifie si on quitte vraiment la zone de drop externe
   * @param e - l'événement de drag & drop
   */
  const handleExternalDragLeave = (e: React.DragEvent) => {
    if (!editMode) return;

    e.preventDefault();
    e.stopPropagation();

    // Vérifier si on quitte vraiment la zone (pas un enfant)
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOverExternal(false);
    }
  };

  /**
   * Upload des fichiers externes qui ont été drop
   * @param e - l'événement de drag & drop
   * @param targetFolder - dossier cible (optionnel, dossier autres par défaut)
   * @returns
   */
  const handleExternalDrop = async (
    e: React.DragEvent,
    targetFolder?: FileNode
  ) => {
    if (!editMode) return;

    e.preventDefault();
    e.stopPropagation();

    setIsDragOverExternal(false);

    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    setUploading(true);

    try {
      await handleFileUpload(files, targetFolder, onFileUploaded);

      // Recharger l'arborescence après l'upload
      await loadCorpusTree();
    } catch (error) {
      console.error("Erreur lors de l'upload:", error);
      alert("Erreur lors de l'upload des fichiers");
    } finally {
      setUploading(false);
    }
  };

  // ===========================================
  // FONCTIONS POUR L'INTERACTION AVEC LE CORPUS
  // ===========================================

  /**
   * Ouvre le fichier PDF si on clique dessus
   * @param node - le nœud sur lequel on a cliqué
   */
  const handleFileClick = async (node: FileNode) => {
    try {
      await handleFileOpen(node);
    } catch (error) {
      // L'erreur est déjà gérée dans handleFileOpen
    }
  };

  /**
   * Déclenche l'upload via le bouton 'Ajouter un PDF'
   */
  const handleAddFileClick = () => {
    if (!editMode) return;

    // On simule un évènement de drop pour réutiliser la même logique
    createFileInput((files) => {
      handleExternalDrop({
        preventDefault: () => {},
        stopPropagation: () => {},
        dataTransfer: { files },
      } as any);
    });
  };

  /**
   * Fonction de rendu récursif qui crée un nœud de l'arborescence
   * @param node - le nœud qu'on veut afficher
   */
  const renderTreeNode = (node: FileNode): React.ReactElement => {
    return (
      <AdminCorpusTreeNode
        key={node.id}
        node={node}
        depth={0}
        draggedItem={draggedItem}
        dropTarget={dropTarget}
        editMode={editMode}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onToggleFolder={toggleFolder}
        onFileClick={handleFileClick}
        onDeleteFile={handleDeleteFile}
        onRefresh={loadCorpusTree}
      />
    );
  };

  if (loading) {
    return (
      <div className="admin-corpus-tree-wrapper">
        <div style={{ textAlign: "center", padding: "2rem" }}>
          <div className="spinner"></div>
          <p>Chargement du corpus...</p>
        </div>
      </div>
    );
  }

  if (!corpusTree) {
    return (
      <div className="admin-corpus-tree-wrapper">
        <div style={{ textAlign: "center", padding: "2rem", color: "#666" }}>
          Erreur lors du chargement du corpus
        </div>
      </div>
    );
  }

  // ===============
  // RENDU PRINCIPAL
  // ===============

  return (
    <div
      className={`admin-corpus-tree-wrapper ${
        isDragOverExternal ? "external-drag-over" : ""
      } ${uploading ? "uploading" : ""}`}
      onDragOver={handleExternalDragOver}
      onDragLeave={handleExternalDragLeave}
      onDrop={(e) => handleExternalDrop(e)}
    >
      {/* Bouton d'ajout et indication */}
      <div className="admin-corpus-tree-controls">
        {editMode && (
          <>
            <button
              className="admin-corpus-add-btn"
              onClick={handleAddFileClick}
              disabled={uploading}
            >
              Ajouter un PDF
            </button>
            <span className="admin-corpus-drag-hint">
              ou glissez-déposez vos fichiers PDF
            </span>
          </>
        )}
      </div>

      {/* Indicateur de drop externe */}
      {isDragOverExternal && (
        <div className="admin-corpus-external-drop-overlay">
          <div className="admin-corpus-external-drop-message">
            📄 Déposer les fichiers PDF ici
          </div>
        </div>
      )}

      {/* Indicateur d'upload */}
      {uploading && (
        <div className="admin-corpus-upload-overlay">
          <div className="spinner"></div>
          <p>Upload en cours...</p>
        </div>
      )}

      {/* En-tête avec les colonnes */}
      <div className="admin-corpus-tree-header">
        <div className="admin-corpus-tree-header-item">
          <span className="admin-corpus-tree-header-name">Nom</span>
          <span className="admin-corpus-tree-header-date">Date d'ajout</span>
          <span className="admin-corpus-tree-header-actions">Actions</span>
        </div>
      </div>

      {/* Arborescence principale des fichiers */}
      <div className="admin-corpus-tree-content">
        {renderTreeNode(corpusTree)}
      </div>
    </div>
  );
});

AdminCorpusFileTree.displayName = "AdminCorpusFileTree";

export default AdminCorpusFileTree;
