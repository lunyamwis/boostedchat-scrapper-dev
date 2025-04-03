import pandas as pd
from datetime import datetime, timedelta
from ..models import SalesRep, LeadAssignmentHistory
from django.db.models import Q

def no_consecutives(allocation):
    """Check that there are no consecutive list items"""
    for i in range(1, len(allocation)):
        if allocation[i] == allocation[i - 1]:
            return False
    return True


def no_more_than_x(allocation):
    """Check that no list item appears more than twice"""
    # import pdb;pdb.set_trace()
    for i in allocation:
        # print(i)

        if allocation.count(i) > 2:
            return False
    return True


def get_moving_average(sales_rep=None, influencer=None, days=7):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    assignments = LeadAssignmentHistory.objects.filter(
        Q(sales_rep=sales_rep,assigned_at__range=[start_date, end_date]) |
        Q(influencer=influencer,assigned_at__range=[start_date, end_date])).order_by('assigned_at')
    
    if not assignments:
        return 0
    
    data = {
        'date':[assignment.assigned_at.date() for assignment in assignments],
        'count': [1] * len(assignments)
    }

    df = pd.DataFrame(data)
    df = df.groupby('date').sum().reset_index()
    df.set_index('date',inplace=True)
    moving_average = df['count'].rolling(window=days).mean().iloc[-1]
    return moving_average if not pd.isna(moving_average) else 0
    