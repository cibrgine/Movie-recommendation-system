import os
import ast
import json
import pickle
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

def parse_json_column(val, key="name"):
    if not val or not isinstance(val, str) or val.strip() == "":
        return []
    try:
        data = ast.literal_eval(val)
        if isinstance(data, list):
            return [item.get(key) for item in data if isinstance(item, dict) and key in item]
    except (ValueError, SyntaxError):
        try:
            data = json.loads(val)
            if isinstance(data, list):
                return [item.get(key) for item in data if isinstance(item, dict) and key in item]
        except Exception:
            return []
    return []

def get_director(val):
    if not val or not isinstance(val, str) or val.strip() == "":
        return ""
    try:
        data = ast.literal_eval(val)
    except Exception:
        try:
            data = json.loads(val)
        except Exception:
            return ""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("job") == "Director":
                return item.get("name", "")
    return ""

def get_top_cast(val, limit=3):
    if not val or not isinstance(val, str) or val.strip() == "":
        return []
    try:
        data = ast.literal_eval(val)
    except Exception:
        try:
            data = json.loads(val)
        except Exception:
            return []
    if isinstance(data, list):
        return [item.get("name", "") for item in data[:limit] if isinstance(item, dict)]
    return []

def main():
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(workspace_dir, "data")
    models_dir = os.path.join(workspace_dir, "models")
    
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Created models directory at: {models_dir}")
        
    movies_path = os.path.join(data_dir, "tmdb_5000_movies.csv")
    credits_path = os.path.join(data_dir, "tmdb_5000_credits.csv")
    ratings_path = os.path.join(data_dir, "ml-latest-small", "ratings.csv")
    links_path = os.path.join(data_dir, "ml-latest-small", "links.csv")
    
    print("\nLoading datasets...")
    df_movies = pd.read_csv(movies_path)
    df_credits = pd.read_csv(credits_path)
    print(f"Loaded {len(df_movies)} movies from TMDB.")

    print("Merging movies and credits...")
    df_movies = df_movies.merge(df_credits, left_on='id', right_on='movie_id', suffixes=('', '_credits'))

    print("Parsing movie metadata (genres, keywords, cast, crew)...")
    df_movies['parsed_genres'] = df_movies['genres'].apply(parse_json_column)
    df_movies['parsed_keywords'] = df_movies['keywords'].apply(parse_json_column)
    df_movies['parsed_cast'] = df_movies['cast'].apply(lambda x: get_top_cast(x, 3))
    df_movies['director'] = df_movies['crew'].apply(get_director)
  
    print("Creating text descriptions for embedding...")
    texts = []
    for idx, row in df_movies.iterrows():
        title = row['title']
        genres = ", ".join(row['parsed_genres'])
        keywords = ", ".join(row['parsed_keywords'])
        cast = ", ".join(row['parsed_cast'])
        director = row['director']
        overview = row['overview'] if isinstance(row['overview'], str) else ""
        
        text = f"Title: {title}. Genres: {genres}. Keywords: {keywords}. Cast: {cast}. Director: {director}. Overview: {overview}."
        texts.append(text)
        
    df_movies['combined_text'] = texts

    metadata_cols = [
        'id', 'title', 'parsed_genres', 'parsed_keywords', 'parsed_cast', 
        'director', 'overview', 'popularity', 'vote_average', 'vote_count', 'release_date'
    ]
    df_metadata = df_movies[metadata_cols].copy()

    print("Loading Sentence-Transformer model ('all-MiniLM-L6-v2')...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Generating embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)
    print(f"Generated embeddings shape: {embeddings.shape}")

    print("\nMapping MovieLens ratings to TMDB IDs...")
    if os.path.exists(ratings_path) and os.path.exists(links_path):
        df_ratings = pd.read_csv(ratings_path)
        df_links = pd.read_csv(links_path)

        df_links = df_links.dropna(subset=['tmdbId'])
        df_links['tmdbId'] = df_links['tmdbId'].astype(int)
        df_links['movieId'] = df_links['movieId'].astype(int)

        movielens_to_tmdb = dict(zip(df_links['movieId'], df_links['tmdbId']))

        df_ratings['tmdbId'] = df_ratings['movieId'].map(movielens_to_tmdb)
        df_ratings = df_ratings.dropna(subset=['tmdbId'])
        df_ratings['tmdbId'] = df_ratings['tmdbId'].astype(int)

        tmdb_ids_set = set(df_metadata['id'])
        df_ratings_filtered = df_ratings[df_ratings['tmdbId'].isin(tmdb_ids_set)].copy()
        print(f"Mapped {len(df_ratings_filtered)} ratings from MovieLens matching TMDB movies.")

        ratings_save_path = os.path.join(models_dir, "ratings_mapped.pkl")
        with open(ratings_save_path, 'wb') as f:
            pickle.dump(df_ratings_filtered, f)
        print(f"Saved mapped ratings to {ratings_save_path}")
    else:
        print("Warning: MovieLens ratings or links not found, user profiling will not be available.")

    metadata_save_path = os.path.join(models_dir, "movies_metadata.pkl")
    embeddings_save_path = os.path.join(models_dir, "embeddings.pkl")
    
    with open(metadata_save_path, 'wb') as f:
        pickle.dump(df_metadata, f)
    print(f"Saved movies metadata to {metadata_save_path}")
    
    with open(embeddings_save_path, 'wb') as f:
        pickle.dump(embeddings, f)
    print(f"Saved movie embeddings to {embeddings_save_path}")
    
    print("\nTraining TV Shows Similarity Model")
    tv_shows_path = os.path.join(data_dir, "tv_shows.csv")
    
    if os.path.exists(tv_shows_path):
        print("Loading TV shows dataset...")
        df_tv = pd.read_csv(tv_shows_path)
        print(f"Loaded {len(df_tv)} TV shows.")
        
        df_tv = df_tv.rename(columns={'Unnamed: 0': 'id'})
        
        df_tv['title'] = df_tv['title'].fillna('Unknown')
        df_tv['genre'] = df_tv['genre'].fillna('')
        df_tv['text'] = df_tv['text'].fillna('')
        
        df_tv['votes'] = df_tv['votes'].astype(str).str.replace(',', '').str.strip()
        df_tv['parsed_votes'] = pd.to_numeric(df_tv['votes'], errors='coerce').fillna(0).astype(int)
        
        df_tv['parsed_rating'] = pd.to_numeric(df_tv['rating'], errors='coerce').fillna(0.0).astype(float)
        
        df_tv['parsed_genres'] = df_tv['genre'].apply(lambda x: [g.strip() for g in x.split(',')] if x else [])
        
        tv_texts = []
        for idx, row in df_tv.iterrows():
            title = row['title']
            year = row['year']
            genres = row['genre']
            synopsis = row['text']
            
            text = f"Title: {title}. Year: {year}. Genre: {genres}. Synopsis: {synopsis}."
            tv_texts.append(text)
            
        df_tv['combined_text'] = tv_texts
        
        df_tv_metadata = pd.DataFrame({
            'id': df_tv['id'].astype(int),
            'title': df_tv['title'],
            'parsed_genres': df_tv['parsed_genres'],
            'parsed_keywords': [[] for _ in range(len(df_tv))],
            'parsed_cast': [[] for _ in range(len(df_tv))],
            'director': ['' for _ in range(len(df_tv))],
            'overview': df_tv['text'],
            'popularity': df_tv['parsed_votes'].astype(float),
            'vote_average': df_tv['parsed_rating'],
            'vote_count': df_tv['parsed_votes'],
            'release_date': df_tv['year'].astype(str)
        })
        
        print("Generating TV show embeddings...")
        tv_embeddings = model.encode(tv_texts, show_progress_bar=True)
        print(f"Generated TV show embeddings shape: {tv_embeddings.shape}")
        
        tv_metadata_path = os.path.join(models_dir, "tv_metadata.pkl")
        tv_embeddings_path = os.path.join(models_dir, "tv_embeddings.pkl")
        
        with open(tv_metadata_path, 'wb') as f:
            pickle.dump(df_tv_metadata, f)
        print(f"Saved TV shows metadata to {tv_metadata_path}")
        
        with open(tv_embeddings_path, 'wb') as f:
            pickle.dump(tv_embeddings, f)
        print(f"Saved TV show embeddings to {tv_embeddings_path}")
    else:
        print("Warning: tv_shows.csv not found, skipping TV shows training.")
        
    print("\nTraining completed successfully! Both model artifacts saved.")

if __name__ == "__main__":
    main()
