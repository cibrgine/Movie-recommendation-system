import os
import pickle
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="CineMatch AI")

# Load model data
workspace_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(workspace_dir, "models")

metadata_path = os.path.join(models_dir, "movies_metadata.pkl")
embeddings_path = os.path.join(models_dir, "embeddings.pkl")
ratings_path = os.path.join(models_dir, "ratings_mapped.pkl")
tv_metadata_path = os.path.join(models_dir, "tv_metadata.pkl")
tv_embeddings_path = os.path.join(models_dir, "tv_embeddings.pkl")

# Global variables to store loaded data
df_metadata = None
embeddings = None
df_ratings = None
df_tv_metadata = None
tv_embeddings = None

@app.on_event("startup")
def startup_event():
    global df_metadata, embeddings, df_ratings, df_tv_metadata, tv_embeddings
    
    if not os.path.exists(metadata_path) or not os.path.exists(embeddings_path):
        raise RuntimeError("Movie model files not found. Please run train.py first to generate the models.")
        
    print("Loading movies metadata...")
    with open(metadata_path, 'rb') as f:
        df_metadata = pickle.load(f)
        
    print("Loading movie embeddings...")
    with open(embeddings_path, 'rb') as f:
        embeddings = pickle.load(f)
        
    # Standardize embeddings shape and convert to float32
    embeddings = np.array(embeddings, dtype=np.float32)
    
    if os.path.exists(ratings_path):
        print("Loading user ratings...")
        with open(ratings_path, 'rb') as f:
            df_ratings = pickle.load(f)
    else:
        print("Warning: ratings_mapped.pkl not found. User personalized recommendations will not be available.")
        
    # Load TV show models
    if os.path.exists(tv_metadata_path) and os.path.exists(tv_embeddings_path):
        print("Loading TV shows metadata...")
        with open(tv_metadata_path, 'rb') as f:
            df_tv_metadata = pickle.load(f)
            
        print("Loading TV show embeddings...")
        with open(tv_embeddings_path, 'rb') as f:
            tv_embeddings = pickle.load(f)
            
        tv_embeddings = np.array(tv_embeddings, dtype=np.float32)
    else:
        print("Warning: TV show model files not found. TV show recommendations will not be available.")

