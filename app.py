# Test
import pickle
import streamlit as st
import requests
import pandas as pd # Import pandas, needed for reading the pickle if it's a DataFrame

# --- Page Configuration (MUST be the first Streamlit command) ---
st.set_page_config(layout="wide") # Use wide layout for better left alignment feel

# --- Custom CSS (Optional - adjust font size as needed) ---
# You can experiment with the font-size value (e.g., 1.1em, 16px, etc.)
st.markdown("""
<style>
/* Increase font size for the main text elements */
.stText, .stMarkdown, .stSelectbox > div, .stButton > button {
    /* font-size: 1.1em;  */ /* Uncomment and adjust if needed */
}
/* Style for the recommended movie titles specifically */
.movie-title {
    font-size: 1em; /* Adjusted font size slightly */
    font-weight: bold; /* Make titles bold */
    text-align: center; /* Center title below poster */
    height: 3em; /* Give fixed height to prevent layout shifts, allows up to 2 lines */
    line-height: 1.5em; /* Adjust line height for two lines */
    overflow: hidden; /* Hide overflow if title is too long */
    text-overflow: ellipsis; /* Add ellipsis for long titles */
    /* Removed flexbox centering as text-align handles horizontal centering */
    margin-top: 5px; /* Add a small gap between poster and title */
}
/* Ensure columns are vertically aligned at the top */
/* .stHorizontalBlock > div {
    vertical-align: top;
} */ /* May not be needed depending on exact layout */

/* Center images within their column container */
.stImage > img {
    display: block;
    margin-left: auto;
    margin-right: auto;
    max-height: 500px; /* Optional: constrain max image height */
    object-fit: contain; /* Scale the image while preserving aspect ratio */
}
</style>
""", unsafe_allow_html=True)
# --- End Custom CSS ---


def fetch_poster(movie_id):
    """Fetches the movie poster URL from TMDB API."""
    try:
        # IMPORTANT: Replace with your actual API key or use st.secrets
        api_key = "8265bd1679663a7ea12ac168da84d2e8" # Consider hiding API keys (e.g., using st.secrets['tmdb_api_key'])
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(url, timeout=10) # Add a timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            full_path = f"https://image.tmdb.org/t/p/w500/{poster_path}"
            return full_path
        else:
            # Return a placeholder if no poster is found
            return "https://via.placeholder.com/500x750.png?text=No+Poster+Found" # More specific placeholder
    except requests.exceptions.Timeout:
        st.warning(f"Timeout fetching poster for movie ID {movie_id}.")
        return "https://via.placeholder.com/500x750.png?text=Timeout"
    except requests.exceptions.RequestException as e:
        st.warning(f"Error fetching poster for movie ID {movie_id}: {e}") # Use warning, not error, to avoid stopping app
        return "https://via.placeholder.com/500x750.png?text=API+Error"
    except Exception as e:
        st.warning(f"An unexpected error occurred in fetch_poster for movie ID {movie_id}: {e}")
        return "https://via.placeholder.com/500x750.png?text=Error"

def recommend(movie_title):
    """Recommends movies based on similarity."""
    try:
        # Find the index of the movie
        matching_movies = movies[movies['title'] == movie_title]
        if matching_movies.empty:
            st.error(f"Movie '{movie_title}' not found in the list.")
            return [], []
        index = matching_movies.index[0]

        # Get similarity scores and sort them
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

        recommended_movie_names = []
        recommended_movie_posters = []

        # Iterate through the top similar movies (excluding the movie itself)
        count = 0
        processed_indices = set([index]) # Keep track of processed indices to avoid duplicates if data has issues

        for i, score in distances:
            if i in processed_indices: # Skip the original movie or already processed ones
                continue
            if count >= 5: # Get top 5 recommendations
                break

            # Ensure index is valid
            if 0 <= i < len(movies):
                try:
                    # Fetch the movie details
                    movie_id = movies.iloc[i].movie_id
                    poster_url = fetch_poster(movie_id) # Fetch poster first
                    # Only add if poster fetch was somewhat successful (not strictly None, maybe check for placeholders too if needed)
                    if poster_url:
                        recommended_movie_posters.append(poster_url)
                        recommended_movie_names.append(movies.iloc[i].title)
                        processed_indices.add(i)
                        count += 1
                    else:
                        st.warning(f"Skipping movie '{movies.iloc[i].title}' due to poster fetch issue.")

                except Exception as e:
                    st.warning(f"Could not process recommendation for index {i} ('{movies.iloc[i].title}'): {e}")
            else:
                 st.warning(f"Invalid movie index {i} found in similarity data.")


        # Handle cases where fewer than 5 recommendations are found by filling with placeholders
        while len(recommended_movie_names) < 5:
             recommended_movie_names.append("N/A")
             recommended_movie_posters.append("https://via.placeholder.com/500x750.png?text=N/A")


        return recommended_movie_names, recommended_movie_posters

    except Exception as e:
        st.error(f"An error occurred during recommendation: {e}")
        # Return empty lists with placeholders if recommendation fails
        names = ["Error"] * 5
        posters = ["https://via.placeholder.com/500x750.png?text=Rec+Error"] * 5
        return names, posters


