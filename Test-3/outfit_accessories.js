document.addEventListener('DOMContentLoaded', function() {
    setupOutfitAccessoryUI();
    setupEventListeners();
    checkBackendServices();
});

let originalOutfitImage = null;
let lastAppliedAccessory = null;
let accessoryServiceAvailable = false;

function setupOutfitAccessoryUI() {
    const styleElement = document.createElement('style');
    styleElement.id = 'outfit-accessory-styles';
    styleElement.textContent = `
        /* Prevent body scrolling when modal is open */
        body.modal-open {
            overflow: hidden;
        }
        
        /* Outfit modal - optimize size and allow internal scrolling */
        #outfitModal .modal-content {
            width: 85%;
            max-width: 1000px;
            max-height: 90vh;
            padding: 20px;
            overflow-y: auto; /* Allow scrolling inside modal if needed */
            display: flex;
            flex-direction: column;
        }
        
        /* Main container for outfit with accessories */
        .outfit-container {
            display: flex;
            gap: 20px;
            margin: 10px 0;
            width: 100%;
        }
        
        /* Main content area with images */
        .outfit-main-content {
            flex: 1;
            display: flex;
            gap: 20px;
        }
        
        /* Sidebar with accessory options */
        .outfit-accessory-sidebar {
            flex: 0 0 130px;
            background-color: rgba(40, 50, 60, 0.7);
            border-radius: 10px;
            padding: 12px;
            align-self: flex-start;
        }
        
        .outfit-accessory-sidebar h3 {
            margin-top: 0;
            margin-bottom: 12px;
            color: #4fc3f7;
            font-size: 0.95rem;
            text-align: center;
        }
        
        .outfit-accessory-buttons {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .outfit-accessory-btn {
            background-color: rgba(50, 70, 90, 0.8);
            border: none;
            color: white;
            padding: 8px 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: left;
            font-size: 0.9rem;
        }
        
        .outfit-accessory-btn:hover:not(:disabled) {
            background-color: rgba(70, 100, 130, 0.9);
            transform: translateX(3px);
        }
        
        .outfit-accessory-btn.active {
            background-color: rgba(79, 195, 247, 0.9);
            box-shadow: 0 0 10px rgba(79, 195, 247, 0.5);
        }

        .outfit-accessory-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Image containers - ensure images fit in viewport */
        .outfit-image-container {
            position: relative;
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .outfit-image-container h4 {
            margin-top: 0;
            margin-bottom: 8px;
            color: #4fc3f7;
            text-align: center;
            font-size: 1rem;
        }
        
        /* Processed image container starts hidden */
        .outfit-processed-container {
            display: none;
        }
        
        /* Original outfit image display - resize to fit modal */
        #outfit-original-img {
            max-width: 100%;
            max-height: 50vh; /* Reduced from 55vh to leave more room for text */
            width: auto;
            height: auto;
            display: block;
            border-radius: 10px;
            background-color: rgba(20, 30, 40, 0.4);
        }
        
        /* Canvas for accessorized outfit - resize to fit modal */
        #outfit-accessory-canvas {
            max-width: 100%;
            max-height: 50vh; /* Reduced from 55vh to leave more room for text */
            width: auto;
            height: auto;
            display: block;
            border-radius: 10px;
            background-color: rgba(20, 30, 40, 0.4);
        }
        
        /* Loading indicator */
        .outfit-accessory-loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 5;
        }
        
        /* Hide the original image that comes with the outfit modal */
        #outfit-image {
            display: none;
        }
        
        /* Service status indicator */
        .service-warning {
            color: #ff5252;
            font-size: 0.8em;
            text-align: center;
            padding: 5px;
            margin-top: 10px;
        }
        
        /* Info sections */
        #outfit-weather-info, #outfit-event-info {
            margin-bottom: 10px;
        }
        
        #outfit-recommendations {
            margin-top: 15px;
            margin-bottom: 10px;
        }
        
        /* Responsive adjustments */
        @media (max-width: 992px) {
            .outfit-container {
                flex-direction: column;
            }
            
            .outfit-accessory-sidebar {
                width: 100%;
                flex: none;
                margin-bottom: 15px;
            }
            
            .outfit-accessory-buttons {
                flex-direction: row;
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .outfit-accessory-btn {
                flex: 1 0 auto;
                text-align: center;
                min-width: 70px;
            }
            
            .outfit-main-content {
                flex-direction: column;
            }
            
            #outfit-original-img, #outfit-accessory-canvas {
                max-height: 35vh; /* Further reduced for mobile to ensure text visibility */
            }
        }
    `;
    document.head.appendChild(styleElement);
    
    setTimeout(() => {
        const outfitModal = document.getElementById('outfitModal');
        if (!outfitModal) return;
        
        outfitModal.addEventListener('show', function() {
            document.body.classList.add('modal-open');
            checkBackendServices();
        });
        
        outfitModal.addEventListener('hide', function() {
            document.body.classList.remove('modal-open');
        });
        
        const modalContent = outfitModal.querySelector('.modal-content');
        const outfitImage = modalContent.querySelector('#outfit-image');
        
        const outfitContainer = document.createElement('div');
        outfitContainer.className = 'outfit-container';
        
        const mainContent = document.createElement('div');
        mainContent.className = 'outfit-main-content';
        
        const originalContainer = document.createElement('div');
        originalContainer.className = 'outfit-image-container original-outfit';
        originalContainer.innerHTML = `
            <h4>Original Outfit</h4>
            <img id="outfit-original-img" src="" alt="Original outfit" />
        `;
        
        const processedContainer = document.createElement('div');
        processedContainer.className = 'outfit-image-container outfit-processed-container';
        processedContainer.innerHTML = `
            <h4>With Accessory</h4>
            <canvas id="outfit-accessory-canvas"></canvas>
            <div class="outfit-accessory-loading loading"></div>
        `;
        
        mainContent.appendChild(originalContainer);
        mainContent.appendChild(processedContainer);
        
        const sidebar = document.createElement('div');
        sidebar.className = 'outfit-accessory-sidebar';
        sidebar.innerHTML = `
            <h3>Try Accessories</h3>
            <div class="outfit-accessory-buttons">
                <button class="outfit-accessory-btn" data-accessory="glasses">Glasses</button>
                <button class="outfit-accessory-btn" data-accessory="hat">Hat</button>
                <button class="outfit-accessory-btn" data-accessory="mask">Mask</button>
                <button class="outfit-accessory-btn" data-accessory="none">Remove All</button>
            </div>
            <div id="service-warning" class="service-warning" style="display: none;">
                Accessory service unavailable
            </div>
        `;
        
        outfitContainer.appendChild(mainContent);
        outfitContainer.appendChild(sidebar);
        
        const eventInfo = modalContent.querySelector('#outfit-event-info');
        const loadingElement = modalContent.querySelector('#outfit-loading');
        const recommendationsElement = modalContent.querySelector('#outfit-recommendations');
        
        if (loadingElement) {
            loadingElement.after(outfitContainer);
        } else if (eventInfo) {
            eventInfo.after(outfitContainer);
        } else if (outfitImage) {
            outfitImage.after(outfitContainer);
        } else if (recommendationsElement) {
            recommendationsElement.before(outfitContainer);
        } else {
            modalContent.appendChild(outfitContainer);
        }
        
        const accessoryLoading = document.querySelector('.outfit-accessory-loading');
        if (accessoryLoading) {
            accessoryLoading.style.display = 'none';
        }
    }, 100);
}

