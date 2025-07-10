// ==========================================================
// Composant AdminCorpusTreeNode
// Gestion d'un seul nœud (fichier/dossier) de l'arborescence
// ==========================================================

import { useState } from "react";
import type { FileNode } from "../../api/corpusApi";
import { 
  renameFile, 
  renameDirectory, 
  createDirectory, 
  deleteDirectory, 
  getDirectoryInfo 
} from "../../api/corpusApi";

// Import des icônes SVG
import deleteIcon from "../../assets/delete.svg";
import editIcon from "../../assets/rename.svg";
import createFolderIcon from "../../assets/folder.svg";

// Interface qui définit toutes les props que ce composant reçoit du parent
interface AdminCorpusTreeNodeProps {
  node: FileNode; // données du fichier/dossier à afficher
  depth?: number; // profondeur dans l'arbre
  draggedItem: FileNode | null; // fichier qui est actuellement en train d'être déplacé
  dropTarget: string | null; // dossier qu'on survole pour déposer
  editMode?: boolean; // mode édition activé ou non

  // Fonctions de callback (le parent nous dit quoi faire quand quelque chose arrive)
  onDragStart: (e: React.DragEvent, node: FileNode) => void;
  onDragOver: (e: React.DragEvent, targetNode: FileNode) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent, targetNode: FileNode) => Promise<void>;
  onToggleFolder: (nodeId: string) => void;
  onFileClick: (node: FileNode) => Promise<void>;
  onDeleteFile: (fileId: string) => Promise<void>;
  onRefresh?: () => void; // Pour rafraîchir l'arborescence après une action
}

