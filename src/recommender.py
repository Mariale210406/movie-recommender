import pandas as pd
import pickle
from sklearn.metrics.pairwise import cosine_similarity

# Cargar el dataset y los modelos
df = pd.read_csv('data/processed/TMDB_clean.csv')

with open('src/tfidf_model.pkl', 'rb') as f:
    tfidf = pickle.load(f)

with open('src/matriz_tfidf.pkl', 'rb') as f:
    matriz_tfidf = pickle.load(f)

def recomendar_peliculas(titulo, n=10, min_imdb=6.0):
    indices = pd.Series(df.index, index=df['title']).drop_duplicates()
    
    if titulo not in indices:
        return None
    
    idx = indices[titulo]
    
    # Calcular similitud solo para esa película
    vector_pelicula = matriz_tfidf[idx]
    puntajes = cosine_similarity(vector_pelicula, matriz_tfidf).flatten()
    
    # Ordenar y tomar los mejores
    indices_similares = puntajes.argsort()[::-1][1:n*5+1]
    
    # Filtrar por IMDB rating mínimo
    resultado = df[['title', 'genres', 'imdb_rating', 'release_year', 'poster_path']].iloc[indices_similares]
    resultado = resultado[resultado['imdb_rating'] >= min_imdb]
    
    # Ordenar por IMDB rating
    resultado = resultado.sort_values('imdb_rating', ascending=False)
    
    return resultado.head(n).to_dict('records') 