function checkBackendServices() {
    const warningElement = document.getElementById('service-warning');
    if (warningElement) {
        warningElement.style.display = 'none';
    }
    
    fetch('http://localhost:5002/status', { 
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        // Add a timeout to prevent hanging
        signal: AbortSignal.timeout(2000)
    })
    .then(response => {
        if (!response.ok) throw new Error('API not available');
        return response.json();
    })
    .then(data => {
        console.log('Accessory service available:', data);
        accessoryServiceAvailable = true;
        
        // Enable accessory buttons
        document.querySelectorAll('.outfit-accessory-btn').forEach(btn => {
            btn.disabled = false;
        });
        
        if (warningElement) {
            warningElement.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Accessory service unavailable:', error);
        accessoryServiceAvailable = false;
        
        // Disable accessory buttons and show warning
        document.querySelectorAll('.outfit-accessory-btn').forEach(btn => {
            if (btn.getAttribute('data-accessory') !== 'none') {
                btn.disabled = true;
            }
        });
        
        if (warningElement) {
            warningElement.style.display = 'block';
        }
    });
}

function setupEventListeners() {
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('outfit-accessory-btn')) {
            const accessory = e.target.getAttribute('data-accessory');
            
            document.querySelectorAll('.outfit-accessory-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            e.target.classList.add('active');
            
            applyOutfitAccessory(accessory);
        }
    });
    
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    if (modal.style.display === 'block') {
                        document.body.classList.add('modal-open');
                        modal.dispatchEvent(new Event('show'));
                    } else {
                        document.body.classList.remove('modal-open');
                        modal.dispatchEvent(new Event('hide'));
                    }
                }
            });
        });
        
        observer.observe(modal, { attributes: true });
    });
    
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'src') {
                const outfitImage = document.getElementById('outfit-image');
                const originalImg = document.getElementById('outfit-original-img');
                
                if (outfitImage && outfitImage.src && originalImg) {
                    // Use the actual outfit image source directly
                    originalOutfitImage = outfitImage.src;
                    originalImg.src = originalOutfitImage;
                    
                    resetOutfitAccessories();
                }
            }
        });
    });
    
    setTimeout(() => {
        const outfitImage = document.getElementById('outfit-image');
        if (outfitImage) {
            observer.observe(outfitImage, { attributes: true });
            
            if (outfitImage.complete && outfitImage.src) {
                const originalImg = document.getElementById('outfit-original-img');
                if (originalImg) {
                    // Use the actual outfit image source directly
                    originalOutfitImage = outfitImage.src;
                    originalImg.src = originalOutfitImage;
                }
            }
        }
        
        const originalFetchOutfitData = window.fetchOutfitData;
        if (typeof originalFetchOutfitData === 'function') {
            window.fetchOutfitData = function() {
                originalFetchOutfitData.apply(this, arguments);
                
                setTimeout(resetOutfitAccessories, 100);
            };
        }
        
        const closeButtons = document.querySelectorAll('.modal .close');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                document.body.classList.remove('modal-open');
            });
        });
    }, 200);
}

