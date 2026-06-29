import pandas as pd
import pickle
import random
from sklearn.metrics.pairwise import cosine_similarity

# Cargar dataset y modelos
df = pd.read_csv('data/processed/TMDB_clean.csv')

with open('src/tfidf_model.pkl', 'rb') as f:
    tfidf = pickle.load(f)

with open('src/matriz_tfidf.pkl', 'rb') as f:
    matriz_tfidf = pickle.load(f)

# Diccionarios de traducción
GENEROS_ES = {
    'tristeza': 'Drama',
    'triste': 'Drama',
    'llorar': 'Drama',
    'reir': 'Comedy',
    'reír': 'Comedy',
    'comedia': 'Comedy',
    'gracioso': 'Comedy',
    'feliz': 'Comedy',
    'miedo': 'Horror',
    'terror': 'Horror',
    'suspenso': 'Thriller',
    'accion': 'Action',
    'acción': 'Action',
    'romance': 'Romance',
    'amor': 'Romance',
    'familia': 'Family',
    'niños': 'Animation',
    'animacion': 'Animation',
    'animación': 'Animation',
    'ciencia ficcion': 'Science Fiction',
    'aventura': 'Adventure',
    'musical': 'Music',
    'historia': 'History',
    'guerra': 'War',
    'crimen': 'Crime',
    'misterio': 'Mystery',
}

COMPANIAS = {
    'disney': 'Walt Disney',
    'marvel': 'Marvel',
    'pixar': 'Pixar',
    'warner': 'Warner',
    'netflix': 'Netflix',
    'dreamworks': 'DreamWorks',
    'universal': 'Universal',
    'sony': 'Sony',
}

def detectar_intencion(mensaje):
    mensaje = mensaje.lower().strip()

    # 1. Similar a una película
    if 'como' in mensaje or 'similar' in mensaje or 'parecida' in mensaje:
        return 'similar'

    # 2. Por director
    if 'director' in mensaje or 'dirigida' in mensaje or 'hizo' in mensaje:
        return 'director'

    # 3. Por duración
    if 'hora' in mensaje or 'minuto' in mensaje or 'corta' in mensaje or 'larga' in mensaje:
        return 'duracion'

    # 4. Por compañía
    for compania in COMPANIAS:
        if compania in mensaje:
            return 'compania'

    # 5. Por género/emoción
    for palabra in GENEROS_ES:
        if palabra in mensaje:
            return 'genero'

    # 6. Por año
    for palabra in mensaje.split():
        if palabra.isdigit() and 1900 <= int(palabra) <= 2030:
            return 'año'

    # 7. Por idioma
    if 'español' in mensaje or 'ingles' in mensaje or 'inglés' in mensaje or 'idioma' in mensaje:
        return 'idioma'

    # 8. Familia
    if 'familia' in mensaje or 'niños' in mensaje or 'hijos' in mensaje:
        return 'familia'

    # 9. Estado de ánimo feliz
    if 'feliz' in mensaje or 'reir' in mensaje or 'reír' in mensaje or 'alegre' in mensaje:
        return 'feliz'

    # 10. No sé qué ver
    if 'no se' in mensaje or 'no sé' in mensaje or 'recomienda' in mensaje or 'sorpresa' in mensaje:
        return 'sorpresa'

    return 'desconocido'


