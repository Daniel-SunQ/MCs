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
    // ======================== UI Switching Logic (UNIFIED) =================
    // =======================================================================

    function showView(viewId) {
        // Hide all major views first
        mainContent.style.display = 'none';
        appDrawer.style.display = 'none';
        modules.forEach(m => m.style.display = 'none');

        const viewToShow = document.getElementById(viewId);
        if (viewToShow) {
            const displayStyle = viewId === 'app-drawer' ? 'grid' : 'flex';
            viewToShow.style.display = displayStyle;
            
            if (viewId === 'map-module') {
                initMap();
            }
        } else {
            mainContent.style.display = 'flex';
        }
    }

    // --- Event Listener Binding ---
    appDockIcon.addEventListener('click', () => showView('app-drawer'));
    
    closeModuleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetViewId = btn.getAttribute('data-target');
            showView(targetViewId || 'main-content');
        });
    });

    functionCards.forEach(card => {
        card.addEventListener('click', () => {
            const targetViewId = card.getAttribute('data-target');
            if (targetViewId) showView(targetViewId);
        });
    });

    // --- Unify Dock Buttons to use the same showView logic ---
    if (acDockButton) acDockButton.addEventListener('click', () => showView('ac-module'));
    if (settingsDockButton) settingsDockButton.addEventListener('click', () => showView('settings-module'));
    if (mapDockButton) mapDockButton.addEventListener('click', () => showView('map-module'));
    if (mediaDockWidget) mediaDockWidget.addEventListener('click', () => showView('media-module'));

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

    // =======================================================================
    // ====================== TEMPERATURE SYNC LOGIC =========================
    // =======================================================================

    function updateAllTempDisplays() {
        // Update Dock displays
        if (driverTempDisplayDock) driverTempDisplayDock.textContent = `${driverTemp.toFixed(1)}°`;
        if (passengerTempDisplayDock) passengerTempDisplayDock.textContent = `${passengerTemp.toFixed(1)}°`;

        // Update AC module displays
        if (acDriverTempDisplay) acDriverTempDisplay.textContent = driverTemp.toFixed(1);
        if (acPassengerTempDisplay) acPassengerTempDisplay.textContent = passengerTemp.toFixed(1);
    }
    
    function changeTemp(zone, direction) {
        const step = 0.5;
        const minTemp = 16;
        const maxTemp = 30;

        if (zone === 'driver') {
            driverTemp += direction * step;
            driverTemp = Math.max(minTemp, Math.min(maxTemp, driverTemp));
        } else if (zone === 'passenger') {
            passengerTemp += direction * step;
            passengerTemp = Math.max(minTemp, Math.min(maxTemp, passengerTemp));
        }
        updateAllTempDisplays();
    }

    // --- Event Listeners for All Temperature Buttons ---
    if(driverTempUpDock) driverTempUpDock.addEventListener('click', (e) => { e.stopPropagation(); changeTemp('driver', 1); });
    if(driverTempDownDock) driverTempDownDock.addEventListener('click', (e) => { e.stopPropagation(); changeTemp('driver', -1); });
    if(passengerTempUpDock) passengerTempUpDock.addEventListener('click', (e) => { e.stopPropagation(); changeTemp('passenger', 1); });
    if(passengerTempDownDock) passengerTempDownDock.addEventListener('click', (e) => { e.stopPropagation(); changeTemp('passenger', -1); });

    if(acDriverTempUp) acDriverTempUp.addEventListener('click', () => changeTemp('driver', 1));
    if(acDriverTempDown) acDriverTempDown.addEventListener('click', () => changeTemp('driver', -1));
    if(acPassengerTempUp) acPassengerTempUp.addEventListener('click', () => changeTemp('passenger', 1));
    if(acPassengerTempDown) acPassengerTempDown.addEventListener('click', () => changeTemp('passenger', -1));


    // =======================================================================
    // =========================== UI HELPERS ================================
    // =======================================================================
    function updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
        if (smallTimeDisplay) smallTimeDisplay.textContent = timeString;
        if (largeTimeDisplay) largeTimeDisplay.textContent = timeString;
    }

    function formatDate() {
        const dateLine2 = document.getElementById('large-date-display-line2');
        const dateLine3 = document.getElementById('large-date-display-line3');
        if (dateLine2 && dateLine3) {
            const now = new Date();
            const day = String(now.getDate()).padStart(2, '0');
            const month = now.toLocaleString('en-US', { month: 'short' }).toUpperCase();
            dateLine2.textContent = day;
            dateLine3.textContent = month;
        }
    }
    
    // =======================================================================
    // ============================ WEATHER LOGIC ============================
    // =======================================================================
    const weatherIconMap = {
        // Mapping QWeather icon codes to Font Awesome icons
        "100": "fas fa-sun", // 晴
        "101": "fas fa-cloud-sun", // 多云
        "102": "fas fa-cloud", // 少云
        "103": "fas fa-cloud", // 晴间多云
        "104": "fas fa-cloud", // 阴
        "300": "fas fa-cloud-showers-heavy", // 阵雨
        "301": "fas fa-cloud-showers-heavy", // 强阵雨
        "305": "fas fa-cloud-rain", // 小雨
        "306": "fas fa-cloud-rain", // 中雨
        "307": "fas fa-cloud-showers-heavy", // 大雨
        "400": "fas fa-snowflake", // 小雪
        "401": "fas fa-snowflake", // 中雪
        "402": "fas fa-snowflake", // 大雪
        "501": "fas fa-smog", // 雾
        // Add more mappings as needed
    };

    function updateWeatherUI(data) {
        if (!data || !data.temp || !data.text) {
            weatherDisplay.textContent = '天气未知';
            weatherIcon.className = 'fas fa-question-circle';
            return;
        }
        weatherDisplay.textContent = `${data.text} ${data.temp}°C`;
        weatherIcon.className = weatherIconMap[data.icon] || 'fas fa-cloud'; // Default icon
    }

    async function getWeather(city) {
        if (!weatherIcon || !weatherDisplay) return;
        
        weatherIcon.className = 'fas fa-spinner fa-spin';
        weatherDisplay.textContent = '加载中...';

        try {
            const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const weatherData = await response.json();
            updateWeatherUI(weatherData);
        } catch (error) {
            console.error("获取天气失败:", error);
            weatherDisplay.textContent = "获取失败";
            weatherIcon.className = 'fas fa-exclamation-triangle';
        }
    }

    // =======================================================================
    // ======================== MOCK VOICE COMMAND HANDLING ==================
    // =======================================================================
    /**
     * Handles function calls returned by the NLU model.
     * This is where you would integrate the weather function.
     * @param {Array<object>} toolCalls - The array of tool calls from the API.
     */
    function handleToolCalls(toolCalls) {
        if (!toolCalls || toolCalls.length === 0) {
            console.log("没有工具调用需要处理。");
            return;
        }

        for (const call of toolCalls) {
            const functionName = call.function.name;
            const args = JSON.parse(call.function.arguments);

            console.log(`执行工具调用: ${functionName}，参数:`, args);

            if (functionName === 'set_weather') {
                if (args.city) {
                    getWeather(args.city);
                } else {
                    console.error("调用 set_weather 缺少 city 参数");
                }
            }
            // Add other function handlers here, e.g., for AC, music, etc.
        }
    }

    // =======================================================================
    // =========================== INITIALIZATION ============================
    // =======================================================================
    showView('main-content');
    updateAllTempDisplays();

    // Start clock and set date
    updateTime();
    formatDate();
    setInterval(updateTime, 1000); // Update time every second
    
    // Initial weather fetch
    getWeather('北京');
});