# Mount static folder
static_dir = os.path.join(workspace_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(workspace_dir, "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Index page not found")

@app.get("/api/movies")
def search_movies(q: str = ""):
    if not q or len(q.strip()) < 2:
        return []
    
    query = q.strip().lower()
    
    movie_results = []
    if df_metadata is not None:
        matches_movie = df_metadata[df_metadata['title'].str.lower().str.contains(query, na=False)].copy()
        matches_movie = matches_movie.sort_values(by='popularity', ascending=False).head(10)
        for _, row in matches_movie.iterrows():
            movie_results.append({
                "id": int(row['id']),
                "title": str(row['title']),
                "release_date": str(row['release_date']) if pd.notna(row['release_date']) else "",
                "parsed_genres": list(row['parsed_genres']),
                "type": "movie"
            })
            
    tv_results = []
    if df_tv_metadata is not None:
        matches_tv = df_tv_metadata[df_tv_metadata['title'].str.lower().str.contains(query, na=False)].copy()
        matches_tv = matches_tv.sort_values(by='popularity', ascending=False).head(10)
        for _, row in matches_tv.iterrows():
            tv_results.append({
                "id": int(row['id']),
                "title": str(row['title']),
                "release_date": str(row['release_date']) if pd.notna(row['release_date']) else "",
                "parsed_genres": list(row['parsed_genres']),
                "type": "tv"
            })
            
    # Combine and limit to 10 overall. Show top 5 movie matches and top 5 TV show matches if both exist.
    return movie_results[:5] + tv_results[:5]

@app.get("/api/recommend/movie/{movie_id}")
def recommend_by_movie(movie_id: int):
    matching_idx = df_metadata[df_metadata['id'] == movie_id].index
    if len(matching_idx) == 0:
        raise HTTPException(status_code=404, detail="Movie not found in dataset")
    
    idx = matching_idx[0]
    target_embedding = embeddings[idx]
    
    # Compute cosine similarity
    dot_products = np.dot(embeddings, target_embedding)
    norms = np.linalg.norm(embeddings, axis=1)
    target_norm = np.linalg.norm(target_embedding)
    
    # Prevent division by zero
    norms[norms == 0] = 1e-9
    if target_norm == 0:
        target_norm = 1e-9
        
    similarities = dot_products / (norms * target_norm)
    
    # Get top 11 indices (including the movie itself)
    top_indices = np.argsort(similarities)[::-1][:11]
    
    results = []
    for i in top_indices:
        movie_row = df_metadata.iloc[i]
        curr_id = int(movie_row['id'])
        if curr_id == movie_id:
            continue
            
        results.append({
            "id": curr_id,
            "title": str(movie_row['title']),
            "parsed_genres": list(movie_row['parsed_genres']),
            "overview": str(movie_row['overview']) if pd.notna(movie_row['overview']) else "",
            "popularity": float(movie_row['popularity']),
            "vote_average": float(movie_row['vote_average']),
            "vote_count": int(movie_row['vote_count']),
            "director": str(movie_row['director']),
            "parsed_cast": list(movie_row['parsed_cast']),
            "similarity": float(similarities[i])
        })
        
    return {"recommendations": results[:10]}

@app.get("/api/recommend/tv/{tv_id}")
def recommend_by_tv(tv_id: int):
    if df_tv_metadata is None or tv_embeddings is None:
        raise HTTPException(status_code=503, detail="TV show recommendations not ready")
        
    matching_idx = df_tv_metadata[df_tv_metadata['id'] == tv_id].index
    if len(matching_idx) == 0:
        raise HTTPException(status_code=404, detail="TV show not found in dataset")
    
    idx = matching_idx[0]
    target_embedding = tv_embeddings[idx]
    
    # Compute cosine similarity
    dot_products = np.dot(tv_embeddings, target_embedding)
    norms = np.linalg.norm(tv_embeddings, axis=1)
    target_norm = np.linalg.norm(target_embedding)
    
    # Prevent division by zero
    norms[norms == 0] = 1e-9
    if target_norm == 0:
        target_norm = 1e-9
        
    similarities = dot_products / (norms * target_norm)
    
    # Get top 11 indices (including the show itself)
    top_indices = np.argsort(similarities)[::-1][:11]
    
    results = []
    for i in top_indices:
        show_row = df_tv_metadata.iloc[i]
        curr_id = int(show_row['id'])
        if curr_id == tv_id:
            continue
            
        results.append({
            "id": curr_id,
            "title": str(show_row['title']),
            "parsed_genres": list(show_row['parsed_genres']),
            "overview": str(show_row['overview']) if pd.notna(show_row['overview']) else "",
            "popularity": float(show_row['popularity']),
            "vote_average": float(show_row['vote_average']),
            "vote_count": int(show_row['vote_count']),
            "director": str(show_row['director']),
            "parsed_cast": list(show_row['parsed_cast']),
            "similarity": float(similarities[i]),
            "release_date": str(show_row['release_date']) if pd.notna(show_row['release_date']) else ""
        })
        
    return {"recommendations": results[:10]}

@app.get("/api/recommend/user/{user_id}")
def recommend_by_user(user_id: int):
    if df_ratings is None:
        raise HTTPException(status_code=503, detail="Ratings dataset not available")
        
    user_ratings = df_ratings[df_ratings['userId'] == user_id].copy()
    if len(user_ratings) == 0:
        raise HTTPException(status_code=404, detail="User rating history not found")
        
    # Get user highly rated movies
    liked_movies = user_ratings[user_ratings['rating'] >= 3.5].sort_values(by='rating', ascending=False)
    
    # Fallback: if user has no ratings >= 3.5, take top 5 highest rated movies
    if len(liked_movies) < 3:
        liked_movies = user_ratings.sort_values(by='rating', ascending=False).head(5)
        
    if len(liked_movies) == 0:
        return {"user_liked_movies": [], "recommendations": []}
        
    liked_movie_ids = liked_movies['tmdbId'].tolist()
    liked_movie_indices = []
    liked_metadata = []
    
    for i, row in liked_movies.iterrows():
        m_id = int(row['tmdbId'])
        match_idx = df_metadata[df_metadata['id'] == m_id].index
        if len(match_idx) > 0:
            liked_movie_indices.append(match_idx[0])
            m_row = df_metadata.iloc[match_idx[0]]
            liked_metadata.append({
                "id": m_id,
                "title": str(m_row['title']),
                "rating": float(row['rating'])
            })
            
    if not liked_movie_indices:
        raise HTTPException(status_code=404, detail="Liked movies not present in metadata subset")
        
    # Profile embedding: mean of liked movie vectors
    liked_embeddings = embeddings[liked_movie_indices]
    user_profile = np.mean(liked_embeddings, axis=0)
    
    # Calculate similarities
    dot_products = np.dot(embeddings, user_profile)
    norms = np.linalg.norm(embeddings, axis=1)
    profile_norm = np.linalg.norm(user_profile)
    
    norms[norms == 0] = 1e-9
    if profile_norm == 0:
        profile_norm = 1e-9
        
    similarities = dot_products / (norms * profile_norm)
    
    sorted_indices = np.argsort(similarities)[::-1]
    rated_movie_ids_set = set(user_ratings['tmdbId'])
    
    results = []
    for idx in sorted_indices:
        movie_row = df_metadata.iloc[idx]
        curr_id = int(movie_row['id'])
        if curr_id in rated_movie_ids_set:
            continue
            
        results.append({
            "id": curr_id,
            "title": str(movie_row['title']),
            "parsed_genres": list(movie_row['parsed_genres']),
            "overview": str(movie_row['overview']) if pd.notna(movie_row['overview']) else "",
            "popularity": float(movie_row['popularity']),
            "vote_average": float(movie_row['vote_average']),
            "vote_count": int(movie_row['vote_count']),
            "director": str(movie_row['director']),
            "parsed_cast": list(movie_row['parsed_cast']),
            "similarity": float(similarities[idx])
        })
        
        if len(results) >= 10:
            break
            
    return {
        "user_liked_movies": liked_metadata[:5],
        "recommendations": results
    }
