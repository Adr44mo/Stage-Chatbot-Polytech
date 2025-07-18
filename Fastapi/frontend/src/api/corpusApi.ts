// ==============================================
// Gestionnaire des appels API pour le corpus PDF
// ==============================================

import { runProcessingAndVectorization } from "./scrapingApi";

/**
 * Types pour la gestion des fichiers et dossiers
 */
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

/**
 * Interface pour les éléments de l'arborescence depuis l'API
 */
interface DirectoryItem {
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  date_added?: string;
  date_modified?: string;
  children?: DirectoryItem[];
}

/**
 * Récupère l'arborescence du corpus depuis l'API
 * @returns FileNode - L'arborescence des fichiers et dossiers du corpus
 */
export const fetchCorpusTree = async (): Promise<FileNode> => {
  try {
    const response = await fetch("/pdf_manual/admin/tree");
    if (!response.ok) {
      throw new Error(
        `Erreur lors de la récupération du corpus: ${response.status}`
      );
    }
    const data = await response.json();

    // Convertir l'arborescence de l'API en FileNode
    const convertToFileNode = (item: DirectoryItem): FileNode => {
      const node: FileNode = {
        id: item.path || item.name,
        name: item.name,
        path: item.path || item.name,
        type: item.type === "directory" ? "folder" : "file",
        dateAdded: item.date_added,
        dateModified: item.date_modified,
        isExpanded: item.type === "directory",
        size: item.size ? `${Math.round(item.size / 1024)} KB` : undefined,
      };

      if (item.children) {
        node.children = item.children.map(convertToFileNode);
      }

      return node;
    };

    // Créer le nœud racine
    const corpusTree: FileNode = {
      id: "root",
      name: "Corpus PDF",
      path: "",
      type: "folder",
      isExpanded: true,
      children: data.tree.map(convertToFileNode),
    };

    return corpusTree;
  } catch (error) {
    console.error("Erreur lors du chargement du corpus :", error);
    throw error;
  }
};

/**
 * Obtient l'URL de prévisualisation d'un fichier
 * @param fileId - Le chemin du fichier relatif au corpus
 * @returns l'URL pour prévisualiser un fichier PDF
 */
export const getFilePreviewUrl = async (fileId: string): Promise<string> => {
  try {
    const configResponse = await fetch("/pdf_manual/admin/config");
    if (!configResponse.ok) {
      throw new Error("Erreur lors de la récupération de la configuration");
    }
    const config = await configResponse.json();

    // On construit le chemin en utilisant le chemin relatif
    const filePath = `/${config.corpus_root_path}/${fileId}`;
    const fileUrl = `/files${encodeURIComponent(filePath)}`;

    return fileUrl;
  } catch (error) {
    console.error(
      "Erreur lors de la génération de l'URL de prévisualisation:",
      error
    );
    throw error;
  }
};

/**
 * Upload un nouveau fichier PDF dans le corpus
 * @param file - Le fichier à uploader
 * @param targetFolder - Le dossier cible (utilise le dossier "autre" par défaut)
 * @returns le nouveau nœud de fichier
 */
export const uploadFile = async (
  file: File,
  targetFolder?: string
): Promise<FileNode> => {
  try {
    let dirPath = "autre"; // dossier par défaut
    if (targetFolder && targetFolder !== "" && targetFolder !== "root") {
      dirPath = targetFolder;
    }

    // On crée le FormData pour l'upload
    const formData = new FormData();
    formData.append("files", file);
    formData.append("dir", dirPath);

    // On appelle l'API pour uploader le fichier
    const response = await fetch("/pdf_manual/admin/upload-files", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`Erreur lors de l'upload: ${response.status}`);
    }

    // On crée le nœud de fichier pour la réponse
    const filePath = targetFolder ? `${targetFolder}/${file.name}` : file.name;
    const newFile: FileNode = {
      id: filePath,
      name: file.name,
      path: filePath,
      type: "file",
      dateAdded: new Date().toISOString().split("T")[0],
      dateModified: new Date().toISOString().split("T")[0],
    };

    return newFile;
  } catch (error) {
    console.error("Erreur lors de l'upload:", error);
    throw error;
  }
};

/**
 * Supprime un fichier du corpus
 * @param fileId - Le chemin du fichier relatif au corpus
 * @returns Promise qui se résout quand la suppression est terminée
 */
export const deleteFile = async (fileId: string): Promise<void> => {
  try {
    const response = await fetch(
      `/pdf_manual/admin/delete-file?file_path=${encodeURIComponent(fileId)}`,
      {
        method: "DELETE",
      }
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors de la suppression: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors de la suppression:", error);
    throw error;
  }
};

/**
 * Déplace un fichier vers un nouveau dossier
 * @param fileId - Le chemin du fichier relatif au corpus
 * @param targetFolderId - Le chemin du dossier de destination
 * @returns Promise qui se résout quand le déplacement est terminé
 */
export const moveFile = async (
  fileId: string,
  targetFolderId: string
): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append("source_path", fileId);
    formData.append("target_path", targetFolderId);

    const response = await fetch("/pdf_manual/admin/move-file", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors du déplacement: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors du déplacement:", error);
    throw error;
  }
};

/**
 * Crée un nouveau dossier
 * @param dirPath - Le chemin du dossier à créer
 * @returns Promise qui se résout quand la création est terminée
 */
