// ==============================================
// Gestionnaire des appels API pour le corpus PDF
// ==============================================

// Types pour la gestion des fichiers et dossiers
export interface FileNode {
  id: string;
  name: string;
  path: string;
  type: "file" | "folder";
  size?: string;
  dateAdded?: string;
  dateModified?: string;
  children?: FileNode[];
  isExpanded?: boolean;
}

// Données mockées pour le développement (à remplacer par des appels API)
const mockCorpusTree: FileNode = {
  id: "root",
  name: "Corpus",
  path: "/corpus",
  type: "folder",
  isExpanded: true,
  children: [
    {
      id: "documents",
      name: "documents",
      path: "/corpus/documents",
      type: "folder",
      isExpanded: false,
      children: [
        {
          id: "doc1",
          name: "reglement.pdf",
          path: "/corpus/documents/reglement.pdf",
          type: "file",
          dateAdded: "2025-06-20",
          dateModified: "2025-06-20",
        },
        {
          id: "doc2",
          name: "charte.pdf",
          path: "/corpus/documents/charte.pdf",
          type: "file",
          dateAdded: "2025-06-19",
          dateModified: "2025-06-19",
        },
      ],
    },
    {
      id: "guides",
      name: "guides",
      path: "/corpus/guides",
      type: "folder",
      isExpanded: false,
      children: [
        {
          id: "guide1",
          name: "tutoriel.pdf",
          path: "/corpus/guides/tutoriel.pdf",
          type: "file",
          dateAdded: "2025-06-18",
          dateModified: "2025-06-18",
        },
      ],
    },
    {
      id: "faq",
      name: "faq",
      path: "/corpus/faq",
      type: "folder",
      isExpanded: false,
      children: [
        {
          id: "faq1",
          name: "FAQ_polytech.pdf",
          path: "/corpus/faq/FAQ_polytech.pdf",
          type: "file",
          dateAdded: "2025-06-15",
          dateModified: "2025-06-15",
        },
      ],
    },
    {
      id: "standalone1",
      name: "presentation_ecole.pdf",
      path: "/corpus/presentation_ecole.pdf",
      type: "file",
      dateAdded: "2025-06-10",
      dateModified: "2025-06-10",
    },
  ],
};

/**
 * Récupère l'arborescence complète du corpus
 * TODO: Remplacer par un vrai appel API
 */
export const fetchCorpusTree = async (): Promise<FileNode> => {
  // Simule un délai d'API
  await new Promise((resolve) => setTimeout(resolve, 100));
  return mockCorpusTree;
};

/**
 * Supprime un fichier du corpus
 * TODO: Remplacer par un vrai appel API
 */
export const deleteFile = async (fileId: string): Promise<void> => {
  // Simule un délai d'API
  await new Promise((resolve) => setTimeout(resolve, 200));
  console.log(`Suppression du fichier ${fileId} (API à implémenter)`);
  // TODO: Appel API DELETE /api/corpus/files/{fileId}
};

/**
 * Upload un nouveau fichier PDF dans le corpus
 * TODO: Remplacer par un vrai appel API
 */
export const uploadFile = async (
  file: File,
  path?: string
): Promise<FileNode> => {
  // Simule un délai d'API
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // TODO: Appel API POST /api/corpus/files avec FormData
  const newFile: FileNode = {
    id: `file_${Date.now()}`,
    name: file.name,
    path: path ? `${path}/${file.name}` : `/corpus/${file.name}`,
    type: "file",
    dateAdded: new Date().toISOString().split("T")[0],
    dateModified: new Date().toISOString().split("T")[0],
  };

  console.log(`Upload du fichier ${file.name} (API à implémenter)`);
  return newFile;
};

/**
 * Déplace un fichier vers un nouveau dossier
 * TODO: Remplacer par un vrai appel API
 */
export const moveFile = async (fileId: string, newPath: string): Promise<void> => {
  // Simule un délai d'API
  await new Promise(resolve => setTimeout(resolve, 300));
  console.log(`Déplacement du fichier ${fileId} vers ${newPath} (API à implémenter)`);
  // TODO: Appel API PUT /api/corpus/files/{fileId}/move
};

