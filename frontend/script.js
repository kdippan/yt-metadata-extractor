// ✅ CONFIGURATION
const BACKEND_URL = 'https://yt-metadata-extractor.onrender.com'; 

let currentData = null;
let isDescExpanded = false;

// --- 1. INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    checkCookies();
    loadHistory();
    
    // Add enter key listener
    document.getElementById('videoUrl').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') fetchData();
    });
});

// --- 2. MAIN FETCH FUNCTION ---
async function fetchData() {
    const input = document.getElementById('videoUrl');
    const url = input.value.trim();
    
    if (!url) return showError('Please enter a YouTube URL');
    
    // Reset UI
    resetUI();
    document.getElementById('loader').classList.remove('hidden');

    // Extract ID
    const videoId = extractVideoID(url);
    if (!videoId) {
        document.getElementById('loader').classList.add('hidden');
        return showError('Invalid YouTube URL format');
    }

    try {
        // Fetch Basic Info
        const res = await fetch(`${BACKEND_URL}/api/basic-info?id=${videoId}`);
        const data = await res.json();
        
        if (data.error) throw new Error(data.error);
        if (!data.items || data.items.length === 0) throw new Error("Video not found or private");

        currentData = data.items[0];
        
        // Render UI
        renderBasicInfo(currentData);
        saveToHistory(currentData);
        
        // Show Results
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('results').classList.remove('hidden');
        
    } catch (e) {
        document.getElementById('loader').classList.add('hidden');
        showError(e.message);
    }
}

// --- 3. RENDERING FUNCTIONS ---
function renderBasicInfo(item) {
    const s = item.snippet;
    const st = item.statistics;

    // Header Info
    document.getElementById('thumb').src = s.thumbnails.maxres?.url || s.thumbnails.high?.url || s.thumbnails.medium.url;
    document.getElementById('title').innerText = s.title;
    document.getElementById('channel').innerText = s.channelTitle;
    document.getElementById('video-date').innerText = new Date(s.publishedAt).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
    
    // Stats
    document.getElementById('views').innerText = formatNumber(st.viewCount);
    document.getElementById('likes').innerText = formatNumber(st.likeCount);
    document.getElementById('comments').innerText = formatNumber(st.commentCount);

    // Description
    const descEl = document.getElementById('desc-text');
    descEl.innerText = s.description;
    // Reset Read More
    isDescExpanded = false;
    descEl.classList.add('h-32', 'overflow-hidden');
    descEl.classList.remove('h-auto');
    document.getElementById('desc-fade').classList.remove('hidden');
    document.getElementById('toggle-desc-btn').innerText = "Read More";
    document.getElementById('toggle-desc-btn').classList.toggle('hidden', !s.description || s.description.length < 200);

    // Tags
    const tagsContainer = document.getElementById('tags');
    tagsContainer.innerHTML = '';
    if (s.tags) {
        s.tags.forEach(tag => {
            const span = document.createElement('span');
            span.className = "bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded hover:bg-gray-200 transition cursor-default";
            span.innerText = tag;
            tagsContainer.appendChild(span);
        });
    } else {
        tagsContainer.innerHTML = '<span class="text-gray-400 text-sm italic">No tags found</span>';
    }

    // JSON
    document.getElementById('json-preview').innerText = JSON.stringify(item, null, 2);
    document.getElementById('json-full').innerText = JSON.stringify(item, null, 2);
}

// --- 4. BACKEND FEATURES (Transcript & Download) ---

async function fetchTranscript() {
    const btn = document.getElementById('trans-btn');
    const container = document.getElementById('trans-container');
    const textBox = document.getElementById('trans-text');
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    btn.disabled = true;

    try {
        const res = await fetch(`${BACKEND_URL}/api/transcript?id=${currentData.id}`);
        const data = await res.json();
        
        if (data.error) throw new Error(data.error);

        textBox.innerText = data.full_text;
        container.classList.remove('hidden');
        btn.innerHTML = '<i class="fas fa-check"></i> Loaded';
        btn.classList.replace('bg-brand-black', 'bg-green-600');
    } catch (e) {
        btn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Retry';
        btn.disabled = false;
        alert("Transcript Error: " + e.message); // Simple alert for specific action error
    }
}

async function fetchFormats() {
    const btn = document.getElementById('dl-btn');
    const list = document.getElementById('dl-links');
    const url = `https://www.youtube.com/watch?v=${currentData.id}`;
    
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing Server...';
    btn.disabled = true;
    list.innerHTML = '';

    try {
        const res = await fetch(`${BACKEND_URL}/api/formats?url=${encodeURIComponent(url)}`);
        const data = await res.json();
        
        if (data.error) {
            // Special handling for the IP Ban error to make it look "Pro"
            if (data.error.includes("YouTube IP Ban")) {
                list.innerHTML = `
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                        <div class="flex">
                            <div class="flex-shrink-0"><i class="fas fa-clock text-yellow-400"></i></div>
                            <div class="ml-3">
                                <p class="text-sm text-yellow-700">
                                    Server is currently cooling down from high traffic.
                                    <br><span class="font-bold">Please try again in a few hours.</span>
                                </p>
                            </div>
                        </div>
                    </div>
                `;
                throw new Error("Server Cooldown");
            }
            throw new Error(data.error);
        }

        data.formats.forEach(f => {
            const size = f.filesize ? (f.filesize / 1024 / 1024).toFixed(1) + ' MB' : 'N/A';
            const item = document.createElement('a');
            item.href = f.url;
            item.target = '_blank';
            item.className = "flex justify-between items-center p-3 bg-gray-50 border border-gray-200 rounded hover:bg-gray-100 transition group";
            item.innerHTML = `
                <div class="flex items-center gap-3">
                    <div class="bg-white p-2 rounded border border-gray-200 text-red-500"><i class="fas fa-video"></i></div>
                    <div>
                        <p class="text-sm font-bold text-gray-700 group-hover:text-brand-black">${f.resolution}</p>
                        <p class="text-xs text-gray-400">${f.ext.toUpperCase()}</p>
                    </div>
                </div>
                <span class="text-xs font-mono bg-gray-200 px-2 py-1 rounded text-gray-600">${size}</span>
            `;
            list.appendChild(item);
        });
        
        btn.innerHTML = 'Analysis Complete';
        btn.classList.add('hidden'); // Hide button after success

    } catch (e) {
        if(e.message !== "Server Cooldown") {
            btn.innerHTML = 'Analysis Failed';
            list.innerHTML = `<p class="text-red-500 text-sm text-center mt-2">${e.message}</p>`;
        }
    }
}