function resetOutfitAccessories() {
    lastAppliedAccessory = null;
    
    const processedContainer = document.querySelector('.outfit-processed-container');
    if (processedContainer) {
        processedContainer.style.display = 'none';
    }
    
    document.querySelectorAll('.outfit-accessory-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const outfitImage = document.getElementById('outfit-image');
    const originalImg = document.getElementById('outfit-original-img');
    
    if (outfitImage && outfitImage.src && originalImg) {
        // Use the actual outfit image source directly
        originalOutfitImage = outfitImage.src;
        originalImg.src = originalOutfitImage;
    }
}

function applyOutfitAccessory(accessory) {
    const outfitImage = document.getElementById('outfit-image');
    const originalImg = document.getElementById('outfit-original-img');
    const processedContainer = document.querySelector('.outfit-processed-container');
    const canvas = document.getElementById('outfit-accessory-canvas');
    const loadingIndicator = document.querySelector('.outfit-accessory-loading');
    
    if (!canvas || !processedContainer || !originalImg) {
        console.error('Required elements not found for accessory application');
        return;
    }
    
    if (accessory === 'none') {
        processedContainer.style.display = 'none';
        lastAppliedAccessory = null;
        return;
    }
    
    // Check if accessory service is available
    if (!accessoryServiceAvailable && accessory !== 'none') {
        displayNotification('Accessory service is unavailable. Please start the server.', 3000);
        return;
    }
    
    processedContainer.style.display = 'block';
    
    if (accessory === lastAppliedAccessory) return;
    
    lastAppliedAccessory = accessory;
    
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
    
    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onerror = function() {
        console.error('Error loading outfit image');
        displayNotification('Error loading outfit image', 3000);
        
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    };
    
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob(function(blob) {
            const formData = new FormData();
            formData.append('image', blob, 'outfit.jpg');
            formData.append('accessory', accessory);
            
            fetch('http://localhost:5002/apply_accessory', {
                method: 'POST',
                body: formData,
                signal: AbortSignal.timeout(5000)
            })
            .then(response => response.json())
            .then(data => {
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                if (data.image) {
                    const resultImg = new Image();
                    resultImg.onload = function() {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(resultImg, 0, 0, canvas.width, canvas.height);
                    };
                    resultImg.onerror = function() {
                        console.error('Error loading processed image');
                        displayNotification('Error loading processed image', 3000);
                    };
                    resultImg.src = data.image;
                } else {
                    console.error('No image in response:', data);
                    displayNotification('Failed to apply accessory', 3000);
                }
            })
            .catch(error => {
                console.error('Error applying accessory:', error);
                displayNotification('Error applying accessory. Is the server running?', 3000);
                
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
                
                // Service might have gone down, recheck
                checkBackendServices();
            });
        }, 'image/jpeg', 0.95);
    };
    
    // Use the originalOutfitImage variable which now contains the correct image source
    img.src = originalOutfitImage;
}

// Create a completely separate notification function to avoid conflicts
function displayNotification(message, duration) {
    console.log(message); // Always log to console
    
    // Create a new message div each time to avoid any state issues
    const messageDiv = document.createElement('div');
    messageDiv.className = 'notification-message';
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
    
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 500);
    }, duration || 3000);
}

// For backward compatibility - completely separate from displayNotification
function showErrorMessage(message, duration) {
    console.log("Error: " + message);
    
    // Use the native window.alert for simplicity to avoid any recursion
    if (duration > 5000) {
        window.alert(message);
        return;
    }
    
    const messageElement = document.createElement('div');
    messageElement.className = 'error-notification';
    messageElement.style.position = 'fixed';
    messageElement.style.bottom = '20px'; // Different position to avoid conflicts
    messageElement.style.left = '50%';
    messageElement.style.transform = 'translateX(-50%)';
    messageElement.style.padding = '10px 20px';
    messageElement.style.backgroundColor = 'rgba(200, 0, 0, 0.7)';
    messageElement.style.color = 'white';
    messageElement.style.borderRadius = '5px';
    messageElement.style.zIndex = '9999';
    
    messageElement.textContent = message;
    document.body.appendChild(messageElement);
    
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.parentNode.removeChild(messageElement);
        }
    }, duration || 3000);
}