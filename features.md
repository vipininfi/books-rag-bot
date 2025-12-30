# BookRAG Pro - Comprehensive Feature List

BookRAG Pro is an AI-powered book search and analysis platform that allows authors to upload their books and readers to perform semantic searches and ask AI-powered questions based on the book content.

## 1. Core Platform Features

### Authentication & User Management
- **Secure Authentication**: JWT-based login and signup system.
- **Role-Based Access Control (RBAC)**:
    - **Readers**: Can browse authors, subscribe to them, and search/chat with their books.
    - **Authors**: Can upload and manage their own books, view analytics, and have a public bio.
- **Profile Management**:
    - Update username and email.
    - Change password with current password verification.
    - **Author Bio**: Authors can manage a public bio that readers see when browsing.

### Subscription System
- **Author Discovery**: A dedicated tab to browse all registered authors and their bios.
- **One-Click Subscription**: Readers can subscribe to authors to gain access to their entire library.
- **Subscription Management**: View and manage active subscriptions in a dedicated "My Subscriptions" tab.
- **Access Control**: Search and RAG functionality are restricted to books from authors the user is currently subscribed to.

---

## 2. Book Management (Author Features)

### Book Upload & Processing
- **PDF Upload**: Support for PDF files up to 100MB.
- **Automated Processing Pipeline**:
    - **Text Extraction**: High-quality text extraction from PDF files.
    - **Hybrid Chunking**: Combines structural (chapters/sections) and semantic chunking for better context preservation.
    - **Embedding Generation**: Uses the BGE-Base model to generate high-quality vector representations of book content.
- **Vector Storage**: Chunks are stored in a high-performance vector database (Pinecone) for fast retrieval.

### Library Management
- **My Books Dashboard**: Authors can view all their uploaded books and their current processing status (Processing, Completed, Error).
- **Book Deletion**: Authors can remove their books, which also cleans up the associated vector embeddings.
- **Book Viewer**: Integrated PDF viewer (PDF.js) to read books directly in the browser.

---

## 3. Search & AI Assistant (Reader Features)

### Semantic Search
- **Concept-Based Search**: Find information based on meaning rather than just keywords.
- **Subscribed Library Search**: Automatically searches across all books from all authors the user is subscribed to.
- **Optimized Performance**:
    - **Intelligent Query Routing**: Skips unnecessary steps for simple queries.
    - **Parallel Search**: Executes vector searches in parallel for speed.
    - **Persistent Caching**: Caches search results to provide instant answers for repeat queries.
- **Rich Search Results**: Displays relevant snippets with book titles and author names.

### AI Assistant (RAG)
- **Context-Aware Answers**: AI answers questions using *only* the content from the books in the user's subscribed library.
- **Streaming Responses**: Real-time answer generation where users see the AI "typing" its response.
- **Source Citations**: Every AI answer provides direct links to the source material, including:
    - Book Title
    - Section/Chapter Title
    - Page Number
    - Exact text snippet used for the answer.
- **Advanced Reranking**: Uses a composite scoring system (Vector Similarity + Keyword Overlap + Title Relevance) to find the most accurate context.

### Voice & Speech Integration
- **Voice Input**: Users can speak their questions instead of typing.
- **Auto-Submit**: Voice recognition automatically submits the query after a brief period of silence.
- **Text-to-Speech (TTS)**: The AI Assistant can read its answers aloud.
- **Speech Controls**: Users can stop the AI from speaking at any time.

---

## 4. Analytics & Token Tracking

### Usage Dashboard
- **Real-Time Stats**: Track total searches, AI questions, and total tokens used.
- **Cost Tracking**: Estimated cost calculation based on actual token consumption.
- **Granular Breakdown**:
    - **Book Processing**: Tokens and cost for uploading and embedding books.
    - **AI Conversations**: Breakdown of embedding, prompt (input), and answer (output) costs.
    - **Search Activity**: Tokens used for semantic search queries.
- **Usage Over Time**: Visual charts showing platform usage trends (Daily/Monthly).

---

## 5. Technical Highlights
- **Backend**: FastAPI (Python) for high-performance asynchronous API.
- **Frontend**: Modern, responsive UI with Vanilla CSS and JavaScript.
- **Database**: PostgreSQL (SQLAlchemy) for relational data and Pinecone for vector data.
- **AI Models**: OpenAI GPT-4o mini for RAG and BGE-Base for embeddings.
- **Performance**: Integrated performance metrics tracking and multi-level caching.
