# rag_tools.py

import faiss
import numpy as np
import os
import json
import threading
from typing import List, Tuple, Dict, Optional
import tiktoken
import openai
import logging
import util
import shutil
import glob


# Importáljuk a meglévő kereső toolokat
from tools.search_tool import (
    PubMedSearchRetrieveAndSaveTool,
    MicrosoftNewsSearchRetrieveAndSaveTool,
    SearchRetrieveAndSaveTool,
    CoreSearchRetrieveAndSaveTool,
    WikipediaSearchRetrieveAndSaveTool
)

# 2. RAGIndexerTool Osztály
class RAGIndexerTool:
    """
    Class Name: RAGIndexerTool
    Description: Singleton osztály a FAISS index betöltésére és frissítésére a meglévő kereső toolok segítségével.
    
    Attributes:
        name (str): A tool neve.
        description (str): A tool leírása.
        parameters (str): A tool paraméterei.
    
    Methods:
        _run(directory, queries, **kwargs):
            Betölti a FAISS indexet, meghívja a kereső toolokat új tartalmak letöltésére és indexeli őket.
        
        clone():
            Visszaad egy új példányt a RAGIndexerTool-ból.
    """
    
    name: str = "RAGIndexerTool"
    description: str = "Loads existing FAISS index, invokes existing search tools to retrieve new content, and indexes them. Ensures a single instance using Singleton pattern."
    parameters: str = "Mandatory: queries (list of queries), languages (list of language codes), directory (str), filename (str). Optional: url_file, country, geolocation, results_per_page, date_range (e.g., 'w' for last week, 'm' for last month, 'y' for last year)"
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, index_path: str = 'faiss_index.bin', doc_ids_path: str = 'doc_ids.json'):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RAGIndexerTool, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, index_path: str = 'faiss_index.bin', doc_ids_path: str = 'doc_ids.json'):
        if self._initialized:
            return
        self.index_path = index_path
        self.doc_ids_path = doc_ids_path
        self.embedding_model = "text-embedding-ada-002"
        self.dimension = 1536  # A text-embedding-ada-002 modell dimenziója
        
        # Inicializáljuk a kereső toolokat
        self.search_tools = [
            SearchRetrieveAndSaveTool(),
            CoreSearchRetrieveAndSaveTool(),
            PubMedSearchRetrieveAndSaveTool(),
            MicrosoftNewsSearchRetrieveAndSaveTool(),
            WikipediaSearchRetrieveAndSaveTool()
        ]
        
        # Flag az index betöltésének ellenőrzésére
        self.index_loaded = False
        self.index = None
        self.doc_ids = []
        
        self._initialized = True

    @staticmethod
    def parse_parameters(instance, method_name: str) -> List[str]:
        """
        Helper függvény egy osztálypéldány és metódus név alapján a metódus paramétereinek kivonásához.
        
        :param instance: Az osztály példánya, aminek a metódusát vizsgáljuk.
        :param method_name: A metódus neve, amelynek a paramétereit ki akarjuk vonni.
        :return: Lista a paraméterek neveivel.
        """
        import inspect
        params = []
        
        # Az instance alapján a metódus dinamikus lekérése a method_name segítségével
        method = getattr(instance, method_name)
        
        # Lekérjük a metódus aláírását
        signature = inspect.signature(method)
        
        # Végigmegyünk a paramétereken
        for param in signature.parameters.values():
            # A paraméter neve
            param_name = param.name
            params.append(param_name)
        
        return params

    def get_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Optional[List[float]]:
        """
        Lekér egy embeddinget a megadott szöveghez az OpenAI API segítségével.
        
        :param text: A szöveg, amit embedelni szeretnél.
        :param model: Az OpenAI embedding modell neve.
        :return: A szöveg embeddingje listaként, vagy None hibát esetén.
        """
        try:
            response = openai.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error generating embedding: {e}")
            return None

    def get_tokenizer(self) -> tiktoken.Encoding:
        """
        Betölti az OpenAI tiktoken encodert a text-embedding-ada-002 modellhez.
        """
        return tiktoken.get_encoding("cl100k_base")

    def generate_document_embeddings(self, documents: List[Dict[str, str]], chunk_size: int = 8000, overlap: int = 0) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generálja a dokumentumok chunkjainak embeddingjeit, kezelve a hosszú szövegeket is.
        
        :param documents: Lista dokumentumokkal, amelyek tartalmazzák az 'id' és 'text' kulcsokat.
        :param chunk_size: A maximális token szám egy chunkban.
        :param overlap: Az átfedés mértéke a chunkok között.
        :return: Tuple (embeddings, doc_ids)
        """
        embeddings = []
        doc_ids = []
        tokenizer = self.get_tokenizer()
        chunk_id_counter = 0  # Egyedi chunk ID-k generálásához
        
        for doc in documents:
            logging.info(f"Processing document ID: {doc['id']}")
            text = doc['text']
            tokens = tokenizer.encode(text)
            doc_id = doc['id']
            url = doc.get('url', None)
            
            # Daraboljuk fel a dokumentumot chunkokra
            chunks = []
            start = 0
            while start < len(tokens):
                end = start + chunk_size
                chunk_tokens = tokens[start:end]
                chunk_text = tokenizer.decode(chunk_tokens)
                chunks.append(chunk_text)
                start += chunk_size - overlap  # Átfedés
            
            # Generáljunk embeddingeket minden chunkhoz
            for chunk in chunks:
                embedding = self.get_embedding(chunk, model=self.embedding_model)
                if embedding:
                    embeddings.append(embedding)
                    doc_ids.append({
                        "chunk_id": chunk_id_counter,
                        "doc_id": doc_id,
                        "url": url,
                        "content": chunk  # Tároljuk a chunk tartalmát, ha szükséges
                    })
                    chunk_id_counter += 1
                else:
                    logging.warning(f"Failed to generate embedding for a chunk in document ID: {doc_id}")
        
        embeddings = np.array(embeddings).astype('float32')
        return embeddings, doc_ids

    def index_existing_documents(self, directory: str):
        """
        Betölti a már meglévő, indexelt RAG adatokat a megadott könyvtárból, indexeli őket, és végül logolja az összes indexált URL-t.
        
        :param directory: A könyvtár, ahol a kereső toolok mentett fájljai találhatók.
        """
        logging.info(f"Indexing existing documents from directory: {directory}")
        indexed_urls = []
        documents = []
        logging.info(os.listdir(directory))
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                filepath = os.path.join(directory, filename)
                if os.path.getsize(filepath) == 0:
                    logging.warning(f"Empty JSON file skipped: {filepath}")
                    continue
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        s = f.read()
                        f = util.extract_json_string(s)
                        data = json.loads(f)
                        for item in data:
                            url = item.get('url')
                            content = item.get('content')
                            import uuid
                            doc_id = uuid.uuid4()
                            if url and content:
                                documents.append({
                                    "id": str(doc_id),
                                    "url": url,
                                    "text": content
                                })
                                indexed_urls.append(url)
                    except json.JSONDecodeError as e:
                        logging.error(f"Error decoding JSON from file {filepath}: {e}")
        # Generáljuk az embeddingeket és indexeljük őket
        if documents:
            embeddings, doc_ids = self.generate_document_embeddings(documents)
            if embeddings.size > 0:
                if self.index is None:
                    self.index = faiss.IndexFlatL2(self.dimension)
                    logging.info("Created a new FAISS index.")
                self.index.add(embeddings)
                self.doc_ids.extend(doc_ids)
                self.save_index()
            else:
                logging.warning("No embeddings were generated.")
        else:
            logging.warning("No documents to index.")

        archive_directory = os.path.join(directory, 'archive')
        # Ha az archive könyvtár nem létezik, hozzuk létre
        os.makedirs(archive_directory, exist_ok=True)

        # JSON fájlok áthelyezése az archive könyvtárba
        for file in glob.glob(os.path.join(directory, "*.json")):
            if "doc_ids.json" in file:
                continue
            shutil.move(file, archive_directory)

        # Logoljuk az összes indexált URL-t
        if indexed_urls:
            logging.info("Indexed URLs:")
            for url in indexed_urls:
                logging.info(url)
        else:
            logging.info("No URLs were indexed.")

    def create_faiss_index(self, embeddings: np.ndarray) -> faiss.IndexFlatL2:
        """
        Létrehoz egy FAISS IndexFlatL2 indexet az embeddingekhez.
        
        :param embeddings: NumPy tömb az embeddingekkel.
        :return: FAISS index.
        """
        index = faiss.IndexFlatL2(self.dimension)  # Euclidean distance alapú index
        index.add(embeddings)
        logging.info(f"FAISS index létrehozva és feltöltve {len(embeddings)} embeddinggel.")
        return index

    def update_index_with_new_documents(self, directory: str, queries: Optional[List[str]] = None, **kwargs):
        """
        Meghívja a meglévő kereső toolokat, letölti az új tartalmakat és indexeli őket.
        
        :param directory: A könyvtár, ahová a kereső toolok mentik az új fájlokat.
        :param queries: Lista lekérdezések, amelyeket a kereső tooloknak futtatniuk kell.
        :param kwargs: Opcionális paraméterek a kereső toolok számára.
        """
        logging.info("Running existing search tools to retrieve new documents...")
        for tool in self.search_tools:
            try:
                logging.info(f"Search with {tool.name}")
                # Meghatározzuk a lekérdezéseket és opcionális paramétereket
                tool_queries = queries if queries else ["default query"]  # Cseréld ki valós lekérdezésekre
                output_filename = f"{tool.name}_new.json"
                
                # Készítünk egy dict-et a tool paramétereihez
                tool_params = {
                    "queries": tool_queries,
                    "directory": directory,
                    "filename": output_filename
                }
                
                # Kiszűrjük a tool által elvárt paramétereket
                expected_params = self.parse_parameters(tool,"_run")
                filtered_kwargs = {k: v for k, v in kwargs.items() if k in expected_params}
                
                # Hozzáadjuk a szűrt paramétereket a tool_params-hoz
                tool_params.update(filtered_kwargs)
                
                # Meghívjuk a tool _run metódusát
                tool._run(**tool_params)
                logging.info(f"Tool {tool.name} futtatása sikeres.")
            except TypeError as te:
                logging.error(f"Parameter mismatch when running tool {tool.name}: {te}")
            except Exception as e:
                logging.error(f"Error running tool {tool.name}: {e}")
        
        # Indexeljük az újonnan mentett fájlokat
        logging.info("Indexing new documents...")
        self.index_existing_documents(directory)
        logging.info("Index frissítése befejeződött.")

    def save_index(self):
        """
        Mentse a FAISS indexet és a doc_ids mappingot fájlba.
        """
        try:
            if self.index is not None:
                faiss.write_index(self.index, self.index_path)
                logging.info(f"FAISS index mentve a következő helyre: {self.index_path}")
            with open(self.doc_ids_path, 'w', encoding='utf-8') as f:
                json.dump(self.doc_ids, f, ensure_ascii=False, indent=4)
            logging.info(f"doc_ids mapping mentve a következő helyre: {self.doc_ids_path}")
        except Exception as e:
            logging.error(f"Error saving index and doc_ids: {e}")

    def _run(self, directory: str, queries: Optional[List[str]] = None, **kwargs) -> Tuple[str, bool]:
        """
        Betölti a meglévő FAISS indexet (ha még nem történt meg), meghívja a kereső toolokat új tartalmak letöltésére és indexeli őket.
        
        :param directory: A könyvtár, ahol a kereső toolok mentik az eredményeket.
        :param queries: Lista lekérdezések a kereső tooloknak.
        :param kwargs: Opcionális paraméterek a kereső toolok számára.
        :return: Tuple (result message, success flag)
        """
        try:
            if not self.index_loaded:
                # Betöltjük a FAISS indexet és a doc_ids mappingot
                if os.path.exists(self.index_path):
                    logging.info("Loading existing FAISS index...")
                    self.index = faiss.read_index(self.index_path)
                    logging.info("FAISS index loaded successfully.")
                else:
                    logging.info("FAISS index not found. Creating a new index...")
                    self.index = faiss.IndexFlatL2(self.dimension)
                
                if os.path.exists(self.doc_ids_path):
                    logging.info("Loading existing doc_ids mapping...")
                    with open(self.doc_ids_path, 'r', encoding='utf-8') as f:
                        self.doc_ids = json.load(f)
                    logging.info("doc_ids mapping loaded successfully.")
                else:
                    logging.info("doc_ids mapping not found. Creating a new mapping...")
                    self.doc_ids = []
                
                self.index_loaded = True
            
            # Frissítjük az indexet új dokumentumokkal
            self.update_index_with_new_documents(directory, queries, **kwargs)
            return "Index successfully updated with new documents.", True
        except Exception as e:
            logging.error(f"Failed to update index with new documents: {e}")
            return f"Failed to update index: {e}", False

    def clone(self):
        """
        Visszaad egy új példányt a RAGIndexerTool-ból.
        
        Returns:
            RAGIndexerTool: Egy új példány a RAGIndexerTool osztályból.
        """
        return RAGIndexerTool()

# 2. RAGIndexerToolWithoutNet Osztály
class RAGIndexerToolWithoutNet:
    """
    Class Name: RAGIndexerToolWithoutNet
    Description: Singleton osztály a FAISS index betöltésére és frissítésére a megadott könyvtárban lévő fájlokból. Nem támaszkodik netes keresésre.
    
    Attributes:
        name (str): A tool neve.
        description (str): A tool leírása.
        parameters (str): A tool paraméterei.
    
    Methods:
        _run(input_directory, output_directory):
            Betölti a FAISS indexet és a megadott könyvtárban lévő fájlokból épít adatbázist.
        
        clone():
            Visszaad egy új példányt a RAGIndexerToolWithoutNet-ból.
    """
    
    name: str = "RAGIndexerToolWithoutNet"
    description: str = "Loads existing FAISS index and indexes documents found in the given directory without relying on internet search."
    parameters: str = "Mandatory: input_directory (str), output_directory (str)"
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, index_path: str = 'faiss_index.bin', doc_ids_path: str = 'doc_ids.json'):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RAGIndexerToolWithoutNet, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, index_path: str = 'faiss_index.bin', doc_ids_path: str = 'doc_ids.json'):
        if self._initialized:
            return
        self.index_path = index_path
        self.doc_ids_path = doc_ids_path
        self.embedding_model = "text-embedding-ada-002"
        self.dimension = 1536  # A text-embedding-ada-002 modell dimenziója
        
        # Flag az index betöltésének ellenőrzésére
        self.index_loaded = False
        self.index = None
        self.doc_ids = []
        
        self._initialized = True

    def get_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Optional[List[float]]:
        """
        Lekér egy embeddinget a megadott szöveghez az OpenAI API segítségével.
        
        :param text: A szöveg, amit embedelni szeretnél.
        :param model: Az OpenAI embedding modell neve.
        :return: A szöveg embeddingje listaként, vagy None hibát esetén.
        """
        try:
            response = openai.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error generating embedding: {e}")
            return None

    def get_tokenizer(self) -> tiktoken.Encoding:
        """
        Betölti az OpenAI tiktoken encodert a text-embedding-ada-002 modellhez.
        """
        return tiktoken.get_encoding("cl100k_base")

    def generate_document_embeddings(self, documents: List[Dict[str, str]], chunk_size: int = 8000, overlap: int = 0) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generálja a dokumentumok chunkjainak embeddingjeit, kezelve a hosszú szövegeket is.
        
        :param documents: Lista dokumentumokkal, amelyek tartalmazzák az 'id' és 'text' kulcsokat.
        :param chunk_size: A maximális token szám egy chunkban.
        :param overlap: Az átfedés mértéke a chunkok között.
        :return: Tuple (embeddings, doc_ids)
        """
        embeddings = []
        doc_ids = []
        tokenizer = self.get_tokenizer()
        chunk_id_counter = 0  # Egyedi chunk ID-k generálásához
        
        for doc in documents:
            logging.info(f"Processing document ID: {doc['id']}")
            text = doc['text']
            tokens = tokenizer.encode(text)
            doc_id = doc['id']
            
            # Daraboljuk fel a dokumentumot chunkokra
            chunks = []
            start = 0
            while start < len(tokens):
                end = start + chunk_size
                chunk_tokens = tokens[start:end]
                chunk_text = tokenizer.decode(chunk_tokens)
                chunks.append(chunk_text)
                start += chunk_size - overlap  # Átfedés
            
            # Generáljunk embeddingeket minden chunkhoz
            for chunk in chunks:
                embedding = self.get_embedding(chunk, model=self.embedding_model)
                if embedding:
                    embeddings.append(embedding)
                    doc_ids.append({
                        "chunk_id": chunk_id_counter,
                        "doc_id": doc_id,
                        "content": chunk  # Tároljuk a chunk tartalmát, ha szükséges
                    })
                    chunk_id_counter += 1
                else:
                    logging.warning(f"Failed to generate embedding for a chunk in document ID: {doc_id}")
        
        embeddings = np.array(embeddings).astype('float32')
        return embeddings, doc_ids

    def index_existing_documents(self, input_directory: str):
        """
        Betölti a már meglévő, indexelt RAG adatokat a megadott könyvtárból, indexeli őket, és végül logolja az összes indexált URL-t.
        
        :param input_directory: A könyvtár, ahol a fájlok találhatók.
        """
        logging.info(f"Indexing existing documents from directory: {input_directory}")
        documents = []
        logging.info(os.listdir(input_directory))
        for filename in os.listdir(input_directory):
            if filename.endswith('.json'):
                filepath = os.path.join(input_directory, filename)
                if os.path.getsize(filepath) == 0:
                    logging.warning(f"Empty JSON file skipped: {filepath}")
                    continue
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        for item in data:
                            content = item.get('content')
                            import uuid
                            doc_id = uuid.uuid4()
                            if content:
                                documents.append({
                                    "id": str(doc_id),
                                    "text": content
                                })
                    except json.JSONDecodeError as e:
                        logging.error(f"Error decoding JSON from file {filepath}: {e}")
        # Generáljuk az embeddingeket és indexeljük őket
        if documents:
            embeddings, doc_ids = self.generate_document_embeddings(documents)
            if embeddings.size > 0:
                if self.index is None:
                    self.index = faiss.IndexFlatL2(self.dimension)
                    logging.info("Created a new FAISS index.")
                self.index.add(embeddings)
                self.doc_ids.extend(doc_ids)
                self.save_index()
            else:
                logging.warning("No embeddings were generated.")
        else:
            logging.warning("No documents to index.")

    def save_index(self, output_directory: str):
        """
        Mentse a FAISS indexet és a doc_ids mappingot fájlba.
        
        :param output_directory: A könyvtár, ahová az index és a doc_ids fájlokat menti.
        """
        try:
            index_path = os.path.join(output_directory, self.index_path)
            doc_ids_path = os.path.join(output_directory, self.doc_ids_path)
            if self.index is not None:
                faiss.write_index(self.index, index_path)
                logging.info(f"FAISS index mentve a következő helyre: {index_path}")
            with open(doc_ids_path, 'w', encoding='utf-8') as f:
                json.dump(self.doc_ids, f, ensure_ascii=False, indent=4)
            logging.info(f"doc_ids mapping mentve a következő helyre: {doc_ids_path}")
        except Exception as e:
            logging.error(f"Error saving index and doc_ids: {e}")

    def _run(self, input_directory: str, output_directory: str) -> Tuple[str, bool]:
        """
        Betölti a meglévő FAISS indexet (ha még nem történt meg), és a megadott könyvtárban található fájlokból épít adatbázist.
        
        :param input_directory: A könyvtár, ahol a fájlok találhatók.
        :param output_directory: A könyvtár, ahová az index és a doc_ids fájlokat menti.
        :return: Tuple (result message, success flag)
        """
        try:
            if not self.index_loaded:
                # Betöltjük a FAISS indexet és a doc_ids mappingot
                index_path = os.path.join(output_directory, self.index_path)
                doc_ids_path = os.path.join(output_directory, self.doc_ids_path)
                if os.path.exists(index_path):
                    logging.info("Loading existing FAISS index...")
                    self.index = faiss.read_index(index_path)
                    logging.info("FAISS index loaded successfully.")
                else:
                    logging.info("FAISS index not found. Creating a new index...")
                    self.index = faiss.IndexFlatL2(self.dimension)
                
                if os.path.exists(doc_ids_path):
                    logging.info("Loading existing doc_ids mapping...")
                    with open(doc_ids_path, 'r', encoding='utf-8') as f:
                        self.doc_ids = json.load(f)
                    logging.info("doc_ids mapping loaded successfully.")
                else:
                    logging.info("doc_ids mapping not found. Creating a new mapping...")
                    self.doc_ids = []
                
                self.index_loaded = True
            
            # Indexeljük a könyvtárban található dokumentumokat
            self.index_existing_documents(input_directory)
            self.save_index(output_directory)
            return "Index successfully updated with documents from the directory.", True
        except Exception as e:
            logging.error(f"Failed to update index with documents: {e}")
            return f"Failed to update index: {e}", False

    def clone(self):
        """
        Visszaad egy új példányt a RAGIndexerToolWithoutNet-ból.
        
        Returns:
            RAGIndexerToolWithoutNet: Egy új példány a RAGIndexerToolWithoutNet osztályból.
        """
        return RAGIndexerToolWithoutNet()
        
