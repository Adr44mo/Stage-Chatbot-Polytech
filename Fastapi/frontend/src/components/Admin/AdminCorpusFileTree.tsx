// ====================================================
// Composant AdminCorpusFileTree
// Gestion de l'arborescence des fichiers PDF du corpus
// ====================================================

import { useState, useEffect, forwardRef, useImperativeHandle } from "react";
import type { FileNode } from "../../api/corpusApi";
import {
  fetchCorpusTree,
  deleteFile,
  updateFolderExpansion,
  removeFileFromTree,
  moveFile,
  getFilePreviewUrl,
  moveFileInTree,
  isDescendant,
  uploadFile,
} from "../../api/corpusApi";

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
      console.error("Erreur lors du chargement de l'arborescence:", error);
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
    if (confirm("Êtes-vous sûr de vouloir supprimer ce fichier ?")) {
      try {
        await deleteFile(fileId);

        if (corpusTree) {
          const updatedTree = removeFileFromTree(corpusTree, fileId);
          setCorpusTree(updatedTree);
        }

        // Notifier le composant parent si nécessaire
        onFileDeleted?.(fileId);
      } catch (error) {
        console.error("Erreur lors de la suppression:", error);
        alert("Erreur lors de la suppression du fichier");
      }
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
        !isDescendant(corpusTree, draggedItem?.id || '', targetNode.id)
      ) {
        setDropTarget(targetNode.id);
        e.dataTransfer.dropEffect = "move";
      } else {
        setDropTarget(null);
        e.dataTransfer.dropEffect = "none";
      }
    }
    // Gérer le drag & drop externe (fichiers depuis l'OS)
    else if (e.dataTransfer.types.includes('Files') && targetNode.type === "folder") {
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
    if (draggedItem && targetNode.type === "folder" && draggedItem.id !== targetNode.id) {
      try {
        // Mise à jour optimiste de l'UI
        if (corpusTree) {
          const updatedTree = moveFileInTree(corpusTree, draggedItem.id, targetNode.id);
          setCorpusTree(updatedTree);
        }
        
        // Appeler l'API pour déplacer le fichier
        await moveFile(draggedItem.id, targetNode.path);

        console.log(`Fichier ${draggedItem.name} déplacé vers ${targetNode.name}`);
      } catch (error) {
        console.error("Erreur lors du déplacement:", error);
        alert("Erreur lors du déplacement du fichier");
        
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
    if (node.type === "file") {
      try {
        const previewUrl = await getFilePreviewUrl(node.id);
        window.open(previewUrl, "_blank");
      } catch (error) {
        console.error("Erreur lors de l'ouverture du fichier:", error);
        alert("Erreur lors de l'ouverture du fichier");
      }
    }
  };

  // Fonctions de drag & drop de fichiers externes (depuis l'OS)
  const handleExternalDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Vérifier si ce sont des fichiers depuis l'extérieur
    if (e.dataTransfer.types.includes('Files')) {
      setIsDragOverExternal(true);
      e.dataTransfer.dropEffect = 'copy';
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

  const handleExternalDrop = async (e: React.DragEvent, targetFolder?: FileNode) => {
    e.preventDefault();
    e.stopPropagation();
    
    setIsDragOverExternal(false);
    
    const files = e.dataTransfer.files;
    if (files.length === 0) return;
    
    setUploading(true);
    
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.type === "application/pdf") {
          console.log("PDF à uploader:", file);
          
          // Utiliser l'API d'upload avec le chemin du dossier cible
          const targetPath = targetFolder?.path || "/corpus";
          await uploadFile(file, targetPath);
          
          // Notifier le composant parent
          onFileUploaded?.(file.name);
        } else {
          alert(`Le fichier ${file.name} n'est pas un PDF`);
        }
      }
      
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
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/pdf';
    input.multiple = true;
    input.onchange = (e) => {
      const files = (e.target as HTMLInputElement).files;
      if (files) {
        handleExternalDrop({
          preventDefault: () => {},
          stopPropagation: () => {},
          dataTransfer: { files }
        } as any);
      }
    };
    input.click();
  };

  // Fonction récursive pour rendre l'arborescence
  const renderTreeNode = (
    node: FileNode,
    depth: number = 0
  ): React.ReactElement => {
    const isFile = node.type === "file";
    const isFolder = node.type === "folder";
    const hasChildren = node.children && node.children.length > 0;

    return (
      <div key={node.id} className="admin-corpus-tree-node">
        <div
          className={`admin-corpus-tree-item ${isFile ? "file" : "folder"} ${
            draggedItem?.id === node.id ? "dragging" : ""
          } ${dropTarget === node.id ? "drag-over" : ""}`}
          style={{ paddingLeft: `${depth * 20}px` }}
          draggable={isFile}
          onDragStart={(e) => isFile && handleDragStart(e, node)}
          onDragOver={(e) => isFolder && handleDragOver(e, node)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => isFolder && handleDrop(e, node)}
        >
          {isFolder && (
            <button
              className="admin-corpus-tree-toggle"
              onClick={() => toggleFolder(node.id)}
            >
              {node.isExpanded ? "📂" : "📁"}
            </button>
          )}

          {isFile && <span className="admin-corpus-tree-file-icon">📄</span>}

          <span
            className={`admin-corpus-tree-name ${isFile ? 'clickable' : ''} ${isFolder ? 'folder-clickable' : ''}`}
            onClick={() => {
              if (isFile) {
                handleFileClick(node);
              } else if (isFolder) {
                toggleFolder(node.id);
              }
            }}
            title={isFile ? "Cliquer pour ouvrir le fichier" : isFolder ? "Cliquer pour ouvrir/fermer le dossier" : ""}
          >
            {node.name}
          </span>

          {isFile && (
            <>
              <span className="admin-corpus-tree-date">
                {node.dateAdded
                  ? new Date(node.dateAdded).toLocaleDateString("fr-FR")
                  : ""}
              </span>
              <div className="admin-corpus-tree-actions">
                <button
                  className="admin-scraping-delete-btn"
                  onClick={() => handleDeleteFile(node.id)}
                  title="Supprimer"
                >
                  Supprimer
                </button>
              </div>
            </>
          )}

          {isFolder && (
            <>
              <span className="admin-corpus-tree-date"></span>
              <div className="admin-corpus-tree-actions"></div>
            </>
          )}

          {/* Indicateur de zone de drop pour les dossiers */}
          {isFolder && dropTarget === node.id && (
            <span className="admin-corpus-tree-drop-indicator">
              📁 Déposer ici
            </span>
          )}
        </div>

        {isFolder && node.isExpanded && hasChildren && (
          <div className="admin-corpus-tree-children">
            {node.children!.map((child) => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="admin-corpus-tree-wrapper">
        <div style={{ textAlign: "center", padding: "2rem" }}>
          <div className="spinner"></div>
          <p>Chargement de l'arborescence...</p>
        </div>
      </div>
    );
  }

  if (!corpusTree) {
    return (
      <div className="admin-corpus-tree-wrapper">
        <div style={{ textAlign: "center", padding: "2rem", color: "#666" }}>
          Erreur lors du chargement de l'arborescence
        </div>
      </div>
    );
  }
  return (
    <div 
      className={`admin-corpus-tree-wrapper ${isDragOverExternal ? 'external-drag-over' : ''} ${uploading ? 'uploading' : ''}`}
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
          ➕ Ajouter un PDF
        </button>
        <span className="admin-corpus-drag-hint">
          ou glissez-déposez vos fichiers PDF ici
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

      {/* Bouton pour ajouter des fichiers */}
      <div className="admin-corpus-add-file">
      </div>
    </div>
  );
});

AdminCorpusFileTree.displayName = "AdminCorpusFileTree";

export default AdminCorpusFileTree;
