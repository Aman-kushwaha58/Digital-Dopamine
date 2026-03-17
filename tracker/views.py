# tracker/views.py
import datetime
import io
import csv
from datetime import timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg, Sum
from django.db.models.functions import ExtractWeekDay
from django.utils import timezone
from .models import UserActivity
from .data_collector import DataCollector
from django.db import connection
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

@csrf_exempt
def dashboard(request):
    """Main dashboard view"""
    return render(request, 'tracker/dashboard.html')

@csrf_exempt
def get_recent_activity(request):
    """API endpoint to get recent activity data"""
    activities = UserActivity.objects.all().order_by('-timestamp')[:50]
    collector = get_collector()

    data = {
        'activities': [
            {
                'timestamp': timezone.localtime(activity.timestamp).strftime('%H:%M:%S'),
                'app': activity.active_app,
                'category': get_category(activity.active_app),
                'typing_speed': activity.typing_speed,
                'app_switches': activity.app_switch_count,
                'dopamine_score': activity.dopamine_score,
                'status': activity.status
            }
            for activity in activities
        ],
        'total_records': UserActivity.objects.count(),
        'current_app': activities[0].active_app if activities.exists() else "None"
    }

    return JsonResponse(data)

@csrf_exempt
def start_tracking(request):
    """API endpoint to start data collection"""
    collector = get_collector()
    if not collector.is_collecting:
        collector.start_collection()
        message = 'Data collection started'
    else:
        message = 'Data collection is already running'

    return JsonResponse({
        'status': 'started',
        'message': message
    })

@csrf_exempt
def stop_tracking(request):
    """API endpoint to stop data collection"""
    collector = get_collector()
    if collector.is_collecting:
        collector.stop_collection()
        message = 'Data collection stopped'
    else:
        message = 'Data collection is not running'

    return JsonResponse({
        'status': 'stopped',
        'message': message
    })

@csrf_exempt
def clear_history(request):
    """API endpoint to clear all activity history"""
    if request.method == 'POST':
        UserActivity.objects.all().delete()
        return JsonResponse({'status': 'success', 'message': 'History cleared'})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)

@csrf_exempt
def statistics(request):
    """Get overall statistics"""
    today = timezone.localtime(timezone.now()).date()
    activities = UserActivity.objects.all()
    today_activities = activities.filter(timestamp__date=today)

    if today_activities.exists():
        total = today_activities.count()
        
        # Status counts including Neutral
        status_counts = dict(today_activities.values('status').annotate(count=Count('id')).values_list('status', 'count'))
        
        focused = status_counts.get('Focused', 0) + status_counts.get('Deep Focus Session', 0)
        distracted = status_counts.get('Distracted', 0) + status_counts.get('DOPAMINE SPIKE DETECTED', 0)
        doomscrolling = status_counts.get('Doomscrolling', 0) + status_counts.get('High Dopamine Risk', 0)
        neutral = status_counts.get('Neutral', 0)
        
        total_active = focused + distracted + doomscrolling + neutral

        aggregates = today_activities.aggregate(
            avg_dopamine=Avg('dopamine_score'),
            avg_typing_speed=Avg('typing_speed')
        )
        avg_dopamine = aggregates['avg_dopamine'] or 0
        avg_typing_speed = aggregates['avg_typing_speed'] or 0

        # Efficient night usage calculation (7s intervals)
        night_seconds = today_activities.filter(timestamp__hour__in=[23, 0, 1, 2]).count() * 7
        late_night_usage = format_time(night_seconds)

        # Daily report
        focus_seconds = focused * 7
        doomscroll_seconds = doomscrolling * 7
        
        distraction_by_hour = today_activities.filter(status__in=['Distracted', 'Doomscrolling', 'High Dopamine Risk']).values('timestamp__hour').annotate(count=Count('timestamp__hour')).order_by('-count')
        peak_distraction_time = f"{distraction_by_hour[0]['timestamp__hour'] % 12 or 12} {'PM' if distraction_by_hour[0]['timestamp__hour'] >= 12 else 'AM'}" if distraction_by_hour else "N/A"
        
        top_apps_list = get_top_apps()
        most_used_app = top_apps_list[0]['active_app'] if top_apps_list else "None"

        # Distraction alert (last 10 mins)
        ten_min_ago = timezone.now() - timedelta(minutes=10)
        distraction_alert = today_activities.filter(timestamp__gte=ten_min_ago, status__in=['Distracted', 'DOPAMINE SPIKE DETECTED']).count() >= 3

        # Weekly report
        week_ago = timezone.now() - timedelta(days=7)
        weekly_activities = UserActivity.objects.filter(timestamp__gte=week_ago)
        weekly_total = weekly_activities.count()
        
        if weekly_total > 0:
            weekly_focus_count = weekly_activities.filter(status__in=['Focused', 'Deep Focus Session']).count()
            weekly_focus_score = (weekly_focus_count / weekly_total * 100)
            
            # Day analysis
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            focus_by_day = weekly_activities.filter(status__in=['Focused', 'Deep Focus Session']).annotate(day=ExtractWeekDay('timestamp')).values('day').annotate(count=Count('day')).order_by('-count')
            most_productive_day = days[focus_by_day[0]['day'] - 1] if focus_by_day else 'N/A'
            
            distracted_by_day = weekly_activities.filter(status__in=['Distracted', 'DOPAMINE SPIKE DETECTED']).annotate(day=ExtractWeekDay('timestamp')).values('day').annotate(count=Count('day')).order_by('-count')
            worst_day = days[distracted_by_day[0]['day'] - 1] if distracted_by_day else 'N/A'
        else:
            weekly_focus_score = 0
            most_productive_day = 'N/A'
            worst_day = 'N/A'

        # Today's insights
        total_switches = today_activities.aggregate(total=Sum('app_switch_count'))['total'] or 0
        total_minutes = float(total * 7 / 60)
        switches_per_minute = total_switches / total_minutes if total_minutes > 0 else 0
        switches_every_minutes = round(float(1 / switches_per_minute), 1) if switches_per_minute > 0 else 0

        productive_by_hour = today_activities.filter(status__in=['Focused', 'Deep Focus Session']).values('timestamp__hour').annotate(count=Count('timestamp__hour')).order_by('-count')
        most_productive_time = f"{productive_by_hour[0]['timestamp__hour'] % 12 or 12} {'PM' if productive_by_hour[0]['timestamp__hour'] >= 12 else 'AM'}" if productive_by_hour else "N/A"

        doomscroll_by_hour = today_activities.filter(status__in=['Doomscrolling', 'High Dopamine Risk']).values('timestamp__hour').annotate(count=Count('timestamp__hour')).order_by('-count')
        doomscroll_peak = f"at {doomscroll_by_hour[0]['timestamp__hour'] % 12 or 12} {'PM' if doomscroll_by_hour[0]['timestamp__hour'] >= 12 else 'AM'}" if doomscroll_by_hour else "N/A"

        # Timeline
        recent_dopamine = today_activities.order_by('-timestamp')[:50]
        dopamine_timeline = [timezone.localtime(a.timestamp).strftime('%H:%M:%S') for a in reversed(recent_dopamine)]
        dopamine_scores = [a.dopamine_score for a in reversed(recent_dopamine)]

        # Total active sessions for meaningful percentages
        total_active = focused + distracted + doomscrolling + neutral
        
        stats = {
            'total_sessions': total,
            'focused_percentage': (focused / total * 100) if total > 0 else 0,
            'distracted_percentage': (distracted / total * 100) if total > 0 else 0,
            'doomscrolling_percentage': (doomscrolling / total * 100) if total > 0 else 0,
            'neutral_percentage': (neutral / total * 100) if total > 0 else 0,
            'high_risk_percentage': 0, # Legacy support for UI
            'avg_dopamine_score': round(float(avg_dopamine), 2),
            'avg_typing_speed': round(float(avg_typing_speed), 2),
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
                'app_switch_frequency': f"{switches_every_minutes} mins" if switches_every_minutes > 0 else "N/A",
                'most_productive_time': most_productive_time,
                'doomscroll_peak': doomscroll_peak
            },
            'distraction_alert': distraction_alert,
            'top_apps': top_apps_list
        }
    else:
        stats = {
            'total_sessions': 0,
            'focused_percentage': 0,
            'distracted_percentage': 0,
            'doomscrolling_percentage': 0,
            'neutral_percentage': 0,
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
            'top_apps': []
        }

    return JsonResponse(stats)