class RAGSemanticSearchTool:
    """
    Class Name: RAGSemanticSearchTool
    Description: Singleton osztály, amely semantikus keresést végez FAISS index alapján és visszaadja a releváns dokumentumokat.
    
    Attributes:
        name (str): A tool neve.
        description (str): A tool leírása.
        parameters (str): A tool paraméterei.
    
    Methods:
        _run(query, top_k):
            Keresést végez a FAISS indexben a lekérdezés alapján és visszaadja a találatokat.
        
        clone():
            Visszaad egy új példányt a RAGSemanticSearchTool-ból.
    """
    
    name: str = "RAGSemanticSearchTool"
    description: str = "Performs semantic search using a FAISS index and returns relevant documents based on the query."
    parameters: str = "query (str), top_k (int, optional)"
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, index_path: str = 'faiss_index.bin', doc_ids_path: str = 'doc_ids.json', top_k: int = 10):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RAGSemanticSearchTool, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, index_path: str = 'faiss_index.bin', doc_ids_path: str = 'doc_ids.json', top_k: int = 10):
        if self._initialized:
            return
        self.index_path = index_path
        self.doc_ids_path = doc_ids_path
        self.top_k = top_k
        self.embedding_model = "text-embedding-ada-002"
        self.dimension = 1536  # A text-embedding-ada-002 modell dimenziója
        
        # Flag az index betöltésének ellenőrzésére
        self.index_loaded = False
        self.index = None
        self.doc_ids = []
        
        self._initialized = True

    def get_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Optional[List[float]]:
        """
        Lekér egy embeddinget a megadott szöveghez az OpenAI API segítségével.
        
        :param text: A szöveg, amit embedelni szeretnél.
        :param model: Az OpenAI embedding modell neve.
        :return: A szöveg embeddingje listaként, vagy None hibát esetén.
        """
        try:
            response = openai.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error generating embedding: {e}")
            return None


    def retrieve(self, query: str, faiss_top_k: int = 51, return_top_n: int = 10) -> List[Dict[str, float]]:
        """
        Retrieves the most relevant documents based on the query by aggregating the number of similar chunks per document.
        
        :param query: The search query.
        :param faiss_top_k: The number of top similar chunks to retrieve from FAISS.
        :param return_top_n: The number of top documents to return after aggregation.
        :return: List of the most relevant documents with their URLs, content, and aggregated distance.
        """
        logging.info("Generating embedding for the query...")
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            logging.error("Query embedding generation failed.")
            return []
        query_embedding = np.array([query_embedding]).astype('float32')
        
        logging.info(f"Searching FAISS index for top {faiss_top_k} similar chunks...")
        distances, indices = self.index.search(query_embedding, faiss_top_k)
        
        # Aggregáljuk a találatokat dokumentumok szerint
        doc_scores = {}
        
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.doc_ids):
                doc_info = self.doc_ids[idx]
                doc_id = doc_info['doc_id']
                if doc_id in doc_scores:
                    doc_scores[doc_id]['score'] += 1
                    doc_scores[doc_id]['distances'].append(distance)
                else:
                    doc_scores[doc_id] = {
                        "url": doc_info.get("url"),
                        "content": "",  # A teljes dokumentum tartalma
                        "score": 1,
                        "distances": [distance]
                    }
            else:
                logging.warning(f"Index {idx} out of bounds for doc_ids list.")
        
        if not doc_scores:
            logging.warning("No relevant documents found after aggregation.")
            return []
        
        # Betöltjük a teljes dokumentum tartalmát
        for doc_id in doc_scores.keys():
            # Keresd meg a dokumentum összes chunkját és fűzd össze a tartalmakat
            contents = [doc_info['content'] for doc_info in self.doc_ids if doc_info['doc_id'] == doc_id]
            full_content = " ".join(contents)
            doc_scores[doc_id]['content'] = full_content
            
            # Távolítsuk el az érvénytelen (NaN vagy inf) távolságokat, mielőtt az átlagot kiszámítjuk
            MAX_DISTANCE = 1e6  # Például, ha tudjuk, hogy a távolságok nem lehetnek ilyen nagyok.
            valid_distances = [d for d in doc_scores[doc_id]['distances'] if not (np.isnan(d) or np.isinf(d) or d > MAX_DISTANCE)]

            if valid_distances:  # Ellenőrizzük, hogy van-e érvényes távolság
                doc_scores[doc_id]['avg_distance'] = np.mean(valid_distances)
            else:
                doc_scores[doc_id]['avg_distance'] = float('inf')  # Ha nincs érvényes távolság, állítsuk végtelenre

        # Rangsoroljuk a dokumentumokat a score és az átlagos távolság alapján
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: (-x[1]['score'], x[1]['avg_distance'])
        )
        
        # Kiválasztjuk a legjobb `return_top_n` dokumentumot, figyelve az URL-ek duplikációjára
        top_docs = []
        seen_urls = set()  # Halmaz az URL-ek követésére

        for doc_id, doc_data in sorted_docs:
            url = doc_data.get("url")
            if url not in seen_urls:  # Csak akkor adjuk hozzá, ha az URL még nincs a listában
                top_docs.append((doc_id, doc_data))
                seen_urls.add(url)

        # A kiválasztott dokumentumok maximális száma
        top_docs = top_docs[:return_top_n]

        # A végső eredmények összeállítása
        retrieved_documents = []
        for doc_id, doc_data in top_docs:
            retrieved_documents.append({
                "doc_id": doc_id,
                "url": doc_data.get("url"),
                "content": doc_data.get("content"),
                "avg_distance": str(doc_data.get("avg_distance")),
                "score": doc_data.get("score")  # Opció: hozzáadjuk a hasonló chunkok számát
            })
        
        logging.info(f"Retrieved {len(retrieved_documents)} unique documents after aggregation.")
        return retrieved_documents

    def _run(self, query: str, top_k: Optional[int] = None) -> Tuple[str, bool]:
        """
        Keresést végez a FAISS indexben a lekérdezés alapján és visszaadja a találatokat.
        
        :param query: A keresendő szöveg.
        :param top_k: A visszakeresendő dokumentumok száma (alapértelmezett: osztály szintű top_k).
        :return: Tuple (result JSON string, success flag)
        """
        try:
            if not self.index_loaded:
                # Betöltjük a FAISS indexet és a doc_ids mappingot
                if os.path.exists(self.index_path):
                    logging.info("Loading existing FAISS index for semantic search...")
                    self.index = faiss.read_index(self.index_path)
                    logging.info("FAISS index loaded successfully.")
                else:
                    raise FileNotFoundError(f"FAISS index not found at {self.index_path}.")
                
                if os.path.exists(self.doc_ids_path):
                    logging.info("Loading doc_ids mapping...")
                    with open(self.doc_ids_path, 'r', encoding='utf-8') as f:
                        self.doc_ids = json.load(f)
                    logging.info("doc_ids mapping loaded successfully.")
                else:
                    raise FileNotFoundError(f"doc_ids mapping not found at {self.doc_ids_path}.")
                
                self.index_loaded = True

            actual_top_k = top_k if top_k else self.top_k
            logging.info(f"Performing semantic search for query: '{query}' with top_k={actual_top_k}")
            results = self.retrieve(query, return_top_n=actual_top_k)
            
            if not results:
                logging.warning("No relevant documents found.")
                return "No relevant documents found.", False
            
            # Formázzuk az eredményeket JSON formátumba
            result_json = json.dumps(results, indent=4, ensure_ascii=False)
            return result_json, True
        except Exception as e:
            logging.error(f"Semantic search failed: {e}")
            return f"Semantic search failed: {e}", False

    def clone(self):
        """
        Visszaad egy új példányt a RAGSemanticSearchTool-ból.
        
        Returns:
            RAGSemanticSearchTool: Egy új példány a RAGSemanticSearchTool osztályból.
        """
        return RAGSemanticSearchTool(index_path=self.index_path, doc_ids_path=self.doc_ids_path, top_k=self.top_k)


