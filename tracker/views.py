# tracker/views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import UserActivity
from django.views.decorators.csrf import csrf_exempt

def dashboard(request):
    """Main dashboard view"""
    return render(request, 'tracker/dashboard.html')

def get_recent_activity(request):
    """API endpoint to get recent activity data"""
    activities = UserActivity.objects.all().order_by('-timestamp')[:50]

    data = {
        'activities': [
            {
                'timestamp': activity.timestamp.strftime('%H:%M:%S'),
                'app': activity.active_app,
                'typing_speed': activity.typing_speed,
                'app_switches': activity.app_switch_count,
                'dopamine_score': activity.dopamine_score,
                'status': activity.status
            }
            for activity in activities
        ],
        'total_records': UserActivity.objects.count(),
        'current_app': "Unknown"
    }

    return JsonResponse(data)

@csrf_exempt
def start_tracking(request):
    """API endpoint to start data collection"""
    from .data_collector import DataCollector  # ✅ import INSIDE function

    collector = DataCollector()
    collector.start_collection()

    return JsonResponse({
        'status': 'started',
        'message': 'Data collection started'
    })

@csrf_exempt
def stop_tracking(request):
    """API endpoint to stop data collection"""
    # (Later you can manage shared state, for now keep simple)
    return JsonResponse({
        'status': 'stopped',
        'message': 'Data collection stopped'
    })

def statistics(request):
    """Get overall statistics"""
    activities = UserActivity.objects.all()

    if activities.exists():
        total = activities.count()
        focused = activities.filter(status='Focused').count()
        distracted = activities.filter(status='Distracted').count()
        doomscrolling = activities.filter(status='Doomscrolling').count()

        avg_dopamine = sum(a.dopamine_score for a in activities) / total
        avg_typing_speed = sum(a.typing_speed for a in activities) / total

        stats = {
            'total_sessions': total,
            'focused_percentage': (focused / total) * 100,
            'distracted_percentage': (distracted / total) * 100,
            'doomscrolling_percentage': (doomscrolling / total) * 100,
            'avg_dopamine_score': round(avg_dopamine, 2),
            'avg_typing_speed': round(avg_typing_speed, 2),
            'top_apps': get_top_apps()
        }
    else:
        stats = {
            'total_sessions': 0,
            'focused_percentage': 0,
            'distracted_percentage': 0,
            'doomscrolling_percentage': 0,
            'avg_dopamine_score': 0,
            'avg_typing_speed': 0,
            'top_apps': []
        }

    return JsonResponse(stats)

def get_top_apps():
    from django.db.models import Count
    return list(
        UserActivity.objects
        .values('active_app')
        .annotate(count=Count('active_app'))
        .order_by('-count')[:5]
    )
