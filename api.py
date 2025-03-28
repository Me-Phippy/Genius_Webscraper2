from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote
import os
import json

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

def search_song(artist, song_title):
    """Search for a song on Genius and return the URL of the first result."""
    search_term = f"{artist} {song_title}"
    search_url = f"https://genius.com/api/search/song?q={quote(search_term)}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(search_url, headers=headers)
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    
    # Check if we have search results
    if 'response' in data and 'sections' in data['response']:
        for section in data['response']['sections']:
            if section['hits']:
                # Get the URL of the first result
                song_url = section['hits'][0]['result']['url']
                return song_url
    
    return None

def get_song_info(url):
    """Extract comprehensive song information from Genius page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return None
        
        # Parse page content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title from the SongHeader__Title element
        title_element = soup.find('h1', class_=re.compile(r'SongHeader-desktop__Title'))
        title = title_element.get_text(strip=True) if title_element else 'Unknown Title'
        
        # Extract artist from the HeaderArtistAndTracklist container
        artist_element = soup.find('a', class_=re.compile(r'StyledLink'), href=re.compile(r'/artists/'))
        artist = artist_element.get_text(strip=True) if artist_element else 'Unknown Artist'
        
        # Extract album from the primary-album link
        album_element = soup.find('a', href=re.compile(r'#primary-album'))
        album = album_element.get_text(strip=True) if album_element else 'Unknown Album'
        
        # Extract cover art
        cover_art = None
        cover_element = soup.find('img', class_=re.compile(r'SongHeader-desktop__CoverArt'))
        if cover_element and 'src' in cover_element.attrs:
            cover_art = cover_element['src']
        
        # Extract release date
        release_date = "Unknown"
        release_element = soup.find('div', string=re.compile(r'Release Date'))
        if release_element and release_element.find_next():
            release_date = release_element.find_next().text.strip()
        
        # Extract producers from HeaderCredits section
        producers = []
        producer_label = soup.find('p', class_=re.compile(r'HeaderCredits__Label'), string=re.compile(r'Producers'))
        if producer_label:
            producer_container = producer_label.find_next('div', class_=re.compile(r'HeaderCredits__List'))
            if producer_container:
                producer_links = producer_container.find_all('a', class_=re.compile(r'StyledLink'))
                for producer in producer_links:
                    producers.append(producer.get_text(strip=True))
        
        # Extract writers
        writers = []
        writer_label = soup.find('p', class_=re.compile(r'HeaderCredits__Label'), string=re.compile(r'Written By'))
        if writer_label:
            writer_container = writer_label.find_next('div', class_=re.compile(r'HeaderCredits__List'))
            if writer_container:
                writer_links = writer_container.find_all('a', class_=re.compile(r'StyledLink'))
                for writer in writer_links:
                    writers.append(writer.get_text(strip=True))
        
        return {
            'title': title,
            'artist': artist,
            'album': album,
            'cover_art': cover_art,
            'release_date': release_date,
            'producers': producers,
            'writers': writers
        }
    
    except Exception as e:
        print(f"Error extracting song info: {e}")
        return {
            'title': 'Unknown Title',
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'cover_art': None,
            'release_date': 'Unknown',
            'producers': [],
            'writers': []
        }

def get_lyrics(url):
    """Extract complete lyrics from a Genius song page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return "Could not access the lyrics page."
        
        # Get the page content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Try to find the lyrics div directly
        lyrics_div = soup.find('div', class_=re.compile(r'Lyrics__Root'))
        if not lyrics_div:
            lyrics_div = soup.find('div', class_=re.compile(r'lyrics|Lyrics'))
        
        if lyrics_div:
            # Process the lyrics div to extract all text
            # Replace <br> tags with newlines
            for br in lyrics_div.find_all('br'):
                br.replace_with('\n')
            
            # Get all text content
            lyrics = lyrics_div.get_text()
            
            # Clean up the lyrics
            lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)  # Remove excessive newlines
            lyrics = lyrics.strip()
            return lyrics
        
        # Method 2: Try to find all lyrics containers
        lyrics_containers = soup.find_all('div', class_=re.compile(r'Lyrics__Container'))
        if lyrics_containers:
            full_lyrics = ""
            for container in lyrics_containers:
                # Replace <br> tags with newlines
                for br in container.find_all('br'):
                    br.replace_with('\n')
                
                # Get text and append to full lyrics
                container_text = container.get_text()
                full_lyrics += container_text + "\n\n"
            
            # Clean up the lyrics
            full_lyrics = re.sub(r'\n{3,}', '\n\n', full_lyrics)  # Remove excessive newlines
            return full_lyrics.strip()
        
        # Method 3: Try to find the lyrics in any element with lyrics-related class
        lyrics_elements = soup.select('[class*="lyrics"], [class*="Lyrics"]')
        if lyrics_elements:
            full_lyrics = ""
            for element in lyrics_elements:
                # Replace <br> tags with newlines
                for br in element.find_all('br'):
                    br.replace_with('\n')
                
                element_text = element.get_text()
                if len(element_text) > 100:  # Only include substantial text blocks
                    full_lyrics += element_text + "\n\n"
            
            if full_lyrics:
                full_lyrics = re.sub(r'\n{3,}', '\n\n', full_lyrics)  # Remove excessive newlines
                return full_lyrics.strip()
        
        # Method 4: Last resort - try to find the main content area
        main_content = soup.find('main') or soup.find('div', class_=re.compile(r'Main|Content|Container'))
        if main_content:
            # Replace <br> tags with newlines
            for br in main_content.find_all('br'):
                br.replace_with('\n')
            
            # Get all text content
            content_text = main_content.get_text()
            
            # Try to extract lyrics by looking for verse/chorus patterns
            lyrics_pattern = re.compile(r'(\[.*?\].*?)(?=\[|$)', re.DOTALL)
            lyrics_matches = lyrics_pattern.findall(content_text)
            
            if lyrics_matches:
                full_lyrics = "\n\n".join(lyrics_matches)
                full_lyrics = re.sub(r'\n{3,}', '\n\n', full_lyrics)  # Remove excessive newlines
                return full_lyrics.strip()
        
        # If all methods fail, return a message
        return "Could not extract lyrics from the page. The website structure might have changed."
    
    except Exception as e:
        return f"Error extracting lyrics: {str(e)}"

def fetch_lyrics(artist, song_title):
    """Main function to fetch lyrics and song info."""
    song_url = search_song(artist, song_title)
    
    if not song_url:
        return {
            'success': False,
            'message': f"Could not find lyrics for '{song_title}' by {artist}"
        }
    
    lyrics = get_lyrics(song_url)
    song_info = get_song_info(song_url)
    
    if not lyrics or lyrics.startswith("Could not extract lyrics"):
        return {
            'success': False,
            'message': f"Found the song but could not extract lyrics for '{song_title}' by {artist}"
        }
    
    return {
        'success': True,
        'lyrics': lyrics,
        'song_info': song_info,
        'url': song_url
    }

@app.route('/api/lyrics', methods=['GET'])
def get_lyrics_api():
    artist = request.args.get('artist', '')
    song = request.args.get('song', '')
    
    if not artist or not song:
        return jsonify({
            'success': False,
            'message': 'Both artist and song parameters are required'
        }), 400
    
    result = fetch_lyrics(artist, song)
    
    # Debug: Print the first 100 characters of lyrics to console
    if result['success']:
        print(f"Lyrics length: {len(result['lyrics'])}")
        print(f"First 100 chars: {result['lyrics'][:100]}")
    
    return jsonify(result)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("Lyrics Finder is running at http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)