// --- 5. UTILITIES ---

function extractVideoID(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

function formatNumber(num) {
    return parseInt(num).toLocaleString('en-US', { notation: "compact", compactDisplay: "short" });
}

function toggleDescription() {
    const descEl = document.getElementById('desc-text');
    const btn = document.getElementById('toggle-desc-btn');
    const fade = document.getElementById('desc-fade');
    
    if (isDescExpanded) {
        descEl.classList.add('h-32', 'overflow-hidden');
        descEl.classList.remove('h-auto');
        fade.classList.remove('hidden');
        btn.innerText = "Read More";
    } else {
        descEl.classList.remove('h-32', 'overflow-hidden');
        descEl.classList.add('h-auto');
        fade.classList.add('hidden');
        btn.innerText = "Show Less";
    }
    isDescExpanded = !isDescExpanded;
}

function showError(msg) {
    const box = document.getElementById('error-box');
    document.getElementById('error-msg').innerText = msg;
    box.classList.remove('hidden');
}

function resetUI() {
    document.getElementById('error-box').classList.add('hidden');
    document.getElementById('results').classList.add('hidden');
    document.getElementById('trans-container').classList.add('hidden');
    document.getElementById('dl-links').innerHTML = '';
    
    // Reset buttons
    const transBtn = document.getElementById('trans-btn');
    transBtn.innerHTML = 'Load Transcript';
    transBtn.disabled = false;
    transBtn.classList.replace('bg-green-600', 'bg-brand-black');
    
    const dlBtn = document.getElementById('dl-btn');
    dlBtn.innerHTML = 'Analyze Formats';
    dlBtn.disabled = false;
    dlBtn.classList.remove('hidden');
}

function toggleJsonModal() {
    const modal = document.getElementById('json-modal');
    modal.classList.toggle('hidden');
}

function downloadJsonFile() {
    if(!currentData) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentData, null, 2));
    const a = document.createElement('a');
    a.href = dataStr;
    a.download = `yt-data-${currentData.id}.json`;
    a.click();
}

function copyTags() {
    if(currentData?.snippet?.tags) {
        navigator.clipboard.writeText(currentData.snippet.tags.join(', '));
        alert('Tags copied to clipboard!');
    }
}

function copyTranscript() {
    const text = document.getElementById('trans-text').innerText;
    if(text) {
        navigator.clipboard.writeText(text);
        alert('Transcript copied!');
    }
}

// --- 6. HISTORY & COOKIES ---

function checkCookies() {
    if (!localStorage.getItem('cookieConsent')) {
        setTimeout(() => {
            document.getElementById('cookie-banner').classList.remove('translate-y-full');
        }, 1000);
    }
}

function acceptCookies() {
    localStorage.setItem('cookieConsent', 'true');
    document.getElementById('cookie-banner').classList.add('translate-y-full');
}

function saveToHistory(item) {
    let history = JSON.parse(localStorage.getItem('ytHistory') || '[]');
    // Avoid duplicates
    history = history.filter(h => h.id !== item.id);
    // Add new to top
    history.unshift({
        id: item.id,
        title: item.snippet.title,
        thumb: item.snippet.thumbnails.default.url
    });
    // Limit to 5
    if (history.length > 5) history.pop();
    
    localStorage.setItem('ytHistory', JSON.stringify(history));
    loadHistory();
}

function loadHistory() {
    const history = JSON.parse(localStorage.getItem('ytHistory') || '[]');
    const container = document.getElementById('history-list');
    const section = document.getElementById('history-section');
    
    if (history.length === 0) {
        section.classList.add('hidden');
        return;
    }
    
    section.classList.remove('hidden');
    container.innerHTML = history.map(h => `
        <div onclick="document.getElementById('videoUrl').value='https://youtu.be/${h.id}'; fetchData()" 
             class="flex-shrink-0 w-48 bg-white p-2 rounded-lg border border-gray-200 cursor-pointer hover:shadow-md transition">
            <img src="${h.thumb}" class="w-full h-24 object-cover rounded mb-2">
            <p class="text-xs font-semibold truncate text-gray-700">${h.title}</p>
        </div>
    `).join('');
}

function clearHistory() {
    localStorage.removeItem('ytHistory');
    loadHistory();
}
