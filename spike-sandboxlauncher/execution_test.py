# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import time
import datetime
import errno
from pathlib2 import Path
from yamlns import namespace as ns
from execution import (
    Execution,
    executionRoot,
    PlannerExecution,
    removeRecursive,
    children,
)

def assertSandboxes(self, expected):
    result = [
        str(p)
        for p in sorted(executionRoot.glob('**/*'))
    ]
    self.assertEqual(result, expected)

def assertContentEqual(self, path1, path2):
    self.assertMultiLineEqual(
        path1.read_text(encoding='utf8'),
        path2.read_text(encoding='utf8'),
    )


class Execution_Test(unittest.TestCase):

    assertSandboxes = assertSandboxes
    assertContentEqual = assertContentEqual

    def setUp(self):
        removeRecursive(executionRoot)
        executionRoot.mkdir()

    def test_simpleProperties(self):
        e = Execution(name="hola")
        self.assertEqual(e.name, 'hola')
        self.assertEqual(e.path, executionRoot/'hola')
        self.assertEqual(e.outputFile, executionRoot/'hola'/'output.txt')
        self.assertEqual(e.pidFile, executionRoot/'hola'/'pid')
        self.assertEqual(e.pid, None)

    def test_createSandbox(self):
        e = Execution(name="hola")
        self.assertEqual(False, e.path.exists())
        e.createSandbox()
        self.assertEqual(True, e.path.exists())
        self.assertSandboxes([
            'executions/hola',
        ])

    def test_list_noExecutions(self):
        result = [e.name for e in Execution.list()]
        self.assertEqual(result,[
        ])

    def test_list_singleExecution(self):
        execution = Execution(name="First")
        execution.createSandbox()
        result = [e.name for e in Execution.list()]
        self.assertEqual(result,[
            "First",
        ])

    def test_list_manyExecutions(self):
        execution1 = Execution(name="First")
        execution1.createSandbox()
        execution2 = Execution(name="Last")
        execution2.createSandbox()
        result = [e.name for e in Execution.list()]
        self.assertEqual(result,[
            "Last",
            "First",
        ])

    def waitExist(self, file, miliseconds=100):
        for i in range(miliseconds):
            if file.exists():
                return True
            time.sleep(0.001)
        return False
        

    def test_run_executesCommand(self):
        execution = Execution(name="One")
        execution.createSandbox()
        execution.run([
            "python",
            "-c",
            "open('{}','w').write('hola')".format(execution.path.resolve()/'itworks'),
        ])
        self.assertEqual(self.waitExist(execution.path/'itworks',1000), True)
        self.assertEqual((execution.path/'itworks').read_text(), 'hola')

    def test_run_inSandbox(self):
        execution = Execution(name="One")
        execution.createSandbox()
        execution.run([
            "python",
            "-c",
            "open('{}','w').write('hola')".format('itworks'),
        ])
        self.waitExist(execution.path/'itworks')
        self.assertEqual((execution.path/'itworks').read_text(), 'hola')

    def test_run_generatesPidFile(self):
        execution = Execution(name="One")
        execution.createSandbox()
        execution.run([
            "python",
            "-c",
            "import os; open('mypid','w').write('{}'.format(os.getpid()))",
        ])
        self.waitExist(execution.path/'mypid')
        self.assertContentEqual(
            execution.path/'mypid',
            execution.pidFile)

    def test_run_capturesStdOut(self):
        execution = Execution(name="One")
        execution.createSandbox()
        execution.run([
            "python",
            "-c",
            "import sys;"
                "sys.stdout.write('Hola'); sys.stdout.flush();"
                "open('ended','w').write('')",
        ])
        self.waitExist(execution.path/'ended')
        self.assertEqual((execution.outputFile).read_text(), "Hola") 

    def test_run_capturesStdErr(self):
        execution = Execution(name="One")
        execution.createSandbox()
        execution.run([
            "python",
            "-c",
            "import sys;"
                "sys.stderr.write('Hola'); sys.stderr.flush();"
                "open('ended','w').write('')",
        ])
        self.waitExist(execution.path/'ended')
        self.assertEqual((execution.outputFile).read_text(), "Hola") 

    def test_run_badCommand(self):
        execution = Execution(name="One")
        execution.createSandbox()
        with self.assertRaises(OSError) as ctx:
            execution.run([
                "badcommandthatdoesnotexist",
            ])
        self.assertEqual(format(ctx.exception),
            "[Errno 2] No such file or directory")

        # TODO: This should be more detectable for the listing

    def test_pid_whenNotRunning(self):
        execution = Execution(name="One")
        execution.createSandbox()
        self.assertEqual(None, execution.pid)

    def test_pid_afterRunning(self):
        execution = Execution(name="One")
        execution.createSandbox()
        p = execution.run('ls') # This is new
        self.assertEqual(p.pid, execution.pid)

    def test_pid_onceRunningIsCached(self):
        execution = Execution(name="One")
        execution.createSandbox()
        p = execution.run('ls')
        execution.pid # this access caches
        execution.pidFile.unlink() # This is new
        self.assertEqual(p.pid, execution.pid)

    def test_stop_sendsSigInt_python(self):
        execution = Execution(name="One")
        execution.createSandbox()
        execution.run([
            "python",
            "-c",
            "import signal, time;\n"
            "from pathlib2 import Path;\n"
            "terminated=False;\n"
            "def stop(signal, frame):\n"
            "  global terminated\n"
            "  terminated=True\n"
            "signal.signal(signal.SIGINT, stop)\n"
            "Path('ready').touch()\n"
            "while not terminated: time.sleep(0.01)\n"
            "Path('ended').touch()\n"
            ,
        ])
        self.assertEqual(self.waitExist(execution.path/'ready',1000), True)
        self.assertEqual((execution.path/'ended').exists(), False)
        found = execution.stop()
        self.assertEqual(self.waitExist(execution.path/'ended',1000), True)
        self.assertEqual(found, True)

    def test_stop_sendsSigInt_bash(self):
        execution = Execution(name="One")
        execution.createSandbox()
        execution.run([
            "bash",
            "-c",
            "terminated=0\n"
            "function stop() {\n"
            "    touch stopping\n"
            "    terminated=1\n"
            "}\n"
            "trap 'stop' SIGINT\n"
            "touch ready\n"
            "while true; do\n"
            "  [ $terminated == 1 ] && {\n"
            "    touch terminated\n"
            "    break\n"
            "}\n"
            "done\n"
            "touch ended\n"
            ,
        ])
        self.assertEqual(self.waitExist(execution.path/'ready',1000), True)
        self.assertEqual((execution.path/'ended').exists(), False)
        found = execution.stop()
        self.assertEqual(found, True)
        self.assertEqual(self.waitExist(execution.path/'ended',1000), True)

    def test_stop_afterProcessEnds_exitsSilently(self):
        execution = Execution(name="One")
        execution.createSandbox()
        p = execution.run([
            "false",
        ])
        p.wait()
        stopped = execution.stop()
        self.assertEqual(stopped, False)

    def test_stop_unlaunched_exitsSilently(self):
        execution = Execution(name="One")
        execution.createSandbox()
        stopped = execution.stop()
        self.assertEqual(stopped, False)

    def test_stop_otherOSErrorsPassThrough(self):
        execution = Execution(name="One")
        execution.createSandbox()
        # Init process (1) belongs to root, cannot send it a signal
        execution.pidFile.write_text("1")
        with self.assertRaises(OSError) as ctx:
            execution.stop()
        self.assertEqual(ctx.exception.errno, errno.EPERM)

    def test_name_byDefault(self):
        execution = Execution(name='')
        self.assertRegexpMatches(
            execution.name,
            r'^{:%Y-%m-%d-%H:%M:%S}-[0-9a-f-]{{36}}$'.format(
                datetime.datetime.now()))


    def test_start_namesByDefault(self):
        sandbox = Execution.start(
            command=[
                "bash",
                "-c",
                "touch itworked",
            ])
        self.assertRegexpMatches(sandbox,
            r'^{:%Y-%m-%d-%H:%M:%S}-[0-9a-f-]{{36}}$'.format(
                datetime.datetime.now()))
        execution = Execution(sandbox)
        self.waitExist(execution.path/'itworked',1000)

    def test_start_createsSandbox(self):
        sandbox = Execution.start(
            command=[
                "bash",
                "-c",
                "touch itworked",
            ])
        execution = Execution(sandbox)
        self.assertEqual(True, execution.path.exists())

    def test_start_executesCommand(self):
        sandbox = Execution.start(
            command=[
                "bash",
                "-c",
                "touch itworked",
            ])
        execution = Execution(sandbox)
        self.assertEqual(self.waitExist(execution.path/'itworked',1000), True)

    def test_start_extendChildren(self):
        sandbox = Execution.start(
            command=[
                "bash",
                "-c",
                "touch itworked",
            ])
        execution = Execution(sandbox)
        self.assertIn(execution.pid, children)
        self.assertEqual(children[execution.pid].pid, execution.pid)


    def test_remove_whenFinished(self):
        execution = Execution(name="One")
        execution.createSandbox()
        p = execution.run([
            "python",
            "-c",
            "from pathlib2 import Path\n"
            "Path('ended').touch()",
        ])
        p.wait()
        success = execution.remove()
        self.assertEqual(Execution.list(), [])
        self.assertEqual(success, True)

    def test_remove_unstarted(self):
        execution = Execution(name="One")
        execution.createSandbox()
        success = execution.remove()
        self.assertEqual([e.name for e in Execution.list()], ['One'])
        self.assertEqual(success, False)

    def test_remove_unfinished(self):
        execution = Execution(name="One")
        execution.createSandbox()
        p = execution.run([
            "bash",
            "-c",
            "trap 'echo aborted; exit 0' SIGINT\n"
            "touch ready\n"
            "while true; do sleep 1; done\n"
            "touch ended\n"
            "echo ended\n"
        ])
        print(execution.outputFile.read_text())
        self.waitExist(execution.path/'ready')
        success = execution.remove()
        self.assertEqual([e.name for e in Execution.list()], ['One'])
        self.assertEqual(success, False)
        execution.stop()
        p.wait()


    def test_kill_unstarted(self):
        execution = Execution("One")
        execution.createSandbox()
        found = execution.kill()
        self.assertEqual(found, False)

    def test_kill_finished(self):
        execution = Execution(name="One")
        execution.createSandbox()
        p = execution.run([
            "bash",
            "-c",
            "echo ended\n"
        ])
        p.wait()
        found = execution.kill()
        self.assertEqual(found, False)

    def test_kill_running(self):
        execution = Execution(name="One")
        execution.createSandbox()
        p = execution.run([
            "bash",
            "-c",
            "touch ready\n"
            "while true; do sleep 1; done\n"
        ])
        self.waitExist(execution.path/'ready')
        found = execution.kill()
        self.assertEqual(found, True)

    def test_kill_otherOSErrorsPassThrough(self):
        execution = Execution(name="One")
        execution.createSandbox()
        # Init process (1) belongs to root, cannot send it a signal
        execution.pidFile.write_text("1")
        with self.assertRaises(OSError) as ctx:
            execution.kill()
        self.assertEqual(ctx.exception.errno, errno.EPERM)

