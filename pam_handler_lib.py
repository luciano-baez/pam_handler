# encoding: utf-8
## #!/usr/bin/python
#
# Copyright: (c) 2020, Luciano Baez <lucianobaez@ar.ibm.com>
#                                   <lucianobaez@kyndyl.com>
#                                   <lucianobaez@outlook.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#  This is a module to handle /etc/pam.d files
#
# History
#   -Ver 0.1 : Aug 14 2020
#           - Implement the report option gets the PAM configuration 


import os
import pwd
import grp
import platform
import subprocess
import json
import shutil
import filecmp
import datetime

def logtofile(filename,logline):
    # open a file to append
    f = open(filename, "a")
    f.write(datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+' : '+logline)
    f.write("\n")
    f.close()

def addtolog(logdic,line):
    logtofile(logdic['logfile'],line)

def catfile(filename):
    f = open(filename, "r")
    text = f.read()
    print(text)
    f.close()
def gettimestampstring():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")

def execute(cmdtoexecute,pamlogdic):
    #executable=" su - db2inst1 -c \""+cmdtoexecute+"\""
    executable=cmdtoexecute
    stdout=""
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    if pamlogdic['log']==True:
        logtofile(pamlogdic['logfile'],'Excecute cmd '+cmdtoexecute+' rc:'+str(rc)+' (execute)')
    stdoutstr=str(stdout, "utf-8")
    #(str(hexlify(b"\x13\x37"), "utf-8"))
    #print (stdoutstr)
    return stdoutstr
    #return stdout

def executefull(cmdtoexecute,pamlogdic):
    executeresult={'stdout':'','stderr':'','rc':''}
    executable=cmdtoexecute
    stdout=""
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    executeresult['stdout']=stdout
    executeresult['stderr']=stderr
    executeresult['rc']=rc
    if pamlogdic['log']==True:
        #logtofile(pamlogdic['logfile'],'Excecute out '+stdout+' ')
        #logtofile(pamlogdic['logfile'],'Excecute err '+stderr+' ')
        logtofile(pamlogdic['logfile'],'Excecute cmd '+cmdtoexecute+' rc:'+str(rc)+' (executefull')
    return executeresult

def executeas(cmdtoexecute,userexe,pamlogdic):
    executable=" su - "+userexe.strip()+" -c \""+cmdtoexecute.strip().replace("\"","\\\"")+"\""
    if (userexe.strip() == "root"):
        # if user is "root" will remove the "su -" (swich user)
        executable=cmdtoexecute.strip()
    else:
        try:
            pwd.getpwnam(userexe.strip())
        except KeyError:
            # if user "userexe" doesen't exists will run as root
            executable=cmdtoexecute.strip()
    #executable=cmdtoexecute
    stdout=""
    #print(executable)
    #print(cmdtoexecute.strip())
    CmdOut = subprocess.Popen([executable], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=True)
    stdout,stderr = CmdOut.communicate()
    rc = CmdOut.returncode
    if pamlogdic['log']==True:
        logtofile(pamlogdic['logfile'],'Excecute cmd '+cmdtoexecute+' by '+userexe+'  rc:'+str(rc)+' (executeas')
    return stdout


def getuserlist():
    resultlist=[]
    usersfile="/etc/passwd"
    if os.path.isfile(usersfile):
        with open(usersfile,"r") as sourcefh:
            line = sourcefh.readline()
            while line:
                auxline=line.replace('\n', '').strip().split(':')
                firstword=''
                if (len(auxline)>0):
                    firstword=auxline[0]
                if (firstword != ''):
                    resultlist.append(firstword)
                line = sourcefh.readline()
            sourcefh.close
    return resultlist

def getgrouplist():
    resultlist=[]
    usersfile="/etc/group"
    if os.path.isfile(usersfile):
        with open(usersfile,"r") as sourcefh:
            line = sourcefh.readline()
            while line:
                auxline=line.replace('\n', '').strip().split(':')
                firstword=''
                if (len(auxline)>0):
                    firstword=auxline[0]
                if (firstword != ''):
                    resultlist.append(firstword)
                line = sourcefh.readline()
            sourcefh.close
    return resultlist


def getlinefromfile(linenumber,file):
    lineresult=""
    linepos=1
    done=0
    if os.path.isfile(file):
        with open(file,"r") as filefh:
            stringline = filefh.readline()
            while stringline and done==0:
                if (linenumber==linepos):
                    lineresult=stringline
                    done=1
                stringline = filefh.readline()
                linepos=linepos+1
            filefh.close
    else:
        lineresult="-1"
    return lineresult

