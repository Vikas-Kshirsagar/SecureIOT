// static/js/security.js
function updateSecurity() {
    // Get device IP from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const deviceIp = urlParams.get('device');
    
    // Choose endpoint based on whether device parameter exists
    const endpoint = deviceIp 
        ? `/api/device/${deviceIp}/security`
        : '/api/security/recommendations';

    fetch(endpoint)
        .then(response => response.json())
        .then(recommendations => {
            const recommendationsHtml = recommendations.map(rec => `
                <div class="border-l-4 ${rec.status === 'critical' ? 'border-red-500' : 'border-yellow-500'} p-4">
                    <h3 class="font-bold">${rec.device_name} (${rec.device_ip}:${rec.port})</h3>
                    <p class="text-gray-600">${rec.service}</p>
                    <p class="mt-2">${rec.current_state}</p>
                    <p class="mt-2 font-semibold">${rec.recommendation}</p>
                </div>
            `).join('');
            document.getElementById('securityRecommendations').innerHTML = recommendationsHtml;
        });
}

setInterval(updateSecurity, 10000);
updateSecurity();