class PlannerExecution_Test(unittest.TestCase):

    assertSandboxes = assertSandboxes
    assertContentEqual = assertContentEqual
    from yamlns.testutils import assertNsEqual

    def setUp(self):
        self.configPath = Path('dummyconfig')
        removeRecursive(self.configPath)
        removeRecursive(executionRoot)
        executionRoot.mkdir()
        self.configPath.mkdir()
        (self.configPath/'config.yaml').write_text("""
            nTelefons: 7
        """)
        (self.configPath/'holidays.conf').write_text(
            "2020-12-25\tNadal"
        )
        (self.configPath/'drive-certificate.json').write_text(
            "{}"
        )

    def tearDown(self):
        removeRecursive(self.configPath)
        removeRecursive(executionRoot)

    def test_path_noDescription(self):
        e = PlannerExecution(
            monday='2020-05-04',
            configPath=self.configPath,
        )
        self.assertEqual(e.path,
            executionRoot/'2020-05-04')

    def test_path_withDescription(self):
        e = PlannerExecution(
            monday='2020-05-04',
            description="description",
            configPath=self.configPath,
        )
        self.assertEqual(e.path,
            executionRoot/'2020-05-04-description')

    def test_path_withDescription_withSlug(self):
        e = PlannerExecution(
            monday='2020-05-04',
            description=u"Una Descripción", # Spaces, accent and uppercase
            configPath=self.configPath,
        )
        self.assertEqual(e.path,
            executionRoot/'2020-05-04-una-descripcion')

    def test_createSandbox_baseCase(self):
        e = PlannerExecution(
            monday='2020-05-04',
            configPath=self.configPath,
        )

        e.createSandbox()

        self.assertSandboxes([
            'executions/2020-05-04',
            'executions/2020-05-04/config.yaml',
            'executions/2020-05-04/drive-certificate.json',
            'executions/2020-05-04/holidays.conf',
        ])

    def test_createSandbox_createsConfig(self):
        e = PlannerExecution(
            monday='2020-05-04',
            configPath=self.configPath,
        )

        e.createSandbox()

        self.assertNsEqual(
            ns.load(self.configPath/'config.yaml'),
            ns.load(e.path/'config.yaml'))

    def test_createSandbox_createsHolidays(self):
        e = PlannerExecution(
            monday='2020-05-04',
            configPath=self.configPath,
        )

        e.createSandbox()

        self.assertContentEqual(
            self.configPath/'holidays.conf',
            e.path/'holidays.conf')

    def test_createSandbox_linksCertificate(self):
        e = PlannerExecution(
            monday='2020-05-04',
            configPath=self.configPath,
        )

        e.createSandbox()

        self.assertContentEqual(
            self.configPath/'drive-certificate.json',
            e.path/'drive-certificate.json')

        self.assertEqual(True,
            (e.path/'drive-certificate.json').is_symlink())
        self.assertEqual(
            (self.configPath/'drive-certificate.json').resolve(),
            (e.path/'drive-certificate.json').resolve())

    def test_createSandbox_changingLines(self):
        e = PlannerExecution(
            monday='2020-05-04',
            configPath=self.configPath,
            nlines=8,
        )
        e.createSandbox()
        config = ns.load(e.path/'config.yaml')
        self.assertEqual(config.nTelefons, 8)



# vim: ts=4 sw=4 et
