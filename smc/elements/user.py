"""
User module to hold accounts related to users (admin or local) in the SMC

You can create an Admin User, enable superuser, enable/disable the account,  
assign local access to engines, and change the account password for SMC or
engine access.
"""
import smc.actions.search as search
from smc.elements.util import find_link_by_name
from smc.elements.element import SMCElement
from smc.api.common import SMCRequest

class AdminUser(SMCElement):
    """ Represents an Adminitrator account on the SMC
    Use the constructor to create the user. 
    
    :param name: name of admin
    :param boolean local_admin: should be local admin on specified engines
    :param boolean allow_sudo: allow sudo on specified engines
    :param boolean superuser: is a super user (no restrictions) in SMC
    :param admin_domain: reference to admin domain, shared by default
    :param list engine_target: ref to engines for local admin access
    
    Create an Admin::
        
        admin = AdminUser(name='dlepage', superuser=True).create()
        
    If modifications are required after you can access the admin and
    make changes::
    
        for admin in collection.describe_admin_users():
            if admin.name == 'dlepage':
                admin.change_password('mynewpassword1')
                admin.enable_disable()
    """
    typeof = 'admin_user'
    
    def __init__(self, name, meta=None):
        SMCElement.__init__(self, name, meta)
        pass
    
    @classmethod
    def create(cls, name, local_admin=False, allow_sudo=False, 
               superuser=False, admin_domain=None, enabled=True,
               engine_target=None):
        engines = [] if engine_target is None else engine_target
        cls.json = {'name': name,
                    'enabled': enabled,
                    'allow_sudo': allow_sudo,
                    'engine_target': engines,
                    'local_admin': local_admin,
                    'superuser': superuser}
        return cls._create()

    @property
    def link(self):
        result = search.element_by_href_as_json(self.href)
        return result.get('link')

    def change_password(self, password):
        """ Change admin password 
        
        :method: PUT
        :param str password: new password
        :return: :py:class:`smc.api.web.SMCResult`
        """
        href = find_link_by_name('change_password', self.link)
        params = {'password': password}
        return SMCRequest(href=href, params=params).update()
           
    def change_engine_password(self, password):
        """ Change Engine password for engines on allowed
        list.
        
        :method: PUT
        :param str password: password for engine level
        :return: :py:class:`smc.api.web.SMCResult`
        """
        href = find_link_by_name('change_engine_password', self.link)
        params = {'password': password}
        return SMCRequest(href=href, params=params).update()
    
    def enable_disable(self):
        """ Toggle enable and disable of administrator account
        
        :method: PUT
        :return: :py:class:`smc.api.web.SMCResult`
        """
        href = find_link_by_name('enable_disable', self.link)
        return SMCRequest(href=href).update()