def responder(mensaje):
    intencion = detectar_intencion(mensaje)
    mensaje_lower = mensaje.lower()

    # 1. Similar a una película
    if intencion == 'similar':
        palabras = mensaje.split()
        for i, palabra in enumerate(palabras):
            if palabra.lower() in ['como', 'similar', 'parecida']:
                titulo = ' '.join(palabras[i+1:]).strip('?').strip()
                indices = pd.Series(df.index, index=df['title']).drop_duplicates()
                if titulo in indices:
                    idx = indices[titulo]
                    vector = matriz_tfidf[idx]
                    puntajes = cosine_similarity(vector, matriz_tfidf).flatten()
                    indices_similares = puntajes.argsort()[::-1][1:50]
                    resultado = df[['title', 'genres', 'imdb_rating', 'release_year']].iloc[indices_similares]
                    resultado = resultado[resultado['imdb_rating'] >= 6.0].head(5)
                    return formatear_respuesta(f"Películas similares a {titulo}", resultado)
        return "¿Puedes decirme el nombre exacto de la película? Por ejemplo: 'Dame películas como Inception'"

    # 2. Por director
    elif intencion == 'director':
        palabras = mensaje.split()
        for i, palabra in enumerate(palabras):
            if palabra.lower() in ['director', 'dirigida', 'hizo']:
                nombre = ' '.join(palabras[i+1:]).strip('?').strip()
                resultado = df[df['director'].str.contains(nombre, case=False, na=False)]
                resultado = resultado[['title', 'genres', 'imdb_rating', 'release_year']].sort_values('imdb_rating', ascending=False).head(5)
                if not resultado.empty:
                    return formatear_respuesta(f"Películas de {nombre}", resultado)
                return f"No encontré películas del director {nombre}. ¿Puedes verificar el nombre?"

    # 3. Por duración
    elif intencion == 'duracion':
        minutos = None
        for palabra in mensaje_lower.split():
            if palabra.isdigit():
                num = int(palabra)
                if 'hora' in mensaje_lower:
                    minutos = num * 60
                else:
                    minutos = num
                break

        resultado = df.copy()

        # Detectar género adicional
        for palabra, genero in GENEROS_ES.items():
            if palabra in mensaje_lower:
                resultado = resultado[resultado['genres'].str.contains(genero, case=False, na=False)]
                break

        if minutos:
            resultado = resultado[
                (resultado['runtime'] >= minutos - 20) &
                (resultado['runtime'] <= minutos + 20)
            ]

        resultado = resultado[resultado['imdb_rating'] >= 6.0].sort_values('imdb_rating', ascending=False).head(5)
        return formatear_respuesta("Películas que coinciden con tu búsqueda", resultado)

    # 4. Por compañía
    elif intencion == 'compania':
        for compania, nombre_real in COMPANIAS.items():
            if compania in mensaje_lower:
                resultado = df[df['production_companies'].str.contains(nombre_real, case=False, na=False)]
                resultado = resultado[['title', 'genres', 'imdb_rating', 'release_year']].sort_values('imdb_rating', ascending=False).head(5)
                if not resultado.empty:
                    return formatear_respuesta(f"Mejores películas de {nombre_real}", resultado)
        return "No encontré películas de esa compañía."

    # 5. Por género
    elif intencion == 'genero':
        for palabra, genero in GENEROS_ES.items():
            if palabra in mensaje_lower:
                resultado = df[df['genres'].str.contains(genero, case=False, na=False)]
                resultado = resultado[resultado['imdb_rating'] >= 6.0].sort_values('imdb_rating', ascending=False).head(5)
                return formatear_respuesta(f"Mejores películas de {genero}", resultado)

    # 6. Por año
    elif intencion == 'año':
        for palabra in mensaje_lower.split():
            if palabra.isdigit() and 1900 <= int(palabra) <= 2030:
                año = int(palabra)
                resultado = df[df['release_year'] == año]
                resultado = resultado[['title', 'genres', 'imdb_rating', 'release_year']].sort_values('imdb_rating', ascending=False).head(5)
                if not resultado.empty:
                    return formatear_respuesta(f"Mejores películas del {año}", resultado)
                return f"No encontré películas del año {año}."

    # 7. Por idioma
    elif intencion == 'idioma':
        if 'español' in mensaje_lower:
            resultado = df[df['original_language'] == 'es']
        else:
            resultado = df[df['original_language'] == 'en']
        resultado = resultado[['title', 'genres', 'imdb_rating', 'release_year']].sort_values('imdb_rating', ascending=False).head(5)
        return formatear_respuesta("Películas en ese idioma", resultado)

    # 8. Familia
    elif intencion == 'familia':
        resultado = df[df['genres'].str.contains('Family|Animation', case=False, na=False)]
        resultado = resultado[resultado['imdb_rating'] >= 6.0].sort_values('imdb_rating', ascending=False).head(5)
        return formatear_respuesta("Películas perfectas para ver en familia", resultado)

    # 9. Feliz
    elif intencion == 'feliz':
        resultado = df[df['genres'].str.contains('Comedy', case=False, na=False)]
        resultado = resultado[resultado['imdb_rating'] >= 6.0].sort_values('imdb_rating', ascending=False).head(5)
        return formatear_respuesta("Películas para reír y pasar un buen rato", resultado)

    # 10. Sorpresa
    elif intencion == 'sorpresa':
        resultado = df[df['imdb_rating'] >= 7.5].sample(5)
        return formatear_respuesta("Te recomiendo estas películas altamente valoradas", resultado)

    return "No entendí tu pregunta. Puedes preguntarme cosas como: 'Dame películas como Inception', 'Películas de Disney', 'Quiero algo para reír', etc."


def formatear_respuesta(titulo, df_resultado):
    if df_resultado.empty:
        return {
            'texto': 'No encontré películas que coincidan. Intenta con otros términos.',
            'peliculas': []
        }
    peliculas = df_resultado.to_dict('records')
    for p in peliculas:
        p['release_year'] = int(p.get('release_year', 0))
        p['imdb_rating'] = round(float(p.get('imdb_rating', 0)), 1)
    return {
        'texto': titulo + ':',
        'peliculas': peliculas
    } 

