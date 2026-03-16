# tracker/views.py
<<<<<<< HEAD
import datetime
import io
import csv
from datetime import timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg
from django.db.models.functions import ExtractWeekDay
from django.utils import timezone
from .models import UserActivity
from .data_collector import DataCollector
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:
    letter = None
    canvas = None

_collector_instance = None

def get_collector():
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = DataCollector()
    return _collector_instance
=======
from django.shortcuts import render
from django.http import JsonResponse
from .models import UserActivity
from django.views.decorators.csrf import csrf_exempt
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52

def dashboard(request):
    """Main dashboard view"""
    return render(request, 'tracker/dashboard.html')

def get_recent_activity(request):
    """API endpoint to get recent activity data"""
    activities = UserActivity.objects.all().order_by('-timestamp')[:50]
<<<<<<< HEAD
    collector = get_collector()
=======
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52

    data = {
        'activities': [
            {
<<<<<<< HEAD
                'timestamp': timezone.localtime(activity.timestamp).strftime('%H:%M:%S'),
                'app': activity.active_app,
                'category': get_category(activity.active_app),
=======
                'timestamp': activity.timestamp.strftime('%H:%M:%S'),
                'app': activity.active_app,
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
                'typing_speed': activity.typing_speed,
                'app_switches': activity.app_switch_count,
                'dopamine_score': activity.dopamine_score,
                'status': activity.status
            }
            for activity in activities
        ],
        'total_records': UserActivity.objects.count(),
<<<<<<< HEAD
        'current_app': collector.current_app if collector else "Unknown"
=======
        'current_app': "Unknown"
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
    }

    return JsonResponse(data)

@csrf_exempt
def start_tracking(request):
    """API endpoint to start data collection"""
