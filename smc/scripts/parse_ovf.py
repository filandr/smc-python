try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

# GW, IP network SMC API

xml = '''<?xml version="1.0" encoding="UTF-8"?>
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
         <Property oe:key="agentName" oe:value="serviceinstance-113"/>
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
         <Property oe:key="smcaddress" oe:value="172.18.1.151"/>
         <Property oe:key="smcapikey" oe:value="abcdefgh123456"/>
         
   </PropertySection>
   <ve:EthernetAdapterSection>
      <ve:Adapter ve:mac="00:50:56:b5:0e:c5" ve:network="DPortGroup" ve:unitNumber="7"/>
   </ve:EthernetAdapterSection>
</Environment>
'''

def parse_ovf(ovf):
    ovf = xml
    #try:
    #    with open(filename,'r') as f:
    #        ovf = f.read()
    #except IOError:
    #    print("ERROR, %s not found" % filename)
            
    namespace = {'oe': '{http://schemas.dmtf.org/ovf/environment/1}'}

    root = ET.fromstring(ovf)
    for child in root.iter():
        if child.tag.endswith('PropertySection'):
            return [
                {section.attrib.get('{}key'.format(namespace['oe'])):
                 section.attrib.get('{}value'.format(namespace['oe']))}
                    for section in child.iter()
                    if section.attrib
            ]

if __name__ == '__main__':
    import os
    import subprocess
    import sys
    
    FILENAME = '/spool/cpa/ovf-env.xml'
    SCRIPT_DIR = '/spool/cpa/bin/ngfw-appliance-scripts'
    SET_NETWORK_SCRIPT = 'set-ngfw-network-info'
    
    if len(sys.argv) > 1:
        FILENAME = sys.argv[1]
    
    try:
        config = parse_ovf(FILENAME)
    except IOError as e:
        print(e)
        
    from pprint import pprint
    pprint(config)

    mgmt = {key:value
            for setting in config
            for key, value in setting.items()
            if key.startswith('management.')}
    
    
    return_code = subprocess.call("echo Hello World", shell=True)
    #set-ngfw-network-info node-ip node-netmask default-gateway
    os.system('{}/{} {} {} {}'.format(
        SCRIPT_DIR, SET_NETWORK_SCRIPT)) 
    
    
    
    