class RAGSearchAndSaveTool:
    """
    A class that combines the indexing and search steps, and saves the results to a file.
    """
    name: str = "RAGSearchAndSaveTool"
    description: str = "Searches the internet using search engines, retrieves content, and saves the result to a file in a specified directory."
    parameters: str = (
        "Mandatory: queries (list of queries), languages (list of language codes), "
        "directory (str), filename (str). "
        "Optional: url_file, country, geolocation, results_per_page, date_range "
        "(e.g., 'w' for last week, 'm' for last month, 'y' for last year)"
    )

    def __init__(self):
        """
        Initializes the RAGSearchAndSaveTool without creating the tools.
        The tools will be created inside the _run() method based on the given directory, queries, and languages.
        """
        self.indexer_tool = None
        self.search_tool = None

    def _run(self, queries: List[str], languages: List[str], directory: str, filename: str, top_k: int = 10, **kwargs):
        """
        1. Creates the indexer and search tools using the given directory.
        2. Indexes new documents based on queries and languages.
        3. Runs semantic search on the same queries.
        4. Saves the search results to the specified file.

        :param queries: The list of queries to run both indexing and search.
        :param languages: The list of language codes to use for the search.
        :param directory: The directory where the index and doc_ids will be stored.
        :param filename: The name of the file to save the search results.
        :param top_k: The number of top documents to retrieve in the semantic search.
        :param kwargs: Optional arguments for the search (e.g., url_file, country, geolocation).
        """
        # Paths for the FAISS index and doc_ids file
        index_path = os.path.join(directory, 'faiss_index.bin')
        doc_ids_path = os.path.join(directory, 'doc_ids.json')

        # Ensure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 1. Create the indexer and search tools
        self.indexer_tool = RAGIndexerTool(index_path=index_path, doc_ids_path=doc_ids_path)
        self.search_tool = RAGSemanticSearchTool(index_path=index_path, doc_ids_path=doc_ids_path, top_k=top_k)

        # 2. Indexing step with queries and languages
        update_message, success = self.indexer_tool._run(directory=directory, queries=queries, languages=languages, **kwargs)
        if not success:
            raise Exception(f"Indexing failed: {update_message}")

        # 3. Search step using the same queries
        all_results = []
        for query in queries:
            results_json, search_success = self.search_tool._run(query=query)
            if search_success:
                all_results.append(json.loads(results_json))
            else:
                raise Exception(f"Search failed for query '{query}': {results_json}")

        # Flat lista létrehozása az összes eredményből
        flat_results = [item for inner_list in all_results for item in inner_list]
        unique_results = []
        seen_urls = set()

        # Az egyedi URL-ek kiválasztása
        for item in flat_results:
            if item['url'] not in seen_urls:
                unique_results.append(item)
                seen_urls.add(item['url'])
 
        # Flat lista rendezése az "avg_distance" kulcs alapján növekvő sorrendben
        unique_results.sort(key=lambda x: float(x['avg_distance']), reverse=False)

        # Csak az első top_k elem kiválasztása
        top_k_results = unique_results[:top_k]


        # 4. Save results to file
        output_path = os.path.join(directory, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(top_k_results, f, ensure_ascii=False, indent=4)

        return f"Results saved to {output_path}", True

    def clone(self):
        """
        Visszaad egy új példányt a RAGSearchAndSaveTool-ból.
        
        Returns:
            RAGSearchAndSaveTool: Egy új példány a RAGSearchAndSaveTool osztályból.
        """
        return RAGSearchAndSaveTool()



def main():
    index_path = './faiss/faiss_index.bin'
    doc_ids_path = './faiss/doc_ids.json'
    data_directory = './search_results'
    output_directory = './final_results'
    output_filename = 'search_results.json'
    real_queries = ["Budapest news"]
    languages= ["en"]

    indexer = RAGIndexerTool(index_path=index_path, doc_ids_path=doc_ids_path)
    semantic_search = RAGSemanticSearchTool(index_path=index_path, doc_ids_path=doc_ids_path, top_k=5)

    search_and_save_tool = RAGSearchAndSaveTool(indexer, semantic_search)
    search_and_save_tool.run_and_save(directory=data_directory, queries=real_queries, output_directory=output_directory, output_filename=output_filename)



if __name__ == "__main__":
    from dotenv import load_dotenv
    import logging
    from logging.handlers import RotatingFileHandler

    # Ensure the directory exists
    os.makedirs('./log', exist_ok=True)
    # Forgó fájlkezelő létrehozása
    rotating_handler = RotatingFileHandler(
        "./log/app.log",
        mode='a',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=10,
        encoding='utf-8',
        delay=0
    )

    # Beállítjuk a logging konfigurációt
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[rotating_handler, logging.StreamHandler()]
    )

    main()