<<<<<<< HEAD
    collector = get_collector()
    if not collector.is_collecting:
        collector.start_collection()
        message = 'Data collection started'
    else:
        message = 'Data collection is already running'

    return JsonResponse({
        'status': 'started',
        'message': message
=======
    from .data_collector import DataCollector  # ✅ import INSIDE function

    collector = DataCollector()
    collector.start_collection()

    return JsonResponse({
        'status': 'started',
        'message': 'Data collection started'
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
    })

@csrf_exempt
def stop_tracking(request):
    """API endpoint to stop data collection"""
<<<<<<< HEAD
    collector = get_collector()
    if collector.is_collecting:
        collector.stop_collection()
        message = 'Data collection stopped'
    else:
        message = 'Data collection is not running'

    return JsonResponse({
        'status': 'stopped',
        'message': message
=======
    # (Later you can manage shared state, for now keep simple)
    return JsonResponse({
        'status': 'stopped',
        'message': 'Data collection stopped'
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
    })

def statistics(request):
    """Get overall statistics"""
<<<<<<< HEAD
    today = timezone.now().date()
    activities = UserActivity.objects.all()
    today_activities = activities.filter(timestamp__date=today)

    if today_activities.exists():
        total = today_activities.count()
        focused = today_activities.filter(status='Focused').count()
        distracted = today_activities.filter(status='Distracted').count()
        doomscrolling = today_activities.filter(status='Doomscrolling').count()
        high_risk = today_activities.filter(status='High Dopamine Risk').count()
        deep_focus = today_activities.filter(status='Deep Focus Session').count()
        todays_spikes = today_activities.filter(status='DOPAMINE SPIKE DETECTED').count()

        aggregates = today_activities.aggregate(
            avg_dopamine=Avg('dopamine_score'),
            avg_typing_speed=Avg('typing_speed')
        )
        avg_dopamine = aggregates['avg_dopamine'] or 0
        avg_typing_speed = aggregates['avg_typing_speed'] or 0

        # Calculate late night usage (from all activities or today?) 
        # Keep focused seconds for today
        night_seconds = today_activities.filter(timestamp__hour__in=[23, 0, 1, 2]).count() * 5
        late_night_usage = format_time(night_seconds)

        # Daily report
        focus_seconds = today_activities.filter(status__in=['Focused', 'Deep Focus Session']).count() * 5
        doomscroll_seconds = today_activities.filter(status__in=['Doomscrolling', 'High Dopamine Risk']).count() * 5
        
        distraction_by_hour = today_activities.filter(status__in=['Distracted', 'DOPAMINE SPIKE DETECTED', 'Doomscrolling', 'High Dopamine Risk']).values('timestamp__hour').annotate(count=Count('timestamp__hour')).order_by('-count')
        if distraction_by_hour:
            peak_hour = distraction_by_hour[0]['timestamp__hour']
            peak_distraction_time = f"{peak_hour % 12 or 12} {'PM' if peak_hour >= 12 else 'AM'}"
        else:
            peak_distraction_time = "N/A"
        
        top_apps_list = get_top_apps()
        most_used_app = top_apps_list[0]['active_app'] if top_apps_list else "None"

        # Distraction alert
        recent_10_min = today_activities.filter(timestamp__gte=timezone.now() - timedelta(minutes=10))
        distraction_count = recent_10_min.filter(status__in=['Distracted', 'DOPAMINE SPIKE DETECTED']).count()
        distraction_alert = distraction_count >= 3

        # Weekly report
        week_ago = datetime.datetime.now() - timedelta(days=7)
        weekly_activities = activities.filter(timestamp__gte=week_ago)
        weekly_focus = weekly_activities.filter(status__in=['Focused', 'Deep Focus Session'])
        weekly_total = weekly_activities.count()
        weekly_focus_score = (weekly_focus.count() / weekly_total * 100) if weekly_total > 0 else 0

        focus_by_day = weekly_focus.annotate(day=ExtractWeekDay('timestamp')).values('day').annotate(count=Count('day')).order_by('-count')
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        most_productive_day = days[focus_by_day[0]['day'] - 1] if focus_by_day else 'N/A'

        weekly_distracted = weekly_activities.filter(status__in=['Distracted', 'DOPAMINE SPIKE DETECTED'])
        distracted_by_day = weekly_distracted.annotate(day=ExtractWeekDay('timestamp')).values('day').annotate(count=Count('day')).order_by('-count')
        worst_day = days[distracted_by_day[0]['day'] - 1] if distracted_by_day else 'N/A'

        # Today's insights
        total_switches = sum(a.app_switch_count for a in today_activities)
        total_hours = total * 5 / 3600
        switches_per_minute = total_switches / (total_hours * 60) if total_hours > 0 else 0
        switches_every_minutes = round(1 / switches_per_minute, 1) if switches_per_minute > 0 else 0

        productive_by_hour = today_activities.filter(status__in=['Focused', 'Deep Focus Session']).values('timestamp__hour').annotate(count=Count('timestamp__hour')).order_by('-count')
        if productive_by_hour:
            hour = productive_by_hour[0]['timestamp__hour']
            most_productive_time = f"{hour} AM" if hour < 12 else f"{hour % 12 or 12} PM"
        else:
            most_productive_time = "N/A"

        doomscroll_by_hour = today_activities.filter(status__in=['Doomscrolling', 'High Dopamine Risk']).values('timestamp__hour').annotate(count=Count('timestamp__hour')).order_by('-count')
        if doomscroll_by_hour:
            hour = doomscroll_by_hour[0]['timestamp__hour']
            doomscroll_peak = f"at {hour % 12 or 12} {'PM' if hour >= 12 else 'AM'}"
        else:
            doomscroll_peak = "N/A"

        # Dopamine timeline for today - more points for better graph
        recent_dopamine = today_activities.order_by('-timestamp')[:50]
        dopamine_timeline = [timezone.localtime(a.timestamp).strftime('%H:%M:%S') for a in reversed(recent_dopamine)]
        dopamine_scores = [a.dopamine_score for a in reversed(recent_dopamine)]
=======
    activities = UserActivity.objects.all()

    if activities.exists():
        total = activities.count()
        focused = activities.filter(status='Focused').count()
        distracted = activities.filter(status='Distracted').count()
        doomscrolling = activities.filter(status='Doomscrolling').count()

        avg_dopamine = sum(a.dopamine_score for a in activities) / total
        avg_typing_speed = sum(a.typing_speed for a in activities) / total
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52

        stats = {
            'total_sessions': total,
            'focused_percentage': (focused / total) * 100,
            'distracted_percentage': (distracted / total) * 100,
            'doomscrolling_percentage': (doomscrolling / total) * 100,
<<<<<<< HEAD
            'high_risk_percentage': (high_risk / total) * 100,
            'deep_work_sessions': deep_focus,
            'todays_dopamine_spikes': todays_spikes,
            'avg_dopamine_score': round(avg_dopamine, 2),
            'avg_typing_speed': round(avg_typing_speed, 2),
            'late_night_usage': late_night_usage,
            'dopamine_timeline': dopamine_timeline,
            'dopamine_scores': dopamine_scores,
            'daily_report': {
                'focus_time': format_time(focus_seconds),
                'doomscroll_time': format_time(doomscroll_seconds),
                'peak_distraction_time': peak_distraction_time,
                'most_used_app': most_used_app,
                'weekly_focus_score': round(weekly_focus_score, 1),
                'most_productive_day': most_productive_day,
                'worst_day': worst_day
            },
            'todays_insights': {
                'app_switch_frequency': f"every {switches_every_minutes} minutes",
                'most_productive_time': most_productive_time,
                'doomscroll_peak': doomscroll_peak
            },
            'distraction_alert': distraction_alert,
            'top_apps': top_apps_list
=======
            'avg_dopamine_score': round(avg_dopamine, 2),
            'avg_typing_speed': round(avg_typing_speed, 2),
            'top_apps': get_top_apps()
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
        }
    else:
        stats = {
            'total_sessions': 0,
            'focused_percentage': 0,
            'distracted_percentage': 0,
            'doomscrolling_percentage': 0,
<<<<<<< HEAD
            'high_risk_percentage': 0,
            'deep_work_sessions': 0,
            'todays_dopamine_spikes': 0,
            'avg_dopamine_score': 0,
            'avg_typing_speed': 0,
            'late_night_usage': '0h 0m',
            'dopamine_timeline': [],
            'dopamine_scores': [],
            'daily_report': {
                'focus_time': '0h 0m',
                'doomscroll_time': '0h 0m',
                'peak_distraction_time': 'N/A',
                'most_used_app': 'None',
                'weekly_focus_score': 0,
                'most_productive_day': 'N/A',
                'worst_day': 'N/A'
            },
            'todays_insights': {
                'app_switch_frequency': 'N/A',
                'most_productive_time': 'N/A',
                'doomscroll_peak': 'N/A'
            },
            'distraction_alert': False,
=======
            'avg_dopamine_score': 0,
            'avg_typing_speed': 0,
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
            'top_apps': []
        }

    return JsonResponse(stats)

def get_top_apps():
<<<<<<< HEAD
=======
    from django.db.models import Count
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
    return list(
        UserActivity.objects
        .values('active_app')
        .annotate(count=Count('active_app'))
        .order_by('-count')[:5]
    )
<<<<<<< HEAD

def get_category(app_name):
    APP_CATEGORIES = {
        "code": "productive",
        "visual studio": "productive",
        "vscode": "productive",
        "pycharm": "productive",
        "notepad": "productive",
        "word": "productive",
        "excel": "productive",
        "powerpoint": "productive",
        "youtube": "dopamine",
        "instagram": "dopamine",
        "whatsapp": "dopamine",
        "reddit": "dopamine",
        "facebook": "dopamine",
        "tiktok": "dopamine",
        "twitter": "dopamine",
        "netflix": "dopamine",
        "browser": "neutral",
        "explorer": "neutral",
        "terminal": "neutral"
    }
    for key, category in APP_CATEGORIES.items():
        if key in app_name.lower():
            return category
    return "neutral"

def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def export_csv(request):
    today = timezone.now().date()
    activities = UserActivity.objects.filter(timestamp__date=today).order_by('-timestamp')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="activity_report_{today}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'App', 'Category', 'Typing Speed', 'App Switches', 'Dopamine Score', 'Status'])

    for activity in activities:
        category = get_category(activity.active_app)
        local_time = timezone.localtime(activity.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([local_time, activity.active_app, category, activity.typing_speed, activity.app_switch_count, activity.dopamine_score, activity.status])

    return response

def export_pdf(request):
    # Explicitly check for None to satisfy linters
    if canvas is None or letter is None:
        return HttpResponse("ReportLab not installed. Please install with 'pip install reportlab'", status=500)
    
    today = timezone.now().date()
    activities = UserActivity.objects.filter(timestamp__date=today).order_by('-timestamp')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="activity_report_{today}.pdf"'

    # Use a local variable to satisfy linters about NoneType
    c_renderer = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Title
    c_renderer.setFont("Helvetica-Bold", 16)
    c_renderer.drawString(50, height - 50, f"Digital Dopamine Activity Report - {today}")
    
    # Header
    c_renderer.setFont("Helvetica-Bold", 10)
    y = height - 80
    c_renderer.drawString(50, y, "Time")
    c_renderer.drawString(150, y, "Application")
    c_renderer.drawString(300, y, "Category")
    c_renderer.drawString(400, y, "Score")
    c_renderer.drawString(450, y, "Status")
    
    c_renderer.line(50, y - 5, 550, y - 5)
    
    # Data
    c_renderer.setFont("Helvetica", 9)
    y -= 25
    
    for activity in activities:
        if y < 50:
            c_renderer.showPage()
            c_renderer.setFont("Helvetica", 9)
            y = height - 50
            
        category = get_category(activity.active_app)
        local_time = timezone.localtime(activity.timestamp).strftime('%H:%M:%S')
        
        c_renderer.drawString(50, y, local_time)
        c_renderer.drawString(150, y, str(activity.active_app)[:25])
        c_renderer.drawString(300, y, category)
        c_renderer.drawString(400, y, str(activity.dopamine_score))
        c_renderer.drawString(450, y, str(activity.status))
        
        y -= 20

    c_renderer.save()
    return response
=======
>>>>>>> 175a2eeb2c9abb5453e1acd8e58d1893e0848a52
