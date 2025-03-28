// DOM elements
const searchBtn = document.getElementById('search-btn');
const artistInput = document.getElementById('artist');
const songInput = document.getElementById('song');
const loadingElement = document.getElementById('loading');
const errorElement = document.getElementById('error');
const resultElement = document.getElementById('result');
const songTitleElement = document.getElementById('song-title');
const songArtistElement = document.getElementById('song-artist');
const songAlbumElement = document.getElementById('song-album');
const coverArtElement = document.getElementById('cover-art');
const lyricsElement = document.getElementById('lyrics');
const infoTitleElement = document.getElementById('info-title');
const infoArtistElement = document.getElementById('info-artist');
const infoAlbumElement = document.getElementById('info-album');
const infoReleaseDateElement = document.getElementById('info-release-date');
const infoProducersElement = document.getElementById('info-producers');
const infoWritersElement = document.getElementById('info-writers');
const geniusLinkElement = document.getElementById('genius-link');
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
const themeToggle = document.getElementById('theme-toggle');

// Initialize the application
function initApp() {
    // Check for saved theme preference or use preferred color scheme
    const savedTheme = localStorage.getItem('theme') || 
                      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    // Apply the theme
    if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        themeToggle.checked = true;
    }
    
    // Set up event listeners
    setupEventListeners();
}

// Set up all event listeners
function setupEventListeners() {
    // Theme toggle functionality
    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Search button click
    searchBtn.addEventListener('click', searchLyrics);
    
    // Tab functionality
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
    
    // Add Enter key support for search
    artistInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            songInput.focus();
        }
    });
    
    songInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchLyrics();
        }
    });
}

// Format lyrics with verse/chorus labels
function formatLyrics(lyrics) {
    // Add styling to [Verse], [Chorus], etc. labels
    return lyrics.replace(/\[(.*?)\]/g, '<div class="verse-label">[$1]</div>');
}

// Format list of items as tags
function formatTags(items) {
    if (!items || items.length === 0) {
        return 'Unknown';
    }
    
    return items.map(item => `<span class="tag">${item}</span>`).join(' ');
}

// Search function
async function searchLyrics() {
    const artist = artistInput.value.trim();
    const song = songInput.value.trim();
    
    if (!artist || !song) {
        showError('Please enter both artist and song title');
        return;
    }
    
    // Show loading, hide previous results and errors
    loadingElement.style.display = 'block';
    resultElement.style.display = 'none';
    errorElement.style.display = 'none';
    searchBtn.disabled = true;
    
    try {
        // Make API request
        const response = await fetch(`http://localhost:5000/api/lyrics?artist=${encodeURIComponent(artist)}&song=${encodeURIComponent(song)}`);
        const data = await response.json();
        
        // Hide loading
        loadingElement.style.display = 'none';
        searchBtn.disabled = false;
        
        if (!data.success) {
            showError(data.message || 'Failed to fetch lyrics');
            return;
        }
        
        // Display results
        displayResults(data);
    } catch (error) {
        loadingElement.style.display = 'none';
        searchBtn.disabled = false;
        showError('Error connecting to the lyrics service. Make sure the API is running.');
        console.error(error);
    }
}

// Display results function
function displayResults(data) {
    // Set song info
    songTitleElement.textContent = data.song_info.title;
    songArtistElement.textContent = data.song_info.artist;
    infoTitleElement.textContent = data.song_info.title;
    infoArtistElement.textContent = data.song_info.artist;
    
    // Set album info if available
    if (data.song_info.album && data.song_info.album !== "Unknown Album") {
        songAlbumElement.textContent = 'Album: ' + data.song_info.album;
        songAlbumElement.style.display = 'block';
        infoAlbumElement.textContent = data.song_info.album;
    } else {
        songAlbumElement.style.display = 'none';
        infoAlbumElement.textContent = 'Unknown';
    }
    
    // Set additional song info
    infoReleaseDateElement.textContent = data.song_info.release_date || 'Unknown';
    infoProducersElement.innerHTML = formatTags(data.song_info.producers);
    infoWritersElement.innerHTML = formatTags(data.song_info.writers);
    
    // Set cover art if available
    if (data.song_info.cover_art) {
        coverArtElement.src = data.song_info.cover_art;
        coverArtElement.alt = data.song_info.title + ' cover';
        coverArtElement.style.display = 'block';
    } else {
        coverArtElement.style.display = 'none';
    }
    
    // Set lyrics with formatting
    lyricsElement.innerHTML = formatLyrics(data.lyrics);
    
    // Set Genius link
    geniusLinkElement.href = data.url;
    
    // Show result
    resultElement.style.display = 'block';
    
    // Reset tabs to lyrics view
    tabs.forEach(t => t.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));
    document.querySelector('.tab[data-tab="lyrics"]').classList.add('active');
    document.getElementById('lyrics-tab').classList.add('active');
}

// Show error function
function showError(message) {
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);