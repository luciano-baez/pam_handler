# encoding: utf-8
## #!/usr/bin/python
#
# Copyright: (c) 2020, Luciano Baez <lucianobaez@ar.ibm.com>
#                                   <lucianobaez@kyndryl.com>
#                                   <lucianobaez@outlook.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#  This is a module to handle /etc/pam.d files
#
# History
#   -Ver 0.1 : Aug 14 2020
#           - Implement the report option gets the PAM info.
#

import os
import sys
import datetime
# Importing all functions from repo lib pam_handler_lib
from pam_handler_lib import getpam_fact
from pam_handler_lib import getpamline 
from pam_handler_lib import getpamlinestr
from pam_handler_lib import setpamline
from pam_handler_lib import modpamline

# Variable Definition
#------------------------------------------------------------------------------------------------------------
# LogHandling
logdic = dict(
    log=False,
    logfile="/var/log/pam_handler"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".log"
    )
pam_fact={}
pam_handlercfg = dict(
    version="1",
    process=True,
    report=False,
    cmdusage=False,
    backup=True,
    fixincludedir=False
    )

CR="\n"

#List of unknown arguments
pam_module_argumentsnotdetected=[]

# PAM line 
pam_pamfile=""
pam_moduleinterface=""
pam_control=""
pam_modulename=""

#PAM Line strings
pam_stringstoadd=[]
pam_stringstoremove=[]
pam_stringtoget=""
pam_stringtoset=""
pam_stringtomodscr=""
pam_stringtomodtar=""

#PAM Actions
pam_gets=0
pam_sets=0
pam_mod=0

def cmduse():
    print ("Command usage: ")
    print ("  -? or -h                          : Provides this output.")
    print ("  -report                           : Provides a report without any change.")
    print ("  -f:PAM-FILE                       : Specify the PAM file to process.")
    print ("  -mi:MODULE-INTERFACE              : Specify the Module interface to process in the PAM file.")
    print ("  -ctrl:CONTROL                     : Specify the 'Control' to process in the PAM file.")
    print ("  -mn:MODULE-NAME                   : Specify the Module Name to process in the PAM file.")
    print ("  -gets                             : Gets the string line from the PAM file with the sepcified Module Interface, cCntrol and Module name.")
    print ("  -set:STRING                       : Place the string line in the PAM file with the sepcified Module Interface, cCntrol and Module name coincidence.")
    print ("  -add:STRING                       : Add the string to the end of the line in the PAM file with the sepcified Module Interface, Control and Module name coincidence.")
    print ("  -del:STRING                       : Deletes the string from the line in the PAM file with the sepcified Module Interface, Control and Module name coincidence.")
    print ("  -get:STRING                       : Get the first string match from the line in the PAM file with the sepcified Module Interface, Control and Module name coincidence.")
    print ("  -mod:STRMATCH,STRREPLACEMENT      : Replace a match string STRMATCH(could be partial) with STRREPLACEMENT string")
    print ("                                       from the line in the PAM file with the sepcified Module Interface, cCntrol and Module name coincidence.")

    print ("  -delline                          : Deletes the line in the PAM file with the sepcified Module Interface, cCntrol and Module name coincidence.")
    print ("  -addline:STRING                   : Add the line in the PAM file with the sepcified Module Interface, cCntrol and Module name coincidence, with the speciefed STRING.")
    print ("  -moveto:LINE#                     : Move the line in the PAM file with the sepcified Module Interface, cCntrol and Module name coincidence, to the LINE# position.")



# Processs Arguments
#------------------------------------------------------------------------------------------------------------
# Count the arguments
arguments = len(sys.argv) - 1
# Output argument-wise
position = 1
insuficientarguments=False
if arguments == 0:
    # Print cmd usage
    cmdusage=1

if arguments==0:
    pam_handlercfg['cmdusage']=True
print ("INF: pam_handler_cmd Ver:"+pam_handlercfg['version']+" ")
paramargs=[]
paramargs.append("")
paramargs.append("")
paramargs.append("")
paramargs.append("")

