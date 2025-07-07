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
  handleFileUpload,
  handleFileOpen,
} from "../../utils/corpusUtils";
import AdminCorpusTreeNode from "./AdminCorpusTreeNode";

interface AdminCorpusFileTreeProps {
  onFileDeleted?: (fileId: string) => void;
  onFileUploaded?: (fileName: string) => void;
}

export interface AdminCorpusFileTreeRef {
  refreshTree: () => void;
}

const AdminCorpusFileTree = forwardRef<
  AdminCorpusFileTreeRef,
  AdminCorpusFileTreeProps
>(({ onFileDeleted, onFileUploaded }, ref) => {
  const [corpusTree, setCorpusTree] = useState<FileNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [draggedItem, setDraggedItem] = useState<FileNode | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);
  const [isDragOverExternal, setIsDragOverExternal] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Charger l'arborescence au montage du composant
  useEffect(() => {
    loadCorpusTree();
  }, []);

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

  // Exposer la fonction de refresh au composant parent
  useImperativeHandle(ref, () => ({
    refreshTree: loadCorpusTree,
  }));

  // Fonction pour basculer l'expansion d'un dossier
  const toggleFolder = (nodeId: string) => {
    if (corpusTree) {
      const updatedTree = updateFolderExpansion(corpusTree, nodeId);
      setCorpusTree(updatedTree);
    }
  };

  // Actions sur les fichiers
  const handleDeleteFile = async (fileId: string) => {
    try {
      const updatedTree = await handleFileDelete(
        fileId,
        corpusTree!,
        onFileDeleted
      );
      setCorpusTree(updatedTree);
    } catch (error) {
      // L'erreur est déjà gérée dans handleFileDelete
    }
  };

  // Fonctions de drag & drop
  const handleDragStart = (e: React.DragEvent, node: FileNode) => {
    setDraggedItem(node);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", node.id);
  };

  const handleDragOver = (e: React.DragEvent, targetNode: FileNode) => {
    e.preventDefault();

    // Gérer le drag & drop interne (déplacement de fichiers)
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
    // Gérer le drag & drop externe (fichiers depuis l'OS)
    else if (
      e.dataTransfer.types.includes("Files") &&
      targetNode.type === "folder"
    ) {
      setDropTarget(targetNode.id);
      e.dataTransfer.dropEffect = "copy";
    }
  };

  const handleDragLeave = () => {
    setDropTarget(null);
  };

  const handleDrop = async (e: React.DragEvent, targetNode: FileNode) => {
    e.preventDefault();

    // Gérer le drop de fichiers internes (déplacement)
    if (
      draggedItem &&
      targetNode.type === "folder" &&
      draggedItem.id !== targetNode.id
    ) {
      try {
        const updatedTree = await handleFileMove(
          draggedItem,
          targetNode,
          corpusTree!
        );
        setCorpusTree(updatedTree);
      } catch (error) {
        // En cas d'erreur, recharger l'arborescence pour restaurer l'état correct
        await loadCorpusTree();
      }
    }
    // Gérer le drop de fichiers externes (upload)
    else if (e.dataTransfer.files.length > 0 && targetNode.type === "folder") {
      await handleExternalDrop(e, targetNode);
    }

    setDraggedItem(null);
    setDropTarget(null);
  };

  // Fonction pour ouvrir un fichier
  const handleFileClick = async (node: FileNode) => {
    try {
      await handleFileOpen(node);
    } catch (error) {
      // L'erreur est déjà gérée dans handleFileOpen
    }
  };

  // Fonctions de drag & drop de fichiers externes (depuis l'OS)
  const handleExternalDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Vérifier si ce sont des fichiers depuis l'extérieur
    if (e.dataTransfer.types.includes("Files")) {
      setIsDragOverExternal(true);
      e.dataTransfer.dropEffect = "copy";
    }
  };

  const handleExternalDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Vérifier si on quitte vraiment la zone (pas un enfant)
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOverExternal(false);
    }
  };

  const handleExternalDrop = async (
    e: React.DragEvent,
    targetFolder?: FileNode
  ) => {
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

  // Fonction pour déclencher l'upload via un bouton
  const handleAddFileClick = () => {
    createFileInput((files) => {
      handleExternalDrop({
        preventDefault: () => {},
        stopPropagation: () => {},
        dataTransfer: { files },
      } as any);
    });
  };

  // Fonction récursive pour rendre l'arborescence
  const renderTreeNode = (node: FileNode): React.ReactElement => {
    return (
      <AdminCorpusTreeNode
        key={node.id}
        node={node}
        depth={0}
        draggedItem={draggedItem}
        dropTarget={dropTarget}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onToggleFolder={toggleFolder}
        onFileClick={handleFileClick}
        onDeleteFile={handleDeleteFile}
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

      {/* Arborescence des fichiers */}
      <div className="admin-corpus-tree-content">
        {renderTreeNode(corpusTree)}
      </div>
    </div>
  );
});

AdminCorpusFileTree.displayName = "AdminCorpusFileTree";

export default AdminCorpusFileTree;
