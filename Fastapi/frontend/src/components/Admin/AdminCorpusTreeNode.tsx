// ==========================================================
// Composant AdminCorpusTreeNode
// Gestion d'un seul nœud (fichier/dossier) de l'arborescence
// ==========================================================

import type { FileNode } from "../../api/corpusApi";

// Interface qui définit toutes les props que ce composant reçoit du parent
interface AdminCorpusTreeNodeProps {
  node: FileNode; // données du fichier/dossier à afficher
  depth?: number; // profondeur dans l'arbre
  draggedItem: FileNode | null; // fichier qui est actuellement en train d'être déplacé
  dropTarget: string | null; // dossier qu'on survole pour déposer

  // Fonctions de callback (le parent nous dit quoi faire quand quelque chose arrive)
  onDragStart: (e: React.DragEvent, node: FileNode) => void;
  onDragOver: (e: React.DragEvent, targetNode: FileNode) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent, targetNode: FileNode) => Promise<void>;
  onToggleFolder: (nodeId: string) => void;
  onFileClick: (node: FileNode) => Promise<void>;
  onDeleteFile: (fileId: string) => Promise<void>;
}

const AdminCorpusTreeNode: React.FC<AdminCorpusTreeNodeProps> = ({
  node,
  depth = 0, // On est à la racine par défaut (profondeur 0)
  draggedItem,
  dropTarget,
  onDragStart,
  onDragOver,
  onDragLeave,
  onDrop,
  onToggleFolder,
  onFileClick,
  onDeleteFile,
}) => {
  // Variables pour savoir quel type de nœud on affiche
  const isFile = node.type === "file";
  const isFolder = node.type === "folder";
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="admin-corpus-tree-node">
      <div
        className={`admin-corpus-tree-item ${isFile ? "file" : "folder"} ${
          draggedItem?.id === node.id ? "dragging" : ""
        } ${dropTarget === node.id ? "drag-over" : ""}`}
        style={{ paddingLeft: `${depth * 20}px` }}
        draggable={isFile}
        onDragStart={(e) => isFile && onDragStart(e, node)}
        onDragOver={(e) => isFolder && onDragOver(e, node)}
        onDragLeave={onDragLeave}
        onDrop={(e) => isFolder && onDrop(e, node)}
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
                onClick={() => onDeleteFile(node.id)}
                title="Supprimer"
              >
                Supprimer
              </button>
            </div>
          </>
        )}

        {isFolder && (
          <>
            <span className="admin-corpus-tree-date"></span>{" "}
            <div className="admin-corpus-tree-actions"></div>{" "}
          </>
        )}

        {isFolder && dropTarget === node.id && (
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
              onDragStart={onDragStart}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              onToggleFolder={onToggleFolder}
              onFileClick={onFileClick}
              onDeleteFile={onDeleteFile}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminCorpusTreeNode;
