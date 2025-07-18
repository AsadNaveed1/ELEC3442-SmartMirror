
(function() {
    let _isVoicePolling = true;
    let _lastCommand = null;

    /**
     * Start polling the voice command API
     */
    function startVoiceCommandPolling() {
        if (!_isVoicePolling) {
            _isVoicePolling = true;
            showErrorMessage("Voice command activated! Say a command...", 3000);
            pollVoiceCommands();
        }
    }

    /**
     * Stop polling the voice command API
     */
    function stopVoiceCommandPolling() {
        _isVoicePolling = false;
        showErrorMessage("Voice command deactivated", 3000);
    }

    /**
     * Poll the voice command API for new commands
     */
    async function pollVoiceCommands() {
        if (!_isVoicePolling) return;
        
        try {
            console.log('Requesting voice command from backend...');
            const response = await fetch('http://localhost:5005/voice');
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Voice command response:', data);

            if (data.status === 'success' && data.command) {
                const command = data.command.toLowerCase();
                _lastCommand = command;
                
                console.log('Received voice command:', command);
                
                processVoiceCommand(command);
            } else if (data.status === 'error') {
                console.error('Voice recognition error:', data.message);
                showErrorMessage('Voice recognition error: ' + data.message, 3000);
            } else {
                console.log('No voice command detected, continuing to poll...');
            }
        } catch (error) {
            console.error('Error fetching voice command:', error);
        }
        
        if (_isVoicePolling) {
            setTimeout(pollVoiceCommands, 2000);
        }
    }

    /**
     * Process a voice command and trigger the appropriate action
     * @param {string} command - The voice command to process
     */
    function processVoiceCommand(command) {
        console.log('Processing voice command:', command);

        const safeCloseAllModals = function() {
            if (typeof window.closeAllModals === 'function') {
                console.log('Using defined closeAllModals function');
                window.closeAllModals();
            } else {
                console.log('Using fallback closeAllModals');
                const modals = document.getElementsByClassName('modal');
                for (let modal of modals) {
                    modal.style.display = 'none';
                }
            }
        };

        if (command.includes('weather') || command.includes('forecast')) {
            console.log('Opening weather modal');
            
            safeCloseAllModals();
            
            setTimeout(() => {
                const weatherModal = document.getElementById('weatherModal');
                
                if (weatherModal) {
                    console.log('Weather modal found, setting display to block');
                    weatherModal.style.display = 'block';
                    
                    weatherModal.offsetHeight;
                    
                    console.log('Weather modal display style set to:', weatherModal.style.display);
                    
                    if (typeof window.fetchWeatherAndOutfitData === 'function') {
                        console.log('Fetching weather data');
                        window.fetchWeatherAndOutfitData();
                    } else {
                        console.warn('fetchWeatherAndOutfitData function not found');
                    }
                    
                    setTimeout(() => {
                        if (weatherModal.style.display !== 'block') {
                            console.log('Weather modal not displaying, forcing again');
                            weatherModal.style.display = 'block';
                        }
                    }, 100);
                    
                } else {
                    console.error('Weather modal not found in DOM');
                    showErrorMessage("Weather modal not available", 3000);
                }
            }, 100);
        } 
        else if (command.includes('calendar') || command.includes('schedule')) {
            console.log('Opening calendar modal');
            
            safeCloseAllModals();
            
            setTimeout(() => {
                const calendarModal = document.getElementById('calendarModal');
                
                if (calendarModal) {
                    console.log('Calendar modal found, setting display to block');
                    calendarModal.style.display = 'block';
                    
                    calendarModal.offsetHeight;
                    
                    console.log('Calendar modal display style set to:', calendarModal.style.display);
                    
                    if (typeof window.updateCalendarModal === 'function') {
                        console.log('Updating calendar data');
                        window.updateCalendarModal();
                    } else {
                        console.warn('updateCalendarModal function not found');
                    }
                    
                    showErrorMessage("Calendar displayed", 3000);
                } else {
                    console.error('Calendar modal not found');
                    showErrorMessage("Calendar not available", 3000);
                }
            }, 100);
        } 
        else if (command.includes('outfit') || command.includes('clothes') || command.includes('wear')) {
            console.log('Opening outfit modal');
            
            safeCloseAllModals();
            
            setTimeout(() => {
                const outfitModal = document.getElementById('outfitModal');
                
                if (outfitModal) {
                    console.log('Outfit modal found, setting display to block');
                    outfitModal.style.display = 'block';
                    
                    outfitModal.offsetHeight;
                    
                    console.log('Outfit modal display style set to:', outfitModal.style.display);
                    
                    if (typeof window.fetchOutfitData === 'function') {
                        console.log('Fetching outfit data');
                        window.fetchOutfitData();
                    } else {
                        console.warn('fetchOutfitData function not found');
                    }
                    
                    showErrorMessage("Outfit recommendations displayed", 3000);
                } else {
                    console.error('Outfit modal not found');
                    showErrorMessage("Outfit recommendations not available", 3000);
                }
            }, 100);
        } 
        else if (command.includes('music') || command.includes('play')) {
            console.log('Opening music modal');
            
            safeCloseAllModals();
            
            setTimeout(() => {
                const musicModal = document.getElementById('musicModal');
                
                if (musicModal) {
                    console.log('Music modal found, setting display to block');
                    musicModal.style.display = 'block';
                    
                    musicModal.offsetHeight;
                    
                    console.log('Music modal display style set to:', musicModal.style.display);
                    
                    const emotionTag = document.getElementById('emotion-tag');
                    if (emotionTag) {
                        const currentEmotion = emotionTag.textContent.replace('Emotion: ', '');
                        const musicMood = document.getElementById('music-mood');
                        if (musicMood) {
                            musicMood.textContent = currentEmotion;
                        }
                    }
                    
                    if (window.musicPlayer && window.musicPlayer.paused) {
                        window.musicPlayer.play().catch(err => console.error("Music playback error:", err));
                    }
                    
                    showErrorMessage("Music recommendations displayed", 3000);
                } else {
                    console.error('Music modal not found');
                    showErrorMessage("Music not available", 3000);
                }
            }, 100);
        } 
        else if (command.includes('face') || command.includes('emotion') || command.includes('look')) {
            console.log('Performing face and emotion recognition');
            
            safeCloseAllModals();
            
            setTimeout(() => {
                if (typeof window.detectFaceAndEmotion === 'function') {
                    console.log('Calling face detection function');
                    window.detectFaceAndEmotion();
                    showErrorMessage("Detecting face and emotion...", 3000);
                } else {
                    console.error('detectFaceAndEmotion function not found');
                    showErrorMessage("Face detection not available", 3000);
                }
            }, 100);
        }
        else if (command.includes('accessories')) {
            console.log('Opening accessories modal');
            
            safeCloseAllModals();
            
            setTimeout(() => {
                if (typeof window.openAccessoriesModal === 'function') {
                    console.log('Calling accessories modal function');
                    window.openAccessoriesModal();
                    showErrorMessage("Virtual accessories opened", 3000);
                } else {
                    console.error('openAccessoriesModal function not found');
                    showErrorMessage('Accessories feature not available', 3000);
                }
            }, 100);
        }
        else if (command.includes('stop') || command.includes('close') || command.includes('exit') || command.includes('turn off')) {
            console.log('Closing modals');
            safeCloseAllModals();
            showErrorMessage("Closed all open windows", 3000);
            
            if (command.includes('stop voice') || command.includes('stop listening')) {
                stopVoiceCommandPolling();
            }
        }
        else {
            showErrorMessage(`Unknown command: ${command}`, 3000);
        }
    }

    /**
     * Check if a voice command service is available
     */
    function checkVoiceCommandService() {
        fetch('http://localhost:5005/status', { 
            signal: AbortSignal.timeout(2000) 
        })
        .then(response => {
            if (!response.ok) throw new Error('Service unavailable');
            return response.json();
        })
        .then(data => {
            console.log('Voice command service status:', data);
            startVoiceCommandPolling();
        })
        .catch(error => {
            console.error('Voice command service unavailable:', error);
            showErrorMessage('Voice commands unavailable. Start the service first.', 5000);
            _isVoicePolling = false;
        });
    }

    /**
     * Helper function to check if a modal is open
     */
    function isModalOpen(modalId) {
        const modal = document.getElementById(modalId);
        return modal && modal.style.display === 'block';
    }

    function showErrorMessage(message, duration) {
        console.log("Voice Integration Message: " + message);
        
        if (typeof window.showErrorMessage === 'function') {
            window.showErrorMessage(message, duration);
            return;
        }
        
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
            document.body.appendChild(messageDiv);
        }
        
        messageDiv.textContent = message;
        messageDiv.style.opacity = '1';
        
        setTimeout(() => {
            messageDiv.style.opacity = '0';
        }, duration || 3000);
    }

    function initializeVoiceIntegration() {
        console.log('Voice integration initialized');
        
        const modalIds = ['weatherModal', 'calendarModal', 'outfitModal', 'musicModal', 'accessoriesModal'];
        modalIds.forEach(id => {
            const modal = document.getElementById(id);
            console.log(`Modal '${id}' exists in DOM: ${modal !== null}`);
            if (modal) {
                console.log(`Modal '${id}' current display style: ${modal.style.display}`);
            }
        });
        
        console.log('fetchWeatherAndOutfitData function exists:', typeof window.fetchWeatherAndOutfitData === 'function');
        console.log('updateCalendarModal function exists:', typeof window.updateCalendarModal === 'function');
        console.log('fetchOutfitData function exists:', typeof window.fetchOutfitData === 'function');
        console.log('detectFaceAndEmotion function exists:', typeof window.detectFaceAndEmotion === 'function');
        console.log('openAccessoriesModal function exists:', typeof window.openAccessoriesModal === 'function');
        
        const voiceIndicator = document.createElement('div');
        voiceIndicator.id = 'voice-indicator';
        voiceIndicator.className = 'voice-indicator';
        voiceIndicator.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceIndicator.title = 'Voice Commands Active';
        document.body.appendChild(voiceIndicator);
        
        const style = document.createElement('style');
        style.textContent = `
            .voice-indicator {
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: rgba(0, 0, 0, 0.6);
                color: #4fc3f7;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                cursor: pointer;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(79, 195, 247, 0.4); }
                70% { box-shadow: 0 0 0 10px rgba(79, 195, 247, 0); }
                100% { box-shadow: 0 0 0 0 rgba(79, 195, 247, 0); }
            }
            
            .voice-indicator.disabled {
                color: #ff5252;
                animation: none;
                opacity: 0.7;
            }
        `;
        document.head.appendChild(style);
        
        voiceIndicator.addEventListener('click', function() {
            if (_isVoicePolling) {
                stopVoiceCommandPolling();
                voiceIndicator.classList.add('disabled');
            } else {
                startVoiceCommandPolling();
                voiceIndicator.classList.remove('disabled');
            }
        });
        
        const weatherWidget = document.getElementById('weather-widget');
        if (weatherWidget) {
            weatherWidget.addEventListener('click', function() {
                console.log('Weather widget clicked, should open modal');
                const weatherModal = document.getElementById('weatherModal');
                if (weatherModal) {
                    if (typeof window.closeAllModals === 'function') {
                        window.closeAllModals();
                    }
                    weatherModal.style.display = 'block';
                    console.log('Weather modal display style after click:', weatherModal.style.display);
                }
            });
        }
        
        checkVoiceCommandService();
        
        pollVoiceCommands();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeVoiceIntegration);
    } else {
        initializeVoiceIntegration();
    }

    window.debugProcessVoiceCommand = function(command) {
        console.log('Debug processing voice command:', command);
        processVoiceCommand(command);
        return true;
    };

    window.startVoiceCommandPolling = startVoiceCommandPolling;
    window.stopVoiceCommandPolling = stopVoiceCommandPolling;
    window.processVoiceCommand = processVoiceCommand;
    window.pollVoiceCommands = pollVoiceCommands;
})();