# --- Load Data ---
try:
    # Assuming movie_list.pkl contains a pandas DataFrame
    # Use relative paths assuming the script and pkl files are in the same folder
    movies_path = 'movie_list.pkl'
    similarity_path = 'similarity.pkl'
    movies = pd.read_pickle(movies_path)
    similarity = pickle.load(open(similarity_path,'rb'))
    # Ensure 'movies' is a DataFrame and has the required columns
    if not isinstance(movies, pd.DataFrame) or 'title' not in movies.columns or 'movie_id' not in movies.columns:
        st.error("Error: 'movie_list.pkl' must contain a Pandas DataFrame with 'title' and 'movie_id' columns.")
        st.stop() # Stop execution if data is invalid

    # Convert titles to string just in case to prevent potential errors in selectbox/matching
    movies['title'] = movies['title'].astype(str)
    movie_list = sorted(movies['title'].unique()) # Get unique, sorted list

except FileNotFoundError:
    st.error(f"Error: Make sure '{movies_path}' and '{similarity_path}' are in the same directory as the script.")
    st.stop()
except Exception as e:
    st.error(f"Error loading data files: {e}")
    st.stop()

# --- UI Elements ---
st.title('🎬 Movie Recommender System') # Use st.title for a larger title

selected_movie = st.selectbox(
    "Select or type a movie title:", # Improved prompt
    movie_list,
    index=None, # Start with no selection
    placeholder="Choose a movie..." # Add a placeholder
)

if st.button('Show Recommendations', key='recommend_button'): # Added a key for stability
    if selected_movie: # Check if a movie is selected
        # Show a spinner during recommendation process
        with st.spinner(f'Finding recommendations for {selected_movie}...'):
            recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

        if not recommended_movie_names: # Check if recommendation failed severely
             st.error("Could not generate recommendations. Please try again or select a different movie.")
        else:
            # Display recommendations in columns
            cols = st.columns(5) # Create 5 columns

            for i in range(5):
                with cols[i]:
                    # Check if recommendation data exists for this index
                    if i < len(recommended_movie_names):
                        poster_url = recommended_movie_posters[i]
                        title_display = recommended_movie_names[i]

                        # --- Display Poster First ---
                        st.image(poster_url, use_container_width='always', caption="" if title_display not in ["Error", "N/A"] else title_display) # Use caption for alt text/hover, keep width always

                        # --- Display Title Below ---
                        # Only display title text if it's not an error/placeholder shown in caption
                        if title_display not in ["Error", "N/A", "Rec+Error", "Timeout", "API+Error", "No Poster Found"]:
                           st.markdown(f'<p class="movie-title" title="{title_display}">{title_display}</p>', unsafe_allow_html=True) # Add title attribute for full name on hover
                        # If it is a placeholder/error shown in caption, maybe add minimal space or specific text
                        elif title_display != "N/A": # Don't add extra text for N/A if caption handled it
                            st.markdown(f'<p class="movie-title" style="color: #ff4b4b;">{title_display}</p>', unsafe_allow_html=True) # Style error text


                    else:
                        # Fallback placeholder if fewer than 5 recommendations were generated (shouldn't happen often with current logic)
                        st.image("https://via.placeholder.com/500x750.png?text=N/A", use_container_width='always')
                        st.markdown(f'<p class="movie-title">N/A</p>', unsafe_allow_html=True)

    elif selected_movie is None: # Specifically check for None if index=None is used
         st.info("Please select a movie from the dropdown first.") # Use info instead of warning
    else:
         # This case might occur if selected_movie is an empty string or similar, though unlikely with selectbox
         st.warning("Invalid movie selection.") # Use warning for invalid selection
