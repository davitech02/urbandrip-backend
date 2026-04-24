from flask import Blueprint, request, jsonify
from database import db
from models import Visitor
from datetime import datetime, timedelta
from sqlalchemy import func
from app import admin_required

visitors_bp = Blueprint('visitors', __name__)

@visitors_bp.route('/track', methods=['POST'])
def track_visitor():
    """Track a visitor"""
    try:
        data = request.get_json()
        
        visitor = Visitor(
            visitor_id=data.get('visitor_id'),
            page_url=data.get('page_url'),
            referrer=data.get('referrer'),
            device_type=data.get('device_type'),
            browser=data.get('browser'),
            ip_address=request.remote_addr
        )
        
        db.session.add(visitor)
        db.session.commit()
        
        return jsonify({'message': 'Visitor tracked'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@visitors_bp.route('/admin/stats', methods=['GET'])
@admin_required
def get_visitor_stats():
    """Get visitor statistics"""
    try:
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Total visits
        total_visits_today = Visitor.query.filter(Visitor.timestamp >= today).count()
        total_visits_week = Visitor.query.filter(Visitor.timestamp >= week_ago).count()
        total_visits_month = Visitor.query.filter(Visitor.timestamp >= month_ago).count()
        
        # Unique visitors
        unique_today = db.session.query(func.count(func.distinct(Visitor.visitor_id))).filter(
            Visitor.timestamp >= today
        ).scalar() or 0
        
        unique_month = db.session.query(func.count(func.distinct(Visitor.visitor_id))).filter(
            Visitor.timestamp >= month_ago
        ).scalar() or 0
        
        # Device split for pie chart
        device_stats = db.session.query(
            Visitor.device_type,
            func.count(Visitor.id).label('count')
        ).filter(Visitor.timestamp >= month_ago).group_by(Visitor.device_type).all()
        
        device_data = [
            {'name': stat[0] or 'Unknown', 'value': stat[1]}
            for stat in device_stats
        ]
        
        # Top pages for bar chart
        top_pages = db.session.query(
            Visitor.page_url,
            func.count(Visitor.id).label('count')
        ).filter(Visitor.timestamp >= month_ago).group_by(
            Visitor.page_url
        ).order_by(func.count(Visitor.id).desc()).limit(5).all()
        
        page_data = [
            {'name': stat[0], 'value': stat[1]}
            for stat in top_pages
        ]
        
        # Daily visits for last 7 days
        daily_visits = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            next_day = day + timedelta(days=1)
            count = Visitor.query.filter(
                Visitor.timestamp >= day,
                Visitor.timestamp < next_day
            ).count()
            daily_visits.append({
                'date': day.strftime('%Y-%m-%d'),
                'visits': count
            })
        
        return jsonify({
            'today_visits': total_visits_today,
            'week_visits': total_visits_week,
            'month_visits': total_visits_month,
            'unique_visitors': unique_month,
            'device_stats': device_data,
            'top_pages': page_data,
            'daily_visits': daily_visits
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@visitors_bp.route('/admin/recent', methods=['GET'])
@admin_required
def get_recent_visits():
    """Get recent visits"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        visits = Visitor.query.order_by(Visitor.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'visits': [visit.to_dict() for visit in visits]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
