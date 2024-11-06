// static/js/dashboard.js

let charts = {};

function initializeCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: true,
        animation: {
            duration: 300
        }
    };

    // Traffic Chart
    const trafficCtx = document.getElementById('trafficChart');
    if (trafficCtx) {
        charts.trafficChart = new Chart(trafficCtx, {
            type: 'pie',
            data: {
                labels: ['Encrypted', 'Unencrypted'],
                datasets: [{
                    data: [0, 0],
                    backgroundColor: ['#4CAF50', '#F44336']
                }]
            },
            options: commonOptions
        });
    }

    // Device Type Chart
    const deviceTypeCtx = document.getElementById('deviceTypeChart');
    if (deviceTypeCtx) {
        charts.deviceTypeChart = new Chart(deviceTypeCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Device Types',
                    data: [],
                    backgroundColor: '#3E95CD'
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Protocol Chart
    const protocolCtx = document.getElementById('protocolChart');
    if (protocolCtx) {
        charts.protocolChart = new Chart(protocolCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: ['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
                }]
            },
            options: commonOptions
        });
    }

    // Port Chart
    const portCtx = document.getElementById('portChart');
    if (portCtx) {
        charts.portChart = new Chart(portCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Connection Count',
                    data: [],
                    backgroundColor: '#3F51B5'
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Security Chart
    const securityCtx = document.getElementById('securityChart');
    if (securityCtx) {
        charts.securityChart = new Chart(securityCtx, {
            type: 'pie',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: ['#F44336', '#FF9800', '#4CAF50']
                }]
            },
            options: commonOptions
        });
    }

    // Protocol Timeline Chart
    const timelineCtx = document.getElementById('protocolTimelineChart');
    if (timelineCtx) {
        charts.protocolTimelineChart = new Chart(timelineCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'TCP',
                        data: [],
                        borderColor: '#2196F3',
                        fill: false
                    },
                    {
                        label: 'UDP',
                        data: [],
                        borderColor: '#4CAF50',
                        fill: false
                    },
                    {
                        label: 'ICMP',
                        data: [],
                        borderColor: '#FF9800',
                        fill: false
                    }
                ]
            },
            options: {
                ...commonOptions,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

function updateCharts() {
    Promise.all([
        fetch('/api/traffic-stats'),
        fetch('/api/packets/recent'),
        fetch('/api/security/recommendations')
    ])
    .then(responses => Promise.all(responses.map(r => r.json())))
    .then(([trafficStats, packets, security]) => {
        // Update Traffic Chart
        if (charts.trafficChart) {
            charts.trafficChart.data.datasets[0].data = [
                trafficStats.encrypted,
                trafficStats.unencrypted
            ];
            charts.trafficChart.update('none');
        }

        // Update Device Types Chart
        if (charts.deviceTypeChart) {
            charts.deviceTypeChart.data.labels = Object.keys(trafficStats.device_types);
            charts.deviceTypeChart.data.datasets[0].data = Object.values(trafficStats.device_types);
            charts.deviceTypeChart.update('none');
        }

        // Update Protocol Distribution Chart
        if (charts.protocolChart) {
            const protocolCounts = packets.reduce((acc, packet) => {
                acc[packet.protocol] = (acc[packet.protocol] || 0) + 1;
                return acc;
            }, {});
            charts.protocolChart.data.labels = Object.keys(protocolCounts);
            charts.protocolChart.data.datasets[0].data = Object.values(protocolCounts);
            charts.protocolChart.update('none');
        }

        // Update Port Chart
        if (charts.portChart) {
            const portCounts = packets.reduce((acc, packet) => {
                if (packet.dst_port) {
                    acc[packet.dst_port] = (acc[packet.dst_port] || 0) + 1;
                }
                return acc;
            }, {});
            const topPorts = Object.entries(portCounts)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 10);
            
            charts.portChart.data.labels = topPorts.map(([port]) => `Port ${port}`);
            charts.portChart.data.datasets[0].data = topPorts.map(([,count]) => count);
            charts.portChart.update('none');
        }

        // Update Security Overview Chart
        if (charts.securityChart) {
            const securityStatus = security.reduce((acc, rec) => {
                acc[rec.status] = (acc[rec.status] || 0) + 1;
                return acc;
            }, {});
            charts.securityChart.data.labels = Object.keys(securityStatus);
            charts.securityChart.data.datasets[0].data = Object.values(securityStatus);
            charts.securityChart.update('none');
        }

        // Update Protocol Timeline Chart
        if (charts.protocolTimelineChart) {
            const timeData = packets.reduce((acc, packet) => {
                const time = new Date(packet.timestamp).toLocaleTimeString();
                if (!acc[time]) {
                    acc[time] = { TCP: 0, UDP: 0, ICMP: 0 };
                }
                acc[time][packet.protocol] = (acc[time][packet.protocol] || 0) + 1;
                return acc;
            }, {});

            const times = Object.keys(timeData);
            charts.protocolTimelineChart.data.labels = times;
            
            ['TCP', 'UDP', 'ICMP'].forEach((protocol, index) => {
                charts.protocolTimelineChart.data.datasets[index].data = 
                    times.map(time => timeData[time][protocol] || 0);
            });
            
            charts.protocolTimelineChart.update('none');
        }
    })
    .catch(error => console.error('Error updating chart data:', error));
}

function updateDashboard() {
    // Update device stats
    fetch('/api/devices')
        .then(response => response.json())
        .then(devices => {
            const stats = {
                total: devices.length,
                active: devices.filter(d => new Date(d.last_seen) > new Date(Date.now() - 300000)).length,
                types: {}
            };
            
            devices.forEach(device => {
                stats.types[device.type] = (stats.types[device.type] || 0) + 1;
            });

            const statsHtml = `
                <p>Total Devices: ${stats.total}</p>
                <p>Active Devices: ${stats.active}</p>
                <div class="mt-2">
                    <h3 class="font-bold">Device Types:</h3>
                    ${Object.entries(stats.types)
                        .map(([type, count]) => `<p>${type}: ${count}</p>`)
                        .join('')}
                </div>
            `;
            document.getElementById('deviceStats').innerHTML = statsHtml;
        });

    // Update recent packets
    fetch('/api/packets/recent')
        .then(response => response.json())
        .then(packets => {
            const recentPacketsHtml = packets.slice(0, 5).map(packet => `
                <div class="border-b py-2">
                    <p class="text-sm text-gray-600">${new Date(packet.timestamp).toLocaleTimeString()}</p>
                    <p>${packet.src_ip}:${packet.src_port} → ${packet.dst_ip}:${packet.dst_port}</p>
                </div>
            `).join('');
            document.getElementById('recentPackets').innerHTML = recentPacketsHtml;
        });

    // Update charts
    updateCharts();
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    updateDashboard();
    setInterval(updateDashboard, 5000);
});