def getosinfo(pamlogdic):
    osdic={}
    osdic['os']=platform.system()
    osdic['distro']=str('')
    osdic['distrocode']=str('')
    osdic['version']=str('')
    osdic['majorversion']=str('')
    if osdic['os'].upper()=='LINUX':
        if os.path.isfile('/etc/SuSE-release'):
            osdic['distrocode']='SLES'
            result1=executefull('cat /etc/SuSE-release | head -1',pamlogdic)
            result2=executefull('cat /etc/SuSE-release| grep PATCHLEVEL',pamlogdic)
            osdic['distro']=result1['stdout'].decode('UTF-8')+' - '+result2['stdout'].decode('UTF-8')
            result1=executefull("cat /etc/SuSE-release | grep VERSION|awk '{print $3}'",pamlogdic)
            osdic['version']=str(result1['stdout'])

        if os.path.isfile('/etc/redhat-release'):
            osdic['distrocode']='RHEL'
            commmand="cat /etc/redhat-release | head -1|tr -d '\n'|tr -d '\r'"
            result1=executefull(commmand,pamlogdic)
            osdic['distro']=result1['stdout']
            commmand="cat /etc/os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'|tr -d '\n'|tr -d '\r'"
            result1=executefull(commmand,pamlogdic)
            osdic['version']=str(result1['stdout'].decode('UTF-8'))

        if os.path.isfile('/etc/fedora-release'):
            osdic['distrocode']='FEDORA'
            result1=executefull('cat /etc/fedora-release | head -1',pamlogdic)
            osdic['distro']=result1['stdout'].decode('UTF-8')
            #result1=executefull("cat os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'",pamlogdic)
            #osdic['version']=result1['stdout']

        if os.path.isfile('/etc/slackware-release'):
            osdic['distrocode']='SLACKWARE'
            result1=executefull('cat /etc/slackware-release | head -1',pamlogdic)
            osdic['distro']=result1['stdout'].decode('UTF-8')
            #result1=executefull("cat os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'",pamlogdic)
            #osdic['version']=result1['stdout']

        if os.path.isfile('/etc/debian_release'):
            osdic['distrocode']='DEBIAN'
            result1=executefull('cat /etc/debian_release | head -1',pamlogdic)
            osdic['distro']=result1['stdout'].decode('UTF-8')
            #result1=executefull("cat os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'",pamlogdic)
            #osdic['version']=result1['stdout']

        if os.path.isfile('/etc/mandrake-release'):
            osdic['distrocode']='MANDRAKE'
            result1=executefull('cat /etc/mandrake-release | head -1',pamlogdic)
            osdic['distro']=result1['stdout'].decode('UTF-8')
            #result1=executefull("cat os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'",pamlogdic)
            #osdic['version']=result1['stdout']

        if os.path.isfile('/etc/yellowdog-release'):
            osdic['distrocode']='YELLOWDOG'
            result1=executefull('cat /etc/yellowdog-release | head -1',pamlogdic)
            osdic['distro']=result1['stdout'].decode('UTF-8')
            #result1=executefull("cat os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'",pamlogdic)
            #osdic['version']=result1['stdout']

        if os.path.isfile('/etc/sun-release'):
            osdic['distrocode']='SUN'
            result1=executefull('cat /etc/sun-release | head -1',pamlogdic)
            osdic['distro']=result1['stdout'].decode('UTF-8')
            #result1=executefull("cat os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'",pamlogdic)
            #osdic['version']=result1['stdout']

        if os.path.isfile('/etc/release'):
            osdic['distrocode']='SUN'
            result1=executefull('cat /etc/release | head -1',pamlogdic)
            osdic['distro']=result1['stdout']
            #result1=executefull("cat os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'",pamlogdic)
            #osdic['version']=result1['stdout']

        if os.path.isfile('/etc/gentoo-release'):
            osdic['distrocode']='GENTOO'
            result1=executefull('cat /etc/gentoo-release | head -1',pamlogdic)
            osdic['distro']=result1['stdout'].decode('UTF-8')
            #result1=executefull("cat os-release| grep ^VERSION_ID|awk -F= '{print $2}'|sed -e 's/\\\"//g'",pamlogdic)
            #osdic['version']=result1['stdout']
        
        #print(osdic['version'])
        auxlist=osdic['version'].split('.')
        if len(auxlist)>0:
            osdic['majorversion']=auxlist[0].strip()
	
    if osdic['os'].upper()=='AIX':
        osdic['distrocode']='AIX'
        result1=executefull('/usr/bin/oslevel -s',pamlogdic)
        osdic['distro']=result1['AIX'].decode('UTF-8')

        osdic['majorversion']=osdic['version'].split('-')[0].strip()
	
    return osdic

