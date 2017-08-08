import argparse
import subprocess 
from io import StringIO
from xml.etree import ElementTree
from smc import session
from smc.core.engine_vss import VSSContainer


class VSSContainerNotFound(Exception):
    pass


xml = u'''<?xml version="1.0" encoding="UTF-8"?>
<Environment
     xmlns="http://schemas.dmtf.org/ovf/environment/1"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xmlns:oe="http://schemas.dmtf.org/ovf/environment/1"
     xmlns:ve="http://www.vmware.com/schema/ovfenv"
     oe:id=""
     ve:vCenterId="vm-320">
   <PlatformSection>
      <Kind>VMware ESXi</Kind>
      <Version>5.5.0</Version>
      <Vendor>VMware, Inc.</Vendor>
      <Locale>en</Locale>
   </PlatformSection>
   <PropertySection>
     <Property oe:key="agentName" oe:value="serviceinstance-119"/>
     <Property oe:key="applianceModel" oe:value="NGFW-CLOUD"/>
     <Property oe:key="applianceSoftwareVersion" oe:value="6.2.1.20170614095114"/>
     <Property oe:key="hostInfo.agentId" oe:value="vsmagent-109"/>
     <Property oe:key="hostInfo.hostId" oe:value="host-50"/>
     <Property oe:key="hostInfo.hostName" oe:value="172.18.1.120"/>
     <Property oe:key="management.DNS" oe:value="172.18.1.20,"/>
     <Property oe:key="management.gateway" oe:value="172.18.1.200"/>
     <Property oe:key="management.ip0" oe:value="172.18.1.111"/>
     <Property oe:key="management.netmask0" oe:value="255.255.255.0"/>
     <Property oe:key="virtualSystemId" oe:value=""/>
     <Property oe:key="vmidcIp" oe:value="192.168.4.84"/>
     <Property oe:key="vmidcPassword" oe:value="1nLY/LVd5tD79E4qSbBD7w=="/>
     <Property oe:key="vmidcUser" oe:value="admin"/>
     <Property oe:key="smcAddress" oe:value="https://172.18.1.151:8082"/>
     <Property oe:key="smcApiKey" oe:value="vsMoA3eb9kB9pvN6vJBLMBNX"/>
         
   </PropertySection>
   <ve:EthernetAdapterSection>
      <ve:Adapter ve:mac="00:50:56:b5:0e:c5" ve:network="DPortGroup" ve:unitNumber="7"/>
   </ve:EthernetAdapterSection>
</Environment>
'''


def parse_ovf(ovf_filename):
    """
    Parse the contents of the VMWare OVF file. The file uses namespaces
    so extract all, regardless of their name. The namespace key associated
    with the environment properties is 'oe'.
    
    :param str ovf_filename: full path to OVF file. Can be overridden
        in main
    :raises IOError: cannot read file, maybe doesn't exist?
    :return: configuration as dict. Dict will be key/value's from
        <Property> section of ovf-env.xml.
    """
    #contents = xml
    with open(ovf_filename,'r') as f:
        contents = f.read()

    namespaces = dict([
        node for _, node in ElementTree.iterparse(
            StringIO(xml), events=('start-ns',)
        )
    ])
    
    namespace = {'oe': '{%s}' % namespaces['oe']}

    root = ElementTree.fromstring(contents)
    for child in root.iter():
        if child.tag.endswith('PropertySection'):
            return {section.attrib.get('{}key'.format(namespace['oe'])):
                    section.attrib.get('{}value'.format(namespace['oe']))
                    for section in child.iter()
                    if section.attrib}

    
def get_initial_config(cfg):
    """
    Get the VSS container node initial configuration.
    
    :param dict cfg: parsed OVF configuration from calling
        parse_ovf()
    :raises VSSContainerNotFound: if the container could not be
        retrieved from the SMC. 
    :return: initial config as TEXT. If base64 is required, add
        change node.initial_contact(base64=True)
    """
    session.login(
        url=cfg.get('smcAddress'),
        api_key=cfg.get('smcApiKey'),
        verify=False,
        beta=True)
    
    # Raises VSSContainerNotFound
    vss_container = get_container_by_svcinstance(cfg.get('agentName'))
    node = vss_container.nodes[0] # Needs to be modified if more than one node
    cfg = node.initial_contact()
    session.logout()
    return cfg


def get_container_by_svcinstance(serviceinstance):
    """
    Get the name of the VSS Container based on the NSX
    ServiceInstance name.
    
    The Serviceinstance is saved on container 'isc_vss_id' attribute
    after the VSSContainerNode has been created by NSX callback.
    
    NSX creates the service instance name and populates the NGFW
    ovf-env.xml with the attribute 'agentName'.
    
    :raises VSSContainerNotFound: cannot locate the container for this
        service instance.
    :return: VSSContainer
    """
    for container in VSSContainer.objects.all(): # 1 Query
        if container.vss_isc['isc_vss_id'] == serviceinstance:
            return container
    raise VSSContainerNotFound(
        'Could not find container for service instance: {}'.format(
            serviceinstance))
    

if __name__ == '__main__':
    
    FILENAME = '/spool/cpa/ovf-env.xml'
    WORKDIR = '/spool/cpa/bin'
    SCRIPT_DIR = WORKDIR + '/ngfw-appliance-scripts'
    
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', nargs='?')
    ns = parser.parse_args()
    
    if ns.filename is not None:
        FILENAME = ns.filename
      
    # Raises IOError
    cfg = parse_ovf(FILENAME)

    from pprint import pprint
    pprint(cfg)

    #set-ngfw-network-info node-ip node-netmask default-gateway
    set_ngfw_network_info = '{}/{} {} {} {}'.format(
        SCRIPT_DIR,
        'set-ngfw-network-info',
        cfg.get('management.ip0'),
        cfg.get('management.netmask0'),
        cfg.get('management.gateway'))
    
    print('Executing: %s' % set_ngfw_network_info)
    rc = subprocess.call(set_ngfw_network_info, shell=True)    
    if rc != 0: # Abort?
        print('Return from subprocess failed setting network info: %s' % rc)
    
    # Get the initial configuration from SMC
    initial_cfg = get_initial_config(cfg)
    print(initial_cfg)
    
    # Save to file
    path_to_initial_cfg = WORKDIR + '/applianceConfig.cfg'
    with open(path_to_initial_cfg, 'w') as f:
        f.write(initial_cfg)
    
    #set-ngfw-mgmt-info fw-hostname smc-ip config-file-with-otp
    set_ngfw_mgmt_info = '{}/{} {} {} {}'.format(
        SCRIPT_DIR,
        'set-ngfw-mgmt-info',
        cfg.get('agentId'),
        cfg.get('smcAddress'),
        path_to_initial_cfg)
    
    print('Executing: %s' % set_ngfw_network_info)
    rc = subprocess.call(set_ngfw_mgmt_info, shell=True)
    print("Return code from set-ngfw-mgmt-info script: %s" % rc)

