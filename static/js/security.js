// static/js/security.js
function updateSecurity() {
    fetch('/api/security/recommendations')
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
setInterval(updateSecurity, 10000); // for security.html
updateSecurity()