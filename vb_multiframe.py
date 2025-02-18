# Multi-frame tkinter application v2.3
import tkinter as tk
from tkinter import filedialog, messagebox
from langchain.document_loaders import JSONLoader
from langchain.embeddings import OpenAIEmbeddings
# from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os
import json
from uuid import uuid4
import PyPDF2
import fnmatch
import re
import shutil


class SampleApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Chroma Processor")
        self._frame = None
        self.switch_frame(StartPage)

    def switch_frame(self, frame_class):
        #faudrait ajouter une possibilité avec genre des kwargs pour rajouter des variables à passer en argument aux nouvelles frames
        """Destroys current frame and replaces it with a new one of the new class (is the new class is the same as the old one, nothing happens)"""
        new_frame = frame_class(self)
        if self._frame is not None: #if there is a frame
            self._frame.destroy() #destroy it
        self._frame = new_frame #replace with the new frame (which is frame_class)
        self._frame.pack()

    def destructor(self) :
        self.destroy()
    
    def walk(self, path, file_extension) :
        corpus = [os.path.join(dirpath, f) for dirpath, dirnames, files in os.walk(path) for f in fnmatch.filter(files, f'*.{file_extension}')]
        return corpus
    

    def process_folder(self, folder_path,db_name):
        SPECIALTIES = ["AGRAL (Agroalimentaire)", "EISE (Électronique - Informatique Parcours systèmes embarqués)", "EI2I (Électronique - Informatique Parcours informatique industrielle)", "GM (Génie Mécanique)", "MAIN (Mathématiques appliquées et informatique)", "MTX (Matériaux - Chimie)", "ROB (Robotique)", "ST (Sciences de la terre : aménagement, environnement, énergie)"]
        SPECIALITIES_short = {"AGRAL" : "AGRAL (Agroalimentaire)", 
                              "EISE" : "EISE (Électronique - Informatique Parcours systèmes embarqués)", 
                              "EI2I" : "EI2I (Électronique - Informatique Parcours informatique industrielle)", 
                              "GM" : "GM (Génie Mécanique)", 
                              "MAIN" : "MAIN (Mathématiques appliquées et informatique)", 
                              "MTX" : "MTX (Matériaux - Chimie)", 
                              "ROB" : "ROB (Robotique)", 
                               "ST" : "ST (Sciences de la terre : aménagement, environnement, énergie)"}
        try:
            # Initialise les documents
            documents = []
            #Traiter les JSON
            json_corpus = self.walk(folder_path,'json')
            for json_file in json_corpus:
                try :
                    loader = JSONLoader(
                        file_path=json_file,
                        jq_schema=".content",
                    )
                    unique_id = str(uuid4())
                    json_docs = loader.load()

                    

                    # Extraire et ajouter les métadonnées pour chaque document
                    # Parce qu'en fait, les json sont direct au format document en gros ; et ducoup on fait que ajouter des metadata sur chaque parties
                    for doc in json_docs:
                        statut = "N/A"
                        speciality = None
                        #on peut ensuite faire le même genre de mic mac pour discerner les informations des spés
                        if 'pub' in json_file : statut = 'publique'
                        else : statut = "privé"

                        for x in SPECIALTIES :
                            if x in json_file : 
                                speciality = x 
                                break
                       


                        json_data = json.load(open(doc.metadata["source"], 'r'))
                         #Si on a rien trouvé
                        if speciality == None :
                            spec = json_data.get("filierespecifique", None)
                            if spec :
                                if spec not in SPECIALTIES :
                                    speciality = SPECIALITIES_short.get(spec,None) #On cherche dans la version abregé
                                    if speciality != None : break #print(f"Spec trouvée pour {json_file} : {speciality}")
                                    else : speciality = "None"
                        metadata = {
                            "ID": unique_id,
                            "URL": json_data.get("url", ""),
                            "Status" : statut,
                            "Speciality" : speciality,
                            "Source": json_file,
                        }
                        doc.metadata.update(metadata)
                    documents.extend(json_docs)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors du traitement de {json_file} : {str(e)}")

            # Traiter les PDF
            pdf_corpus = self.walk(folder_path, 'pdf')
            for pdf_file in pdf_corpus:
                try:
                    # Extraction de texte du PDF
                    # print("processing ", pdf_file)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = "".join(page.extract_text() for page in pdf_reader.pages) #texte de toutes les pages
                    if text :
                        #remplace dans texte tout ce qui est au moins 3 retours à la ligne consecutifs par un retour à la ligne simple
                        text = re.sub(r"[ \t\r\f\v]*\n([ \t\r\f\v]*\n)+", "\n\n", text)

                        text = text.strip()
                        # print(text)
                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=200,
                            chunk_overlap=20,
                            length_function=len,
                            is_separator_regex=False,
                        )
                        chunked_pdf = text_splitter.create_documents([text]) #c'est ÇA qu'on va mettre dans le vector store ! c'est DEJA comme il faut.
                        for chunk in chunked_pdf :
                            #On ajoute juste des meta données à tout les chunks du pdf
                            unique_id = str(uuid4())
                            statut = "N/A"
                            speciality = None
                            #on peut ensuite faire le même genre de mic mac pour discerner les informations des spés
                            if 'public' in pdf_file : statut = 'publique'
                            else : statut = "privé"

                            for x in SPECIALTIES :
                                if x in pdf_file : speciality = x

                            metadata =  {
                                    "ID": unique_id,
                                    "Source": pdf_file,
                                    "Status" : statut,
                                    "Speciality" : speciality,
                                }
                            chunk.metadata.update(metadata)
                        documents.extend(chunked_pdf)
                    else:
                        messagebox.showwarning("Attention", f"Aucun texte extrait de : {pdf_file}")
                
                
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors du traitement de {pdf_file} : {str(e)}")

            # Charger la clé API
            load_dotenv()
            os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_KEY')

            # Création des embeddings et du vector store
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            db = Chroma.from_documents(documents=documents, embedding=embeddings, collection_name=db_name, persist_directory=f"./{db_name}")
            
            messagebox.showinfo("Succès", f"Traitement terminé, la base de donnée {db_name} a été crée avec succès !")
            self.switch_frame(FinishPage)

        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur s'est produite : {str(e)}")

class StartPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        
        def browse_folder():
            """ Function to look a file into a directory, sets the variable folder_path_var to the selected folder """
            folder_selected = filedialog.askdirectory()
            folder_path_var.set(folder_selected)

        def run_process():
            """ Function to launch the process of creating the db, ensuring the name of the db and the folder path are both valid"""
            master.switch_frame(PageOne)
            allowed_characters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 
                                  '0','1', '2', '3', '4', '5', '6', '7', '8', '9']
            
            folder_path = folder_path_var.get()
            db_name = db_name_var.get()
            if not folder_path:
                messagebox.showwarning("Attention", "Veuillez sélectionner un dossier.")
                master.switch_frame(StartPage)
                return
            for e in db_name :
                if e.lower() not in allowed_characters:
                    messagebox.showwarning("Attention", "Le nom de la base de donné ne peut pas contenir d'espace ou de caractères spéciaux tels que des apostrophes('), des underscores (_), les lettres à accents (é, è ...) ou des #.")
                    master.switch_frame(StartPage)
                    return
                
            db_path = os.path.join(os.getcwd(), db_name)
            if os.path.exists(db_path) and os.path.isdir(db_path):
                try:
                    shutil.rmtree(db_path)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer le dossier existant {db_path}.\nErreur : {e}")
                    master.switch_frame(StartPage)
                    return
            
            master.process_folder(folder_path,db_name)


            # tk.Label(self, text="This is the start page").pack(side="top", fill="x", pady=10)

        folder_frame = tk.Frame(self)
        folder_frame.pack(pady=5)


        folder_path_var = tk.StringVar()
        db_name_var = tk.StringVar()

        # # Widgets
        tk.Label(self, text="Sélectionnez un dossier contenant les fichiers à vectoriser pour le RAG :").pack(pady=10)
        folder_frame = tk.Frame(self)
        folder_frame.pack(pady=5)
        tk.Entry(folder_frame, textvariable=folder_path_var, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(folder_frame, text="Parcourir", command=browse_folder).pack(side=tk.LEFT, padx=5)


        tk.Label(self, text="Renseignez le nom de votre base de dnonée").pack(pady=10)
        db_name_frame = tk.Frame(self)
        db_name_frame.pack(pady=5)
        tk.Entry(db_name_frame, textvariable=db_name_var, width = 50 ).pack(padx=5)


        tk.Button(self, text="Lancer le traitement", command=run_process, bg="green", fg="white").pack(padx=150, pady=5)
        tk.Button(self, text="quitter", command=master.destructor, bg="red", fg="white").pack(padx=120, pady=5)

            # tk.Button(self, text="Open page one",
            #             command=lambda: master.switch_frame(PageOne)).pack()
            # tk.Button(self, text="Open page two",
            #             command=lambda: master.switch_frame(PageTwo)).pack()

#cette classe est un peu inutile, tkinter ne la charge pas je capte pas trop pk, sauf si je dit que le bouton doit juste changer la page puis qu'après on lance la fonction.
class PageOne(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        #à transformer comme une page de chargement
        tk.Label(self, text="Veuillez patienter...").pack(side=tk.TOP, fill="x", pady=20, padx=20)

class FinishPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="Tout s'est bien passé ! Vous pouvez quitter, tout est bon.").pack(side=tk.TOP, fill="x", pady=20, padx=20)
        tk.Button(self, text="quitter", command=master.destructor, bg="green", fg="white").pack(padx=120, pady=5)


if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()