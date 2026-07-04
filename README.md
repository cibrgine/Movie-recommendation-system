<div align="center">

  # 🎬 CineMatch AI

  ### *Dual-Engine Hybrid Recommendation System for Movies & TV Shows*

  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![Sentence-Transformers](https://img.shields.io/badge/Sentence--Transformers-v2.2-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
  [![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
  [![UI](https://img.shields.io/badge/UI-Vanilla_CSS_&_JS-512BD4?style=for-the-badge&logo=javascript&logoColor=white)](#-frontend-user-interface)

  <p align="center">
    A premium, glassmorphic web dashboard providing semantic similarities for movies and TV shows alongside collaborative client profiling.
  </p>

  <img src="https://github.com/user-attachments/assets/66fe0c23-c0d1-44bb-b3b3-8c4333857500" alt="CineMatch AI Dashboard Initial State" width="800" style="box-shadow: 0 4px 12px rgba(0,0,0,0.3); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-top: 15px;"/>

</div>

---

## 💡 Engineering Foreword

As a Machine Learning Engineer, my core focus is architecting, training, and optimizing intelligent systems to solve complex data constraints. In modern software engineering, AI tools are powerful force-multipliers.

To maximize workflow velocity, the frontend interface (app.py) and secondary documentation assets of this project were generated using advanced LLM code-generation pipelines under my direct architectural supervision. Treating AI as an automated execution layer allows a single engineer to deploy end-to-end full-stack intelligent applications rapidly without compromising software engineering fundamentals. I take full ownership of the system design, pipeline logic, and underlying local infrastructure.

---

## 💡 Project Overview

**CineMatch AI** is a local hybrid recommendation system that performs content-based semantic matching and collaborative filtering across two distinct media catalogs: **Movies** and **TV Shows**.

By leveraging high-quality textual embeddings and sparse user interaction vectors, the project suggests titles based on descriptive plots, keywords, genres, and cast details. The system runs as two isolated pipelines, preventing crossovers between movies and TV show recommendations while maintaining a unified search interface.

---

## 📋 Key Features

*   🔍 **Unified Search Autocomplete**: Search across both catalogs simultaneously with dynamic **Movie** (indigo) and **TV Show** (purple) type badges in the suggestions panel.
*   🧠 **Dual Content-Based Models**: Uses LLM embeddings (`all-MiniLM-L6-v2`) to encode plot synopses, genres, directors, and actors into 384-dimensional dense vectors.
*   👤 **Client Personalized Matching**: Computes collaborative user preference centroids by averaging embeddings of highly rated movies (rating $\ge$ 3.5), recommending new matching films while filtering out already-watched titles.
*   💎 **Premium Glassmorphic UI**: Features a dark-mode user interface utilizing backdrop filters, radial glowing ambient gradients, animated hover transitions, and customized input forms (arrows hidden on number inputs).
*   🚀 **High Performance Backend**: Scalable FastAPI API endpoints backed by NumPy-optimized matrix dot-products for sub-millisecond similarity queries.

---

## 🖥️ Frontend User Interface

The frontend is designed around a modern glassmorphic dashboard separating content recommendations and client profiling.

<div align="center">
  <img src="https://github.com/user-attachments/assets/debf97db-2917-48f8-b3de-c4667d402283" alt="Movie Recommendations" width="800" style="box-shadow: 0 4px 12px rgba(0,0,0,0.3); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;"/>
  <p><em>Figure 1: Semantic recommendations matching user inputs, tagged by media type.</em></p>

  <img src="https://github.com/user-attachments/assets/a334d4f8-132d-42ef-ad0a-cc4a6d482cf1" alt="Client Personalized Recommendations" width="800" style="box-shadow: 0 4px 12px rgba(0,0,0,0.3); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;"/>
  <p><em>Figure 2: Collaborative user profiling mapping MovieLens client rating logs.</em></p>
</div>

---

## 🛠️ Technical Architecture & Algorithms

### 1. Content-Based Filtering (Semantic Embeddings)
Descriptions are processed by the PyTorch-based Sentence-Transformers model.
*   **Movies Corpus:** Descriptive attributes are concatenated:
    $$\text{Description} = \text{Title} + \text{Genres} + \text{Keywords} + \text{Cast} + \text{Director} + \text{Overview}$$
*   **TV Shows Corpus:** Built using:
    $$\text{Description} = \text{Title} + \text{Year} + \text{Genre} + \text{Synopsis}$$
*   **Similarity Computation:** Calculated as the cosine angle between target vector $A$ and index library matrix $B$:
    $$\text{Similarity}(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$

### 2. Collaborative Filtering (User Interest Profiles)
For client profiles, we represent a user's tastes by computing the centroid (mean vector) of all their liked movies.
1.  Filter ratings to keep films with rating $R \ge 3.5$.
2.  Extract the vector $E_i$ for each liked movie $i$:
    $$U_{\text{profile}} = \frac{1}{N} \sum_{i=1}^{N} E_i$$
3.  Compute similarities against all candidate movies in the library, sorting results and removing already-watched IDs.

---

## 🏗️ Directory Structure

```
movie-recommendation/
├── data/                      # Raw datasets (MovieLens, TMDB, IMDB)
├── models/                    # Pickled metadata and vector representations
├── static/                    # Frontend client files
│   ├── index.html             # Glassmorphic single page markup
│   ├── style.css              # Styling sheets and custom badges
│   └── script.js              # Event routing and rendering script
├── requirements.txt           # Python application dependencies
├── download_dataset.py        # Dataset fetcher script
├── train.py                   # Embeddings generator pipeline
└── app.py                     # Backend FastAPI server
```

---

## 💻 Installation & Setup

### Prerequisites
*   Python 3.10+
*   Internet connection (to download datasets and load the Hugging Face transformer model)

### 1. Setup Environment
Clone the repository and initialize a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate      # On Windows
source venv/bin/activate   # On Linux/MacOS
```

### 2. Install Dependencies
Install all package requirements using `pip`:
```bash
pip install -r requirements.txt
```

### 3. Retrieve Datasets
Execute the downloader script to gather MovieLens Small, TMDB 5000 Movies, and the IMDB TV Shows datasets:
```bash
python download_dataset.py
```

### 4. Run Model Training
Start the model pipeline to tokenize fields and compute sentence embeddings. This saves the pickle artifacts to the `models/` directory:
```bash
python train.py
```

### 5. Launch the Server
Execute the FastAPI web application using the Uvicorn ASGI server:
```bash
python -m uvicorn app:app --port 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 🚀 API Documentation

### 1. Autocomplete Search
*   **Endpoint:** `/api/movies`
*   **Method:** `GET`
*   **Query Params:** `q` (string, minimum 2 characters)
*   **Response:**
    ```json
    [
      {
        "id": 10,
        "title": "Breaking Bad",
        "release_date": "2008",
        "parsed_genres": ["Crime", "Drama", "Thriller"],
        "type": "tv"
      }
    ]
    ```

### 2. Similar Movie Recommendations
*   **Endpoint:** `/api/recommend/movie/{movie_id}`
*   **Method:** `GET`

### 3. Similar TV Show Recommendations
*   **Endpoint:** `/api/recommend/tv/{tv_id}`
*   **Method:** `GET`

### 4. Client Personalized Movie Recommendations
*   **Endpoint:** `/api/recommend/user/{user_id}`
*   **Method:** `GET`