const AdminCorpusTreeNode: React.FC<AdminCorpusTreeNodeProps> = ({
  node,
  depth = 0, // On est à la racine par défaut (profondeur 0)
  draggedItem,
  dropTarget,
  editMode = false,
  onDragStart,
  onDragOver,
  onDragLeave,
  onDrop,
  onToggleFolder,
  onFileClick,
  onDeleteFile,
  onRefresh,
}) => {
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(node.name);

  // Variables pour savoir quel type de nœud on affiche
  const isFile = node.type === "file";
  const isFolder = node.type === "folder";
  const hasChildren = node.children && node.children.length > 0;
  const isRootCorpus = node.id === "root" || node.path === "";

  // Gestion du renommage
  const handleRename = async () => {
    if (!newName.trim() || newName === node.name) {
      setIsRenaming(false);
      setNewName(node.name);
      return;
    }

    try {
      if (isFile) {
        await renameFile(node.path, newName);
      } else {
        await renameDirectory(node.path, newName);
      }
      onRefresh?.();
      setIsRenaming(false);
    } catch (error) {
      console.error("Erreur lors du renommage:", error);
      alert("Erreur lors du renommage");
      setNewName(node.name);
      setIsRenaming(false);
    }
  };

  // Gestion de la suppression de dossier
  const handleDeleteFolder = async () => {
    if (isRootCorpus) return;
    
    try {
      const dirInfo = await getDirectoryInfo(node.path);
      const confirmMessage = dirInfo.file_count > 0 
        ? `Êtes-vous sûr de vouloir supprimer le dossier "${node.name}" ? Cela supprimera ${dirInfo.file_count} fichier(s) et ${dirInfo.dir_count} sous-dossier(s). Cette action ne peut pas être annulée.`
        : `Êtes-vous sûr de vouloir supprimer le dossier "${node.name}" ?`;
      
      if (!confirm(confirmMessage)) return;
      
      await deleteDirectory(node.path, true);
      onRefresh?.();
    } catch (error) {
      console.error("Erreur lors de la suppression du dossier:", error);
      alert("Erreur lors de la suppression du dossier");
    }
  };

  // Gestion de la création de sous-dossier
  const handleCreateSubfolder = async () => {
    const folderName = prompt("Nom du nouveau dossier:");
    if (!folderName?.trim()) return;
    
    try {
      const subfolderPath = node.path ? `${node.path}/${folderName}` : folderName;
      await createDirectory(subfolderPath);
      onRefresh?.();
    } catch (error) {
      console.error("Erreur lors de la création du dossier:", error);
      alert("Erreur lors de la création du dossier");
    }
  };

  return (
    <div className="admin-corpus-tree-node">
      <div
        className={`admin-corpus-tree-item ${isFile ? "file" : "folder"} ${
          draggedItem?.id === node.id ? "dragging" : ""
        } ${dropTarget === node.id ? "drag-over" : ""}`}
        style={{ paddingLeft: `${depth * 20}px` }}
        draggable={isFile && editMode}
        onDragStart={(e) => isFile && editMode && onDragStart(e, node)}
        onDragOver={(e) => isFolder && editMode && onDragOver(e, node)}
        onDragLeave={editMode ? onDragLeave : undefined}
        onDrop={(e) => isFolder && editMode && onDrop(e, node)}
      >
        {isFolder && (
          <button
            className="admin-corpus-tree-toggle"
            onClick={() => onToggleFolder(node.id)}
          >
            {node.isExpanded ? "📂" : "📁"}
          </button>
        )}

        {isFile && <span className="admin-corpus-tree-file-icon">📄</span>}

        <span
          className={`admin-corpus-tree-name ${isFile ? "clickable" : ""} ${
            isFolder ? "folder-clickable" : ""
          }`}
          onClick={() => {
            if (isRenaming) return;
            if (isFile) {
              onFileClick(node);
            } else if (isFolder) {
              onToggleFolder(node.id);
            }
          }}
          title={
            isFile
              ? "Cliquer pour ouvrir le fichier"
              : isFolder
              ? "Cliquer pour ouvrir/fermer le dossier"
              : ""
          }
        >
          {isRenaming ? (
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onBlur={handleRename}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleRename();
                if (e.key === "Escape") {
                  setIsRenaming(false);
                  setNewName(node.name);
                }
              }}
              className="admin-corpus-rename-input"
              autoFocus
            />
          ) : (
            node.name
          )}
        </span>

        {isFile && (
          <>
            <span className="admin-corpus-tree-date">
              {node.dateAdded
                ? new Date(node.dateAdded).toLocaleDateString("fr-FR")
                : ""}
            </span>
            <div className="admin-corpus-tree-actions">
              {editMode && (
                <>
                  <button
                    className="admin-corpus-action-btn admin-corpus-rename-btn"
                    onClick={() => setIsRenaming(true)}
                    title="Renommer"
                  >
                    <img src={editIcon} alt="Renommer" width="20" height="20" />
                  </button>
                  <button
                    className="admin-corpus-action-btn admin-corpus-delete-btn"
                    onClick={() => onDeleteFile(node.id)}
                    title="Supprimer"
                  >
                    <img src={deleteIcon} alt="Supprimer" width="20" height="20" />
                  </button>
                </>
              )}
            </div>
          </>
        )}

        {isFolder && (
          <>
            <span className="admin-corpus-tree-date"></span>
            <div className="admin-corpus-tree-actions">
              {editMode && (
                <>
                  <button
                    className="admin-corpus-action-btn admin-corpus-create-btn"
                    onClick={handleCreateSubfolder}
                    title="Créer un sous-dossier"
                  >
                    <img src={createFolderIcon} alt="Créer un sous-dossier" width="20" height="20" />
                  </button>
                  {!isRootCorpus && (
                    <>
                      <button
                        className="admin-corpus-action-btn admin-corpus-rename-btn"
                        onClick={() => setIsRenaming(true)}
                        title="Renommer"
                      >
                        <img src={editIcon} alt="Renommer" width="20" height="20" />
                      </button>
                      <button
                        className="admin-corpus-action-btn admin-corpus-delete-btn"
                        onClick={handleDeleteFolder}
                        title="Supprimer"
                      >
                        <img src={deleteIcon} alt="Supprimer" width="20" height="20" />
                      </button>
                    </>
                  )}
                </>
              )}
            </div>
          </>
        )}

        {isFolder && dropTarget === node.id && editMode && (
          <span className="admin-corpus-tree-drop-indicator">
            📁 Déposer ici
          </span>
        )}
      </div>

      {/* Si c'est un dossier ouvert qui a des fichiers dedans, on les affiche */}
      {isFolder && node.isExpanded && hasChildren && (
        <div className="admin-corpus-tree-children">
          {/* Pour chaque enfant, on crée un nouveau AdminCorpusTreeNode récursivement*/}
          {node.children!.map((child) => (
            <AdminCorpusTreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              draggedItem={draggedItem}
              dropTarget={dropTarget}
              editMode={editMode}
              onDragStart={onDragStart}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              onToggleFolder={onToggleFolder}
              onFileClick={onFileClick}
              onDeleteFile={onDeleteFile}
              onRefresh={onRefresh}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminCorpusTreeNode;
