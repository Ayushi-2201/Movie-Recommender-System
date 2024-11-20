import streamlit as st
import pickle
import requests

st.set_page_config(page_title="Movie Recommender", page_icon=":movie_camera:", layout="wide")

def fetch_poster(movie_id):
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=d04bcdb23bc691fcd083e1b436af2437")
    poster = response.json()['poster_path']
    return "https://image.tmdb.org/t/p/original" + poster

def recommend(movie_name):
    index = movies_list[movies_list['title'] == movie_name].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    movie_recommendations = []
    posters = []
    for i in distances[1:6]:
        movie_recommendations.append(movies_list.iloc[i[0]]['title'])
        posters.append(fetch_poster(movies_list.iloc[i[0]]['id']))
    return movie_recommendations, posters

st.title('Movie Recommender System')

movies_list = pickle.load(open('movies_dataset.pkl', 'rb'))

movies = movies_list['title'].values


selected_movie = st.selectbox('Select a movie', movies)

similarity = pickle.load(open('similarity.pkl', 'rb'))

if st.button("Recommend Movies"):

    recommendations, posters = recommend(selected_movie)
    
    cols = st.columns(5) # creates columns dynamically


    for i in range(len(recommendations)):
        with cols[i]:
    
            st.image(posters[i], use_container_width=True)
            st.text(recommendations[i])