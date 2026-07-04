import os
import urllib.request
import zipfile

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            block_size = 8192
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                if total_size > 0:
                    percent = downloaded * 100 / total_size
                    print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end="")
                else:
                    print(f"\rProgress: {downloaded} bytes", end="")
            print("\nDownload finished successfully.")
    except Exception as e:
        print(f"\nError downloading {url}: {e}")
        raise e

def main():
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(workspace_dir, "data")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory at: {data_dir}")

    ml_url = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
    ml_zip_path = os.path.join(data_dir, "ml-latest-small.zip")
    
    print("\nDownloading MovieLens")
    download_file(ml_url, ml_zip_path)
    
    print("Extracting MovieLens dataset...")
    try:
        with zipfile.ZipFile(ml_zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        print("MovieLens extracted successfully.")
        
        os.remove(ml_zip_path)
        print("Cleaned up MovieLens zip file.")
    except Exception as e:
        print(f"Error during extraction: {e}")
        
    tmdb_movies_url = "https://raw.githubusercontent.com/noahjett/Movie-Goodreads-Analysis/master/tmdb_5000_movies.csv"
    tmdb_credits_url = "https://raw.githubusercontent.com/noahjett/Movie-Goodreads-Analysis/master/tmdb_5000_credits.csv"
    
    tmdb_movies_path = os.path.join(data_dir, "tmdb_5000_movies.csv")
    tmdb_credits_path = os.path.join(data_dir, "tmdb_5000_credits.csv")
    
    print("\nDownloading TMDB 5000 Movies Dataset")
    download_file(tmdb_movies_url, tmdb_movies_path)
    
    print("\nDownloading TMDB 5000 Credits Dataset")
    download_file(tmdb_credits_url, tmdb_credits_path)
    
    tv_shows_url = "https://raw.githubusercontent.com/ankoorb/IMDB/master/tv_shows.csv"
    tv_shows_path = os.path.join(data_dir, "tv_shows.csv")
    
    print("\nDownloading IMDB TV Shows Dataset")
    download_file(tv_shows_url, tv_shows_path)
    
    print("\nAll datasets downloaded!")
    print("\nFiles in data directory:")
    for root, dirs, files in os.walk(data_dir):
        rel_path = os.path.relpath(root, data_dir)
        if rel_path == ".":
            rel_path = "data"
        else:
            rel_path = os.path.join("data", rel_path)
        print(f"{rel_path}/")
        for f in files:
            file_path = os.path.join(root, f)
            sz = os.path.getsize(file_path) / (1024 * 1024)
            print(f"    - {f} ({sz:.2f} MB)")

if __name__ == "__main__":
    main()
