document.addEventListener('DOMContentLoaded', () => {
    // =======================================================================
    // ============================ GLOABL STATE & VARS ======================
    // =======================================================================
    let driverTemp = 22.5;
    let passengerTemp = 22.5;
    let map = null; // To hold the map instance
    let driving = null; // To hold the driving route instance
    let geolocation = null; // To hold the geolocation instance

    // Initialize socket.io with configuration
    const socket = io('http://localhost:8080', {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        debug: true
    });

    // 添加连接事件处理
    socket.on('connect', () => {
        console.log('已连接到服务器');
        // 发送测试消息
        socket.emit('test_message', { data: 'Hello from client!' });
    });

    socket.on('connect_error', (error) => {
        console.error('连接错误:', error);
        console.log('连接状态:', socket.connected);
        console.log('传输方式:', socket.io.engine.transport.name);
    });

    socket.on('disconnect', (reason) => {
        console.log('断开连接:', reason);
        console.log('尝试重新连接...');
    });

    // 添加用户交互状态跟踪
    let hasUserInteraction = false;
    document.addEventListener('click', () => {
        hasUserInteraction = true;
    }, { once: true });

    // Listen for media status updates
    socket.on('media_status_update', function(data) {
        if (data.status) {
            const { current_song, is_playing } = data.status;
            if (is_playing && current_song !== currentSongIndex) {
                loadAndPlay(current_song);
            } else if (is_playing && !isPlaying) {
                if (hasUserInteraction) {
                    audioPlayer.play().catch(console.error);
                }
                isPlaying = true;
                updateUI();
            } else if (!is_playing && isPlaying) {
                audioPlayer.pause();
                isPlaying = false;
                updateUI();
            }
        }
        if (data.message) {
            showToast(data.message);
        }
    });

    // Listen for navigation control events
    socket.on('navigation_control', function(data) {
        if (data.action === 'open_and_search') {
            // 打开导航界面
            showView('map-module');
            // 等待地图初始化完成
            const checkMapInterval = setInterval(() => {
                if (map && mapSearchInput) {
                    clearInterval(checkMapInterval);
                    // 设置搜索目的地并触发搜索
                    mapSearchInput.value = data.destination;
                    searchAndNavigate();
                }
            }, 100);
        } else if (data.action === 'stop') {
            if (driving) {
                driving.clear();
            }
            mapPanel.innerHTML = "";
        }
    });

    // Initialize music player immediately
    initMusicPlayer();

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
    
    async function loadAndPlay(songId) {
        try {
            currentSongIndex = songId;
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
            
            if (hasUserInteraction) {
                // 如果已有用户交互，直接播放
                await audioPlayer.play();
                isPlaying = true;
                updateUI();
            } else {
                // 如果没有用户交互，显示一个临时播放按钮
                const playButton = document.createElement('button');
                playButton.textContent = '点击开始播放';
                playButton.style.position = 'fixed';
                playButton.style.top = '50%';
                playButton.style.left = '50%';
                playButton.style.transform = 'translate(-50%, -50%)';
                playButton.style.padding = '15px 30px';
                playButton.style.backgroundColor = '#4CAF50';
                playButton.style.color = 'white';
                playButton.style.border = 'none';
                playButton.style.borderRadius = '5px';
                playButton.style.cursor = 'pointer';
                playButton.style.zIndex = '9999';
                
                playButton.onclick = async () => {
                    hasUserInteraction = true;
                    await audioPlayer.play();
                    isPlaying = true;
                    updateUI();
                    playButton.remove();
                };
                
                document.body.appendChild(playButton);
            }
        } catch (error) {
            console.error('播放失败:', error);
            isPlaying = false;
            updateUI();
        }
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
            driverTemp += direction === 'up' ? step : -step;
            driverTemp = Math.max(minTemp, Math.min(maxTemp, driverTemp));
        } else {
            passengerTemp += direction === 'up' ? step : -step;
            passengerTemp = Math.max(minTemp, Math.min(maxTemp, passengerTemp));
        }
        updateAllTempDisplays();
    }
    
    if(driverTempUpDock) driverTempUpDock.addEventListener('click', () => changeTemp('driver', 'up'));
    if(driverTempDownDock) driverTempDownDock.addEventListener('click', () => changeTemp('driver', 'down'));
    if(passengerTempUpDock) passengerTempUpDock.addEventListener('click', () => changeTemp('passenger', 'up'));
    if(passengerTempDownDock) passengerTempDownDock.addEventListener('click', () => changeTemp('passenger', 'down'));
    
    if(acDriverTempUp) acDriverTempUp.addEventListener('click', () => changeTemp('driver', 'up'));
    if(acDriverTempDown) acDriverTempDown.addEventListener('click', () => changeTemp('driver', 'down'));
    if(acPassengerTempUp) acPassengerTempUp.addEventListener('click', () => changeTemp('passenger', 'up'));
    if(acPassengerTempDown) acPassengerTempDown.addEventListener('click', () => changeTemp('passenger', 'down'));

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
            mapPanel.innerHTML = '<div style="padding: 20px; color: #ff8a8a;">请输入目的地</div>';
            return;
        }

        // 初始化定位对象
        const geolocation = new AMap.Geolocation({
            enableHighAccuracy: true,
            timeout: 10000,
            buttonPosition: 'RB',
            buttonOffset: new AMap.Pixel(10, 20),
            zoomToAccuracy: true
        });

        // 获取当前位置
        geolocation.getCurrentPosition((status, result) => {
            if (status === 'complete' && result && result.position) {
                const startPoint = [result.position.lng, result.position.lat];
                
                // 安全地获取城市信息
                const city = result.addressComponent && result.addressComponent.city ? result.addressComponent.city : '全国';
                
                const placeSearch = new AMap.PlaceSearch({
                    city: city
                });
                
                placeSearch.search(address, (searchStatus, searchResult) => {
                    if (searchStatus === 'complete' && searchResult && searchResult.poiList && searchResult.poiList.pois.length > 0) {
                        const endPoint = searchResult.poiList.pois[0].location;
                        
                        driving = new AMap.Driving({
                            map: map,
                            panel: "map-panel",
                            policy: AMap.DrivingPolicy.LEAST_TIME,
                            autoFitView: true
                        });
                        
                        driving.search(startPoint, endPoint, (drivingStatus, drivingResult) => {
                            if (drivingStatus === 'complete' && drivingResult && drivingResult.routes && drivingResult.routes.length > 0) {
                                console.log('成功获取驾车方案列表');
                                // 获取第一条路线的信息
                                const route = drivingResult.routes[0];
                                const navigationInfo = {
                                    destination: address,
                                    distance: (route.distance / 1000).toFixed(1), // 转换为公里
                                    duration: Math.ceil(route.time / 60), // 转换为分钟
                                    steps: route.steps.slice(0, 3).map(step => step.instruction), // 获取前三个导航指令
                                    totalSteps: route.steps.length
                                };
                                // 发送导航信息到后端
                                socket.emit('navigation_info', navigationInfo);
                            } else {
                                console.error('获取驾车方案失败：', drivingResult);
                                mapPanel.innerHTML = `<div style="padding: 20px; color: #ff8a8a;">获取驾车方案失败，请稍后重试。</div>`;
                                socket.emit('navigation_info', {
                                    error: true,
                                    message: '获取驾车方案失败，请稍后重试'
                                });
                            }
                        });
                    } else {
                        console.error('搜索目的地失败：', searchResult);
                        mapPanel.innerHTML = `<div style="padding: 20px; color: #ff8a8a;">未能找到目的地："${address}"。</div>`;
                        socket.emit('navigation_info', {
                            error: true,
                            message: `未能找到目的地："${address}"`
                        });
                    }
                });
            } else {
                const errorMsg = result && result.message ? result.message : '定位失败，请检查定位权限';
                console.error('获取当前位置失败:', errorMsg);
                mapPanel.innerHTML = `<div style="padding: 20px; color: #ff8a8a;">${errorMsg}</div>`;
                socket.emit('navigation_info', {
                    error: true,
                    message: errorMsg
                });
            }
        });
    }

    // ================== 语音弹窗+WebSocket监听 ==================
    (function() {
        // 弹窗DOM
        let voiceModal = null;
        function showVoiceModal(status, extra) {
            if (!voiceModal) {
                voiceModal = document.createElement('div');
                voiceModal.id = 'voice-modal';
                voiceModal.style.position = 'fixed';
                voiceModal.style.left = '50%';
                voiceModal.style.top = '20%';
                voiceModal.style.transform = 'translate(-50%, 0)';
                voiceModal.style.background = 'rgba(30,34,40,0.95)';
                voiceModal.style.color = '#fff';
                voiceModal.style.padding = '32px 48px';
                voiceModal.style.borderRadius = '18px';
                voiceModal.style.boxShadow = '0 8px 32px rgba(0,0,0,0.25)';
                voiceModal.style.zIndex = 9999;
                voiceModal.style.fontSize = '1.3rem';
                voiceModal.style.textAlign = 'center';
                voiceModal.style.transition = 'opacity 0.3s';
                document.body.appendChild(voiceModal);
            }
            let html = '';
            if (status === 'wake') {
                html = `<div style=\"font-size:2.5rem;\">🟢</div><div style=\"margin:12px 0 8px;\">唤醒成功</div><div>请说出您的指令...</div>`;
            } else if (status === 'recording') {
                html = `<div style=\"font-size:2.5rem;\">🎤</div><div style=\"margin:12px 0 8px;\">正在监听指令...</div><div>请在7秒内说完</div>`;
            } else if (status === 'processing') {
                html = `<div style=\"font-size:2.5rem;\">⏳</div><div style=\"margin:12px 0 8px;\">正在识别/处理...</div>`;
            } else if (status === 'streaming') {
                html = `<div style=\"font-size:2.5rem;\">⏳</div><div style=\"margin:12px 0 8px;\">正在播报...</div><div style=\"margin-bottom:10px;min-width:320px;max-width:480px;word-break:break-all;text-align:left;\">${extra||''}</div>`;
            } else if (status === 'result') {
                html = `<div style=\"font-size:2.5rem;\">✅</div><div style=\"margin:12px 0 8px;\">AI回复</div><div style=\"margin-bottom:10px;\">${extra||''}</div><button id=\"close-voice-modal\" style=\"margin-top:10px;padding:6px 18px;border:none;border-radius:8px;background:#4ecdc4;color:#fff;font-size:1rem;cursor:pointer;\">关闭</button>`;
            }
            voiceModal.innerHTML = html;
            voiceModal.style.opacity = 1;
            if (status === 'result') {
                document.getElementById('close-voice-modal').onclick = hideVoiceModal;
            }
        }
        function hideVoiceModal() {
            if (voiceModal) {
                voiceModal.style.opacity = 0;
                setTimeout(()=>{if(voiceModal)voiceModal.remove();voiceModal=null;}, 350);
            }
        }
        // WebSocket监听
        let streamingText = '';
        
        socket.on('voice_status', function(data) {
            if (data.status === 'wake') {
                showVoiceModal('wake');
            } else if (data.status === 'recording') {
                showVoiceModal('recording');
            } else if (data.status === 'processing') {
                showVoiceModal('processing');
            } else if (data.status === 'streaming') {
                streamTextToModal(data.text || '', data.duration);
            }
            else if (data.status === 'result') {
                // 流式输出文字（逐字显示）
                showVoiceModal('result', data.text);
            }
        });
        function countValidChars(str) {
            // 只保留汉字、英文字母、数字
            return (str.replace(/[，。！？、,.!?:;；""''\\s]/g, '')).length;
        }
        // 流式输出函数
        function streamTextToModal(fullText, duration) {
            let idx = 0;
            let current = '';
            // 计算有效字数
            const validCharCount = countValidChars(fullText);
            // 打印音频时长和有效字数
            console.log('音频时长（秒）:', duration);
            console.log('有效字数:', validCharCount);
            let intervalTime = 50;
            if (duration && validCharCount > 0) {
                intervalTime = Math.max(30, Math.floor(duration * 1000 / validCharCount));
            }
            showVoiceModal('streaming', '');
            const interval = setInterval(() => {
                if (idx < fullText.length) {
                    current += fullText[idx];
                    showVoiceModal('streaming', current);
                    idx++;
                } else {
                    clearInterval(interval);
                    // 输出完毕，显示关闭按钮
                    showVoiceModal('result', fullText);
                }
            }, intervalTime); // 50ms一个字，可根据实际体验调整
        }
    })();

    // ======================== 防碰撞检测按钮逻辑 =========================
    const collisionDetectBtn = document.getElementById('collision-detect-btn');
    if (collisionDetectBtn) {
        collisionDetectBtn.addEventListener('click', async () => {
            try {
                const resp = await fetch('/api/start_collision_detection', {method: 'POST'});
                if (resp.ok) {
                    alert('已请求本地弹窗显示防碰撞检测画面，请在服务器本地查看。');
                } else {
                    alert('请求失败，请检查后端服务。');
                }
            } catch (e) {
                alert('网络错误，无法请求防碰撞检测。');
            }
        });
    }


    // ======================== 页面加载时自动显示drawer逻辑 =========================
    function getQueryParam(name) {
        const url = window.location.search;
        const params = new URLSearchParams(url);
        return params.get(name);
    }

    if (getQueryParam('drawer') === '1') {
        showView('drawer');
    } else {
        showView('main');
    }


    // ============================ DOM Elements =============================
    const userAvatar = document.querySelector('.user-avatar');
    if (userAvatar) {
        userAvatar.style.cursor = 'pointer';
        userAvatar.addEventListener('click', function() {
            window.location.href = '/user_center';
        });
    }

    const dockMediaIcon = document.getElementById('dock-media-icon');
    if (dockMediaIcon) {
        dockMediaIcon.style.cursor = 'pointer';
        dockMediaIcon.addEventListener('click', function() {
            showView('media-module');
        });
    }

    // =======================================================================
    // ======================== SETTINGS MODULE LOGIC =========================
    // =======================================================================
    
    // 设置导航切换
    const settingsNavItems = document.querySelectorAll('.settings-nav-item');
    const settingsPanels = document.querySelectorAll('.settings-panel');
    
    settingsNavItems.forEach(item => {
        item.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            
            // 移除所有活动状态
            settingsNavItems.forEach(nav => nav.classList.remove('active'));
            settingsPanels.forEach(panel => panel.classList.remove('active'));
            
            // 添加活动状态
            this.classList.add('active');
            document.getElementById(target).classList.add('active');
        });
    });
    
    // 个人资料表单提交
    const profileFormSettings = document.getElementById('profile-form-settings');
    if (profileFormSettings) {
        profileFormSettings.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                username: document.getElementById('profile-username-settings').value,
                email: document.getElementById('profile-email-settings').value,
                phone: document.getElementById('profile-phone-settings').value,
                bio: document.getElementById('profile-bio-settings').value
            };
            
            try {
                const response = await fetch('/api/user/profile', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('个人资料已保存！');
                } else {
                    alert('保存失败: ' + data.error);
                }
            } catch (error) {
                alert('网络错误，请稍后重试');
            }
        });
    }
    
    // 通知设置保存
    const notificationSettings = ['system-notifications', 'security-alerts', 'driving-suggestions', 'marketing-info'];
    notificationSettings.forEach(settingId => {
        const checkbox = document.getElementById(settingId);
        if (checkbox) {
            checkbox.addEventListener('change', async function() {
                const keyMapping = {
                    'system-notifications': 'system_notifications',
                    'security-alerts': 'security_alerts',
                    'driving-suggestions': 'driving_suggestions',
                    'marketing-info': 'marketing_info'
                };
                
                const key = keyMapping[settingId];
                if (key) {
                    try {
                        await fetch('/api/user/settings', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                [key]: this.checked.toString()
                            })
                        });
                    } catch (error) {
                        console.error('保存设置失败:', error);
                    }
                }
            });
        }
    });
    
    // 隐私设置保存
    const privacySettings = ['location-permission', 'voice-recognition'];
    privacySettings.forEach(settingId => {
        const checkbox = document.getElementById(settingId);
        if (checkbox) {
            checkbox.addEventListener('change', async function() {
                const keyMapping = {
                    'location-permission': 'location_permission',
                    'voice-recognition': 'voice_recognition'
                };
                
                const key = keyMapping[settingId];
                if (key) {
                    try {
                        await fetch('/api/user/settings', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                [key]: this.checked.toString()
                            })
                        });
                    } catch (error) {
                        console.error('保存设置失败:', error);
                    }
                }
            });
        }
    });
    
    // 系统设置保存
    const systemSettings = ['theme-select', 'language-select', 'auto-lock-select'];
    systemSettings.forEach(settingId => {
        const select = document.getElementById(settingId);
        if (select) {
            select.addEventListener('change', async function() {
                const keyMapping = {
                    'theme-select': 'theme',
                    'language-select': 'language',
                    'auto-lock-select': 'auto_lock'
                };
                
                const key = keyMapping[settingId];
                if (key) {
                    try {
                        await fetch('/api/user/settings', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                [key]: this.value
                            })
                        });
                    } catch (error) {
                        console.error('保存设置失败:', error);
                    }
                }
            });
        }
    });
    
    // 音量滑块
    const volumeSlider = document.getElementById('volume-slider');
    const volumeValue = document.getElementById('volume-value');
    if (volumeSlider && volumeValue) {
        volumeSlider.addEventListener('input', function() {
            volumeValue.textContent = this.value + '%';
        });
        
        volumeSlider.addEventListener('change', async function() {
            try {
                await fetch('/api/user/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        volume: (this.value / 100).toString()
                    })
                });
            } catch (error) {
                console.error('保存音量设置失败:', error);
            }
        });
    }
    
    // 加载用户设置到设置界面
    async function loadSettingsToUI() {
        try {
            const response = await fetch('/api/user/settings');
            if (response.ok) {
                const settings = await response.json();
                
                // 设置通知开关
                if (settings.system_notifications) {
                    const checkbox = document.getElementById('system-notifications');
                    if (checkbox) checkbox.checked = settings.system_notifications === 'true';
                }
                if (settings.security_alerts) {
                    const checkbox = document.getElementById('security-alerts');
                    if (checkbox) checkbox.checked = settings.security_alerts === 'true';
                }
                if (settings.driving_suggestions) {
                    const checkbox = document.getElementById('driving-suggestions');
                    if (checkbox) checkbox.checked = settings.driving_suggestions === 'true';
                }
                if (settings.marketing_info) {
                    const checkbox = document.getElementById('marketing-info');
                    if (checkbox) checkbox.checked = settings.marketing_info === 'true';
                }
                
                // 设置隐私开关
                if (settings.location_permission) {
                    const checkbox = document.getElementById('location-permission');
                    if (checkbox) checkbox.checked = settings.location_permission === 'true';
                }
                if (settings.voice_recognition) {
                    const checkbox = document.getElementById('voice-recognition');
                    if (checkbox) checkbox.checked = settings.voice_recognition === 'true';
                }
                
                // 设置系统选项
                if (settings.theme) {
                    const select = document.getElementById('theme-select');
                    if (select) select.value = settings.theme;
                }
                if (settings.language) {
                    const select = document.getElementById('language-select');
                    if (select) select.value = settings.language;
                }
                if (settings.auto_lock) {
                    const select = document.getElementById('auto-lock-select');
                    if (select) select.value = settings.auto_lock;
                }
                
                // 设置音量
                if (settings.volume) {
                    const slider = document.getElementById('volume-slider');
                    const value = document.getElementById('volume-value');
                    if (slider && value) {
                        const volumePercent = Math.round(parseFloat(settings.volume) * 100);
                        slider.value = volumePercent;
                        value.textContent = volumePercent + '%';
                    }
                }
            }
        } catch (error) {
            console.error('加载设置失败:', error);
        }
    }
    
    // 当设置模块显示时加载设置
    if (settingsDockButton) {
        settingsDockButton.addEventListener('click', () => {
            showView('settings-module');
            loadSettingsToUI();
            loadVehicleSettingsToUI();
        });
    }
    
    // =======================================================================
    // ======================== VEHICLE SETTINGS LOGIC ========================
    // =======================================================================
    
    // 车辆设置滑块控制
    const vehicleSliders = [
        'driver-seat-height', 'driver-seat-recline', 'driver-seat-lumbar',
        'steering-wheel-height', 'steering-wheel-telescope'
    ];
    
    vehicleSliders.forEach(sliderId => {
        const slider = document.getElementById(sliderId);
        const valueDisplay = document.getElementById(sliderId + '-value');
        
        if (slider && valueDisplay) {
            slider.addEventListener('input', function() {
                valueDisplay.textContent = this.value + '%';
            });
            
            slider.addEventListener('change', async function() {
                const key = sliderId.replace(/-/g, '_');
                try {
                    await fetch('/api/vehicle/settings', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            [key]: (this.value / 100).toString()
                        })
                    });
                } catch (error) {
                    console.error('保存车辆设置失败:', error);
                }
            });
        }
    });
    
    // 车辆设置选择器
    const vehicleSelects = [
        'driver-seat-position', 'steering-wheel-position',
        'ac-fan-speed', 'ac-mode', 'drive-mode', 'suspension-mode',
        'steering-mode', 'brake-mode'
    ];
    
    vehicleSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.addEventListener('change', async function() {
                const key = selectId.replace(/-/g, '_');
                try {
                    await fetch('/api/vehicle/settings', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            [key]: this.value
                        })
                    });
                } catch (error) {
                    console.error('保存车辆设置失败:', error);
                }
            });
        }
    });
    
    // 温度控制
    window.adjustTemp = async function(side, delta) {
        const display = document.getElementById(side + '-temp-display');
        const currentTemp = parseFloat(display.textContent);
        const newTemp = Math.max(16, Math.min(30, currentTemp + delta));
        display.textContent = newTemp.toFixed(1) + '°C';
        
        const key = side === 'driver' ? 'ac_driver_temp' : 'ac_passenger_temp';
        try {
            await fetch('/api/vehicle/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    [key]: newTemp.toFixed(1)
                })
            });
        } catch (error) {
            console.error('保存温度设置失败:', error);
        }
    };
    
    // 加载车辆设置到界面
    async function loadVehicleSettingsToUI() {
        try {
            const response = await fetch('/api/vehicle/settings');
            if (response.ok) {
                const settings = await response.json();
                
                // 设置座椅滑块
                if (settings.driver_seat_height) {
                    const slider = document.getElementById('driver-seat-height');
                    const value = document.getElementById('driver-seat-height-value');
                    if (slider && value) {
                        const percent = Math.round(parseFloat(settings.driver_seat_height) * 100);
                        slider.value = percent;
                        value.textContent = percent + '%';
                    }
                }
                
                if (settings.driver_seat_recline) {
                    const slider = document.getElementById('driver-seat-recline');
                    const value = document.getElementById('driver-seat-recline-value');
                    if (slider && value) {
                        const percent = Math.round(parseFloat(settings.driver_seat_recline) * 100);
                        slider.value = percent;
                        value.textContent = percent + '%';
                    }
                }
                
                if (settings.driver_seat_lumbar) {
                    const slider = document.getElementById('driver-seat-lumbar');
                    const value = document.getElementById('driver-seat-lumbar-value');
                    if (slider && value) {
                        const percent = Math.round(parseFloat(settings.driver_seat_lumbar) * 100);
                        slider.value = percent;
                        value.textContent = percent + '%';
                    }
                }
                
                // 设置方向盘滑块
                if (settings.steering_wheel_height) {
                    const slider = document.getElementById('steering-wheel-height');
                    const value = document.getElementById('steering-wheel-height-value');
                    if (slider && value) {
                        const percent = Math.round(parseFloat(settings.steering_wheel_height) * 100);
                        slider.value = percent;
                        value.textContent = percent + '%';
                    }
                }
                
                if (settings.steering_wheel_telescope) {
                    const slider = document.getElementById('steering-wheel-telescope');
                    const value = document.getElementById('steering-wheel-telescope-value');
                    if (slider && value) {
                        const percent = Math.round(parseFloat(settings.steering_wheel_telescope) * 100);
                        slider.value = percent;
                        value.textContent = percent + '%';
                    }
                }
                
                // 设置选择器
                if (settings.driver_seat_position) {
                    const select = document.getElementById('driver-seat-position');
                    if (select) select.value = settings.driver_seat_position;
                }
                
                if (settings.steering_wheel_position) {
                    const select = document.getElementById('steering-wheel-position');
                    if (select) select.value = settings.steering_wheel_position;
                }
                
                if (settings.ac_fan_speed) {
                    const select = document.getElementById('ac-fan-speed');
                    if (select) select.value = settings.ac_fan_speed;
                }
                
                if (settings.ac_mode) {
                    const select = document.getElementById('ac-mode');
                    if (select) select.value = settings.ac_mode;
                }
                
                if (settings.drive_mode) {
                    const select = document.getElementById('drive-mode');
                    if (select) select.value = settings.drive_mode;
                }
                
                if (settings.suspension_mode) {
                    const select = document.getElementById('suspension-mode');
                    if (select) select.value = settings.suspension_mode;
                }
                
                if (settings.steering_mode) {
                    const select = document.getElementById('steering-mode');
                    if (select) select.value = settings.steering_mode;
                }
                
                if (settings.brake_mode) {
                    const select = document.getElementById('brake-mode');
                    if (select) select.value = settings.brake_mode;
                }
                
                // 设置温度显示
                if (settings.ac_driver_temp) {
                    const display = document.getElementById('driver-temp-display');
                    if (display) display.textContent = settings.ac_driver_temp + '°C';
                }
                
                if (settings.ac_passenger_temp) {
                    const display = document.getElementById('passenger-temp-display');
                    if (display) display.textContent = settings.ac_passenger_temp + '°C';
                }
            }
        } catch (error) {
            console.error('加载车辆设置失败:', error);
        }
    }

    // AC Control Functions
    let acStatus = {
        ac_status: 'on',
        driver_temp: 23.5,
        passenger_temp: 23.5,
        fan_speed: 3,
        ac_mode: 'manual',
        sync_mode: false,
        ac_circulation: 'false',
        defrost: false
    };

    // 所有需要更新的温度显示元素
    const tempDisplayElements = {
        driver: [
            'ac-driver-temp-display',
            'driver-temp-display-dock'
        ],
        passenger: [
            'ac-passenger-temp-display',
            'passenger-temp-display-dock'
        ]
    };

    // WebSocket 连接
    // const socket = io(); // 已在顶部声明

    // 监听空调状态更新
    socket.on('ac_status_update', (response) => {
        console.log('Received AC status update:', response);
        
        // 更新本地状态，但保留未更改的值
        if (response.status) {
            Object.keys(response.status).forEach(key => {
                if (response.status[key] !== undefined) {
                    // 确保布尔值正确处理
                    if (typeof response.status[key] === 'boolean') {
                        acStatus[key] = response.status[key];
                    } else if (response.status[key] === 'true' || response.status[key] === 'false') {
                        acStatus[key] = response.status[key] === 'true';
                    } else {
                        acStatus[key] = response.status[key];
                    }
                }
            });
        }
        
        console.log('Updated acStatus:', acStatus);
        
        // 更新显示
        updateAllDisplays();
        
        // 显示服务器返回的消息
        if (response.message) {
            showToast(response.message);
        }
    });

    // 更新所有温度显示
    function updateAllDisplays() {
        console.log('Updating all displays with acStatus:', acStatus);
        
        // 更新驾驶员温度显示
        tempDisplayElements.driver.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = id.includes('dock') ? 
                    parseFloat(acStatus.driver_temp).toFixed(1) + '°' :
                    parseFloat(acStatus.driver_temp).toFixed(1);
            }
        });

        // 更新副驾驶温度显示
        tempDisplayElements.passenger.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = id.includes('dock') ? 
                    parseFloat(acStatus.passenger_temp).toFixed(1) + '°' :
                    parseFloat(acStatus.passenger_temp).toFixed(1);
            }
        });

        // 更新按钮状态
        updateButtonStates();

        // 更新空调开关状态
        const powerBtn = document.querySelector('.middle-ctrl-btn[title="空调电源"]');
        const acModule = document.getElementById('ac-module');
        
        if (powerBtn && acModule) {
            if (acStatus.ac_status === 'off') {
                powerBtn.classList.add('active');
                acModule.classList.add('inactive');
            } else {
                powerBtn.classList.remove('active');
                acModule.classList.remove('inactive');
            }
        }
    }

    function updateButtonStates() {
        // 获取所有按钮
        const buttons = {
            '自动模式': acStatus.ac_mode === 'auto',
            '同步温度': Boolean(acStatus.sync_mode), // 确保是布尔值
            '内外循环': acStatus.ac_circulation === 'true' || acStatus.ac_circulation === true,
            '前窗除雾': Boolean(acStatus.defrost)
        };

        // 更新每个按钮的状态
        Object.entries(buttons).forEach(([title, state]) => {
            const btn = document.querySelector(`.middle-ctrl-btn[title="${title}"]`);
            if (btn) {
                console.log(`Updating button ${title} state to:`, state);
                btn.classList.toggle('active', state);
            }
        });
    }

    // 温度调节函数
    function adjustTemperature(zone, direction) {
        if (acStatus.ac_status === 'off') {
            showToast('请先开启空调', 'warning');
            return;
        }

        const delta = direction === 'up' ? 0.5 : -0.5;
        const control = {};
        const currentTemp = parseFloat(acStatus[`${zone}_temp`]);

        if (zone === 'driver') {
            control.driver_temp = (currentTemp + delta).toFixed(1);
            if (acStatus.sync_mode) {
                control.passenger_temp = control.driver_temp;
            }
        } else {
            control.passenger_temp = (currentTemp + delta).toFixed(1);
            if (acStatus.sync_mode) {
                control.driver_temp = control.passenger_temp;
            }
        }

        // 先更新本地状态
        Object.assign(acStatus, control);
        
        // 发送到服务器
        socket.emit('ac_control', control);
        
        // 立即更新显示
        updateAllDisplays();
        
        // 添加动画效果
        const displayElement = document.getElementById(`ac-${zone}-temp-display`);
        if (displayElement) {
            displayElement.classList.add('temp-changing');
            setTimeout(() => displayElement.classList.remove('temp-changing'), 300);
        }
    }

    // 温度控制事件监听器
    document.getElementById('ac-driver-temp-up')?.addEventListener('click', () => {
        adjustTemperature('driver', 'up');
    });

    document.getElementById('ac-driver-temp-down')?.addEventListener('click', () => {
        adjustTemperature('driver', 'down');
    });

    document.getElementById('ac-passenger-temp-up')?.addEventListener('click', () => {
        adjustTemperature('passenger', 'up');
    });

    document.getElementById('ac-passenger-temp-down')?.addEventListener('click', () => {
        adjustTemperature('passenger', 'down');
    });

    // 功能按钮事件监听器
    document.querySelectorAll('.middle-ctrl-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // 如果空调关闭且不是电源按钮，则不处理
            if (acStatus.ac_status === 'off' && btn.title !== '空调电源') {
                showToast('请先开启空调', 'warning');
                return;
            }

            const control = {};
            let message = '';

            switch(btn.title) {
                case '空调电源':
                    control.ac_status = acStatus.ac_status === 'on' ? 'off' : 'on';
                    message = control.ac_status === 'on' ? '空调已开启' : '空调已关闭';
                    break;
                case '自动模式':
                    control.ac_mode = acStatus.ac_mode === 'auto' ? 'manual' : 'auto';
                    message = control.ac_mode === 'auto' ? '自动模式已开启' : '自动模式已关闭';
                    break;
                case '同步温度':
                    control.sync_mode = !acStatus.sync_mode;
                    if (!acStatus.sync_mode) {
                        control.passenger_temp = acStatus.driver_temp;
                    }
                    message = !acStatus.sync_mode ? '温度已同步' : '温度同步已关闭';
                    break;
                case '内外循环':
                    control.ac_circulation = acStatus.ac_circulation === 'true' ? 'false' : 'true';
                    message = control.ac_circulation === 'true' ? '已切换到内循环模式' : '已切换到外循环模式';
                    break;
                case '前窗除雾':
                    control.defrost = !acStatus.defrost;
                    message = control.defrost ? '除霜模式已开启' : '除霜模式已关闭';
                    break;
            }

            // 先更新本地状态
            Object.assign(acStatus, control);
            
            // 发送控制命令
            socket.emit('ac_control', control);
            
            // 显示提示
            showToast(message);

            // 立即更新显示
            updateAllDisplays();
        });
    });

    // Toast 通知系统
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast`;
        toast.textContent = message;
        
        const container = document.getElementById('toast-container');
        if (!container) {
            const newContainer = document.createElement('div');
            newContainer.id = 'toast-container';
            document.body.appendChild(newContainer);
            container = newContainer;
        }
        
        container.appendChild(toast);
        
        // 强制重绘
        toast.offsetHeight;
        
        // 添加显示类
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // 3秒后开始淡出
        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }, 3000);
    }

    // 添加 Toast 样式
    const style = document.createElement('style');
    style.textContent = `
        #toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        }
        
        .toast {
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            margin-bottom: 10px;
            animation: slide-in 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .toast.fade-out {
            animation: slide-out 0.3s ease forwards;
        }
        
        @keyframes slide-in {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slide-out {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    
    // 档位和灯光控制
    const gearDisplay = document.getElementById('gear-display');
    const lightsDisplay = document.getElementById('lights-display');
    const gearLightsModule = document.getElementById('gear-lights-module');
    const gearButtons = document.querySelectorAll('.gear-btn');
    const lightButtons = document.querySelectorAll('.light-btn');
    const currentGearSpan = document.getElementById('current-gear');

    // 初始化状态
    let currentGear = 'P';
    let activeLights = new Set();

    // 点击状态栏的档位和灯光显示时打开控制面板
    gearDisplay.addEventListener('click', () => {
        showView('gear-lights-module');
    });

    lightsDisplay.addEventListener('click', () => {
        showView('gear-lights-module');
    });

    // 档位控制
    gearButtons.forEach(button => {
        button.addEventListener('click', () => {
            const gear = button.dataset.gear;
            
            // 移除所有档位按钮的激活状态
            gearButtons.forEach(btn => btn.classList.remove('active'));
            // 移除状态栏所有档位的激活状态
            document.querySelectorAll('#gear-display span').forEach(span => span.classList.remove('active'));
            
            // 激活选中的档位
            button.classList.add('active');
            document.getElementById(`gear-${gear.toLowerCase()}`).classList.add('active');
            
            // 更新当前档位显示
            currentGear = gear;
            currentGearSpan.textContent = gear;

            // 显示提示
            showToast(`已切换到 ${gear} 档`);

            // 发送档位变更事件到后端
            socket.emit('gear_change', { gear: gear });
        });
    });

    // 灯光控制
    lightButtons.forEach(button => {
        button.addEventListener('click', () => {
            const light = button.dataset.light;
            
            if (light === 'off') {
                // 关闭所有灯
                lightButtons.forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('#lights-display i').forEach(icon => icon.classList.remove('active'));
                activeLights.clear();
                button.classList.add('active');
                setTimeout(() => button.classList.remove('active'), 200);
                showToast('已关闭所有车灯');
                console.log('offButton:', button.classList.contains('active'));
            } else {
                // 切换指定车灯的状态
                button.classList.toggle('active');
                
                if (button.classList.contains('active')) {
                    activeLights.add(light);
                    // 如果开启了任何灯，移除"关闭"按钮的激活状态
                    document.querySelector('.light-btn[data-light="off"]').classList.remove('active');
                } else {
                    activeLights.delete(light);
                }

                // 更新状态栏的灯光显示
                updateLightsDisplay();

                // 显示提示
                const lightName = button.querySelector('span').textContent;
                const action = button.classList.contains('active') ? '开启' : '关闭';
                showToast(`已${action}${lightName}`);
            }

            // 发送灯光变更事件到后端
            socket.emit('lights_change', { lights: Array.from(activeLights) });
        });
    });


    // 更新状态栏的灯光显示
    function updateLightsDisplay() {
        const highBeam = document.getElementById('light-high-beam');
        const lowBeam = document.getElementById('light-low-beam');
        const leftTurn = document.getElementById('light-left-turn');
        const rightTurn = document.getElementById('light-right-turn');
        
        highBeam.classList.toggle('active', activeLights.has('high'));
        lowBeam.classList.toggle('active', activeLights.has('low'));
        leftTurn.classList.toggle('active', activeLights.has('left-turn'));
        rightTurn.classList.toggle('active', activeLights.has('right-turn'));
    }

    // 监听模拟器数据更新
    socket.on('simulator_update', (response) => {
        console.log('收到模拟器数据:', response);      
        if (response.status) {
            const state = response.status;
            // 格式化状态数据
            const formattedState = {
                速度: state.speed + ' km/h',
                方向: state.direction,
                档位: state.gear,
                灯光状态: state.lights,
                发动机温度: state.engine_temp + ' °C',
                油量: state.fuel_level + '%'
            };
            
            console.log('车辆状态:', formattedState);
            
            // 更新灯光状态
            if(state.lights){          
                // 遍历服务器返回的灯光状态
                Object.entries(state.lights).forEach(([lightKey, isOn]) => {
                    // 根据灯光键名找到对应的按钮
                    let buttonSelector;
                    switch(lightKey) {
                        case 'left_turn':
                            buttonSelector = '.light-btn[data-light="left-turn"]';
                            break;
                        case 'right_turn':
                            buttonSelector = '.light-btn[data-light="right-turn"]';
                            break;
                        case 'high_beam':
                            buttonSelector = '.light-btn[data-light="high"]';
                            break;
                        case 'low_beam':
                            buttonSelector = '.light-btn[data-light="low"]';
                            break;
                        case 'position':
                            buttonSelector = '.light-btn[data-light="position"]';
                            break;
                        case 'fog':
                            buttonSelector = '.light-btn[data-light="fog"]';
                            break;
                        case 'warning':
                            buttonSelector = '.light-btn[data-light="emergency"]';
                            break;
                        default:
                            return; // 跳过未知的灯光类型
                    }
                    
                    const targetButton = document.querySelector(buttonSelector);
                    const offButton = document.querySelector('.light-btn[data-light="off"]');
                    
                    // 检查按钮是否存在
                    if (!targetButton) {
                        console.warn(`未找到灯光按钮: ${buttonSelector}`);
                        return;
                    }
                    
                    if (targetButton.classList.contains('active')) {
                        if (!isOn) {
                            targetButton.classList.remove('active');
                            if(lightKey === 'high_beam' || lightKey === 'low_beam'){
                                activeLights.delete(lightKey.replace('_beam', ''));
                            }
                            else{
                                activeLights.delete(lightKey.replace('_', '-'));
                            }
                            if (offButton) {
                                offButton.classList.add('active');
                            }
                            showToast('已关闭'+lightKey);
                            socket.emit('lights_change', { lights: Array.from(activeLights) });
                        } 
                    }
                    else{
                        if(isOn){
                            targetButton.classList.add('active');
                            if(lightKey === 'high_beam' || lightKey === 'low_beam'){
                                activeLights.add(lightKey.replace('_beam', ''));
                            }
                            else{
                                activeLights.add(lightKey.replace('_', '-'));
                            }
                            if (offButton) {
                                offButton.classList.remove('active');
                            }
                            showToast('已开启'+lightKey);
                            socket.emit('lights_change', { lights: Array.from(activeLights) });
                        }
                    }
                    updateLightsDisplay();
                    console.log('activeLights:', activeLights);

                });
            }
            
            // 更新档位状态
            if(state.gear){
                const gearButton = document.querySelector(`.gear-btn[data-gear="${state.gear}"]`);

                if (gearButton) {
                    // 移除所有档位按钮的active状态
                    document.querySelectorAll('.gear-btn').forEach(btn => btn.classList.remove('active'));
                    // 移除状态栏所有档位的激活状态
                    document.querySelectorAll('#gear-display span').forEach(span => span.classList.remove('active'));
                    // 添加当前档位的active状态
                    gearButton.classList.add('active');
                    document.getElementById(`gear-${state.gear.toLowerCase()}`).classList.add('active');
                    currentGear = state.gear;
                    currentGearSpan.textContent = state.gear;
                    showToast(`已切换到 ${state.gear} 档`);
                    socket.emit('gear_change', { gear: state.gear });
                }
            }
        }
        
        // 显示消息
        if (response.message) {
            console.log('消息:', response.message);
           
        }
        
        // 显示时间戳
        if (response.timestamp) {
            console.log('数据时间:', new Date(response.timestamp).toLocaleString());
        }
    });
        
    



    // 初始化档位按钮状态
    const initialGearBtn = document.querySelector(`.gear-btn[data-gear="${currentGear}"]`);
    if (initialGearBtn) {
        initialGearBtn.classList.add('active');
    }
});