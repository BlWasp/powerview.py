#!/usr/bin/env python3
from powerview.powerview import PowerView
from powerview.utils.helpers import *
from powerview.utils.native import *
from powerview.utils.formatter import FORMATTER
from powerview.utils.completer import Completer
from powerview.utils.colors import bcolors
from powerview.utils.connections import CONNECTION
from powerview.utils.parsers import powerview_arg_parse, arg_parse

import ldap3
import json
import random
import string
import shlex
from sys import platform
if platform in ["linux","linux2"]:
    import gnureadline as readline
else:
    import readline

def main():
    args = arg_parse()

    domain, username, password, lmhash, nthash, ldap_address = parse_identity(args)

    setattr(args,'domain',domain)
    setattr(args,'username',username)
    setattr(args,'password',password)
    setattr(args,'lmhash',lmhash)
    setattr(args,'nthash', nthash)
    setattr(args, 'ldap_address', ldap_address)

    try:
        conn = CONNECTION(args)
        init_ldap_address = args.ldap_address

        powerview = PowerView(conn, args)
        init_proto = conn.get_proto()
        cur_user = conn.who_am_i()
        server_ip = conn.get_ldap_address()
        temp_powerview = None

        while True:
            try:
                comp = Completer()
                readline.set_completer_delims(' \t\n;')
                readline.parse_and_bind("tab: complete")
                readline.set_completer(comp.complete)

                if args.query:
                    cmd = args.query
                else:
                    cmd = input(f'{bcolors.OKBLUE}({bcolors.ENDC}{bcolors.WARNING}{bcolors.BOLD}{init_proto}{bcolors.ENDC}{bcolors.OKBLUE})-[{bcolors.ENDC}{server_ip}{bcolors.OKBLUE}]-[{bcolors.ENDC}{cur_user}{bcolors.OKBLUE}]{bcolors.ENDC}\n{bcolors.OKBLUE}PV > {bcolors.ENDC}')

                if cmd:
                    try:
                        cmd = shlex.split(cmd)
                    except ValueError as e:
                        logging.error(str(e))
                        continue

                    pv_args = powerview_arg_parse(cmd)

                    if pv_args:
                        if pv_args.server and pv_args.server != args.domain:
                            if args.use_kerberos or not args.nameserver:
                                ldap_address = pv_args.server
                            else:
                                ldap_address = get_principal_dc_address(pv_args.server, args.nameserver)
                            
                            conn.set_ldap_address(ldap_address)
                            conn.set_targetDomain(pv_args.server)
                            
                            try:
                                temp_powerview = PowerView(conn, args, target_domain=pv_args.server)
                            except:
                                logging.error(f'Domain {pv_args.server} not found or probably not alive')
                                continue

                        try:
                            entries = None
                            if pv_args.module.casefold() == 'get-domain' or pv_args.module.casefold() == 'get-netdomain':
                                properties = pv_args.properties.strip(" ").split(',')
                                identity = pv_args.identity.strip()
                                if temp_powerview:
                                    entries = temp_powerview.get_domain(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domain(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'get-domainobject' or pv_args.module.casefold() == 'get-adobject':
                                properties = pv_args.properties.strip(" ").split(',')
                                identity = pv_args.identity.strip()
                                if temp_powerview:
                                    entries = temp_powerview.get_domainobject(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domainobject(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'get-domainobjectowner' or pv_args.module.casefold() == 'get-objectowner':
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domainobjectowner(identity=identity, args=pv_args)
                                else:
                                    entries = powerview.get_domainobjectowner(identity=identity, args=pv_args)
                            elif pv_args.module.casefold() == 'get-domainobjectacl' or pv_args.module.casefold() == 'get-objectacl':
                                identity = pv_args.identity.strip()
                                if temp_powerview:
                                    entries = temp_powerview.get_domainobjectacl(args=pv_args)
                                else:
                                    entries = powerview.get_domainobjectacl(args=pv_args)
                            elif pv_args.module.casefold() == 'get-domainuser' or pv_args.module.casefold() == 'get-netuser':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domainuser(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domainuser(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'get-domaincomputer' or pv_args.module.casefold() == 'get-netcomputer':
                                if pv_args.resolveip and not pv_args.identity:
                                    logging.error("-ResolveIP can only be used with -Identity")
                                    continue
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaincomputer(pv_args, properties, identity, resolveip=pv_args.resolveip, resolvesids=pv_args.resolvesids)
                                else:
                                    entries = powerview.get_domaincomputer(pv_args, properties, identity, resolveip=pv_args.resolveip, resolvesids=pv_args.resolvesids)
                            elif pv_args.module.casefold() == 'get-domaingroup' or pv_args.module.casefold() == 'get-netgroup':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaingroup(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domaingroup(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'get-domaingroupmember' or pv_args.module.casefold() == 'get-netgroupmember':
                                identity = pv_args.identity.strip()
                                if temp_powerview:
                                    entries = temp_powerview.get_domaingroupmember(pv_args, identity)
                                else:
                                    entries = powerview.get_domaingroupmember(pv_args, identity)
                            elif pv_args.module.casefold() == 'get-domainforeigngroupmember' or pv_args.module.casefold() == 'find-foreigngroup':
                                if temp_powerview:
                                    entries = temp_powerview.get_domainforeigngroupmember(pv_args)
                                else:
                                    entries = powerview.get_domainforeigngroupmember(pv_args)
                            elif pv_args.module.casefold() == 'get-domainforeignuser' or pv_args.module.casefold() == 'find-foreignuser':
                                if temp_powerview:
                                    entries = temp_powerview.get_domainforeignuser(pv_args)
                                else:
                                    entries = powerview.get_domainforeignuser(pv_args)
                            elif pv_args.module.casefold() == 'get-domaincontroller' or pv_args.module.casefold() == 'get-netdomaincontroller':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaincontroller(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domaincontroller(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'get-domaingpo' or pv_args.module.casefold() == 'get-netgpo':
                                properties = pv_args.properties.strip(" ").split(',')
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaingpo(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domaingpo(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'get-domaingpolocalgroup' or pv_args.module.casefold() == 'get-gpolocalgroup':
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaingpolocalgroup(pv_args, identity)
                                else:
                                    entries = powerview.get_domaingpolocalgroup(pv_args, identity)
                            elif pv_args.module.casefold() == 'get-domainou' or pv_args.module.casefold() == 'get-netou':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domainou(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domainou(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'get-domaindnszone':
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaindnszone(identity, properties, args=pv_args)
                                else:
                                    entries = powerview.get_domaindnszone(identity, properties, args=pv_args)
                            elif pv_args.module.casefold() == 'get-domaindnsrecord':
                                zonename = pv_args.zonename.strip() if pv_args.zonename else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaindnsrecord(identity, zonename, properties, args=pv_args)
                                else:
                                    entries = powerview.get_domaindnsrecord(identity, zonename, properties, args=pv_args)
                            elif pv_args.module.casefold() == 'get-domainsccm' or pv_args.module.casefold() == 'get-sccm':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domainsccm(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domainsccm(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'get-domainca' or pv_args.module.casefold() == 'get-ca':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domainca(pv_args, properties)
                                else:
                                    entries = powerview.get_domainca(pv_args, properties)
                            elif pv_args.module.casefold() == 'get-domaincatemplate' or pv_args.module.casefold() == 'get-catemplate':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaincatemplate(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domaincatemplate(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'remove-domaincatemplate' or pv_args.module.casefold() == 'remove-catemplate':
                                if not pv_args.identity:
                                    logging.error("-Identity flag is required")
                                    continue

                                if temp_powerview:
                                    temp_powerview.remove_domaincatemplate(identity=pv_args.identity, args=pv_args)
                                else:
                                    powerview.remove_domaincatemplate(identity=pv_args.identity, args=pv_args)
                            elif pv_args.module.casefold() == 'add-domaincatemplate' or pv_args.module.casefold() == 'add-catemplate':
                                if pv_args.displayname is None:
                                    logging.error("-DisplayName flag is required")
                                    continue

                                displayname = pv_args.displayname
                                name = pv_args.name
                                if temp_powerview:
                                    temp_powerview.add_domaincatemplate(displayname, name, args=pv_args)
                                else:
                                    powerview.add_domaincatemplate(displayname, name, args=pv_args)
                            elif pv_args.module.casefold() == 'add-domaincatemplateacl' or pv_args.module.casefold() == 'add-catemplateacl':
                                if pv_args.template is not None and pv_args.principalidentity is not None and pv_args.rights is not None:
                                    if temp_powerview:
                                        temp_powerview.add_domaincatemplateacl(pv_args.template, pv_args.principalidentity, args=pv_args)
                                    else:
                                        powerview.add_domaincatemplateacl(pv_args.template, pv_args.principalidentity, args=pv_args)
                                else:
                                    logging.error('-TargetIdentity , -PrincipalIdentity and -Rights flags are required')
                            elif pv_args.module.casefold() == 'get-domaintrust' or pv_args.module.casefold() == 'get-nettrust':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                identity = pv_args.identity.strip() if pv_args.identity else None
                                if temp_powerview:
                                    entries = temp_powerview.get_domaintrust(pv_args, properties, identity)
                                else:
                                    entries = powerview.get_domaintrust(pv_args, properties, identity)
                            elif pv_args.module.casefold() == 'convertfrom-sid':
                                if pv_args.objectsid:
                                    objectsid = pv_args.objectsid.strip()
                                    if temp_powerview:
                                        temp_powerview.convertfrom_sid(objectsid=objectsid, output=True)
                                    else:
                                        powerview.convertfrom_sid(objectsid=objectsid, output=True)
                                else:
                                    logging.error("-ObjectSID flag is required")
                            elif pv_args.module.casefold() == 'get-namedpipes':
                                if pv_args.computer is not None or pv_args.computername is not None:
                                    if temp_powerview:
                                        entries = temp_powerview.get_namedpipes(pv_args)
                                    else:
                                        entries = powerview.get_namedpipes(pv_args)
                                else:
                                    logging.error('-Computer or -ComputerName is required')
                            elif pv_args.module.casefold() == 'get-netshare':
                                if pv_args.computer is not None or pv_args.computername is not None:
                                    if temp_powerview:
                                        temp_powerview.get_netshare(pv_args)
                                    else:
                                        powerview.get_netshare(pv_args)
                                else:
                                    logging.error('-Computer or -ComputerName is required')
                            elif pv_args.module.casefold() == 'get-netsession':
                                if pv_args.computer is not None or pv_args.computername is not None:
                                    if temp_powerview:
                                        entries = temp_powerview.get_netsession(pv_args)
                                    else:
                                        entries = powerview.get_netsession(pv_args)
                                else:
                                    logging.error('-Computer or -ComputerName is required')
                            elif pv_args.module.casefold() == 'find-localadminaccess':
                                if temp_powerview:
                                    entries = temp_powerview.find_localadminaccess(pv_args)
                                else:
                                    entries = powerview.find_localadminaccess(pv_args)
                            elif pv_args.module.casefold() == 'invoke-kerberoast':
                                properties = pv_args.properties.strip(" ").split(',') if pv_args.properties else None
                                if temp_powerview:
                                    entries = temp_powerview.invoke_kerberoast(pv_args, properties)
                                else:
                                    entries = powerview.invoke_kerberoast(pv_args, properties)
                            elif pv_args.module.casefold() == 'add-domainobjectacl' or pv_args.module.casefold() == 'add-objectacl':
                                if pv_args.targetidentity is not None and pv_args.principalidentity is not None and pv_args.rights is not None:
                                    if temp_powerview:
                                        temp_powerview.add_domainobjectacl(pv_args)
                                    else:
                                        powerview.add_domainobjectacl(pv_args)
                                else:
                                    logging.error('-TargetIdentity , -PrincipalIdentity and -Rights flags are required')
                            elif pv_args.module.casefold() == 'remove-domainobjectacl' or pv_args.module.casefold() == 'remove-objectacl':
                                if pv_args.targetidentity is not None and pv_args.principalidentity is not None and pv_args.rights is not None:
                                    if temp_powerview:
                                        temp_powerview.remove_domainobjectacl(pv_args)
                                    else:
                                        powerview.remove_domainobjectacl(pv_args)
                                else:
                                    logging.error('-TargetIdentity , -PrincipalIdentity and -Rights flags are required')
                            elif pv_args.module.casefold() == 'add-domaingroupmember' or pv_args.module.casefold() == 'add-groupmember':
                                if pv_args.identity is not None and pv_args.members is not None:
                                    suceed = False
                                    if temp_powerview:
                                        succeed = temp_powerview.add_domaingroupmember(pv_args.identity, pv_args.members, pv_args)
                                    else:
                                        succeed =  powerview.add_domaingroupmember(pv_args.identity, pv_args.members, pv_args)

                                    if succeed:
                                        logging.info(f'User {pv_args.members} successfully added to {pv_args.identity}')
                                else:
                                    logging.error('-Identity and -Members flags required')
                            elif pv_args.module.casefold() == 'remove-domaingroupmember' or pv_args.module.casefold() == 'remove-groupmember':
                                if pv_args.identity is not None and pv_args.members is not None:
                                    suceed = False
                                    if temp_powerview:
                                        succeed = temp_powerview.remove_domaingroupmember(pv_args.identity, pv_args.members, pv_args)
                                    else:
                                        succeed =  powerview.remove_domaingroupmember(pv_args.identity, pv_args.members, pv_args)

                                    if succeed:
                                        logging.info(f'User {pv_args.members} successfully removed from {pv_args.identity}')
                                else:
                                    logging.error('-Identity and -Members flags required')
                            elif pv_args.module.casefold() == 'set-domainobject' or pv_args.module.casefold() == 'set-adobject':
                                if pv_args.identity and (pv_args.clear or pv_args.set or pv_args.append):
                                    if temp_powerview:
                                        succeed = temp_powerview.set_domainobject(pv_args.identity, args=pv_args)
                                    else:
                                        succeed = powerview.set_domainobject(pv_args.identity, args=pv_args)
                                else:
                                    logging.error('-Identity and [-Clear][-Set][-Append] flags required')
                            elif pv_args.module.casefold() == 'set-domaindnsrecord':
                                if pv_args.recordname is None or pv_args.recordaddress is None:
                                    logging.error("-RecordName and -RecordAddress flags are required")
                                    continue
                                if temp_powerview:
                                    temp_powerview.set_domaindnsrecord(pv_args)
                                else:
                                    powerview.set_domaindnsrecord(pv_args)
                            elif pv_args.module.casefold() == 'set-domaincatemplate' or pv_args.module.casefold() == 'set-catemplate':
                                if pv_args.identity and (pv_args.clear or pv_args.set or pv_args.append):
                                    if temp_powerview:
                                        temp_powerview.set_domaincatemplate(pv_args.identity, pv_args)
                                    else:
                                        powerview.set_domaincatemplate(pv_args.identity, pv_args)
                                else:
                                    logging.error('-Identity and [-Clear][-Set|-Append] flags required')
                            elif pv_args.module.casefold() == 'set-domainuserpassword':
                                if pv_args.identity and pv_args.accountpassword:
                                    succeed = False
                                    if temp_powerview:
                                        succeed = temp_powerview.set_domainuserpassword(pv_args.identity, pv_args.accountpassword, oldpassword=pv_args.oldpassword, args=pv_args)
                                    else:
                                        succeed = powerview.set_domainuserpassword(pv_args.identity, pv_args.accountpassword, oldpassword=pv_args.oldpassword, args=pv_args)

                                    if succeed:
                                        logging.info(f'Password changed for {pv_args.identity}')
                                    else:
                                        logging.error(f'Failed password change attempt for {pv_args.identity}')
                                else:
                                    logging.error('-Identity and -AccountPassword flags are required')
                            elif pv_args.module.casefold() == 'set-domaincomputerpassword':
                                if pv_args.identity and pv_args.accountpassword:
                                    succeed = False
                                    if temp_powerview:
                                        succeed = temp_powerview.set_domaincomputerpassword(pv_args.identity, pv_args.accountpassword, oldpassword=pv_args.oldpassword, args=pv_args)
                                    else:
                                        succeed = powerview.set_domaincomputerpassword(pv_args.identity, pv_args.accountpassword, oldpassword=pv_args.oldpassword, args=pv_args)

                                    if succeed:
                                        logging.info(f'Password changed for {pv_args.identity}')
                                    else:
                                        logging.error(f'Failed password change attempt for {pv_args.identity}')
                                else:
                                    logging.error('-Identity and -AccountPassword flags are required')
                            elif pv_args.module.casefold() == 'set-domainobjectowner' or pv_args.module.casefold() == 'set-objectowner':
                                if pv_args.targetidentity is not None and pv_args.principalidentity is not None:
                                    if temp_powerview:
                                        temp_powerview.set_domainobjectowner(pv_args.targetidentity, pv_args.principalidentity, args=pv_args)
                                    else:
                                        powerview.set_domainobjectowner(pv_args.targetidentity, pv_args.principalidentity, args=pv_args)
                                else:
                                    logging.error('-TargetIdentity and -PrincipalIdentity flags are required')
                            elif pv_args.module.casefold() == 'add-domaincomputer' or pv_args.module.casefold() == 'add-adcomputer':
                                if pv_args.computername is not None:
                                    if pv_args.computerpass is None:
                                        pv_args.computerpass = ''.join(random.choice(list(string.ascii_letters + string.digits + "!@#$%^&*()")) for _ in range(12))
                                    if temp_powerview:
                                        temp_powerview.add_domaincomputer(pv_args.computername, pv_args.computerpass)
                                    else:
                                        powerview.add_domaincomputer(pv_args.computername, pv_args.computerpass)
                                else:
                                    logging.error(f'-ComputerName and -ComputerPass are required')
                            elif pv_args.module.casefold() == 'add-domaindnsrecord':
                                if pv_args.recordname is None or pv_args.recordaddress is None:
                                    logging.error("-RecordName and -RecordAddress flags are required")
                                    continue
                                if temp_powerview:
                                    temp_powerview.add_domaindnsrecord(pv_args)
                                else:
                                    powerview.add_domaindnsrecord(pv_args)
                            elif pv_args.module.casefold() == 'add-domainuser' or pv_args.module.casefold() == 'add-aduser':
                                if temp_powerview:
                                    temp_powerview.add_domainuser(pv_args.username, pv_args.userpass, args=pv_args)
                                else:
                                    powerview.add_domainuser(pv_args.username, pv_args.userpass, args=pv_args)
                            elif pv_args.module.casefold() == 'remove-domainuser' or pv_args.module.casefold() == 'remove-aduser':
                                if pv_args.identity:
                                    if temp_powerview:
                                        temp_powerview.remove_domainuser(pv_args.identity)
                                    else:
                                        powerview.remove_domainuser(pv_args.identity)
                                else:
                                    logging.error(f'-Identity is required')
                            elif pv_args.module.casefold() == 'remove-domaindnsrecord':
                                if pv_args.identity:
                                    identity = pv_args.identity.strip()
                                else:
                                    logging.error("-Identity flag is required")
                                    continue
                                if temp_powerview:
                                    temp_powerview.remove_domaindnsrecord(identity, args=pv_args)
                                else:
                                    powerview.remove_domaindnsrecord(identity, args=pv_args)
                            elif pv_args.module.casefold() == 'remove-domaincomputer' or pv_args.module.casefold() == 'remove-adcomputer':
                                if pv_args.computername is not None:
                                    if temp_powerview:
                                        temp_powerview.remove_domaincomputer(pv_args.computername)
                                    else:
                                        powerview.remove_domaincomputer(pv_args.computername)
                                else:
                                    logging.error(f'-ComputerName is required')
                            elif pv_args.module.casefold() == 'exit':
                                sys.exit(0)
                            elif pv_args.module.casefold() == 'clear':
                                clear_screen()

                            if entries:
                                if pv_args.outfile:
                                    if os.path.exists(pv_args.outfile):
                                        logging.error("%s exists "%(pv_args.outfile))
                                        continue

                                formatter = FORMATTER(pv_args, args.use_kerberos)
                                if pv_args.where is not None:
                                    # Alter entries
                                    entries = formatter.alter_entries(entries,pv_args.where)
                                if entries is None:
                                    logging.error(f'Key not available')
                                else:
                                    if pv_args.count:
                                        formatter.count(entries)
                                    elif pv_args.select is not None:
                                        if pv_args.select.isdecimal():
                                            formatter.print_index(entries)
                                        else:
                                            formatter.print_select(entries)
                                    else:
                                        formatter.print(entries)

                            temp_powerview = None
                            conn.set_ldap_address(init_ldap_address)
                            conn.set_targetDomain(None)
                        except ldap3.core.exceptions.LDAPInvalidFilterError as e:
                            logging.error(str(e))
                        except ldap3.core.exceptions.LDAPAttributeError as e:
                            logging.error(str(e))
                        except ldap3.core.exceptions.LDAPSocketSendError as e:
                            logging.error(str(e))
                            conn.reset_connection()
                        except ldap3.core.exceptions.LDAPSocketReceiveError as e:
                            logging.error(str(e))
                            conn.reset_connection()
            except KeyboardInterrupt:
                print()
            except EOFError:
                print("Exiting...")
                sys.exit(0)
            except ldap3.core.exceptions.LDAPSocketSendError as e:
                logging.info("Connection dead")
                conn.reset_connection()
            except ldap3.core.exceptions.LDAPSessionTerminatedByServerError as e:
                logging.warning("Server connection terminated. Trying to reconnect")
                conn.reset_connection()
                continue
            except Exception as e:
                logging.error(str(e))

            if args.query:
                sys.exit(0)

    except ldap3.core.exceptions.LDAPSocketOpenError as e:
        print(str(e))
    except ldap3.core.exceptions.LDAPBindError as e:
        print(str(e))

if __name__ == '__main__':
    main()