def getparsedpamline(pamline,comment):
    palmlinerecord={}
    palmlinerecord['ignore']=False
    if comment==False:
        palmlinerecord['line']=pamline.replace('\n', '').strip()
    else:
        palmlinerecord['line']='#pam_handler '+pamline.replace('\n', '').strip()
    palmlinerecord['module_type']='pam_handler'
    palmlinerecord['control_flags']=''
    palmlinerecord['module_path']=''
    palmlinerecord['module_options']=''
    
    completeline=pamline.replace('\t', ' ')    
    if len(completeline.strip())>0:
        firstchar=pamline.strip()[0]
        auxline=completeline.replace('\n', '').strip().split()
        wordcount=len(auxline)
        firstword=""
        secondword=""
        thirdword=""
        lastwords=""
        if (firstchar != "#"):
            if (wordcount>0):
                firstword=auxline[0]
                
                if (wordcount>1):
                    secondword=auxline[1]
                    if (wordcount>2):
                        thirdword=auxline[2]
                        if (wordcount>3):
                            wordpos=3
                            auxstring=""
                            while (wordcount>wordpos):
                                auxstring=auxstring+' '+auxline[wordpos]
                                wordpos=wordpos+1
                            lastwords=auxstring.strip()
            palmlinerecord['module_type']=firstword
            palmlinerecord['control_flags']=secondword
            palmlinerecord['module_path']=thirdword
            palmlinerecord['module_options']=lastwords
        else:
            #Commented Line
            palmlinerecord['ignore']=True
    else:
        #Empty line
        palmlinerecord['ignore']=True

    return palmlinerecord

def getfilepaminfo(filename):
    respamfile={}
    respamfile['filename']=filename
    respamfile['filecontent']=[]
    respamfile['fileexists']=False
    if os.path.isfile(respamfile['filename']):
        respamfile['fileexists']=True
        breakeloop=0
        palmlinenumber=0
        with open(respamfile['filename'],"r") as pamfilehandler:
            pamline = pamfilehandler.readline()            
            while (pamline and breakeloop==0):

                palmlinerecord=getparsedpamline(pamline,False)
                
                respamfile['filecontent'].append(palmlinerecord)
                pamline = pamfilehandler.readline()

        pamfilehandler.close

    return respamfile

def getpamfiles(operatingsystem):
    pamfiles={}

    #definning Redhat
    pamfilesbyservice={}
    pamfilesbyservice['cron']=getfilepaminfo('/etc/pam.d/crond')
    pamfilesbyservice['dtlogin']=getfilepaminfo('/etc/pam.d/crond')
    pamfilesbyservice['dtsession']=getfilepaminfo('')
    pamfilesbyservice['ftp']=getfilepaminfo('')
    pamfilesbyservice['init']=getfilepaminfo('')
    pamfilesbyservice['login']=getfilepaminfo('/etc/pam.d/login')
    pamfilesbyservice['passwd']=getfilepaminfo('/etc/pam.d/passwd')
    pamfilesbyservice['ppp']=getfilepaminfo('/etc/pam.d/ppp')
    pamfilesbyservice['rexd']=getfilepaminfo('')
    pamfilesbyservice['rlogin']=getfilepaminfo('')
    pamfilesbyservice['rsh']=getfilepaminfo('')
    pamfilesbyservice['sac']=getfilepaminfo('')
    pamfilesbyservice['sshd']=getfilepaminfo('/etc/pam.d/sshd')
    pamfilesbyservice['su']=getfilepaminfo('/etc/pam.d/su')
    pamfilesbyservice['system-auth']=getfilepaminfo('/etc/pam.d/system-auth')
    pamfilesbyservice['telnet']=getfilepaminfo('')
    pamfilesbyservice['ttymon']=getfilepaminfo('')
    pamfilesbyservice['uucp']=getfilepaminfo('')

    pamfiles['RHEL']=pamfilesbyservice.copy()
    pamfiles['SLES']={}
    #definning AIX
    pamfilesbyservice={}
    pamfilesbyservice['ALL']=getfilepaminfo('/etc/pam.conf')
    pamfiles['AIX']=pamfilesbyservice.copy()
    filename=''

    return pamfiles[operatingsystem]

