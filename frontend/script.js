// ✅ YOUR BACKEND URL IS NOW CONFIGURED
const BACKEND_URL = 'https://yt-metadata-extractor.onrender.com'; 

let currentVideoId = '';

// 1. Main Function to Get Basic Data
async function fetchData() {
    const inputUrl = document.getElementById('videoUrl').value;
    
    // Extract Video ID
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = inputUrl.match(regExp);
    currentVideoId = (match && match[2].length === 11) ? match[2] : null;

    if (!currentVideoId) return alert('Please enter a valid YouTube URL');

    // UI Reset
    document.getElementById('loader').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    
    // Clear previous results
    document.getElementById('tags').innerHTML = '';
    document.getElementById('trans-text').innerText = '';
    document.getElementById('dl-links').innerHTML = '';
    document.getElementById('json-data').innerText = '';

    try {
        // 🚀 SECURE CALL: Requesting data from YOUR Backend
        const res = await fetch(`${BACKEND_URL}/api/basic-info?id=${currentVideoId}`);
        const data = await res.json();

        if (data.error) throw new Error(data.error);
        if (!data.items || data.items.length === 0) throw new Error("Video not found or private");

        const item = data.items[0];
        const snippet = item.snippet;
        const stats = item.statistics;

        // --- Update UI Elements ---
        
        // Thumbnail
        const thumbUrl = snippet.thumbnails.maxres ? snippet.thumbnails.maxres.url : snippet.thumbnails.medium.url;
        document.getElementById('thumb').src = thumbUrl;

        // Text Info
        document.getElementById('title').innerText = snippet.title;
        document.getElementById('channel').innerText = snippet.channelTitle;
        
        // Stats
        document.getElementById('views').innerText = parseInt(stats.viewCount).toLocaleString();
        document.getElementById('likes').innerText = stats.likeCount ? parseInt(stats.likeCount).toLocaleString() : 'Hidden';

        // JSON Tab
        document.getElementById('json-data').innerText = JSON.stringify(item, null, 2);

        // Tags Tab
        const tagsDiv = document.getElementById('tags');
        if (snippet.tags) {
            tagsDiv.innerHTML = snippet.tags.map(tag => `<span class="tag-pill">${tag}</span>`).join('');
        } else {
            tagsDiv.innerHTML = '<p style="color:#666; font-style:italic;">No tags found.</p>';
        }

        // Show Results
        document.getElementById('results').classList.remove('hidden');

    } catch (e) {
        console.error(e);
        alert('Error: ' + e.message);
    } finally {
        document.getElementById('loader').classList.add('hidden');
    }
}

// 2. Fetch Transcript (Via Backend)
async function fetchTranscript() {
    if (!currentVideoId) return;
    
    const btn = document.getElementById('trans-btn');
    const box = document.getElementById('trans-text');
    
    btn.innerText = "⏳ Loading Transcript...";
    btn.disabled = true;

    try {
        const res = await fetch(`${BACKEND_URL}/api/transcript?id=${currentVideoId}`);
        const data = await res.json();

        if (data.error) throw new Error(data.error);

        box.innerText = data.full_text;
        btn.innerText = "✅ Transcript Loaded";
    } catch (e) {
        box.innerText = "Error: " + e.message;
        btn.innerText = "❌ Retry Transcript";
        btn.disabled = false;
    }
}

// 3. Fetch Download Formats (Via Backend)
async function fetchFormats() {
    if (!currentVideoId) return;

    const btn = document.getElementById('dl-btn');
    const div = document.getElementById('dl-links');
    
    btn.innerText = "⏳ Analyzing Formats...";
    btn.disabled = true;

    try {
        // Construct standard URL for yt-dlp
        const videoUrl = `https://www.youtube.com/watch?v=${currentVideoId}`;
        const res = await fetch(`${BACKEND_URL}/api/formats?url=${encodeURIComponent(videoUrl)}`);
        const data = await res.json();

        if (data.error) throw new Error(data.error);

        // Render Links
        div.innerHTML = data.formats.map(f => {
            const size = f.filesize ? (f.filesize / 1024 / 1024).toFixed(1) + ' MB' : 'Unknown Size';
            return `
                <a href="${f.url}" target="_blank" class="dl-item">
                    <i class="fas fa-download"></i> 
                    <strong>${f.resolution}</strong> (${f.ext}) 
                    <span style="float:right;">${size}</span>
                </a>
            `;
        }).join('');

        btn.innerText = "✅ Formats Loaded";
    } catch (e) {
        div.innerText = "Error: " + e.message;
        btn.innerText = "❌ Retry Formats";
        btn.disabled = false;
    }
}

// 4. Tab Switching Logic
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
}