/**
 * Obtient l'URL de prévisualisation d'un fichier
 * TODO: Remplacer par un vrai appel API
 */
export const getFilePreviewUrl = async (fileId: string): Promise<string> => {
  // Simule un délai d'API
  await new Promise(resolve => setTimeout(resolve, 100));
  console.log(`Ouverture du fichier ${fileId} (API à implémenter)`);
  // TODO: Appel API GET /api/corpus/files/{fileId}/preview
  return `/api/corpus/files/${fileId}/preview`;
};

/**
 * Met à jour l'état d'expansion d'un dossier
 * Cette fonction est locale et ne nécessite pas d'appel API
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
 * Cette fonction est locale et ne nécessite pas d'appel API
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
 * Déplace un fichier dans l'arborescence locale (côté client)
 * Cette fonction est locale et ne nécessite pas d'appel API
 */
export const moveFileInTree = (tree: FileNode, fileId: string, targetFolderId: string): FileNode => {
  let movedFile: FileNode | null = null;
  
  // Fonction pour extraire le fichier de l'arborescence
  const extractFile = (node: FileNode): FileNode => {
    if (node.children) {
      const newChildren = node.children.filter(child => {
        if (child.id === fileId) {
          movedFile = child;
          return false;
        }
        return true;
      }).map(child => extractFile(child));
      
      return { ...node, children: newChildren };
    }
    return node;
  };
  
  // Fonction pour ajouter le fichier au dossier cible
  const addFileToFolder = (node: FileNode): FileNode => {
    if (node.id === targetFolderId && node.type === 'folder' && movedFile) {
      return {
        ...node,
        children: [...(node.children || []), movedFile]
      };
    }
    
    if (node.children) {
      return {
        ...node,
        children: node.children.map(child => addFileToFolder(child))
      };
    }
    
    return node;
  };
  
  // Exécuter le déplacement
  const treeWithoutFile = extractFile(tree);
  return movedFile ? addFileToFolder(treeWithoutFile) : tree;
};

/**
 * Vérifie si un nœud est un descendant d'un autre nœud
 * Empêche de déplacer un dossier dans lui-même ou ses sous-dossiers
 */
export const isDescendant = (tree: FileNode, ancestorId: string, nodeId: string): boolean => {
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
  
  const checkDescendant = (node: FileNode): boolean => {
    if (node.id === nodeId) return true;
    
    if (node.children) {
      return node.children.some(child => checkDescendant(child));
    }
    
    return false;
  };
  
  const ancestorNode = findNode(tree, ancestorId);
  return ancestorNode ? checkDescendant(ancestorNode) : false;
};

// ==============================================
// FONCTIONS DE HAUT NIVEAU POUR LES COMPOSANTS
// ==============================================

/**
 * Gère la suppression complète d'un fichier (API + mise à jour locale)
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
    // Appel API pour supprimer le fichier
    await deleteFile(fileId);

    // Mise à jour locale de l'arborescence
    const updatedTree = removeFileFromTree(currentTree, fileId);

    // Callback optionnel pour notifier le succès
    onSuccess?.(fileId);

    return updatedTree;
  } catch (error) {
    console.error("Erreur lors de la suppression:", error);
    alert("Erreur lors de la suppression du fichier");
    throw error;
  }
};

/**
 * Gère le déplacement complet d'un fichier (API + mise à jour locale)
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

  try {
    // Mise à jour optimiste de l'UI
    const updatedTree = moveFileInTree(currentTree, draggedItem.id, targetNode.id);

    // Appel API pour déplacer le fichier
    await moveFile(draggedItem.id, targetNode.path);

    console.log(`Fichier ${draggedItem.name} déplacé vers ${targetNode.name}`);
    return updatedTree;
  } catch (error) {
    console.error("Erreur lors du déplacement:", error);
    alert("Erreur lors du déplacement du fichier");
    throw error;
  }
};

/**
 * Gère l'upload complet de fichiers (API + rechargement de l'arborescence)
 */
export const handleFileUpload = async (
  files: FileList,
  targetFolder?: FileNode,
  onFileUploaded?: (fileName: string) => void
): Promise<void> => {
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
};

/**
 * Gère l'ouverture d'un fichier
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
 * Crée un élément input pour sélectionner des fichiers via un bouton
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
