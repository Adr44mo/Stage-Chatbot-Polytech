// ===================================================
// Fonctions utilitaires pour la gestion du corpus PDF
// ===================================================

import type { FileNode } from "../api/corpusApi";
import {
  deleteFile,
  moveFile,
  moveDirectory,
  uploadFile,
  getFilePreviewUrl,
} from "../api/corpusApi";

// ========================================
// Fonctions de manipulation d'arborescence
// ========================================

/**
 * Met à jour l'état d'expansion (ouvert/fermé) d'un dossier dans l'arborescence
 * @param tree - l'arborescence de fichiers
 * @param nodeId - l'ID du nœud à modifier
 * @returns la nouvelle arborescence avec l'état mis à jour
 */
export const updateFolderExpansion = (
  tree: FileNode,
  nodeId: string
): FileNode => {
  const updateTree = (node: FileNode): FileNode => {
    if (node.id === nodeId && node.type === "folder") {
      return { ...node, isExpanded: !node.isExpanded };
    }
    if (node.children) {
      return {
        ...node,
        children: node.children.map((child) => updateTree(child)),
      };
    }
    return node;
  };
  return updateTree(tree);
};

/**
 * Supprime un fichier de l'arborescence locale
 * @param tree - l'arborescence de fichiers
 * @param fileId - l'ID du fichier à supprimer
 * @returns la nouvelle arborescence sans le fichier
 */
export const removeFileFromTree = (
  tree: FileNode,
  fileId: string
): FileNode => {
  const updateTree = (node: FileNode): FileNode => {
    if (node.children) {
      return {
        ...node,
        children: node.children
          .filter((child) => {
            if (child.id === fileId) return false;
            return true;
          })
          .map((child) => updateTree(child)),
      };
    }
    return node;
  };
  return updateTree(tree);
};

/**
 * Déplace un fichier dans l'arborescence locale
 * @param tree - l'arborescence de fichiers
 * @param fileId - l'ID du fichier à déplacer
 * @param targetFolderId - l'ID du dossier de destination
 * @returns la nouvelle arborescence avec le fichier déplacé
 */
export const moveFileInTree = (
  tree: FileNode,
  fileId: string,
  targetFolderId: string
): FileNode => {
  let movedFile: FileNode | null = null;

  // Fonction pour extraire le fichier de l'arborescence
  const extractFile = (node: FileNode): FileNode => {
    if (node.children) {
      const newChildren = node.children
        .filter((child) => {
          if (child.id === fileId) {
            movedFile = child;
            return false;
          }
          return true;
        })
        .map((child) => extractFile(child));

      return { ...node, children: newChildren };
    }
    return node;
  };

  // Fonction pour ajouter le fichier au dossier de destination
  const addFileToFolder = (node: FileNode): FileNode => {
    if (node.id === targetFolderId && node.type === "folder" && movedFile) {
      return {
        ...node,
        children: [...(node.children || []), movedFile],
      };
    }

    if (node.children) {
      return {
        ...node,
        children: node.children.map((child) => addFileToFolder(child)),
      };
    }

    return node;
  };

  // On fait le déplacement
  const treeWithoutFile = extractFile(tree);
  return movedFile ? addFileToFolder(treeWithoutFile) : tree;
};

/**
 * Vérifie si un nœud est un descendant d'un autre nœud
 * @param tree - l'arborescence de fichiers
 * @param ancestorId - l'ID du nœud ancêtre
 * @param nodeId - l'ID du nœud à vérifier
 * @returns true si le nœud est un descendant de l'ancêtre
 */
export const isDescendant = (
  tree: FileNode,
  ancestorId: string,
  nodeId: string
): boolean => {
  // Fonction récursive pour trouver le nœud ancêtre
  const findNode = (node: FileNode, targetId: string): FileNode | null => {
    if (node.id === targetId) return node;
    if (node.children) {
      for (const child of node.children) {
        const found = findNode(child, targetId);
        if (found) return found;
      }
    }
    return null;
  };

  // Fonction récursive pour vérifier si le nœud est un descendant
  const checkDescendant = (node: FileNode): boolean => {
    if (node.id === nodeId) return true;
    if (node.children) {
      return node.children.some((child) => checkDescendant(child));
    }
    return false;
  };

  // On cherche le nœud ancêtre dans l'arborescence
  const ancestorNode = findNode(tree, ancestorId);
  return ancestorNode ? checkDescendant(ancestorNode) : false;
};

/**
 * Crée un élément input pour sélectionner des fichiers via un bouton
 * @param onFilesSelected - callback appelé avec les fichiers sélectionnés
 */
export const createFileInput = (
  onFilesSelected: (files: FileList) => void
): void => {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "application/pdf";
  input.multiple = true;
  input.onchange = (e) => {
    const files = (e.target as HTMLInputElement).files;
    if (files) {
      onFilesSelected(files);
    }
  };
  input.click();
};

// ======================================================
// Fonctions de gestion des fichiers (API + arborescence)
// ======================================================

/**
 * Gère la suppression d'un fichier (API + mise à jour locale)
 * @param fileId - l'ID du fichier à supprimer
 * @param currentTree - l'arborescence actuelle
 * @param onSuccess - callback appelé en cas de succès
 * @returns la nouvelle arborescence mise à jour
 */
export const handleFileDelete = async (
  fileId: string,
  currentTree: FileNode,
  onSuccess?: (fileId: string) => void
): Promise<FileNode> => {
  if (!confirm("Êtes-vous sûr de vouloir supprimer ce fichier ?")) {
    return currentTree;
  }

  try {
    await deleteFile(fileId);
    const updatedTree = removeFileFromTree(currentTree, fileId);
    onSuccess?.(fileId); // callback optionnel pour notifier le succès
    return updatedTree;
  } catch (error) {
    console.error("Erreur lors de la suppression:", error);
    alert("Erreur lors de la suppression du fichier");
    throw error;
  }
};