def getservicenamebypamfile(pam_file,pam_fact):
    resultcode={}
    resultcode['rc']=0
    resultcode['results']=''
    resultcode['stdout']=''
    servicenamekey=''
    found=0
    for pamfile in pam_fact['files']:
        if pam_file==pamfile['filename']:
            servicenamekey=keys[pamfile]
            found=1
    if found==1:
        resultcode['results']=servicenamekey
        resultcode['stdout']='INF- Service name found ('+servicenamekey+') (rc=0)'
    else:
        resultcode['rc']=1
        resultcode['stdout']='INF- Service name not found with filename '+pam_file+'(rc=1)'
    return resultcode

def getpam_fact(pamlogdic):
    resultfact={}
    resultfact['detected']=False
    #resultfact['platform']=getsudoplatform(pamlogdic)
    #resultfact['installed']=getsudoinstalled(SUDODIC['platform'],pamlogdic)
    result=executefull("/usr/bin/ldd /bin/su | grep libpam|wc -l|sed -e 's/ //g'",pamlogdic)
    if int(result['stdout']) > 0:
        resultfact['detected']=True
        resultfact['os']=getosinfo(pamlogdic)
        resultfact['conf_file']=''
        if resultfact['os']['os'].upper() == 'LINUX':
            resultfact['conf_file']='/etc/pam.conf'
        if resultfact['os']['os'].upper() == 'AIX':
            resultfact['conf_file']='/etc/pam.conf'
        resultfact['files']=getpamfiles(resultfact['os']['distrocode'])
    addtolog(pamlogdic,"INF- Getting PAM facts.")
    return resultfact

def getfile(service_name,pam_fact):
    fcontent={}
    if pam_fact['os']['distrocode']=="AIX":
        fcontent=pam_fact['files']['ALL']
    if pam_fact['os']['distrocode']=="RHEL":
        fcontent=pam_fact['files'][service_name]
    return fcontent


