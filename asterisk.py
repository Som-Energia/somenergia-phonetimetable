# -*- coding: utf-8 -*-
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
from tempfile import NamedTemporaryFile as mktmpfile

class Pbx(object):

    def __init__(self,pbx,sshconfig):
        self._pbx = pbx
        self._sshconfig = sshconfig

    def sendConfNow(self, conf):
        with SSHClient() as ssh:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            ssh.connect(self._sshconfig['pbxhost'],
                username=self._sshconfig['username'],
                password=self._sshconfig['password'])
            scp = SCPClient(ssh.get_transport())
            with mktmpfile(delete=False) as f:
                f.write(conf)
                tmpConfFile = f.name
            scp.put(tmpConfFile,self._sshconfig['path'])
        self._pbx.Command('reload')
    def _pause(self, day, turn , sip, paused):
        queue="entrada_cua_{day}_{turn}".format(day=day,turn=turn)
        self._pbx.QueuePause(queue,"SIP/{}".format(sip),paused)
        
    def pause(self, day, turn, sip):
        self._pause(day,turn,sip,True)
    
    def resume(self, day, turn, sip):
        self._pause(day,turn,sip,False)

    def parsePause(self, diff):
        for day in diff.keys():
            for turn in diff[day]:
                for ext in diff[day][turn]:
                    if (diff[day][turn][ext]
                        == "added"):
                        self.pause(day,
                            turn,
                            ext)
                    elif (diff[day][turn][name]
                        == "resumed"):
                        self.resume(day,
                            turn,
                            ext)

                            
    def receiveConf(self):
        return self._pbx.Queues()
