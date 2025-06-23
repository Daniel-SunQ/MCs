document.addEventListener('DOMContentLoaded', () => {
    // =======================================================================
    // ============================ GLOABL STATE & VARS ======================
    // =======================================================================
    let driverTemp = 22.5;
    let passengerTemp = 22.5;
    let map = null; // To hold the map instance
    let driving = null; // To hold the driving route instance
    let geolocation = null; // To hold the geolocation instance

    // =======================================================================
    // ============================ DOM Elements =============================
    // =======================================================================
    const mainContent = document.querySelector('.new-main-content');
    const appDrawer = document.getElementById('app-drawer');
    const modules = document.querySelectorAll('.module');

    // --- View Switching Buttons ---
    const appDockIcon = document.getElementById('app-dock-icon');
    const functionCards = document.querySelectorAll('.function-card');
    const closeModuleBtns = document.querySelectorAll('.close-module-btn');
    const acDockButton = document.getElementById('ac-dock-button');
    const settingsDockButton = document.getElementById('settings-dock-button');
    const mapDockButton = document.getElementById('map-dock-button');
    const mediaDockWidget = document.getElementById('media-dock-widget');
    
    // --- Time/Date Displays ---
    const smallTimeDisplay = document.getElementById('small-time-display');
    const largeTimeDisplay = document.getElementById('large-time-display');

    // --- Dock Temperature Controls ---
    const driverTempDisplayDock = document.getElementById('driver-temp-display-dock');
    const driverTempUpDock = document.getElementById('driver-temp-up-dock');
    const driverTempDownDock = document.getElementById('driver-temp-down-dock');
    const passengerTempDisplayDock = document.getElementById('passenger-temp-display-dock');
    const passengerTempUpDock = document.getElementById('passenger-temp-up-dock');
    const passengerTempDownDock = document.getElementById('passenger-temp-down-dock');

    // --- A/C Module Temperature Controls ---
    const acDriverTempDisplay = document.getElementById('ac-driver-temp-display');
    const acDriverTempUp = document.getElementById('ac-driver-temp-up');
    const acDriverTempDown = document.getElementById('ac-driver-temp-down');
    const acPassengerTempDisplay = document.getElementById('ac-passenger-temp-display');
    const acPassengerTempUp = document.getElementById('ac-passenger-temp-up');
    const acPassengerTempDown = document.getElementById('ac-passenger-temp-down');

    // --- Map Search Input and Button ---
    const mapSearchInput = document.getElementById('map-search-input');
    const mapSearchButton = document.getElementById('map-search-button');
    const mapPanel = document.getElementById('map-panel');
    
    // --- Weather display ---
    const weatherIcon = document.getElementById('weather-icon');
    const weatherDisplay = document.getElementById('weather-display');

    // =======================================================================
    // =========================== MUSIC PLAYER LOGIC ======================== */
    // ======================================================================= */
    
    const musicPlayerElements = {
        playPauseBtn: document.getElementById('play-pause-btn'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        shuffleBtn: document.getElementById('shuffle-btn'),
        repeatBtn: document.getElementById('repeat-btn'),
        progressBarContainer: document.querySelector('.progress-bar-container'),
        progressFill: document.querySelector('.progress-fill'),
        currentTimeDisplay: document.getElementById('current-time'),
        totalTimeDisplay: document.getElementById('total-time'),
        volumeBarContainer: document.querySelector('.volume-bar-container'),
        volumeFill: document.querySelector('.volume-fill'),
        currentSongTitle: document.getElementById('current-song-title'),
        currentSongArtist: document.getElementById('current-song-artist'),
        currentSongAlbum: document.getElementById('current-song-album'),
        currentAlbumArt: document.getElementById('current-album-art'),
        playlistContainer: document.querySelector('.playlist-container'),
        lyricsContainer: document.getElementById('lyrics-container'),
        // Dock Widget Elements
        dockSongInfo: document.getElementById('dock-song-info'),
        dockPlayPauseBtn: document.getElementById('dock-play-pause-btn'),
        dockPrevBtn: document.getElementById('dock-prev-btn'),
        dockNextBtn: document.getElementById('dock-next-btn')
    };
    
    let audioPlayer = new Audio();
    let currentPlaylist = [];
    let currentSongIndex = 0;
    let isPlaying = false;
    let isShuffle = false;
    let repeatMode = 'none'; // 'none', 'all', 'one'
    let parsedLyrics = [];

    function formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    function parseLyrics(lrcText) {
        if (!lrcText) return [];
        const lines = lrcText.split('\n');
        const result = [];
        const timeRegex = /\[(\d{2}):(\d{2})\.(\d{2,3})\]/;

        for (const line of lines) {
            const match = timeRegex.exec(line);
            if (match) {
                const minutes = parseInt(match[1], 10);
                const seconds = parseInt(match[2], 10);
                const milliseconds = parseInt(match[3].padEnd(3, '0'), 10);
                const time = minutes * 60 + seconds + milliseconds / 1000;
                const text = line.replace(timeRegex, '').trim();
                if (text) {
                    result.push({ time, text });
                }
            }
        }
        return result;
    }

    function updateUI() {
        if (!musicPlayerElements.currentSongTitle) return;

        // Update song info
        const song = currentPlaylist[currentSongIndex];
        musicPlayerElements.currentSongTitle.textContent = song.title;
        musicPlayerElements.currentSongArtist.textContent = song.artist;
        musicPlayerElements.currentSongAlbum.textContent = song.album;
        musicPlayerElements.currentAlbumArt.src = song.cover;
        musicPlayerElements.totalTimeDisplay.textContent = formatTime(song.duration);

        // Update playlist items
        musicPlayerElements.playlistContainer.innerHTML = '';
        currentPlaylist.forEach((s, index) => {
            const item = document.createElement('div');
            item.className = `playlist-item ${index === currentSongIndex ? 'active' : ''}`;
            item.innerHTML = `<div class="playlist-item-info"><span class="playlist-song-title">${s.title}</span><span class="playlist-song-artist">${s.artist}</span></div><span class="playlist-song-duration">${formatTime(s.duration)}</span>`;
            item.addEventListener('click', () => playSongByIndex(index));
            musicPlayerElements.playlistContainer.appendChild(item);
        });

        // Update play/pause button (main player)
        const playerIcon = musicPlayerElements.playPauseBtn.querySelector('i');
        if(playerIcon) playerIcon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';

        // Update play/pause button (dock widget)
        const dockIcon = musicPlayerElements.dockPlayPauseBtn;
        if(dockIcon) dockIcon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
        
        // Update dock song info
        if(musicPlayerElements.dockSongInfo) {
            musicPlayerElements.dockSongInfo.textContent = `${song.title} - ${song.artist}`;
        }

        // Update shuffle/repeat buttons
        musicPlayerElements.shuffleBtn.classList.toggle('active', isShuffle);
        musicPlayerElements.repeatBtn.classList.remove('active', 'one');
        if (repeatMode === 'one') {
            musicPlayerElements.repeatBtn.classList.add('active', 'one');
            musicPlayerElements.repeatBtn.querySelector('i').className = 'fas fa-redo-alt'; 
        } else if (repeatMode === 'all') {
            musicPlayerElements.repeatBtn.classList.add('active');
            musicPlayerElements.repeatBtn.querySelector('i').className = 'fas fa-redo';
        } else {
             musicPlayerElements.repeatBtn.classList.remove('active');
            musicPlayerElements.repeatBtn.querySelector('i').className = 'fas fa-redo';
        }
    }

    function updateProgress() {
        if (!audioPlayer.duration) return;
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        musicPlayerElements.progressFill.style.width = `${progress}%`;
        musicPlayerElements.currentTimeDisplay.textContent = formatTime(audioPlayer.currentTime);
        updateLyrics();
    }

    function updateLyrics() {
        if (parsedLyrics.length === 0) return;
    
        let currentIndex = -1;
        for (let i = 0; i < parsedLyrics.length; i++) {
            if (audioPlayer.currentTime >= parsedLyrics[i].time) {
                currentIndex = i;
            } else {
                break;
            }
        }
    
        if (currentIndex !== -1) {
            const allLines = musicPlayerElements.lyricsContainer.querySelectorAll('.lyrics-line');
            if (allLines.length === 0) return;
    
            // Check if the active line has changed
            const currentActive = musicPlayerElements.lyricsContainer.querySelector('.lyrics-line.active');
            if (currentActive && parseInt(currentActive.dataset.index, 10) === currentIndex) {
                return; // No change, do nothing
            }
    
            // Remove active class from previous line
            if (currentActive) {
                currentActive.classList.remove('active');
            }
    
            // Add active class to the new line and scroll
            const activeLine = allLines[currentIndex];
            if (activeLine) {
                activeLine.classList.add('active');
                activeLine.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
            }
        }
    }
    
    async function loadAndPlay(index) {
        currentSongIndex = index;
        const song = currentPlaylist[currentSongIndex];
        audioPlayer.src = song.file_path;
        
        // Reset and fetch lyrics
        musicPlayerElements.lyricsContainer.innerHTML = '<p class="lyrics-line">歌词加载中...</p>';
        parsedLyrics = [];
        if (song.has_lyrics) {
            try {
                const response = await fetch(`/api/music/lyrics/${song.id}`);
                const data = await response.json();
                if (data.lyrics) {
                    parsedLyrics = parseLyrics(data.lyrics);
                    renderLyrics();
                } else {
                     musicPlayerElements.lyricsContainer.innerHTML = '<p class="lyrics-line">此歌曲暂无歌词</p>';
                }
            } catch (error) {
                console.error('获取歌词失败:', error);
                musicPlayerElements.lyricsContainer.innerHTML = '<p class="lyrics-line">歌词加载失败</p>';
            }
        } else {
            musicPlayerElements.lyricsContainer.innerHTML = '<p class="lyrics-line">此歌曲暂无歌词</p>';
        }

        audioPlayer.play();
        isPlaying = true;
        updateUI();
    }
    
    function renderLyrics() {
        if (!musicPlayerElements.lyricsContainer) return;
        if (parsedLyrics.length > 0) {
            musicPlayerElements.lyricsContainer.innerHTML = parsedLyrics.map((line, index) => 
                `<p class="lyrics-line" data-index="${index}">${line.text}</p>`
            ).join('');
        } else {
            musicPlayerElements.lyricsContainer.innerHTML = '<p class="lyrics-line">此歌曲暂无歌词</p>';
        }
    }

    function playSongByIndex(index) {
        loadAndPlay(index);
    }

    function togglePlayPause() {
        if (isPlaying) {
            audioPlayer.pause();
            isPlaying = false;
        } else {
            audioPlayer.play();
            isPlaying = true;
        }
        updateUI();
    }

    function changeSong(direction) {
        let nextIndex;
        if (isShuffle) {
            nextIndex = Math.floor(Math.random() * currentPlaylist.length);
        } else {
            nextIndex = (currentSongIndex + direction + currentPlaylist.length) % currentPlaylist.length;
        }
        loadAndPlay(nextIndex);
    }
    
    async function initMusicPlayer() {
        try {
            const response = await fetch('/api/music/playlist');
            if (!response.ok) throw new Error('Network error');
            const data = await response.json();
            currentPlaylist = data.playlist;

            if (currentPlaylist && currentPlaylist.length > 0) {
                // Bind events for main player
                musicPlayerElements.playPauseBtn.addEventListener('click', togglePlayPause);
                musicPlayerElements.nextBtn.addEventListener('click', () => changeSong(1));
                musicPlayerElements.prevBtn.addEventListener('click', () => changeSong(-1));

                // Bind events for DOCK WIDGET
                musicPlayerElements.dockPlayPauseBtn.addEventListener('click', togglePlayPause);
                musicPlayerElements.dockNextBtn.addEventListener('click', () => changeSong(1));
                musicPlayerElements.dockPrevBtn.addEventListener('click', () => changeSong(-1));

                musicPlayerElements.shuffleBtn.addEventListener('click', () => {
                    isShuffle = !isShuffle;
                    updateUI();
                });

                musicPlayerElements.repeatBtn.addEventListener('click', () => {
                    const modes = ['none', 'all', 'one'];
                    repeatMode = modes[(modes.indexOf(repeatMode) + 1) % modes.length];
                    if (repeatMode === 'one') {
                        audioPlayer.loop = true;
                    } else {
                        audioPlayer.loop = false;
                    }
                    updateUI();
                });

                audioPlayer.addEventListener('timeupdate', updateProgress);
                audioPlayer.addEventListener('ended', () => {
                    if (repeatMode !== 'one') { // 'one' is handled by audio.loop
                        changeSong(1);
                    }
                });

                musicPlayerElements.progressBarContainer.addEventListener('click', e => {
                    const rect = musicPlayerElements.progressBarContainer.getBoundingClientRect();
                    const clickX = e.clientX - rect.left;
                    audioPlayer.currentTime = (clickX / rect.width) * audioPlayer.duration;
                });
                
                musicPlayerElements.volumeBarContainer.addEventListener('click', e => {
                     const rect = musicPlayerElements.volumeBarContainer.getBoundingClientRect();
                    const clickX = e.clientX - rect.left;
                    audioPlayer.volume = Math.max(0, Math.min(1, clickX / rect.width));
                    musicPlayerElements.volumeFill.style.width = `${audioPlayer.volume * 100}%`;
                });
                
                // Initial load
                const song = currentPlaylist[currentSongIndex];
                audioPlayer.src = song.file_path;
                musicPlayerElements.volumeFill.style.width = `${audioPlayer.volume * 100}%`;
                updateUI();
            }
        } catch (error) {
            console.error('Failed to initialize music player:', error);
        }
    }

    // =======================================================================
    // ====================== TEMPERATURE SYNC LOGIC =========================
    // =======================================================================
    function updateAllTempDisplays() {
        if(driverTempDisplayDock) driverTempDisplayDock.textContent = `${driverTemp.toFixed(1)}°`;
        if(passengerTempDisplayDock) passengerTempDisplayDock.textContent = `${passengerTemp.toFixed(1)}°`;
        if(acDriverTempDisplay) acDriverTempDisplay.textContent = driverTemp.toFixed(1);
        if(acPassengerTempDisplay) acPassengerTempDisplay.textContent = passengerTemp.toFixed(1);
    }
    
    function changeTemp(zone, direction) {
        const step = 0.5;
        const minTemp = 16;
        const maxTemp = 30;
        if (zone === 'driver') {
            driverTemp += direction * step;
            driverTemp = Math.max(minTemp, Math.min(maxTemp, driverTemp));
        } else {
            passengerTemp += direction * step;
            passengerTemp = Math.max(minTemp, Math.min(maxTemp, passengerTemp));
        }
        updateAllTempDisplays();
    }
    
    if(driverTempUpDock) driverTempUpDock.addEventListener('click', () => changeTemp('driver', 1));
    if(driverTempDownDock) driverTempDownDock.addEventListener('click', () => changeTemp('driver', -1));
    if(passengerTempUpDock) passengerTempUpDock.addEventListener('click', () => changeTemp('passenger', 1));
    if(passengerTempDownDock) passengerTempDownDock.addEventListener('click', () => changeTemp('passenger', -1));
    
    if(acDriverTempUp) acDriverTempUp.addEventListener('click', () => changeTemp('driver', 1));
    if(acDriverTempDown) acDriverTempDown.addEventListener('click', () => changeTemp('driver', -1));
    if(acPassengerTempUp) acPassengerTempUp.addEventListener('click', () => changeTemp('passenger', 1));
    if(acPassengerTempDown) acPassengerTempDown.addEventListener('click', () => changeTemp('passenger', -1));

    // =======================================================================
    // ======================== CLOCK & DATE LOGIC ===========================
    // =======================================================================
    function updateTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const currentTime = `${hours}:${minutes}`;
        if(smallTimeDisplay) smallTimeDisplay.textContent = currentTime;
        if(largeTimeDisplay) largeTimeDisplay.textContent = currentTime;
    }

    function formatDate() {
        const now = new Date();
        const optionsLine2 = { weekday: 'long' };
        const optionsLine3 = { year: 'numeric', month: 'long', day: 'numeric' };
        
        const dateLine2 = new Intl.DateTimeFormat('zh-CN', optionsLine2).format(now);
        const dateLine3 = new Intl.DateTimeFormat('zh-CN-u-ca-chinese', optionsLine3).format(now);
        
        const largeDateDisplayLine2 = document.getElementById('large-date-display-line2');
        const largeDateDisplayLine3 = document.getElementById('large-date-display-line3');

        if(largeDateDisplayLine2) largeDateDisplayLine2.textContent = dateLine2;
        if(largeDateDisplayLine3) largeDateDisplayLine3.textContent = dateLine3;
    }

    setInterval(updateTime, 1000);
    updateTime();
    formatDate();
    
    // =======================================================================
    // ============================ WEATHER LOGIC ============================
    // =======================================================================
    async function getWeather(city) {
        const weatherApiUrl = `/api/weather?city=${encodeURIComponent(city)}`;
        try {
            const response = await fetch(weatherApiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            updateWeatherUI(data);
        } catch (error) {
            console.error('获取天气数据失败:', error);
            updateWeatherUI({ error: true });
        }
    }

    function updateWeatherUI(data) {
        if (!weatherIcon || !weatherDisplay) return;
        if (data.error || !data.text) {
            weatherDisplay.textContent = '天气未知';
            weatherIcon.className = 'fas fa-question-circle';
        } else {
            weatherDisplay.textContent = `${data.text} ${data.temp}°C`;
            weatherIcon.className = `qi-${data.icon}`;
        }
    }
    
    // Initial weather fetch
    getWeather('重庆');

    // =======================================================================
    // ======================== UI Switching Logic (UNIFIED) =================
    // =======================================================================

    // Store the original display style for the main content
    const mainContentOriginalDisplay = window.getComputedStyle(mainContent).display;

    function showView(viewId) {
        // --- HIDE ALL ---
        mainContent.style.display = 'none';
        appDrawer.style.display = 'none';
        modules.forEach(m => {
            m.style.display = 'none';
        });

        // --- SHOW TARGET ---
        if (viewId === 'main') {
            mainContent.style.display = mainContentOriginalDisplay;
        } else if (viewId === 'drawer') {
            appDrawer.style.display = 'grid'; // app-drawer uses grid
        } else {
            const targetModule = document.getElementById(viewId);
            if (targetModule) {
                // Modules use 'flex' or 'block' based on their content, let's use a robust approach
                // Most of our modules are designed as flex containers
                targetModule.style.display = 'flex'; 

                // --- POST-SWITCH LOGIC for specific modules ---
                if (viewId === 'map-module') {
                    initMap(); // initMap needs to be called when map is visible
                } else if (viewId === 'media-module' && !window.musicPlayerInitialized) {
                    initMusicPlayer();
                    window.musicPlayerInitialized = true;
                }
            } else {
                // Fallback to main content if ID is not found
                mainContent.style.display = mainContentOriginalDisplay;
            }
        }
    }

    // --- Event Listeners for Switching ---

    // Open App Drawer from Dock
    if (appDockIcon) {
        appDockIcon.addEventListener('click', () => showView('drawer'));
    }

    // Open specific modules from App Drawer cards
    functionCards.forEach(card => {
        card.addEventListener('click', () => {
            const target = card.getAttribute('data-target');
            if (target) showView(target);
        });
    });

    // Close any open module / drawer to go back to the main view
    closeModuleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            showView('main');
        });
    });

    // --- Direct Dock Button Listeners ---
    if (acDockButton) acDockButton.addEventListener('click', () => showView('ac-module'));
    if (settingsDockButton) settingsDockButton.addEventListener('click', () => showView('settings-module'));
    if (mapDockButton) mapDockButton.addEventListener('click', () => showView('map-module'));

    // =======================================================================
    // ======================== MAP & NAVIGATION LOGIC =======================
    // =======================================================================
    async function initMap() {
        if (map) return;

        try {
            const response = await fetch('/api/config');
            if (!response.ok) throw new Error('Network response was not ok');
            const config = await response.json();

            if (!config.amap_key || !config.amap_security_secret) {
                console.error("高德Key或安全密钥未能在后端正确加载！");
                document.getElementById('amap-container').innerHTML = '<div style="color:red; text-align:center; padding-top: 50px;">地图加载失败：缺少API配置。</div>';
                return;
            }

            window._AMapSecurityConfig = {
                securityJsCode: config.amap_security_secret,
            };

            AMapLoader.load({
                "key": config.amap_key,
                "version": "2.0",
                "plugins": ['AMap.ToolBar', 'AMap.Scale', 'AMap.Geolocation', 'AMap.Driving', 'AMap.PlaceSearch'],
            }).then((AMap) => {
                map = new AMap.Map("amap-container", {
                    zoom: 11,
                    viewMode: '3D',
                    pitch: 50,
                    center: [116.397428, 39.90923],
                });
                
                map.addControl(new AMap.ToolBar({position: 'LB', offset: [20, 20]}));
                map.addControl(new AMap.Scale({position: 'LB', offset: [80, 20]}));
                
                // Initialize Geolocation plugin ONCE and store it
                geolocation = new AMap.Geolocation({
                    enableHighAccuracy: true,
                    timeout: 10000,
                    buttonPosition: 'RB',
                    buttonOffset: new AMap.Pixel(10, 20),
                    zoomToAccuracy: true,
                });
                map.addControl(geolocation);

                console.log("高德地图及定位插件初始化成功！");

                if(mapSearchButton) mapSearchButton.addEventListener('click', searchAndNavigate);
                if(mapSearchInput) mapSearchInput.addEventListener('keyup', (event) => {
                    if (event.key === 'Enter') {
                        searchAndNavigate();
                    }
                });

            }).catch(e => {
                console.error("地图资源加载失败:", e);
                 document.getElementById('amap-container').innerHTML = `<div style="color:red; text-align:center; padding-top: 50px;">地图资源加载失败: ${e.message}</div>`;
            });

        } catch (error) {
            console.error('获取地图配置或初始化失败:', error);
            document.getElementById('amap-container').innerHTML = `<div style="color:red; text-align:center; padding-top: 50px;">获取地图配置失败: ${error.message}</div>`;
        }
    }

    function searchAndNavigate() {
        const address = mapSearchInput.value;
        if (!address) {
            console.log("请输入目的地");
            return;
        }
        if (!map || !geolocation) {
            console.error("地图或定位功能尚未初始化！");
            alert("地图服务正在初始化，请稍后再试。");
            return;
        }

        if (driving) driving.clear();
        mapPanel.innerHTML = ""; 

        // 1. Use the single, pre-initialized geolocation instance
        geolocation.getCurrentPosition((status, result) => {
            if (status === 'complete') {
                const startPoint = result.position;
                
                const placeSearch = new AMap.PlaceSearch();
                placeSearch.search(address, (searchStatus, searchResult) => {
                    if (searchStatus === 'complete' && searchResult.poiList.pois.length > 0) {
                        const endPoint = searchResult.poiList.pois[0].location;
                        
                        driving = new AMap.Driving({
                            map: map,
                            panel: "map-panel",
                            policy: AMap.DrivingPolicy.LEAST_TIME, 
                            autoFitView: true
                        });
                        
                        driving.search(startPoint, endPoint, (drivingStatus, drivingResult) => {
                            if (drivingStatus === 'complete') {
                                console.log('成功获取驾车方案列表');
                            } else {
                                console.error('获取驾车方案失败：' + drivingResult);
                                mapPanel.innerHTML = `<div style="padding: 20px; color: #ff8a8a;">获取驾车方案失败，请稍后重试。</div>`;
                            }
                        });

                    } else {
                        console.error('搜索目的地失败：' + searchResult);
                        mapPanel.innerHTML = `<div style="padding: 20px; color: #ff8a8a;">未能找到目的地："${address}"。</div>`;
                    }
                });

            } else {
                console.error('获取当前位置失败: ' + result.message);
                alert('定位失败: ' + result.message + '\n\n请按照提示检查您的浏览器或操作系统的定位权限。');
            }
        });
    }
});