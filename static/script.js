// Update player status every second
function updateStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            // Update track name
            const trackElement = document.getElementById('trackName');
            trackElement.textContent = data.track_name || 'No track loaded';

            // Update status
            const statusElement = document.getElementById('status');
            statusElement.textContent = data.status || 'Stopped';
            statusElement.className = 'status ' + (data.status || 'stopped').toLowerCase();

            // Update volume
            const volumeElement = document.getElementById('volume');
            volumeElement.textContent = `Volume: ${data.volume}%`;

            // Update playlist
            updatePlaylist(data.playlist, data.current_index, data.favorites);
        })
        .catch(error => {
            console.error('Error fetching status:', error);
        });
}

// Update playlist display
function updatePlaylist(playlist, currentIndex, favorites) {
    const container = document.getElementById('playlistContainer');

    if (!playlist || playlist.length === 0) {
        container.innerHTML = '<p>No music files found</p>';
        return;
    }

    container.innerHTML = '';

    playlist.forEach((track, index) => {
        const item = document.createElement('div');
        item.className = 'playlist-item';

        if (index === currentIndex) {
            item.classList.add('active');
        }

        if (favorites && favorites.includes(index)) {
            item.classList.add('favorite');
        }

        item.textContent = track;
        container.appendChild(item);
    });
}

// Initialize status updates
document.addEventListener('DOMContentLoaded', function() {
    // Update immediately
    updateStatus();

    // Update every second
    setInterval(updateStatus, 1000);
});