def pamlinepresent(service_name,pam_line,atpos,comment,pam_fact,logdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['results']=[]
    resultcode['stdout']=''
    filename=''
    filecontent=getfile(service_name,pam_fact)

    #line to find
    linerecord=getparsedpamline(pam_line,comment)
    if filecontent['fileexists']==True:
        #Process file in memory
        palmlinerecord=getparsedpamline(pam_line,comment)
        entriefound=False
        entriefoundat=0
        filepos=0
        for filerecord in filecontent["filecontent"]:
            if entriefound==False:
                if filerecord['ignore']==False:
                    if filerecord['module_type'].upper()==linerecord['module_type'].upper():
                        if filerecord['control_flags'].upper()==linerecord['control_flags'].upper():
                            if filerecord['module_path'].upper()==linerecord['module_path'].upper():
                                filerecord['module_options']=linerecord['module_options']
                                filerecord['line']=linerecord['line']
                                entriefound=True
                                entriefoundat=filepos
            filepos=filepos+1
            
        if entriefound == False:
            filecontent["filecontent"].insert(atpos,linerecord)
            # Line was not present and added
            resultcode['rc']=1
        else:
          if entriefoundat != atpos:
            filecontent["filecontent"].insert(atpos, filecontent["filecontent"].pop(entriefoundat))
            # Line was present and moved to the right position
            resultcode['rc']=2
          else:
            # Line was present and in the right position
            resultcode['rc']=0

    else:
        # File not found
        resultcode['rc']=3
    
    #End
    rcstdout=["INF: Pam line \""+pam_line+"\" is already present at "+filecontent["filename"]+" file at "+str(atpos)+" position (rc=0).",
            "INF: Pam line \""+pam_line+"\" not present at "+filecontent["filename"]+" but added at position "+str(atpos)+" (rc=1).",
            "INF: Pam line \""+pam_line+"\" is already present at "+filecontent["filename"]+" file on position "+str(entriefoundat)+" and moved to position "+str(atpos)+"(rc=2).",
            "ERR: file "+filecontent["filename"]+" not found (rc=3).",
            "ERR: Pam line \""+pam_line+"\" cooulnd't be added to "+filecontent["filename"]+" (rc=4)."
            ]
    resultcode['stdout']=rcstdout[resultcode['rc']]
    addtolog(logdic,resultcode['stdout'])
    return resultcode

def pamlinepresentatend(service_name,pam_line,comment,pam_fact,logdic):
    resultcode={}
    filecontent=getfile(service_name,pam_fact)
    #print(filecontent)
    atpos=len(filecontent['filecontent'])
    resultcode=pamlinepresent(service_name,pam_line,atpos,comment,pam_fact,logdic)
    return resultcode

def pamlinepresentafterlinerecord(service_name,pam_line,linereferencerecord,comment,pam_fact,logdic):
    resultcode={}
    resultcode['rc']=2
    resultcode['results']=[]
    resultcode['stdout']=''
    filecontent=getfile(service_name,pam_fact)
    entriefound=False
    if filecontent['fileexists']==True:
        #Process file in memory
        #palmlinerecord=getparsedpamline(pam_line,comment)
        entriefoundat=0
        filepos=0
        auxfilerecord={}
        for filerecord in filecontent["filecontent"]:
            if entriefound==False:
                if filerecord['ignore']==False:
                    if filerecord['module_type'].upper()==linereferencerecord['module_type'].upper():
                        if filerecord['control_flags'].upper()==linereferencerecord['control_flags'].upper():
                            if filerecord['module_path'].upper()==linereferencerecord['module_path'].upper():
                                #filerecord['module_options']=linereferencerecord['module_options']
                                #filerecord['line']=linereferencerecord['line']
                                entriefound=True
                                entriefoundat=filepos
            filepos=filepos+1

        if entriefound==True:
            resultcode=pamlinepresent(service_name,pam_line,entriefoundat+1,comment,pam_fact,logdic)
        else:
            resultcode['rc']=4

    else:
        # File not presnet
        resultcode['rc']=3


    #End
    if entriefound==False:
        rcstdout=["INF:  (rc=0).",
                "INF: (rc=1).",
                "INF: (rc=2).",
                "ERR: File  "+filecontent['filename']+" not present (rc=3).",
                "ERR: Reference Pam line \""+linereferencerecord['line']+"\" not present at "+filecontent['filename']+" (rc=4).",
                "ERR: Not defined (rc=5)."
                ]
        resultcode['stdout']=rcstdout[resultcode['rc']]
    addtolog(logdic,resultcode['stdout'])
    return resultcode

def pamlinepresentafterline(service_name,pam_line,pam_line_after,comment,pam_fact,logdic):
    resultcode={}
    print(pam_line_after)
    linereferencerecord=getparsedpamline(pam_line_after,comment)
    resultcode=pamlinepresentafterlinerecord(service_name,pam_line,linereferencerecord,comment,pam_fact,logdic)
    return resultcode

def pamremovelinerecord(service_name,linerecord,pam_fact,logdic):
    resultcode={}
    resultcode['rc']=0
    resultcode['results']=[]
    resultcode['stdout']=''
    filecontent=getfile(service_name,pam_fact)

    if filecontent['fileexists']==True:
        #Process file in memory
        entriefound=False
        entriefoundat=0
        filepos=0
        for filerecord in filecontent["filecontent"]:
            if entriefound==False:
                if filerecord['ignore']==False:
                    if filerecord['module_type'].upper()==linerecord['module_type'].upper():
                        if filerecord['control_flags'].upper()==linerecord['control_flags'].upper():
                            if filerecord['module_path'].upper()==linerecord['module_path'].upper():
        
                                #filerecord['module_options']=linerecord['module_options']
                                #filerecord['line']=linerecord['line']
                                entriefound=True
                                entriefoundat=filepos
            filepos=filepos+1

        if entriefound==True:
            filecontent["filecontent"].pop(entriefoundat)
        else:
            resultcode['rc']=1

    else:
        # File not presnet
        resultcode['rc']=2


    #End

    rcstdout=["INF: Pam line \""+linerecord['line']+"\" removed from "+filecontent["filename"]+"file at position "+str(entriefoundat)+"  (rc=0). ",
            "WAR: Pam line \""+linerecord['line']+"\" is not present at "+filecontent["filename"]+" file (rc=1).",
            "ERR: Pam file "+filecontent["filename"]+" does not exists (rc=2).",
            "ERR: Not defined (rc=3)."
            ]
    resultcode['stdout']=rcstdout[resultcode['rc']]
    addtolog(logdic,resultcode['stdout'])
    return resultcode

def pamremoveline(service_name,pam_line,pam_fact,logdic):
    resultcode={}
    linerecord=getparsedpamline(pam_line,False)
    resultcode=pamremovelinerecord(service_name,linerecord,pam_fact,logdic)
    return resultcode

def pamcommentlinerecord(service_name,linerecord,pam_fact,logdic):
    resultcode={}
    resultcode['rc']=1
    resultcode['results']=[]
    resultcode['stdout']=''
    filecontent=getfile(service_name,pam_fact)

    if filecontent['fileexists']==True:
        #Process file in memory
        entriefound=False
        entriefoundat=0
        filepos=0
        for filerecord in filecontent["filecontent"]:
            if filerecord['ignore']==False:
                if filerecord['module_type'].upper()==linerecord['module_type'].upper():
                    if filerecord['control_flags'].upper()==linerecord['control_flags'].upper():
                        if filerecord['module_path'].upper()==linerecord['module_path'].upper():
                            filerecord['line']="#"+filerecord['line']
                            filerecord['ignore']=True
                            entriefound=True
                            entriefoundat=filepos
                            resultcode['rc']=0
            filepos=filepos+1

    else:
        # File not presnet
        resultcode['rc']=2


    #End
    if entriefound==False:
        rcstdout=["INF: Pam line \""+linerecord['line']+"\" commentedd on file "+filecontent["filename"]+" at position "+str(entriefoundat)+"  (rc=0).",
                "WAR: Pam line \""+linerecord['line']+"\" is not present at "+filecontent["filename"]+" file (rc=1).",
                "ERR: Pam file "+filecontent["filename"]+" does not exists (rc=2).",
                "ERR: Not defined (rc=3)."
                ]
        resultcode['stdout']=rcstdout[resultcode['rc']]
    addtolog(logdic,resultcode['stdout'])
    return resultcode

def pamcommentline(service_name,pam_line,pam_fact,logdic):
    resultcode={}
    linerecord=getparsedpamline(pam_line,False)
    resultcode=pamcommentlinerecord(service_name,linerecord,pam_fact,logdic)
    return resultcode

def pamsavefile(service_name,pam_fact,logdic,backup):
    resultcode={}
    resultcode['rc']=0
    resultcode['results']=[]
    resultcode['stdout']=''
    filecontent=getfile(service_name,pam_fact)
    if backup==True:
        backupfilename=filecontent['filename']+"_"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".bkp"
        shutil.copy2(filecontent['filename'],backupfilename)
        os.chmod(backupfilename, 0o644)
        addtolog(logdic,"INF: "+backupfilename+" backup file created from file "+filecontent['filename'])

    pamtempfile="/tmp/pam_handler_"+service_name+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".tmp"
    if filecontent['fileexists']==True:
        entriefound=False
        entriefoundat=0
        filepos=0
        addtolog(logdic,"INF: Generating file "+pamtempfile+" from pam_handler module.")
        # open a file to append
        newpamfilehandler = open(pamtempfile, "a")        
        for filerecord in filecontent["filecontent"]:
            auxline=filerecord['line'].replace('\n', '')
            newpamfilehandler.write(auxline)
            newpamfilehandler.write("\n")            
            filepos=filepos+1
        newpamfilehandler.close()

        if filecmp.cmp(pamtempfile,filecontent['filename'],shallow=False):
            addtolog(logdic,"INF: File "+filecontent['filename']+" was not modified .")
            os.remove(pamtempfile)
        else:
            addtolog(logdic,"INF: Updating file "+filecontent['filename']+" .")
            shutil.copy2(pamtempfile,filecontent['filename'])
            os.remove(pamtempfile)
            
        
    else:
        resultcode['rc']=1

    #End
    rcstdout=["INF: Pam file \""+filecontent['filename']+"\" saved succesfully (rc=0).",
            "ERR: Pam file \""+filecontent['filename']+"\" doesen't exists (rc=1).",
            "ERR: Pam file \""+filecontent['filename']+"\" could not be saved (rc=2).",
            "ERR: Pam ERROR (rc=3)."
            ]
    resultcode['stdout']=rcstdout[resultcode['rc']]
    return resultcode
