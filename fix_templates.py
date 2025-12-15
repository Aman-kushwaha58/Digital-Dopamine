# fix_templates.py - UPDATED WITH FULL DASHBOARD
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digital_dopamine_project.settings')
django.setup()

def create_full_dashboard():
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Dopamine - Screen Addiction Tracker</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; justify-content: center; }
        button { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .start-btn { background: #4CAF50; color: white; }
        .stop-btn { background: #f44336; color: white; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .activity-table { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .status-focused { color: #4CAF50; }
        .status-distracted { color: #FF9800; }
        .status-doomscrolling { color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Digital Dopamine Tracker</h1>
            <p>Monitor your screen addiction in real-time</p>
        </div>

        <div class="controls">
            <button class="start-btn" onclick="startTracking()">Start Tracking</button>
            <button class="stop-btn" onclick="stopTracking()">Stop Tracking</button>
        </div>

        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <div>Loading...</div>
                <div class="stat-value">-</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <canvas id="statusChart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="dopamineChart"></canvas>
            </div>
        </div>

        <div class="activity-table">
            <h3>Recent Activity</h3>
            <div id="activityTable">
                Loading activity data...
            </div>
        </div>
    </div>

    <script>
        let statusChart, dopamineChart;
        
        async function startTracking() {
            try {
                const response = await fetch('/api/start/', {method: 'POST'});
                const data = await response.json();
                alert(data.message);
            } catch (error) {
                alert('Error starting tracking: ' + error);
            }
        }

        async function stopTracking() {
            try {
                const response = await fetch('/api/stop/', {method: 'POST'});
                const data = await response.json();
                alert(data.message);
            } catch (error) {
                alert('Error stopping tracking: ' + error);
            }
        }

        async function loadStats() {
            try {
                const response = await fetch('/api/stats/');
                const stats = await response.json();
                
                document.getElementById('statsGrid').innerHTML = `
                    <div class="stat-card">
                        <div>Total Sessions</div>
                        <div class="stat-value">${stats.total_sessions}</div>
                    </div>
                    <div class="stat-card">
                        <div>Focused</div>
                        <div class="stat-value" style="color: #4CAF50">${stats.focused_percentage.toFixed(1)}%</div>
                    </div>
                    <div class="stat-card">
                        <div>Distracted</div>
                        <div class="stat-value" style="color: #FF9800">${stats.distracted_percentage.toFixed(1)}%</div>
                    </div>
                    <div class="stat-card">
                        <div>Doomscrolling</div>
                        <div class="stat-value" style="color: #f44336">${stats.doomscrolling_percentage.toFixed(1)}%</div>
                    </div>
                    <div class="stat-card">
                        <div>Avg Dopamine Score</div>
                        <div class="stat-value">${stats.avg_dopamine_score}</div>
                    </div>
                    <div class="stat-card">
                        <div>Avg Typing Speed</div>
                        <div class="stat-value">${stats.avg_typing_speed} KPM</div>
                    </div>
                `;

                updateCharts(stats);
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        function updateCharts(stats) {
            const statusCtx = document.getElementById('statusChart').getContext('2d');
            if (statusChart) statusChart.destroy();
            statusChart = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Focused', 'Distracted', 'Doomscrolling'],
                    datasets: [{
                        data: [stats.focused_percentage, stats.distracted_percentage, stats.doomscrolling_percentage],
                        backgroundColor: ['#4CAF50', '#FF9800', '#f44336']
                    }]
                }
            });

            const dopamineCtx = document.getElementById('dopamineChart').getContext('2d');
            if (dopamineChart) dopamineChart.destroy();
            dopamineChart = new Chart(dopamineCtx, {
                type: 'line',
                data: {
                    labels: ['1', '2', '3', '4', '5'],
                    datasets: [{
                        label: 'Dopamine Score',
                        data: [stats.avg_dopamine_score, stats.avg_dopamine_score-10, stats.avg_dopamine_score+5, stats.avg_dopamine_score-5, stats.avg_dopamine_score+2],
                        borderColor: '#2196F3',
                        tension: 0.1
                    }]
                }
            });
        }

        async function loadActivity() {
            try {
                const response = await fetch('/api/activity/');
                const data = await response.json();
                
                let tableHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>App</th>
                                <th>Typing Speed</th>
                                <th>App Switches</th>
                                <th>Dopamine Score</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.activities.forEach(activity => {
                    const statusClass = `status-${activity.status.toLowerCase()}`;
                    tableHTML += `
                        <tr>
                            <td>${activity.timestamp}</td>
                            <td>${activity.app}</td>
                            <td>${activity.typing_speed} KPM</td>
                            <td>${activity.app_switches}</td>
                            <td>${activity.dopamine_score}</td>
                            <td class="${statusClass}">${activity.status}</td>
                        </tr>
                    `;
                });
                
                tableHTML += '</tbody></table>';
                document.getElementById('activityTable').innerHTML = tableHTML;
            } catch (error) {
                console.error('Error loading activity:', error);
                document.getElementById('activityTable').innerHTML = 'Error loading activity data';
            }
        }

        function refreshData() {
            loadStats();
            loadActivity();
        }

        // Initial load
        refreshData();
        // Auto-refresh every 3 seconds
        setInterval(refreshData, 3000);
    </script>
</body>
</html>'''
    
    # Create the directory structure
    template_dir = os.path.join('tracker', 'templates', 'tracker')
    os.makedirs(template_dir, exist_ok=True)
    
    # Create the template file
    template_path = os.path.join(template_dir, 'dashboard.html')
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"✅ Full dashboard template created at: {template_path}")
    print("✅ Now run: python manage.py runserver")

if __name__ == "__main__":
    create_full_dashboard()