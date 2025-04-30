from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore

# Load the api
load_dotenv()
QDRANT_URL=os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Extract Data From the PDF File
def load_pdf_file(data):
    loader= DirectoryLoader(data,
                            glob="*.pdf",  # Load Only Pdf documents
                            loader_cls=PyPDFLoader)

    documents=loader.load()

    return documents



# Load pdf from the data folder
extracted_data=load_pdf_file(data='Data/')


# Chunking Operation
def text_split(extracted_data):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    text_chunks=text_splitter.split_documents(extracted_data)
    return text_chunks

# Chunked data
text_chunks=text_split(extracted_data)


# Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")





# Pushing to vector database
url = QDRANT_URL
api_key = QDRANT_API_KEY
qdrant = QdrantVectorStore.from_documents(
    text_chunks,
    embeddings,
    url=url,
    prefer_grpc=True,
    api_key=api_key,
    collection_name="my_documents",
)






