// ==============================================
// Gestionnaire des appels API pour le corpus PDF
// ==============================================

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
 * Récupère l'arborescence du corpus depuis l'API
 * @returns FileNode - L'arborescence des fichiers et dossiers du corpus
 */
export const fetchCorpusTree = async (): Promise<FileNode> => {
  try {
    // On récupère la liste des dossiers
    const dirsResponse = await fetch("/pdf_manual/admin/list-dirs");
    if (!dirsResponse.ok) {
      throw new Error(
        `Erreur lors de la récupération des dossiers: ${dirsResponse.status}`
      );
    }
    const dirsData = await dirsResponse.json();

    // On récupère tous les fichiers
    const allFilesResponse = await fetch("/pdf_manual/admin/list-all-files");
    if (!allFilesResponse.ok) {
      throw new Error(
        `Erreur lors de la récupération des fichiers: ${allFilesResponse.status}`
      );
    }
    const allFilesData = await allFilesResponse.json();

    // On construit l'arborescence
    const children: FileNode[] = [];

    // On ajoute les dossiers
    for (const dirName of dirsData.directories) {
      const dirFiles: FileNode[] = [];

      // On ajoute les fichiers de ce dossier
      for (const fileInfo of allFilesData.files) {
        if (fileInfo.dir === dirName) {
          dirFiles.push({
            id: `${dirName}_${fileInfo.file}`,
            name: fileInfo.file,
            path: `/corpus/${dirName}/${fileInfo.file}`,
            type: "file",
            dateAdded: new Date().toISOString().split("T")[0], // TODO: changer avec vraie date d'ajout
            dateModified: new Date().toISOString().split("T")[0], //TODO: changer avec vraie date de modif
          });
        }
      }

      children.push({
        id: dirName,
        name: dirName,
        path: `/corpus/${dirName}`,
        type: "folder",
        isExpanded: false,
        children: dirFiles,
      });
    }

    // On crée la racine
    const corpusTree: FileNode = {
      id: "root",
      name: "Corpus PDF",
      path: "/corpus",
      type: "folder",
      isExpanded: true,
      children: children,
    };

    return corpusTree;
  } catch (error) {
    console.error("Erreur lors du chargement du corpus :", error);
    throw error;
  }
};

/**
 * Obtient l'URL de prévisualisation d'un fichier
 * @param fileId - L'ID du fichier au format "dossier_nomfichier.pdf"
 * @returns l'URL pour prévisualiser un fichier PDF
 */
export const getFilePreviewUrl = async (fileId: string): Promise<string> => {
  try {
    const configResponse = await fetch("/pdf_manual/admin/config");
    if (!configResponse.ok) {
      throw new Error("Erreur lors de la récupération de la configuration");
    }
    const config = await configResponse.json();

    // On récupère tous les fichiers pour trouver le fichier correspondant à l'ID
    const allFilesResponse = await fetch("/pdf_manual/admin/list-all-files");
    if (!allFilesResponse.ok) {
      throw new Error("Erreur lors de la récupération des fichiers");
    }
    const allFilesData = await allFilesResponse.json();
    const fileInfo = allFilesData.files.find(
      (file: any) => `${file.dir}_${file.file}` === fileId
    );
    if (!fileInfo) {
      throw new Error(`Fichier non trouvé pour l'ID: ${fileId}`);
    }

    // On construit le chemin en utilisant les noms de dossier et fichier
    const filePath = `/${config.corpus_root_path}/${fileInfo.dir}/${fileInfo.file}`;
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
    let dirName = "autre"; // dossier par défaut
    if (targetFolder && targetFolder !== "/corpus") {
      // Extraire le nom du dossier depuis le path
      //TODO: changer pour pouvoir gérer les sous-dossiers (éventuellement upload dans corpus directement)
      const pathParts = targetFolder.split("/");
      if (pathParts.length >= 3) {
        dirName = pathParts[2];
      }
    }

    // On crée le FormData pour l'upload
    const formData = new FormData();
    formData.append("files", file);
    formData.append("dir", dirName);

    // On appelle l'API pour uploader le fichier
    const response = await fetch("/pdf_manual/admin/upload-files", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error(`Erreur lors de l'upload: ${response.status}`);
    }

    // On crée le nœud de fichier pour la réponse
    const newFile: FileNode = {
      id: `${dirName}_${file.name}`,
      name: file.name,
      path: `/corpus/${dirName}/${file.name}`,
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
 * @param fileId - L'ID du fichier au format "dossier_nomfichier.pdf"
 * @returns Promise qui se résout quand la suppression est terminée
 */
export const deleteFile = async (fileId: string): Promise<void> => {
  try {
    // On récupère tous les fichiers pour trouver le fichier correspondant à l'ID
    const allFilesResponse = await fetch("/pdf_manual/admin/list-all-files");
    if (!allFilesResponse.ok) {
      throw new Error("Erreur lors de la récupération des fichiers");
    }
    const allFilesData = await allFilesResponse.json();
    const fileInfo = allFilesData.files.find(
      (file: any) => `${file.dir}_${file.file}` === fileId
    );
    if (!fileInfo) {
      throw new Error(`Fichier non trouvé pour l'ID: ${fileId}`);
    }

    // On appelle l'API pour supprimer le fichier
    const response = await fetch(
      `/pdf_manual/admin/delete-file/${encodeURIComponent(
        fileInfo.dir
      )}/${encodeURIComponent(fileInfo.file)}`,
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
 * @param fileId - L'ID du fichier au format "dossier_nomfichier.pdf"
 * @param targetFolderId - L'ID du dossier de destination
 * @returns Promise qui se résout quand le déplacement est terminé
 */
export const moveFile = async (
  fileId: string,
  targetFolderId: string
): Promise<void> => {
  try {
    // On récupère tous les fichiers pour trouver le fichier correspondant à l'ID
    const allFilesResponse = await fetch("/pdf_manual/admin/list-all-files");
    if (!allFilesResponse.ok) {
      throw new Error("Erreur lors de la récupération des fichiers");
    }
    const allFilesData = await allFilesResponse.json();
    const fileInfo = allFilesData.files.find(
      (file: any) => `${file.dir}_${file.file}` === fileId
    );
    if (!fileInfo) {
      throw new Error(`Fichier non trouvé pour l'ID: ${fileId}`);
    }

    // On crée le FormData pour le déplacement
    const formData = new FormData();
    formData.append("dir", fileInfo.dir);
    formData.append("filename", fileInfo.file);
    formData.append("target_dir", targetFolderId);

    // On appelle l'API pour déplacer le fichier
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
