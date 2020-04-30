# -*- coding: utf-8 -*-

"""
TODO:
- Function to create sandbox
- Exit code
"""

from future import standard_library
standard_library.install_aliases()

import os
import signal
import errno
import subprocess
import uuid
import datetime
from pathlib2 import Path
from consolemsg import step, success, warn, u
from yamlns import namespace as ns

executionRoot = Path('executions')
children = {}

class Execution(object):
    """
    @staticmethod
    def start(name=None, command=None):
        executionName = "{}-{}".format(datetime.datetime.now(), uuid.uuid4())
        execution = Execution(executionName)
        step("Running task '{}'", executionName )
        execution.createSandbox()
        command = "../../example.sh /usr".split()
        #command = "launcherwrapper.sh tomatic_scheduler.py afasdflkjas "
        step("Running {}", command)
        log = execution.outputFile.open('w')
        process = subprocess.Popen(
            command,
            cwd=str(execution.path),
            stdout=log,
            stderr=log,
        )
        success("Running child: {}", process.pid)
        (execution.path / 'pid').write_text(u(process.pid))
        children[process.pid] = process
        return executionName

    @staticmethod
    def list():
        return (
            Execution(executiondir.name)
            for executiondir in sorted(executionRoot.iterdir(), reverse=True)
        )
    """

    def __init__(self, name):
        self.name = name
        self.path = executionRoot/name

    def createSandbox(self):
        self.path.mkdir()

    @property
    def outputFile(self):
        return self.path / 'output.txt'

    @property
    def pidFile(self):
        return self.path / 'pid'

    """
    @property
    def pid(self):
        if hasattr(self, '_pid'):
            return self._pid
        if not self.pidFile.exists():
            return None
        self._pid = int(self.pidFile.read_text())
        return self._pid

    @property
    def isAlive(self):
        import psutil
        if not psutil.pid_exists(self.pid):
            return False
        status = psutil.Process(self.pid).status()
        if status == psutil.STATUS_ZOMBIE:
            children[self.pid].wait()
            del children[self.pid]
            return False
        if status == psutil.STATUS_DEAD:
            return False
        return True

    @property
    def state(self):
        if self.pid is None: return 'Launching'
        if self.isAlive: return 'Running'
        return 'Stopped'

    def stop(self):
        warn("Stoping {}", self.pid)
        try:
            os.kill(self.pid, signal.SIGINT)
        except OSError as err:
            if err.errno == errno.ESRCH: # Process not found
                print(type(err))
                return
            raise

    def listInfo(self):
        return ns(
            name = self.name,
            killDisplay = 'inline' if self.state == 'Running' else 'none',
            state = self.state,
            )

    """


class PlannerExecution(Execution):

    def __init__(self, monday, configPath):
        name = monday
        super(PlannerExecution, self).__init__(name=name)

    def createSandbox(self):
        super(PlannerExecution, self).createSandbox()
        (self.path/'config.yaml').write_text("")
        (self.path/'holidays.conf').write_text("")
        (self.path/'drive-certificate.json').write_text("")


# TODO: Testing del sandbox



# vim: ts=4 sw=4 et
