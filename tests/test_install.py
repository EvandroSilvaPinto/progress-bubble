import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'install.py'


class InstallTests(unittest.TestCase):
    def test_global_installation_for_all_agents_in_isolated_home(self):
        with tempfile.TemporaryDirectory(prefix='agent homes ') as tmp:
            home = Path(tmp)
            env = dict(os.environ,HOME=tmp,USERPROFILE=tmp)
            cmd = [sys.executable,str(SCRIPT),'--agent','all']
            preview = subprocess.run(cmd+['--dry-run'],env=env,capture_output=True,text=True)
            self.assertEqual(preview.returncode,0,preview.stderr)
            # Check isolation before allowing the subprocess to copy files.
            self.assertEqual(preview.stdout.count(tmp),3)
            result = subprocess.run(cmd,env=env,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            for relative in ('.agents/skills','.claude/skills','.gemini/config/skills'):
                skill = home/relative/'progress-bubble'
                self.assertTrue((skill/'SKILL.md').is_file())
                self.assertEqual((skill/'scripts/status.py').read_bytes(),
                                 (ROOT/'skills/progress-bubble/scripts/status.py').read_bytes())

    def test_global_paths_follow_each_agent(self):
        self.assertTrue(SCRIPT.is_file(), 'Falta o instalador multiagente')
        spec = importlib.util.spec_from_file_location('installer', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        home = Path('/example-home')
        expected = {'codex':'.agents/skills', 'claude':'.claude/skills',
                    'antigravity':'.gemini/config/skills'}
        for agent, relative in expected.items():
            self.assertEqual(module.skill_root(agent,'user',Path('/project'),home),home/relative)

    def test_project_installation_for_all_agents_and_existing_files(self):
        self.assertTrue(SCRIPT.is_file(), 'Falta o instalador multiagente')
        with tempfile.TemporaryDirectory(prefix='three agents ') as tmp:
            project = Path(tmp)
            cmd = [sys.executable,str(SCRIPT),'--agent','all','--scope','project',
                   '--project-root',str(project)]
            dry = subprocess.run(cmd+['--dry-run'], capture_output=True)
            self.assertEqual(dry.returncode,0,dry.stderr)
            self.assertEqual(list(project.iterdir()),[])
            result = subprocess.run(cmd,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            for folder in ('.agents/skills','.claude/skills'):
                skill = project/folder/'progress-bubble'
                script = skill/'scripts/status.py'
                out = project/folder/'demo.html'
                run = subprocess.run([sys.executable,str(script),'--output',str(out),
                    '--title','Teste portátil','--percent','25','--message','Executando'],capture_output=True)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertTrue(out.is_file())
                sentinel = skill/'custom.txt'
                sentinel.write_text('preservar')
            repeat = subprocess.run(cmd,capture_output=True)
            self.assertNotEqual(repeat.returncode,0)
            self.assertEqual(sentinel.read_text(),'preservar')

    def test_always_on_is_registered_idempotently_and_preserves_user_files(self):
        import json
        with tempfile.TemporaryDirectory(prefix='always on ') as tmp:
            home = Path(tmp)
            env = dict(os.environ,HOME=tmp,USERPROFILE=tmp)
            (home/'.claude').mkdir()
            (home/'.claude/settings.json').write_text(json.dumps({'theme':'dark','hooks':{'UserPromptSubmit':[{'hooks':[{'type':'command','command':'echo mine'}]}]}}))
            (home/'.codex').mkdir()
            (home/'.codex/AGENTS.md').write_text('# Minhas regras\n')
            cmd = [sys.executable,str(SCRIPT),'--agent','all']
            self.assertEqual(subprocess.run(cmd,env=env,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(cmd+['--update'],env=env,capture_output=True).returncode,0)
            data = json.loads((home/'.claude/settings.json').read_text(encoding='utf-8'))
            commands = [h['command'] for e in data['hooks']['UserPromptSubmit'] for h in e['hooks']]
            self.assertEqual(data['theme'],'dark')
            self.assertIn('echo mine',commands)
            self.assertEqual(sum('remind.py' in c for c in commands),1)
            for relative in ('.codex/AGENTS.md','.gemini/GEMINI.md'):
                text = (home/relative).read_text(encoding='utf-8')
                self.assertEqual(text.count('progress-bubble:start'),1)
            self.assertIn('# Minhas regras',(home/'.codex/AGENTS.md').read_text(encoding='utf-8'))

    def test_always_on_can_be_disabled(self):
        with tempfile.TemporaryDirectory(prefix='no always on ') as tmp:
            env = dict(os.environ,HOME=tmp,USERPROFILE=tmp)
            result = subprocess.run([sys.executable,str(SCRIPT),'--agent','all','--no-always-on'],env=env,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse((Path(tmp)/'.claude/settings.json').exists())


if __name__ == '__main__':
    unittest.main()