/**
 * Gère le déplacement d'un fichier (API + mise à jour locale)
 * @param draggedItem - le fichier à déplacer
 * @param targetNode - le dossier de destination
 * @param currentTree - l'arborescence actuelle
 * @returns la nouvelle arborescence mise à jour
 */
export const handleFileMove = async (
  draggedItem: FileNode,
  targetNode: FileNode,
  currentTree: FileNode
): Promise<FileNode> => {
  if (
    !draggedItem ||
    targetNode.type !== "folder" ||
    draggedItem.id === targetNode.id
  ) {
    return currentTree;
  }

  // On vérifie si le fichier est déjà dans le dossier cible
  if (draggedItem.type === "file") {
    const lastUnderscoreIndex = draggedItem.id.lastIndexOf("_");
    if (lastUnderscoreIndex !== -1) {
      const sourceFolder = draggedItem.id.substring(0, lastUnderscoreIndex);
      if (sourceFolder === targetNode.id) {
        return currentTree;
      }
    }
  }

  try {
    // Mise à jour de l'UI
    const updatedTree = moveFileInTree(
      currentTree,
      draggedItem.id,
      targetNode.id
    );
    // Appel API pour déplacer le fichier
    await moveFile(draggedItem.id, targetNode.id);
    return updatedTree;
  } catch (error) {
    console.error("Erreur lors du déplacement:", error);
    alert("Erreur lors du déplacement du fichier");
    throw error;
  }
};

/**
 * Gère l'upload des fichiers (API + rechargement du corpus)
 * @param files - liste des fichiers à uploader
 * @param targetFolder - dossier cible (optionnel)
 * @param onFileUploaded - callback appelé après chaque upload réussi
 */
export const handleFileUpload = async (
  files: FileList,
  targetFolder?: FileNode,
  onFileUploaded?: (fileName: string) => void
): Promise<void> => {
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (file.type === "application/pdf") {
      try {
        // On utiliser l'API d'upload avec le chemin du dossier cible
        const targetPath = targetFolder?.path;
        await uploadFile(file, targetPath);

        // On notifie le composant parent
        onFileUploaded?.(file.name);
      } catch (error) {
        console.error(`Erreur upload ${file.name}:`, error);
        alert(`Erreur lors de l'upload de ${file.name}`);
      }
    } else {
      alert(`Le fichier ${file.name} n'est pas un PDF`);
    }
  }
};

/**
 * Gère l'ouverture d'un fichier
 * @param node - le fichier à ouvrir
 */
export const handleFileOpen = async (node: FileNode): Promise<void> => {
  if (node.type !== "file") return;

  try {
    const previewUrl = await getFilePreviewUrl(node.id);
    window.open(previewUrl, "_blank");
  } catch (error) {
    console.error("Erreur lors de l'ouverture du fichier:", error);
    alert("Erreur lors de l'ouverture du fichier");
  }
};

/**
 * Déplace un dossier dans l'arborescence locale
 * @param tree - l'arborescence de fichiers
 * @param folderId - l'ID du dossier à déplacer
 * @param targetFolderId - l'ID du dossier de destination
 * @returns la nouvelle arborescence avec le dossier déplacé
 */
export const moveFolderInTree = (
  tree: FileNode,
  folderId: string,
  targetFolderId: string
): FileNode => {
  let movedFolder: FileNode | null = null;

  /**
   * Fonction pour extraire le dossier de l'arborescence
   */
  const extractFolder = (node: FileNode): FileNode => {
    if (node.children) {
      const newChildren = node.children
        .filter((child) => {
          if (child.id === folderId) {
            movedFolder = child;
            return false;
          }
          return true;
        })
        .map((child) => extractFolder(child));

      return { ...node, children: newChildren };
    }
    return node;
  };

  /**
   * Fonction pour ajouter le dossier au dossier de destination
   */
  const addFolderToTarget = (node: FileNode): FileNode => {
    if (node.id === targetFolderId && node.type === "folder" && movedFolder) {
      return {
        ...node,
        children: [...(node.children || []), movedFolder],
      };
    }

    if (node.children) {
      return {
        ...node,
        children: node.children.map((child) => addFolderToTarget(child)),
      };
    }

    return node;
  };

  // Exécution du déplacement
  const treeWithoutFolder = extractFolder(tree);
  return movedFolder ? addFolderToTarget(treeWithoutFolder) : tree;
};

/**
 * Gère le déplacement d'un dossier (API + mise à jour locale)
 * @param draggedFolder - le dossier à déplacer
 * @param targetNode - le dossier de destination
 * @param currentTree - l'arborescence actuelle
 * @returns la nouvelle arborescence mise à jour
 */
export const handleFolderMove = async (
  draggedFolder: FileNode,
  targetNode: FileNode,
  currentTree: FileNode
): Promise<FileNode> => {
  try {
    // Mise à jour optimiste de l'arborescence locale
    const updatedTree = moveFolderInTree(
      currentTree,
      draggedFolder.id,
      targetNode.id
    );

    // Appel API pour déplacer le dossier
    await moveDirectory(draggedFolder.path, targetNode.path);

    return updatedTree;
  } catch (error) {
    console.error("Erreur lors du déplacement du dossier:", error);
    alert("Erreur lors du déplacement du dossier");
    throw error;
  }
};