def get_top_apps():
    return list(
        UserActivity.objects
        .values('active_app')
        .annotate(count=Count('active_app'))
        .order_by('-count')[:5]
    )

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
    if not app_name:
        return "neutral"
    
    for key, category in APP_CATEGORIES.items():
        if key in str(app_name).lower():
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
    if not canvas:
        return HttpResponse("ReportLab not installed. Please install with 'pip install reportlab'", status=500)
    
    today = timezone.now().date()
    activities = UserActivity.objects.filter(timestamp__date=today).order_by('-timestamp')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="activity_report_{today}.pdf"'

    if not letter or not canvas:
        return HttpResponse("PDF generation library (reportlab) not installed.", status=501)
        
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    height = float(height)

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Digital Dopamine Activity Report - {today}")
    
    # Header
    p.setFont("Helvetica-Bold", 10)
    y = height - 80
    p.drawString(50, y, "Time")
    p.drawString(150, y, "Application")
    p.drawString(300, y, "Category")
    p.drawString(400, y, "Score")
    p.drawString(450, y, "Status")
    
    p.line(50, y - 5, 550, y - 5)
    
    # Data
    p.setFont("Helvetica", 9)
    y -= 25
    
    for activity in activities:
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 9)
            y = height - 50.0
            
        category = get_category(activity.active_app)
        local_time = timezone.localtime(activity.timestamp).strftime('%H:%M:%S')
        
        p.drawString(50, y, local_time)
        app_name = str(activity.active_app or "Unknown")
        p.drawString(150, y, str(app_name)[0:25])
        p.drawString(300, y, category)
        p.drawString(400, y, str(activity.dopamine_score))
        p.drawString(450, y, str(activity.status))
        
        y -= 20

    p.save()
    return response

@csrf_exempt
def report_activity(request):
    """API endpoint for remote clients to submit activity data"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            app = data.get('app', 'Unknown')
            typing_speed = data.get('typing_speed', 0)
            switches = data.get('switches', 0)
            
            # Server-side re-categorization for better accuracy
            category = get_category(app)
            low_activity_apps = ["Desktop", "Browser", "File Explorer", "Terminal", "Unknown", ""]
            
            if category == 'productive':
                status = "Focused"
            elif category == 'dopamine':
                status = "Doomscrolling" if typing_speed < 10 else "Distracted"
            elif switches > 3:
                status = "Distracted"
            elif typing_speed < 5 and app not in low_activity_apps:
                status = "Doomscrolling"
            else:
                status = "Neutral"
                
            # Recalculate dopamine score on server
            raw_score = float(typing_speed * 0.2 + switches * 15)
            if category == 'dopamine': raw_score += 40
            score = int(min(100.0, raw_score))
            
            activity = UserActivity(
                active_app=app,
                typing_speed=typing_speed,
                app_switch_count=switches,
                dopamine_score=score,
                status=status
            )
            activity.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
