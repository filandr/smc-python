"""
A Query is the top level object used to construct parameters to make queries
to the SMC. 

"""

from smc.monitoring import websocket_query
from smc.monitoring.filters import TranslatedFilter, InFilter, AndFilter,\
    OrFilter, NotFilter, DefinedFilter
from smc.monitoring.formats import TextFormat
from smc.monitoring.formatters import TimeFormat


class Query(object):
    def __init__(self, definition=None, target=None,
                 format=None):  # @ReservedAssignment
        self.request = {
            'query': {},
            'fetch':{},
            'format':{
                'type':'texts',
                "field_format": "pretty"}}
        
        self.format = format if format is not None else TextFormat() #: TextFormat
        self.request.update(format=self.format.data)
        
        if target is not None:
            self.update_query(target=target)
        
        if definition is not None:
            self.update_query(definition=definition)
    
    @property
    def fetch_size(self):
        """
        Return the fetch size for this query. If fetch size is set
        to 0, the query will be aborted after the first response message.
        If the fetch_size is None, it is considered undefined which
        indicates there is no fetch bound set on this query (i.e. fetch
        all).
        
        ..note:: It is recommended to provide a fetch_size to limit the
            results when doing a 'stored' query.
        """
        if 'quantity' in self.request['fetch']:
            return self.request['fetch']['quantity']
    
    def update_query(self, **kw):
        self.request['query'].update(**kw)
        
    def update_filter(self, filt):
        """
        Update the query with a new filter.
        
        :param QueryFilter filt: change query to use new filter
        """
        self.update_query(filter=filt.filter)

    def execute(self, timeout=60, sock_timeout=5, **kw):
        """
        Execute the query with optional timeout.
        
        :param int timeout: specifies how long (in seconds) to wait when not
            receiving updates before closing the socket.
        :param int sock_timeout: specifies how long (in seconds) to sleep
            between recv calls when buffering data back to the client. For
            'current' queries, this value should be set to 1.
        :return: dict of list items. Returned dict key will either be 'fields'
            or 'records' with a list of dict as value/s. ``Fields`` will only
            be returned if detailed format is used and provides the field to
            name, ID mapping as the first payload reply.
        :rtype: dict(list)
        """
        try:
            if 'current' in self.request['query']['type']:
                sock_timeout = 1
        except KeyError:
            pass
        return websocket_query(self, timeout, sock_timeout, **kw)


def resolve_field_ids(ids):
    """
    Retrieve the log field details based on the LogField constant
    IDs. This provides a helper to view the fields representation
    when using different field_formats.
    
    :param list ids: list of log field IDs. Use LogField constants
        to simplify search.
    :return: raw dict representation of log fields 
    :rtype: list(dict)
    """
    request = {
        'fetch': {'quantity': 0},
        'format': {
            'type': 'detailed',
            'field_ids': ids},
        'query': {}
    }
    query = LogQuery()
    query.request = request
    for fields in query.execute():
        if 'fields' in fields:
            return fields['fields']
    return []
        
    
