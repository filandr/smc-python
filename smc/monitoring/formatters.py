"""
Helper formatters
"""
from datetime import datetime, timedelta

    
class TimeFormat(object):
    """
    Construct a time format to control the start and end times
    for a query. If unspecified, results will be limited by the
    fetch size quantity only. If providing start_time and end_time
    in the constructor, values should be datetime objects converted
    to milliseconds. Helper methods are provided to simplify adding
    time based filters once the instance is constructed.
    
    :param int start_time: datetime object in milliseconds. Where to
        start the query in time. If your search should go backwards
        in time, specify the oldest time/date in start_time.
    :param int end_time: datetime object in milliseconds. Where to
        end the query in time. If search should end with current,
        use datetime.now()*1000.
    """
    def __init__(self, start_time=0, end_time=0):
        self.data = {
            'start_ms': start_time,
            'end_ms': end_time
        }
    
    def _timedelta_from_now(self, _timedelta):
        now = datetime.now()
        start_time = int((now - _timedelta).strftime('%s'))*1000
        end_time = int(now.strftime('%s'))*1000
        self.data.update(
            start_ms=start_time,
            end_ms=end_time)
        return self
    
    def last_five_minutes(self):
        """
        Add time from current time back 5 minutes
        """
        return self._timedelta_from_now(
            timedelta(minutes=5))

    def last_fifteen_minutes(self):
        """
        Add time from current time back 15 minutes
        """
        return self._timedelta_from_now(
            timedelta(minutes=15))
        
    def last_thirty_minutes(self):
        """
        Add time from current time back 30 minutes
        """
        return self._timedelta_from_now(
            timedelta(minutes=30))
    
    def last_hour(self):
        """
        Add time from current time back 1 hour
        """
        return self._timedelta_from_now(
            timedelta(minutes=60))
    
    def last_day(self):
        """
        Add time filter from current time back 1 day
        """
        return self._timedelta_from_now(
            timedelta(days=1))
    
    def last_week(self):
        """
        Add time filter from current time back 7 days.
        """
        return self._timedelta_from_now(
            timedelta(days=7))
    
    def custom_range(self, start_time, end_time=None):
        """
        Provide a custom range for the search query.
        ``start`` should be the oldest date, and ``end`` the
        most current. If ``end`` is not provided, datetime.now()
        is used.
        
        Last two minutes from current (py2)::
        
            now = datetime.now()
            start_time = int((now - timedelta(minutes=2)).strftime('%s'))*1000
        
        Specific start time (py2)::
        
            p2time = datetime.strptime("1.8.2017 08:26:42,76", "%d.%m.%Y %H:%M:%S,%f").strftime('%s')
            p2time = int(s)*1000
            
        Same start time (py3)::
        
            p3time = datetime.strptime("1.8.2017 08:40:42,76", "%d.%m.%Y %H:%M:%S,%f")
            p3time.timestamp() * 1000)
        
        :param int start: search start time in milliseconds
        :param int end: search end time in milliseconds
        """
        if end_time is None:
            end_time = int(datetime.now().strftime('%s'))*1000 # Latest
        
        self.data.update(
            start_ms=start_time,
            end_ms=end_time)
        return self

    