export const createDirectory = async (dirPath: string): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append("dir_path", dirPath);

    const response = await fetch("/pdf_manual/admin/create-dir", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors de la création: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors de la création du dossier:", error);
    throw error;
  }
};

/**
 * Supprime un dossier
 * @param dirPath - Le chemin du dossier à supprimer
 * @param force - Forcer la suppression même si le dossier n'est pas vide
 * @returns Promise qui se résout quand la suppression est terminée
 */
export const deleteDirectory = async (
  dirPath: string,
  force: boolean = false
): Promise<void> => {
  try {
    const response = await fetch(
      `/pdf_manual/admin/delete-dir?dir_path=${encodeURIComponent(
        dirPath
      )}&force=${force}`,
      {
        method: "DELETE",
      }
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors de la suppression: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors de la suppression du dossier:", error);
    throw error;
  }
};

/**
 * Renomme un fichier
 * @param filePath - Le chemin du fichier à renommer
 * @param newName - Le nouveau nom du fichier
 * @returns Promise qui se résout quand le renommage est terminé
 */
export const renameFile = async (
  filePath: string,
  newName: string
): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append("file_path", filePath);
    formData.append("new_name", newName);

    const response = await fetch("/pdf_manual/admin/rename-file", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors du renommage: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors du renommage:", error);
    throw error;
  }
};

/**
 * Renomme un dossier
 * @param dirPath - Le chemin du dossier à renommer
 * @param newName - Le nouveau nom du dossier
 * @returns Promise qui se résout quand le renommage est terminé
 */
export const renameDirectory = async (
  dirPath: string,
  newName: string
): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append("dir_path", dirPath);
    formData.append("new_name", newName);

    const response = await fetch("/pdf_manual/admin/rename-dir", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors du renommage: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors du renommage du dossier:", error);
    throw error;
  }
};

/**
 * Déplace un dossier vers un nouveau parent
 * @param sourcePath - Le chemin du dossier à déplacer
 * @param targetPath - Le chemin du dossier parent de destination
 * @returns Promise qui se résout quand le déplacement est terminé
 */
export const moveDirectory = async (
  sourcePath: string,
  targetPath: string
): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append("source_path", sourcePath);
    formData.append("target_path", targetPath);

    const response = await fetch("/pdf_manual/admin/move-dir", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors du déplacement: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors du déplacement du dossier:", error);
    throw error;
  }
};

/**
 * Obtient les informations sur un dossier
 * @param dirPath - Le chemin du dossier
 * @returns Promise avec les informations du dossier
 */
export const getDirectoryInfo = async (dirPath: string = ""): Promise<any> => {
  try {
    const response = await fetch(
      `/pdf_manual/admin/dir-info?dir_path=${encodeURIComponent(dirPath)}`
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          `Erreur lors de la récupération des informations: ${response.status}`
      );
    }
    return await response.json();
  } catch (error) {
    console.error(
      "Erreur lors de la récupération des informations du dossier:",
      error
    );
    throw error;
  }
};

/**
 * Active le mode édition
 * @returns Promise avec l'ID du snapshot
 */
export const enableEditMode = async (): Promise<string> => {
  try {
    const response = await fetch("/pdf_manual/admin/enable-edit-mode", {
      method: "POST",
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          `Erreur lors de l'activation du mode édition: ${response.status}`
      );
    }
    const data = await response.json();
    return data.snapshot_id;
  } catch (error) {
    console.error("Erreur lors de l'activation du mode édition:", error);
    throw error;
  }
};

/**
 * Sauvegarde les changements
 * @param snapshotId - L'ID du snapshot
 * @returns Promise qui se résout quand la sauvegarde est terminée
 */
export const saveChanges = async (snapshotId: string): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append("snapshot_id", snapshotId);

    const response = await fetch("/pdf_manual/admin/save-changes", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors de la sauvegarde: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors de la sauvegarde:", error);
    throw error;
  }
};

/**
 * Annule les changements
 * @param snapshotId - L'ID du snapshot
 * @returns Promise qui se résout quand l'annulation est terminée
 */
export const cancelChanges = async (snapshotId: string): Promise<void> => {
  try {
    const formData = new FormData();
    formData.append("snapshot_id", snapshotId);

    const response = await fetch("/pdf_manual/admin/cancel-changes", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Erreur lors de l'annulation: ${response.status}`
      );
    }
  } catch (error) {
    console.error("Erreur lors de l'annulation:", error);
    throw error;
  }
};

/**
 * Obtient le statut du mode édition
 * @returns Promise avec le statut du mode édition
 */
export const getEditStatus = async (): Promise<any> => {
  try {
    const response = await fetch("/pdf_manual/admin/edit-status");
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          `Erreur lors de la récupération du statut: ${response.status}`
      );
    }
    return await response.json();
  } catch (error) {
    console.error("Erreur lors de la récupération du statut:", error);
    throw error;
  }
};

/**
 * Lance le traitement et la vectorisation du corpus
 * (réutilise la même logique que pour le scraping)
 * @returns Promise qui se résout quand la vectorisation est terminée
 */
export const runCorpusVectorization = runProcessingAndVectorization;

//TODO: rajouter les autres fonctions pour la barre de progression ou les importer direct
