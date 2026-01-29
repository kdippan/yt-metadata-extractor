const BACKEND_URL = 'https://yt-metadata-extractor.onrender.com';

async function fetchData() {
    const url = document.getElementById('videoUrl').value;
    const videoId = extractID(url);
    if (!videoId) return alert("Invalid URL");

    document.getElementById('loader').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');

    try {
        const res = await fetch(`${BACKEND_URL}/api/basic-info?id=${videoId}`);
        const data = await res.json();

        if (data.error) throw new Error(data.error);

        renderDashboard(data);
        
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');

    } catch (e) {
        alert("Error: " + e.message);
        document.getElementById('loader').classList.add('hidden');
    }
}

function renderDashboard(data) {
    const b = data.basic;
    const m = data.metrics;
    const t = data.technical;
    const s = data.status;

    // Hero
    document.getElementById('thumb').src = b.thumbnails.maxres?.url || b.thumbnails.high.url;
    document.getElementById('video-title').innerText = b.title;
    document.getElementById('video-id-badge').innerText = data.id;
    document.getElementById('publish-date').innerText = new Date(b.publishedAt).toLocaleDateString('en-US', { dateStyle: 'long' });

    // Stats
    document.getElementById('stat-views').innerText = parseInt(m.viewCount).toLocaleString();
    document.getElementById('stat-likes').innerText = parseInt(m.likeCount).toLocaleString();
    document.getElementById('stat-comments').innerText = parseInt(m.commentCount).toLocaleString();

    // Specs Card
    document.getElementById('meta-channel').innerText = b.channelTitle;
    document.getElementById('meta-channel-id').innerText = b.channelId;
    
    document.getElementById('meta-def').innerText = t.definition;
    document.getElementById('meta-dim').innerText = t.dimension;
    document.getElementById('meta-dur').innerText = parseDuration(t.duration);

    // License Card
    document.getElementById('meta-license').innerText = s.license === 'creativeCommon' ? 'Creative Commons' : 'Standard License';
    document.getElementById('meta-privacy').innerText = s.privacyStatus;

    // Location/Kids Card
    if (data.location) {
        document.getElementById('meta-location').innerHTML = `<a href="https://maps.google.com/?q=${data.location.latitude},${data.location.longitude}" target="_blank" class="text-blue-600 hover:underline">View Map</a>`;
    } else {
        document.getElementById('meta-location').innerText = "None";
    }
    document.getElementById('meta-kids').innerText = s.madeForKids ? "Made for Kids" : "General Audience";

    // Description & Tags
    document.getElementById('video-desc').innerText = b.description;
    
    const tagBox = document.getElementById('video-tags');
    tagBox.innerHTML = '';
    if (b.tags) {
        b.tags.forEach(tag => {
            tagBox.innerHTML += `<span class="bg-gray-100 px-2 py-1 rounded text-xs text-gray-600">#${tag}</span>`;
        });
    } else {
        tagBox.innerHTML = '<span class="text-gray-400 italic">No tags</span>';
    }
}

// Transcript
async function getTranscript() {
    const id = document.getElementById('video-id-badge').innerText;
    const box = document.getElementById('transcript-box');
    box.classList.remove('hidden');
    box.innerText = "Loading...";
    
    try {
        const res = await fetch(`${BACKEND_URL}/api/transcript?id=${id}`);
        const d = await res.json();
        if (d.error) throw new Error(d.error);
        box.innerText = d.full_text;
    } catch(e) {
        box.innerText = "Not Available: " + e.message;
    }
}

// Downloads
async function getFormats() {
    const url = `https://youtu.be/${document.getElementById('video-id-badge').innerText}`;
    const btn = document.getElementById('dl-btn');
    const list = document.getElementById('dl-list');
    
    btn.innerText = "Scanning...";
    btn.disabled = true;
    
    try {
        const res = await fetch(`${BACKEND_URL}/api/formats?url=${encodeURIComponent(url)}`);
        const d = await res.json();
        
        if (d.error === 'Server Cooldown') {
            list.innerHTML = `<div class="bg-yellow-50 text-yellow-700 p-2 rounded">⚠️ High traffic. Downloads paused for 3h.</div>`;
        } else if (d.formats) {
            list.innerHTML = d.formats.map(f => `
                <a href="${f.url}" target="_blank" class="block bg-gray-50 p-2 rounded mb-1 hover:bg-gray-100 flex justify-between">
                    <span class="font-bold">${f.res}</span>
                    <span class="text-gray-500">${(f.size/1024/1024).toFixed(1)}MB</span>
                </a>
            `).join('');
        }
    } catch(e) {
        list.innerText = "Error loading formats.";
    }
    btn.innerText = "Analyze Links";
    btn.disabled = false;
}

// Helpers
function extractID(url) {
    const m = url.match(/^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/);
    return (m && m[2].length === 11) ? m[2] : null;
}

function parseDuration(d) {
    if (!d) return "--:--";
    const m = d.match(/PT(\d+H)?(\d+M)?(\d+S)?/);
    const h = (m[1]||'').replace('H','');
    const min = (m[2]||'').replace('M','');
    const s = (m[3]||'').replace('S','');
    if (h) return `${h}:${min.padStart(2,'0')}:${s.padStart(2,'0')}`;
    return `${min}:${s.padStart(2,'0')}`;
}

function toggleDesc() {
    const box = document.getElementById('desc-box');
    box.classList.toggle('h-32');
    box.classList.toggle('h-auto');
}
