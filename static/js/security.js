// static/js/security.js

// State management
let openDetailStates = new Set();
let isUpdating = false;

// Loading state management
function showLoading() {
    document.querySelector('.loading-overlay').classList.add('active');
}

function hideLoading() {
    document.querySelector('.loading-overlay').classList.remove('active');
}

function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    document.getElementById('lastUpdate').textContent = `Last updated: ${timeString}`;
}

// Toggle details section
function toggleDetails(elementId) {
    const detailsElement = document.getElementById(`details-${elementId}`);
    const button = document.querySelector(`[data-recommendation-id="${elementId}"]`);
    
    if (detailsElement.style.display === 'none' || !detailsElement.style.display) {
        detailsElement.style.display = 'block';
        button.textContent = 'Show Less';
        openDetailStates.add(elementId);
    } else {
        detailsElement.style.display = 'none';
        button.textContent = 'Show More';
        openDetailStates.delete(elementId);
    }
}

// async function to fetch and display the firmware update information
let firmwareCheckInProgress = false;

async function checkFirmwareUpdate(ip) {
    if (firmwareCheckInProgress) return;
    
    try {
        firmwareCheckInProgress = true;
        const response = await fetch(`/check_firmware_update/${ip}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        let messageHtml = '';
        if (data.status === 'success') {
            messageHtml = `
                <div class="p-4 bg-green-50 rounded-lg">
                    <h3 class="font-bold text-green-800">Available Firmware Version</h3>
                    <pre class="mt-2 text-sm text-green-700">${JSON.stringify(data.data, null, 2)}</pre>
                </div>
            `;
        } else {
            messageHtml = `
                <div class="p-4 bg-yellow-50 rounded-lg">
                    <h3 class="font-bold text-yellow-800">No Firmware Updates</h3>
                    <p class="mt-2 text-sm text-yellow-700">${data.message}</p>
                </div>
            `;
        }
        
        document.getElementById('firmwareUpdatePanel').innerHTML = messageHtml;
        
    } catch (error) {
        document.getElementById('firmwareUpdatePanel').innerHTML = `
            <div class="p-4 bg-red-50 rounded-lg">
                <h3 class="font-bold text-red-800">Error</h3>
                <p class="mt-2 text-sm text-red-700">Error fetching firmware update information: ${error.message}</p>
            </div>
        `;
        console.error('Error:', error);
    } finally {
        firmwareCheckInProgress = false;
    }
}
// Main update function
async function updateSecurity(showLoadingIndicator = false) {
    if (isUpdating) return;
    isUpdating = true;

    if (showLoadingIndicator) {
        showLoading();
    }

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const deviceIp = urlParams.get('device');
        const endpoint = deviceIp 
            ? `/api/device/${deviceIp}/security`
            : '/api/security/recommendations';

        const response = await fetch(endpoint);
        const recommendations = await response.json();
        
        const recommendationsPromises = recommendations.map(async (rec, index) => {
            const detailedRecs = await loadDetailedRecommendations(rec.port, rec.service, rec.current_state, rec.device_ip);
            // Only check firmware for the specific device if on device page
            if (deviceIp && deviceIp === rec.device_ip) {
                await checkFirmwareUpdate(rec.device_ip);
            }
            return generateRecommendationHTML(rec, index, detailedRecs);
        });

        const recommendationsHtml = (await Promise.all(recommendationsPromises)).join('');
        document.getElementById('securityRecommendations').innerHTML = recommendationsHtml;
        updateLastUpdateTime();
    } catch (error) {
        console.error('Error updating security recommendations:', error);
    } finally {
        isUpdating = false;
        hideLoading();
    }
}

// HTML generation function
function generateRecommendationHTML(rec, index, detailedRecs) {
    const borderClass = rec.status === 'critical' ? 'border-red-500' : 'border-yellow-500';
    
    const detailsHtml = detailedRecs ? `
        <div id="details-${index}" class="mt-4 p-4 bg-gray-50 rounded-lg" style="display: ${openDetailStates.has(index.toString()) ? 'block' : 'none'}">
            <h3 class="font-bold text-lg mb-4">${detailedRecs.title}</h3>
            ${detailedRecs.steps.map(step => `
                <div class="mb-4">
                    <h4 class="font-bold mb-2">${step.title}</h4>
                    <ul class="list-disc pl-5 space-y-2">
                        ${step.items.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `).join('')}
        </div>
    ` : '';

    return `
        <div class="recommendation-card border-l-4 ${borderClass} bg-white rounded-lg shadow-sm p-6">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="font-bold text-lg">${rec.device_name} (${rec.device_ip}:${rec.port})</h3>
                </div>
                <div class="text-right">
                    <p class="text-sm text-gray-500">Service</p>
                    <p class="font-medium">${rec.service}</p>
                </div>
            </div>
            
            <div class="mt-4">
                <h4 class="font-bold text-gray-700">Current Status:</h4>
                <p class="mt-1 text-gray-600">${rec.current_state}</p>
            </div>
            
            <div class="mt-4">
                <h4 class="font-bold text-gray-700">Recommendation:</h4>
                <p class="mt-1 text-gray-600">${rec.recommendation}</p>
            </div>
            
            ${detailedRecs ? `
                <button 
                    onclick="toggleDetails('${index}')"
                    class="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    data-recommendation-id="${index}">
                    ${openDetailStates.has(index.toString()) ? 'Show Less' : 'Show More'}
                </button>
            ` : ''}
            ${detailsHtml}
        </div>
    `;
}

// Manual refresh handler
function manualRefresh() {
    updateSecurity(true);
}

// Update the loadDetailedRecommendations function
async function loadDetailedRecommendations(port, service, current_state, deviceIp) {
    try {
        let recommendationFile = null;
        
        // Check for HTTP on port 80
        if (port === 80 && service.toLowerCase() === 'http') {
            recommendationFile = '/static/recommendations/port_80_recommendations.json';
            return (await loadRecommendationFile(recommendationFile)).HTTP_to_HTTPS;
        }
        
        // Check for HTTPS on port 443 with SSL errors
        if (port === 443 && service.toLowerCase() === 'https' && 
            (current_state.toLowerCase().includes('ssl error') || 
             current_state.toLowerCase().includes('certificate') ||
             current_state.toLowerCase().includes('handshake failure'))) {
             recommendationFile = '/static/recommendations/port_443_ssl_error_recommendations.json';
             return (await loadRecommendationFile(recommendationFile)).SSL_ERROR;
        }
        
        // Check for unknown service
        if (service.toLowerCase() === 'unknown' || service.toLowerCase() === 'unidentified' || 
            service.toLowerCase() === '' || current_state.toLowerCase().includes('unknown service')) {
            recommendationFile = '/static/recommendations/unknown_port_recommendations.json';
            const recommendations = await loadRecommendationFile(recommendationFile);
            return replaceTemplateValues(recommendations.UNKNOWN_SERVICE, {
                port: port,
                ip_address: deviceIp
            });
        }
        
        // Check for unmodifiable device condition
        if (port === 443 && service.toLowerCase() === 'https' &&
            current_state.toLowerCase().includes('timed out') ||
            current_state.toLowerCase().includes('error') ||
            current_state.toLowerCase().includes('refused') ||
            current_state.toLowerCase().includes('unmodifiable') || 
            current_state.toLowerCase().includes('cannot modify') || 
            current_state.toLowerCase().includes('no configuration access')) {
            recommendationFile = '/static/recommendations/reverse_proxy_recommendations.json';
            const recommendations = await loadRecommendationFile(recommendationFile);
            return replaceTemplateValues(recommendations.UNMODIFIABLE_DEVICE, {
                port: port,
                ip_address: deviceIp,
                domain: `${deviceIp.split('.').join('-')}.example.com` // Example domain name generation
            });
        }
        
        return null;
    } catch (error) {
        console.error('Error loading recommendations:', error);
        return null;
    }
}

// Helper function to load recommendation files
async function loadRecommendationFile(path) {
    const response = await fetch(path);
    return await response.json();
}

// Helper function to replace template values in recommendations
function replaceTemplateValues(recommendations, values) {
    const replacedRecs = JSON.parse(JSON.stringify(recommendations)); // Deep clone
    
    // Replace [port] and [ip_address] in all items
    replacedRecs.steps.forEach(step => {
        step.items = step.items.map(item => {
            let replacedItem = item;
            Object.entries(values).forEach(([key, value]) => {
                replacedItem = replacedItem.replace(`[${key}]`, value);
            });
            return replacedItem;
        });
    });
    
    return replacedRecs;
}

// Call this function when loading the security page
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const deviceIp = urlParams.get('device');
    checkFirmwareUpdate(deviceIp);
});

// Initial update and set interval
updateSecurity();
setInterval(() => updateSecurity(), 10000);