while (arguments >= position):
    argunknown=True
    arg=sys.argv[position]
    #print ("Parameter %i: %s" % (position, arg))
    argcomponents=arg.strip().split(':')
    directive=argcomponents[0]
    if len(argcomponents)>1:
        directiveargs=argcomponents[1].strip().split(',')
    else:
        aux=",,"
        directiveargs=aux.strip().split(',')

    # Hadling Help
    if directive == "-h":
        pam_handlercfg['cmdusage']=True
        argunknown=False
    if directive == "-?":
        pam_handlercfg['cmdusage']=True
        argunknown=False

    # Hadling actions
    if directive == "-report":
        pam_handlercfg['report']=True
        argunknown=False
    if directive == "-r":
        pam_handlercfg['report']=True
        argunknown=False
        

    if directive == "-f":
        pam_pamfile=argcomponents[1]
        argunknown=False

    if directive == "-mi":
        pam_moduleinterface=argcomponents[1]
        argunknown=False

    if directive == "-ctrl":
        pam_control=argcomponents[1]
        argunknown=False

    if directive == "-mn":
        pam_modulename=argcomponents[1]
        argunknown=False

    if directive == "-gets":
        pam_gets=1

    if directive == "-get":
        pam_stringtoget=argcomponents[1]
        pam_gets=1

    if directive == "-set":
        pam_stringtoset=argcomponents[1]
        pam_sets=1

    if directive == "-mod":
        auxmod=argcomponents[1]
        auxmodlist=auxmod.split(',')
        pam_stringtomodscr=auxmodlist[0]
        pam_stringtomodtar=auxmodlist[1]
        pam_mod=1        
        


    paramargs[0]=""
    paramargs[1]=""
    paramargs[2]=""
    if len(directiveargs)>3:
        paramargs[3]=directiveargs[3]

    insuficientarguments=False

    #Process unknown arguments
    if argunknown == True:
        pam_module_argumentsnotdetected.append(directive)
    position = position + 1

# Processing Detected Arguments
#------------------------------------------------------------------------------------------------------------
if pam_handlercfg['process']==True:
    #Getting PAM Facts
    pam_fact=getpam_fact(logdic)

    # Detect if have PAM
    if pam_fact['detected']== True:
        #Process options
        #print("PAM detected")
        if (pam_gets==1):
            #print("gets detected")
            #print("pamfile:"+pam_pamfile+" MInterface:"+pam_moduleinterface+" Control:"+pam_control+" ModuleName:"+pam_modulename)
            #print()
            if ((len(pam_pamfile)>0) and (len(pam_moduleinterface)>0) and (len(pam_control)>0) and (len(pam_modulename)>0)):
                if len(pam_stringtoget)==0:
                    result=getpamline(pam_pamfile,pam_moduleinterface,pam_control,pam_modulename,0)
                    print(result)
                else:
                    ##
                    if len(pam_stringtoget)>0:
                        result=getpamlinestr(pam_pamfile,pam_moduleinterface,pam_control,pam_modulename,0,pam_stringtoget)
                        print(result)
                        print("result: "+result['results'][0]['result1'])
                    else:
                        print("ERR: Provide a string to match with '-get=string' parameter. ")

        if (pam_sets==1):
            if ((len(pam_pamfile)>0) and (len(pam_moduleinterface)>0) and (len(pam_control)>0) and (len(pam_modulename)>0) and (len(pam_stringtoset)>0)):
                result=setpamline(pam_pamfile,pam_moduleinterface,pam_control,pam_modulename,1,pam_stringtoset)
                print(result)
            else:
                print("ERR: Couldn't set a the string:"+pam_stringtoset+" to pamfile:"+pam_pamfile+" MInterface:"+pam_moduleinterface+" Control:"+pam_control+" ModuleName:"+pam_modulename)
        
        if (pam_mod==1):
            if ((len(pam_pamfile)>0) and (len(pam_moduleinterface)>0) and (len(pam_control)>0) and (len(pam_modulename)>0) and (len(pam_stringtomodscr)>0) and (len(pam_stringtomodtar)>0)):
                result=modpamline(pam_pamfile,pam_moduleinterface,pam_control,pam_modulename,1,pam_stringtomodscr,pam_stringtomodtar)
                print(result)
        #def modpamline(pamfile,moduleinterface,control,modulename,occurrencenumber,stringmatch,targetstring):
    else:
        print("ERR: PAM not detected")    
#Handling Help
if pam_handlercfg['cmdusage'] == True:
    cmduse()
#------------------------------------------------------------------------------------------------------------
