let activeAccessory = null;
let processingVideo = false;
let videoInterval = null;
let accessoriesLoaded = false;
let availableAccessories = [];

document.addEventListener('DOMContentLoaded', function() {
    const iconBar = document.querySelector('.icon-bar');
    
    const accessoriesIcon = document.createElement('div');
    accessoriesIcon.className = 'icon';
    accessoriesIcon.id = 'accessories-icon';
    accessoriesIcon.innerHTML = '<i class="fas fa-glasses"></i>';
    accessoriesIcon.title = 'Virtual Accessories';
    accessoriesIcon.addEventListener('click', openAccessoriesModal);
    iconBar.appendChild(accessoriesIcon);
    
    const accessoriesModal = `
    <div id="accessoriesModal" class="modal">
        <div class="modal-content accessories-layout">
            <span class="close">&times;</span>
            <h2>Virtual Accessories</h2>
            
            <div class="accessories-flex-container">
                <div class="accessories-video-container">
                    <!-- This is where the webcam view will be shown -->
                    <div id="accessories-video-wrapper" class="accessories-video-wrapper"></div>
                    <div id="accessories-status" class="accessories-status">
                        Try on virtual accessories in real-time!
                    </div>
                </div>
                
                <div class="accessories-sidebar">
                    <h3>Choose Accessory</h3>
                    <div id="loading-indicator" style="display: none; text-align: center; margin: 10px 0;">
                        Loading accessories...
                    </div>
                    <div class="accessories-menu" id="accessories-menu">
                        <button class="accessory-btn" data-accessory="glasses">Glasses</button>
                        <button class="accessory-btn" data-accessory="hat">Hat</button>
                        <button class="accessory-btn" data-accessory="mask">Mask</button>
                        <button class="accessory-btn active-accessory" data-accessory="none">Remove All</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', accessoriesModal);
    
    const styles = `
    <style>
        .accessories-layout {
            max-width: 95% !important;
            width: 95% !important;
            margin: 5% auto !important;
        }
        
        .accessories-flex-container {
            display: flex;
            flex-direction: row;
            gap: 20px;
            margin-top: 20px;
        }
        
        .accessories-video-container {
            flex: 3; /* Increased from 2 to 3 to make video larger */
            position: relative;
        }
        
        .accessories-video-wrapper {
            position: relative;
            width: 100%;
            height: 0;
            padding-bottom: 75%; /* 4:3 aspect ratio */
            background-color: #000;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .accessories-sidebar {
            flex: 1;
            background-color: rgba(30, 30, 30, 0.7);
            border-radius: 10px;
            padding: 15px;
            align-self: flex-start; /* Keep the sidebar at the top */
            min-width: 150px; /* Ensure minimum width */
            max-width: 200px; /* Ensure it doesn't get too wide */
        }
        
        .accessories-sidebar h3 {
            margin-top: 0;
            margin-bottom: 15px;
            text-align: center;
            color: #4fc3f7;
        }
        
        .accessories-menu {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .accessory-btn {
            background-color: rgba(50, 70, 90, 0.8);
            border: none;
            color: white;
            padding: 12px 15px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 1rem;
            text-align: left;
        }
        
        .accessory-btn:hover {
            background-color: rgba(70, 100, 130, 0.9);
            transform: translateX(5px);
        }
        
        .active-accessory {
            background-color: rgba(79, 195, 247, 0.9);
            box-shadow: 0 0 10px rgba(79, 195, 247, 0.5);
        }
        
        /* Position the video properly */
        #cameraFeed {
            position: relative;
            z-index: 1;
        }
        
        /* Make sure the overlay positions correctly */
        #video-overlay {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            z-index: 10 !important;
            pointer-events: none !important;
        }
        
        /* Custom styles for the accessory modal video feed */
        .accessories-video {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            transform: scaleX(-1);
        }
        
        .accessories-status {
            text-align: center;
            margin-top: 10px;
            color: #4fc3f7;
            font-size: 0.9rem;
        }
        
        /* Media queries for smaller screens */
        @media (max-width: 768px) {
            .accessories-flex-container {
                flex-direction: column;
            }
            
            .accessories-sidebar {
                margin-top: 15px;
                max-width: 100%;
            }
            
            .accessories-menu {
                flex-direction: row;
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .accessory-btn {
                flex: 1 0 40%;
            }
        }
    </style>
    `;
    
    document.head.insertAdjacentHTML('beforeend', styles);
    
    setupAccessoriesEventHandlers();
    
    fetchAvailableAccessories();
});

function setupAccessoriesEventHandlers() {
    const accessoriesModal = document.getElementById('accessoriesModal');
    const closeAccessoriesBtn = accessoriesModal.querySelector('.close');
    
    closeAccessoriesBtn.addEventListener('click', function() {
        accessoriesModal.style.display = 'none';
        stopVideoProcessing();
    });
    
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('accessory-btn') || 
            e.target.parentElement.classList.contains('accessory-btn')) {
                
            const button = e.target.classList.contains('accessory-btn') ? 
                e.target : e.target.parentElement;
                
            const accessory = button.getAttribute('data-accessory');
            
            document.querySelectorAll('.accessory-btn').forEach(btn => {
                btn.classList.remove('active-accessory');
            });
            
            button.classList.add('active-accessory');
            
            applyAccessory(accessory);
        }
    });
}

function fetchAvailableAccessories() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    
    fetch('http://localhost:5002/status', { signal: AbortSignal.timeout(3000) })
        .then(response => response.json())
        .then(data => {
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            
            availableAccessories = data.accessories || [];
            accessoriesLoaded = true;
            
            updateAccessoriesMenu();
            
            if (data.active_accessory) {
                activeAccessory = data.active_accessory;
                updateActiveAccessoryButton();
            }
        })
        .catch(error => {
            console.error('Error fetching accessories:', error);
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            
            const statusElement = document.getElementById('accessories-status');
            if (statusElement) {
                statusElement.textContent = 'Error loading accessories. Is the server running?';
                statusElement.style.color = '#ff5252';
            }
        });
}

function updateAccessoriesMenu() {
    const menuElement = document.getElementById('accessories-menu');
    if (!menuElement || availableAccessories.length === 0) return;
    
    Array.from(menuElement.children).forEach(child => {
        if (child.getAttribute('data-accessory') !== 'none') {
            child.remove();
        }
    });
    
    availableAccessories.forEach(accessory => {
        const button = document.createElement('button');
        button.className = 'accessory-btn';
        button.setAttribute('data-accessory', accessory);
        
        let displayName = accessory.charAt(0).toUpperCase() + accessory.slice(1);
        if (displayName.includes('_')) {
            displayName = displayName.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        }
        
        button.textContent = displayName;
        
        menuElement.insertBefore(button, menuElement.firstChild);
    });
    
    updateActiveAccessoryButton();
}

function updateActiveAccessoryButton() {
    document.querySelectorAll('.accessory-btn').forEach(btn => {
        btn.classList.remove('active-accessory');
    });
    
    if (activeAccessory) {
        const activeButton = document.querySelector(`.accessory-btn[data-accessory="${activeAccessory}"]`);
        if (activeButton) {
            activeButton.classList.add('active-accessory');
        }
    } else {
        const removeButton = document.querySelector('.accessory-btn[data-accessory="none"]');
        if (removeButton) {
            removeButton.classList.add('active-accessory');
        }
    }
}

function setupVideoContainer() {
    const mainVideoElement = document.getElementById('cameraFeed');
    if (!mainVideoElement || !mainVideoElement.srcObject) {
        console.error('Main video element not ready');
        return;
    }
    
    const videoWrapper = document.getElementById('accessories-video-wrapper');
    if (!videoWrapper) return;
    
    videoWrapper.innerHTML = '';
    
    const videoElement = document.createElement('video');
    videoElement.className = 'accessories-video';
    videoElement.id = 'accessories-video';
    videoElement.autoplay = true;
    videoElement.srcObject = mainVideoElement.srcObject;
    
    const overlay = document.createElement('canvas');
    overlay.id = 'video-overlay';
    overlay.className = 'accessories-video';
    overlay.style.position = 'absolute';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.pointerEvents = 'none';
    overlay.style.zIndex = '10';
    
    videoWrapper.appendChild(videoElement);
    videoWrapper.appendChild(overlay);
    
    setTimeout(() => {
        if (videoElement.videoWidth && videoElement.videoHeight) {
            const aspectRatio = videoElement.videoWidth / videoElement.videoHeight;
            const containerWidth = videoWrapper.offsetWidth;
            overlay.width = containerWidth;
            overlay.height = containerWidth / aspectRatio;
        } else {
            overlay.width = videoWrapper.offsetWidth;
            overlay.height = videoWrapper.offsetHeight;
        }
    }, 100);
}

function openAccessoriesModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
    
    const accessoriesModal = document.getElementById('accessoriesModal');
    accessoriesModal.style.display = 'block';
    
    setupVideoContainer();
    
    startVideoProcessing();
}

function applyAccessory(accessoryName) {
    if (accessoryName.toLowerCase() === 'none') {
        activeAccessory = null;
    } else {
        activeAccessory = accessoryName;
    }
    
    const statusElement = document.getElementById('accessories-status');
    if (statusElement) {
        if (activeAccessory) {
            statusElement.textContent = `Wearing: ${activeAccessory.charAt(0).toUpperCase() + activeAccessory.slice(1)}`;
        } else {
            statusElement.textContent = 'No accessories applied';
        }
    }
    
    // Use a timeout to prevent potential fetch request flooding
    setTimeout(() => {
        fetch('http://localhost:5002/set_active_accessory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                accessory: accessoryName
            }),
            signal: AbortSignal.timeout(3000)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Server updated with active accessory:', data);
        })
        .catch(error => {
            console.error('Error setting active accessory:', error);
            
            if (statusElement) {
                statusElement.textContent = 'Error connecting to accessory service';
                statusElement.style.color = '#ff5252';
            }
        });
    }, 100);
}

function startVideoProcessing() {
    if (processingVideo) return;
    
    processingVideo = true;
    
    videoInterval = setInterval(processVideoFrame, 200); // Reduced frequency to 5fps
}

function stopVideoProcessing() {
    processingVideo = false;
    
    if (videoInterval) {
        clearInterval(videoInterval);
        videoInterval = null;
    }
}

async function processVideoFrame() {
    if (!processingVideo) return;
    
    try {
        const videoElement = document.getElementById('accessories-video');
        if (!videoElement || !videoElement.srcObject) {
            console.error('Accessories video element not ready');
            return;
        }
        
        const modal = document.getElementById('accessoriesModal');
        if (modal.style.display !== 'block') {
            return;
        }
        
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth || 640;
        canvas.height = videoElement.videoHeight || 480;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.7)); // Reduced quality
        
        const formData = new FormData();
        formData.append('image', blob, 'face.jpg');
        
        const response = await fetch('http://localhost:5002/process_frame', {
            method: 'POST',
            body: formData,
            signal: AbortSignal.timeout(3000)
        });
        
        if (!processingVideo) return;
        
        const data = await response.json();
        
        if (data.accessory) {
            const img = new Image();
            img.onload = function() {
                if (processingVideo) {
                    const overlay = document.getElementById('video-overlay');
                    if (!overlay) return;
                    
                    const videoRect = videoElement.getBoundingClientRect();
                    overlay.width = videoRect.width;
                    overlay.height = videoRect.height;
                    
                    const ctx = overlay.getContext('2d');
                    ctx.clearRect(0, 0, overlay.width, overlay.height);
                    ctx.drawImage(img, 0, 0, overlay.width, overlay.height);
                }
            };
            
            img.src = data.image;
        } else {
            const overlay = document.getElementById('video-overlay');
            if (overlay) {
                const ctx = overlay.getContext('2d');
                ctx.clearRect(0, 0, overlay.width, overlay.height);
            }
        }
    } catch (error) {
        console.error('Error processing video frame:', error);
        
        // Display error in status
        const statusElement = document.getElementById('accessories-status');
        if (statusElement) {
            statusElement.textContent = 'Error connecting to accessory service';
            statusElement.style.color = '#ff5252';
        }
        
        // Pause processing for a moment to avoid flooding with errors
        stopVideoProcessing();
        setTimeout(startVideoProcessing, 3000);
    }
}

function showMessage(message, duration) {
    // Prevent recursive calls by checking if window.showErrorMessage exists and isn't this function
    if (typeof window.showErrorMessage === 'function' && 
        window.showErrorMessage.toString().indexOf('messageDiv') === -1) {
        window.showErrorMessage(message, duration);
        return;
    }
    
    console.log(message); // Always log to console
    
    let messageDiv = document.getElementById('message-notification');
    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.id = 'message-notification';
        messageDiv.style.position = 'fixed';
        messageDiv.style.top = '20px';
        messageDiv.style.left = '50%';
        messageDiv.style.transform = 'translateX(-50%)';
        messageDiv.style.padding = '10px 20px';
        messageDiv.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        messageDiv.style.color = 'white';
        messageDiv.style.borderRadius = '5px';
        messageDiv.style.zIndex = '9999';
        messageDiv.style.transition = 'opacity 0.5s';
        messageDiv.style.opacity = '0';
        document.body.appendChild(messageDiv);
    }
    
    messageDiv.textContent = message;
    messageDiv.style.opacity = '1';
    
    setTimeout(() => {
        messageDiv.style.opacity = '0';
    }, duration || 3000);
}