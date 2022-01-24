# encoding: utf-8
## #!/usr/bin/python
#
# Copyright: (c) 2020, Luciano Baez <lucianobaez@kyndryl>
#                                   <lucianobaez1@ibm.com>
#                                   <lucianobaez@outlook.com>
#
# Latest version at https://github.kyndryl.net/lucianobaez
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#  This is a module to handle /etc/sudoers file
#
# History
#   -Ver 0.1 : Aug 14 2020
#           - Implement the report option gets the pam configuration file.

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: pam_handler

author:
    - Luciano Báez (@lucianoabez) on Kyndryl slack and on IBM slack (@lucianoabez1)
'''

EXAMPLES = '''
# Get information
- name: Get the PAM information
  pam_handler:
    state: report

# Ensure that a line is present on pam
- name: Add data to pam file
  pam_handler:
    service_name:
    pamfile: /etc/pam.d/sshd
    module_type: auth
    control_flags: requisite
    module_path: pam_succeed_if.so
    module_options: "uid >= 1000 quiet_success"
    state: present
    first: false
    
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the SUDO module generates
    type: str
    returned: always
'''

import os
import pwd
import grp
import platform
import subprocess
import json
import shutil
import datetime

# Importing all functions from repo lib sudo_handler_lib
from ansible.module_utils.pam_handler_lib import *

#Needed to be usable as Ansible Module
from ansible.module_utils.basic import AnsibleModule


#Module Global Variables 

pam_fact={}


def sudoershandle(options):
    SUDOHANDLERESULT={}
    return SUDOHANDLERESULT
    

def run_module():
    #------------------------------------------------------------------------------------------------------------
    # This are the arguments/parameters that a user can pass to this module
    # the action is the only one that is required

    module_args = dict(
        #action=dict(type='str', required=True),
        state=dict(type='str', default='present'),
        service_name=dict(type='str', required=False),
        pam_file=dict(type='str', required=False),
        #
        module_type=dict(type='str', required=False),
        control_flags=dict(type='str', required=False),
        module_path=dict(type='str', required=False),
        #
        reference_module_type=dict(type='str', required=False),
        reference_control_flags=dict(type='str', required=False),
        reference_module_path=dict(type='str', required=False),
        #
        comment=dict(type='str', required=False),
        #
        module_options=dict(type='str', required=False),
        first=dict(type='bool', required=False, default=False),
        backup=dict(type='bool', required=False, default=False),

        # Non documented option For troubleshoot
        log=dict(type='bool', required=False, default=False)
    )
    


    # Acepted values for "state" 
    #   -report                 = Provides a report without any change
    
    #------------------------------------------------------------------------------------------------------------
    # This is the dictionary to handle the module result
    result = dict(
        changed=False,
        failed=False,
        skipped=False,
        original_message='',
        message=''
    )

    # This is the dictionary to handle the logs
    logdic = dict(
        log=False,
        logfile='/tmp/pam_handler'
    )

    # The AnsibleModule object will be our abstraction working with Ansible this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module supports check mode
    
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Define Vaariables to use 
    pam_process=1
    pam_log=False
    
    pam_state=str('')
    pam_service_name=str('')
    pam_file=str('')
    pam_module_type=str('')
    pam_control_flags=str('')
    pam_module_path=str('')

    pam_reference_module_type=str('')
    pam_reference_control_flags=str('')
    pam_reference_module_path=str('')
    
    pam_module_options=str('')
    pam_comment=str('')
    pam_first= False
    pam_iscomment=False
    pam_backup=False

    #

    # Dectecting arguments
    #try:
    #    sudo_module_action=str(module.params['action'])
    #except KeyError:
    #    sudo_process=0


    # Provide the the requested action as the original Message
    CR="\n"
    result['original_message'] = module.params
    #result['message'] = 'goodbye',
    ModuleExitMessage = ''
    ModuleExitChanged = False
    ModuleExitFailed= False

    # <processing parameters>
    try:
        pam_state=str(module.params['state'])
    except KeyError:
        pam_state='report'

    #Getting PAM facts
    pam_fact=getpam_fact(logdic)
    if pam_fact['detected']!=True:
        #PAM not Detected
        result['changed'] = False
        result['failed'] = True
        ModuleExitMessage = ModuleExitMessage + "PAM not detected!" + CR  
    else:
        #PAM Detected    
        if pam_state != 'report':
            #Process when state is present or absent
            try:
                pam_service_name=str(module.params['service_name'])
            except:
                pam_service_name=''
            try:
                pam_file=str(module.params['pam_file'])
            except:
                pam_file=''
            #
            try:
                pam_module_type=str(module.params['module_type'])
            except:
                pam_module_type=''
            try:
                pam_control_flags=str(module.params['control_flags'])
            except:
                pam_control_flags=''
            try:
                pam_module_path=str(module.params['module_path'])
            except:
                pam_module_path=''
            #
            try:
                pam_reference_module_type=str(module.params['reference_module_type'])
            except:
                pam_reference_module_type=''
            try:
                pam_reference_control_flags=str(module.params['reference_control_flags'])
            except:
                pam_reference_control_flags=''
            try:
                pam_reference_module_path=str(module.params['reference_module_path'])
            except:
                pam_reference_module_path=''
            #
            try:
                pam_module_options=str(module.params['module_options'])
            except:
                pam_module_options=''
            try:
                pam_comment=str(module.params['comment'])
            except:
                pam_comment=''

            try:
                pam_first=module.params['first']
            except:
                pam_first= False
            try:
                pam_backup=module.params['backup']
            except:
                pam_backup=False

            #Detecting the include file (could be with full path or without path, adn will asume that are at /etc/sudoers.d )
            try:
                pam_log=module.params['log']       
            except:
                pam_log=False

            if pam_log==True:
                logdic['log']=pam_log
                logdic['logfile']="/var/log/pam_handler_debug"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".log"

            # 
            if pam_state != 'report':
                if pam_service_name=="" and pam_file=="" :
                    pam_process=0
                    ModuleExitMessage = ModuleExitMessage + "pam_service_name:"+pam_service_name+" pam_file:"+pam_file+" "+ CR
                    ModuleExitMessage = ModuleExitMessage + "ERR- You should provide a pam service name or pam file name!" + CR
                else:
                    if pam_service_name=="" and pam_file!="":
                        #Getting the pam_service_name with the pam_file name
                        result=getservicenamebypamfile(pam_file,pam_fact)
                        if result['rc']==0:
                            pam_service_name=result['results']
                        else:
                            pam_process=0
                            ModuleExitMessage = ModuleExitMessage + result['stdout'] + CR
                    #at this point pam_service_name should have a name
                    if pam_service_name!="":
                        if pam_state == 'present' or pam_state == 'absent' or pam_state == 'comment':
                            if (pam_module_type=="" or pam_control_flags=="" or pam_module_path=="") and (pam_comment==""):
                                #Handling module_type, control_flags and module_path
                                pam_process=0
                                ModuleExitMessage = ModuleExitMessage + "ERR- module_type, control_flags and module_path should have values."+ CR
                        if pam_state == 'present' or pam_state == 'absent':
                            if (pam_comment!="") and (pam_module_type!="" or pam_control_flags!="" or pam_module_path!="") :
                                #Handling comment
                                pam_process=0
                                ModuleExitMessage = ModuleExitMessage + "ERR- If 'comment' have value, the attributes module_type, control_flags and module_path shouldn't have values."+ CR
                            
                        if pam_state == 'presentafter':
                            if pam_module_type=="" or pam_control_flags=="" or pam_module_path=="":
                                pam_process=0
                                ModuleExitMessage = ModuleExitMessage + "ERR- module_type, control_flags and module_path should have values."+ CR
                            if pam_reference_module_type=="" or pam_reference_control_flags=="" or pam_reference_module_path=="":
                                pam_process=0
                                ModuleExitMessage = ModuleExitMessage + "ERR- reference_module_type, reference_control_flags and reference_module_path should have values when use 'presentafter'."+ CR
                            if (pam_comment!="") and (pam_module_type!="" or pam_control_flags!="" or pam_module_path!="") :
                                #Handling comment
                                pam_process=0
                                ModuleExitMessage = ModuleExitMessage + "ERR- If 'comment' have value, the attributes module_type, control_flags and module_path shouldn't have values."+ CR
                            
        # </processing parameters>

        if pam_process==1:
                
            if pam_state == 'report':
                result['changed']=False
                result['message']=pam_fact
            else:
                result['changed']=False
                pam_line=pam_module_type+"\t"+pam_control_flags+"\t"+pam_module_path+"\t"+pam_module_options
                if pam_state == 'present':
                    if pam_comment=="":
                        pam_iscomment=False
                    else:
                        pam_iscomment=True
                    if pam_first== True:
                        rc=pamlinepresent(pam_service_name,pam_line,0,pam_iscomment,pam_fact,logdic)
                    else:
                        rc=pamlinepresentatend(pam_service_name,pam_line,pam_iscomment,pam_fact,logdic)
                    if rc['rc'] >= 0 and rc['rc'] <= 2:
                        result['changed'] = True
                        rcsave=pamsavefile(pam_service_name,pam_fact,logdic,pam_backup)
                        if rcsave['rc'] == 0:
                            result['changed'] = True
                        else:
                            result['changed'] = False
                            result['failed'] = True
                        ModuleExitMessage = ModuleExitMessage + rcsave['stdout'] + CR
                        
                    else:
                        result['changed'] = False
                        result['failed'] = True
                    ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                if pam_state == 'presentafter':
                    if pam_comment=="":
                        pam_iscomment=False
                        pam_line_reference=pam_reference_module_type+"\t"+pam_reference_control_flags+"\t"+pam_reference_module_path
                    else:
                        pam_iscomment=True
                        pam_line_reference=pam_comment
                    #print(pam_line+" -> "+pam_line_reference)
                    rc=pamlinepresentafterline(pam_service_name,pam_line,pam_line_reference,pam_iscomment,pam_fact,logdic)
                    if rc['rc'] >= 0 and rc['rc'] <= 2:
                        result['changed'] = True
                        rcsave=pamsavefile(pam_service_name,pam_fact,logdic,pam_backup)
                        if rcsave['rc'] == 0:
                            result['changed'] = True
                        else:
                            result['changed'] = False
                            result['failed'] = True
                        ModuleExitMessage = ModuleExitMessage + rcsave['stdout'] + CR
                        
                    else:
                        result['changed'] = False
                        result['failed'] = True
                    ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                            
                if pam_state == 'absent':
                    rc=pamremoveline(pam_service_name,pam_line,pam_fact,logdic)                    
                    if rc['rc'] == 0:
                        result['changed'] = True
                        rcsave=pamsavefile(pam_service_name,pam_fact,logdic,pam_backup)
                        if rcsave['rc'] == 0:
                            result['changed'] = True
                        else:
                            result['changed'] = False
                            result['failed'] = True
                        ModuleExitMessage = ModuleExitMessage + rcsave['stdout'] + CR
                        
                    else:
                        result['changed'] = False
                        result['failed'] = True
                        if rc['rc'] == 1:
                            result['failed'] = False
                    ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR

                if pam_state == 'comment':
                    rc=pamcommentline(pam_service_name,pam_line,pam_fact,logdic)                   
                    if rc['rc'] == 0:
                        result['changed'] = True
                        rcsave=pamsavefile(pam_service_name,pam_fact,logdic,pam_backup)
                        if rcsave['rc'] == 0:
                            result['changed'] = True
                        else:
                            result['changed'] = False
                            result['failed'] = True
                        ModuleExitMessage = ModuleExitMessage + rcsave['stdout'] + CR
                    else:
                        result['changed'] = False
                        result['failed'] = True
                        if rc['rc'] == 1:
                            result['failed'] = False
                    ModuleExitMessage = ModuleExitMessage + rc['stdout'] + CR
                #if pam_state == 'resave' or result['changed'] == True:

        else:
            # PAM not processed due incorrect parameters
            result['changed'] = False
            result['failed'] = True
    #---------------------------------------------------------------------------------------------------------------------------
    if pam_state != 'report':
        result['message'] = ModuleExitMessage
    # Returning the result
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()