class LogQuery(Query):
    """
    Make a Log Query to the SMC to fetch stored log data or monitor logs in
    real time.
    There are a variety of settings you can configure on a query such as whether
    to execute a real time query versus a stored log fetch, time frame for the
    query, fetch size quantity, returned format style, specify which fields to
    return and adding filters to make a very specific query.

    To make queries, first obtain a query object and optionally (recommended)
    specify a maximum number of records to fetch (for non-real time fetches)::
    
        query = LogQuery(fetch_size=50)
    
    If real time logs are preferred and set fetch_type='current'
    (default is fetch 'stored' logs)::
    
        query = LogQuery(fetch_type='current')
    
    .. note:: Current style log queries are real-time and ignore the
        ``fetch_size``, ``time_range``, and ``backwards`` values if
        provided.

    You can also set a time_range on the query. There are convenience methods
    on a TimeFormat object to simplify time ranges. When using time ranges,
    it is strongly advisable to provide a timezone value equal to your client
    system::
    
        query = LogQuery(fetch_size=50)
        query.time_range.last_five_minutes()
        query.format.timezone('CST')
    
    Or using custom time ranges (time range start/end in milliseconds). Set
    the range on the query format object (or pass in a TimeFormat object
    to the query constructor)::
    
        t = datetime.strptime("4.8.2017 12:22:42,76", "%d.%m.%Y %H:%M:%S,%f").strftime('%s')
        t_in_ms = int(t)*1000
        
        query = LogQuery(fetch_size=50)
        query.time_range.custom_range(start_time=t_in_ms)
        query.format.timezone('CST')
    
    ..note:: If only start_time is provided in a custom_range time query, ``end_time``
        will use current time. Provide an end_time to limit the both ``start_time``
        and ``end_time``.
    
    Adding filters to a query can be achieved by using add_XX_filter convenience
    methods or by calling ``update_filter`` with the filter object.
    
    .. seealso:: :py:mod:`smc.monitoring.filters` for information on how to use and
        combine filters for a query.
    
    :param str fetch_type: 'stored' or 'current'
    :param int fetch_size: max number of logs to fetch
    :param bool backwards: return fetch backwards from most recent to
        oldest (True) or from oldest to most recent (False). (Default: True)
    :param format: A format object specifying format of return data
    :type format: format type from :py:mod:`smc.monitoring.formats`
        (default: TextFormat)
    :param TimeFormat time_range: time filter to add to query
    """
    location = '/monitoring/log/socket'
    
    def __init__(self, fetch_type='stored', fetch_size=None,
                 backwards=True, format=None, time_range=None):  # @ReservedAssignment
        super(LogQuery, self).__init__(format=format)
        
        fetch = {'quantity': fetch_size} if fetch_size is not None else {}
        fetch.update(backwards=backwards)

        self.time_range = time_range if time_range else TimeFormat() #: TimeFormat 
        
        query = self.time_range.data
        query.update(type=fetch_type)
        
        self.request.update(
            fetch=fetch,
            query=query)
    
    def add_translated_filter(self):
        """
        Add a translated filter to the query. A translated filter syntax
        uses the SMC expressions to build the filter. The simplest way to
        see the syntax is to create a filter in SMC under Logs view and
        right click->Show Expression.
        """
        filt = TranslatedFilter()
        self.update_filter(filt)
        return filt

    def add_in_filter(self, *values):
        """
        Add a filter using "IN" logic. This is typically the primary filter
        that will be used to find a match and generally combines other
        filters to get more granular. An example of usage would be searching
        for an IP address (or addresses) in a specific log field. Or looking
        for an IP address in multiple log fields.
        
        :param values: optional constructor args for
            :class:`smc.monitoring.filters.InFilter`
        :rtype: InFilter
        """
        filt = InFilter(*values)
        self.update_filter(filt)
        return filt

    def add_and_filter(self, *values):
        """    
        Add a filter using "AND" logic. This filter is useful when requiring
        multiple matches to evaluate to true. For example, searching for
        a specific IP address in the src field and another in the dst field.
        
        :param values: optional constructor args for
            :class:`smc.monitoring.filters.AndFilter`. Typically this is a
            list of InFilter expressions.
        :type: list(QueryFilter)
        :rtype: AndFilter
        """
        filt = AndFilter(*values)
        self.update_filter(filt)
        return filt

    def add_or_filter(self, *values):
        """
        Add a filter using "OR" logic. This filter is useful when matching
        on one or more criteria. For example, searching for IP 1.1.1.1 and
        service TCP/443, or IP 1.1.1.10 and TCP/80. Either pair would produce
        a positive match.
        
        :param values: optional constructor args for
            :class:`smc.monitoring.filters.OrFilter`. Typically this is a
            list of InFilter expressions.
        :type: list(QueryFilter)
        :rtype: OrFilter
        """
        filt = OrFilter(*values)
        self.update_filter(filt)
        return filt

    def add_not_filter(self, *value):
        """
        Add a filter using "NOT" logic. Typically this filter is used in
        conjunction with and AND or OR filters, but can be used by itself
        as well. This might be more useful as a standalone filter when 
        displaying logs in real time and filtering out unwanted entry types.
        
        :param values: optional constructor args for
            :class:`smc.monitoring.filters.NotFilter`. Typically this is a
            list of InFilter expressions.
        :type: list(QueryFilter)
        :rtype: OrFilter
        """
        filt = NotFilter(*value)
        self.update_filter(filt)
        return filt

    def add_defined_filter(self, *value):
        """
        Add a DefinedFilter expression to the query. This filter will be
        considered true if the :class:`smc.monitoring.values.Value` instance
        has a value.
        
        :param Value value: single value for the filter. Value is of type
            :class:`smc.monitoring.values.Value`.
        """
        filt = DefinedFilter(*value)
        self.update_filter(filt)
        return filt


class BlacklistQuery(Query):
    location = '/monitoring/session/socket'
    
    def __init__(self, target):
        super(BlacklistQuery, self).__init__('BLACKLIST', target)
        
        
class ConnectionQuery(Query):
    location = '/monitoring/session/socket'
    
    def __init__(self, target):
        super(ConnectionQuery, self).__init__('CONNECTIONS', target)


class VPNSAQuery(Query):
    location = '/monitoring/session/socket'
    
    def __init__(self, target):
        super(VPNSAQuery, self).__init__('VPN_SA', target)


class SSLVPNQuery(Query):
    location = '/monitoring/session/socket'
    
    def __init__(self, target):
        super(SSLVPNQuery, self).__init__('SSLVPNV2', target)


class RoutingQuery(Query):
    location = '/monitoring/session/socket'
    
    def __init__(self, target):
        super(RoutingQuery, self).__init__('ROUTING', target)

                
class UserQuery(Query):
    location = '/monitoring/session/socket'
    
    def __init__(self, target):
        super(UserQuery, self).__init__('USERS', target)


class ActiveAlertQuery(Query):
    location = '/monitoring/session/socket'
    
    def __init__(self, target):
        super(ActiveAlertQuery, self).__init__('ACTIVE_ALERTS', target)
