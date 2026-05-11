from pathlib import Path
import json
from datetime import datetime
from litellm import completion
import shutil
import subprocess
import os

from .utils.parse_scripts import env_from_script, ignore_from_script
from .utils.resolve_md import resolve_links, resolve_env
from .utils.parse_files import parse_files


class Lips:
    def __init__(self, root, env={}):
        self.env = env
        self.root = Path(root).resolve()
        self.pipelines = {}
        for root in self.root.iterdir():
            if root.is_dir():
                self.pipelines[root.name] = Pipeline(root, self)

class Pipeline:
    def __init__(self, root, lips):
        self.lips = lips
        self.root = Path(root).resolve()
        self.stages = {}
        for stage_path in self.root.iterdir():
            if stage_path.is_dir():
                self.stages[stage_path.name] = Stage(stage_path.name, self)
    
    def purge(self):
        for stage in self.stages.values():
            stage.purge()

class Stage:
    def __init__(self, name, pipeline):
        self.name = name
        self.pipeline = pipeline
        self.root = pipeline.root / name

    
    def purge(self):
        repo_path = (self.root / 'repo')
        repo_path.mkdir(parents=True, exist_ok=True)
        
        for f in repo_path.rglob('*'):
            if f.is_dir():
                shutil.rmtree(f)
            else:
                if f.name != '.gitignore':
                    f.unlink()
    
        out_path = (self.root / 'out')
        if out_path.exists() and out_path.is_dir():
            shutil.rmtree(out_path)
   
    def build(self, script, messages, message_path, api_key=None, generate_config=None):
        suffix = script.suffix
        with open(self.root / f'build/{script}', 'r', encoding='utf-8') as f:
            text = f.read()
        if suffix == '.md':
            self.build_md(text, messages, message_path, api_key, generate_config)
        elif suffix == '.py':
            self.build_py(text)
        elif suffix == '.sh':
            self.build_sh(text)

    def build_py(self, code):
        env = self.pipeline.lips.env | {
            'PATH': self.pipeline.root,
            'LIPS_PATH': self.pipeline.lips.root,
            'PIPE_PATH': self.pipeline.root,
            'STAGE_PATH': self.root,
            'SOURCE': self.name,
            'SOURCE_PATH': self.root / 'repo',
        }
        code, env, _, _ = self.resolve(code, self.root, env)
        subprocess.run(
            ['python', '-'],
            input=code,
            text=True,
            cwd=env['PATH'],
            check=True,
        )
        
    def build_sh(self, code):
        env = self.pipeline.lips.env | {
            'PATH': self.pipeline.root,
            'LIPS_PATH': self.pipeline.lips.root,
            'PIPE_PATH': self.pipeline.root,
            'STAGE_PATH': self.root,
            'SOURCE': self.name,
            'SOURCE_PATH': self.root / 'repo',
        }
        code, env, _, _ = self.resolve(code, self.root, env)
        # Windows
        if os.name == "nt":
            # Reuse current shell if possible
            shell = os.environ.get("COMSPEC", "cmd.exe")

            subprocess.run(
                shell,
                input=code + '\n',
                text=True,
                shell=True,
                check=True,
                cwd=env['PATH']
            )
        else:
            shell = os.environ.get("SHELL", "/bin/sh")
            subprocess.run(
                [shell, "-s"],
                input=code + '\n',
                text=True,
                check=True,
                cwd=env['PATH']
            )

    def resolve(self, text, root, base_env={}):
        text, env = env_from_script(text, self)
        text, source_ignore, target_ignore = ignore_from_script(text)
        text = resolve_env(text, env)
        text = resolve_env(text, base_env)
        text = resolve_links(text, root)
        return text, base_env | env, source_ignore, target_ignore
    
    def build_md(self, md_text, messages, message_path, api_key, generate_config):
        base_env = self.pipeline.lips.env | {
                    'LIPS_PATH': self.pipeline.lips.root,
                    'PIPE_PATH': self.pipeline.root,
                    'STAGE_PATH': self.root,
                    'SOURCE_MASK': '<masked/path/to/input/repo>',
                    'TARGET_MASK':  '<masked/path/to/output/repo>',
                    'SOURCE_PATH': self.root / 'repo'
        }
        
        build_prompt_base_env = base_env | {
                'PATH': self.root / 'build',
                'SOURCE': self.name
        }
        

        
        build_prompt, env, sourceignore, targetignore = self.resolve(
            md_text, 
            self.root / 'build',
            build_prompt_base_env
        )
        target = self.pipeline.stages[env['TARGET']]

        message_base_env = base_env | {
            'PATH': message_path,
            'TARGET_PATH': target.root / 'repo',
            'BUILD_PROMPT': build_prompt,
            'PRINT_SOURCE': resolve_links(
                f"[write:{base_env['SOURCE_MASK']}](./)", 
                self.root/'repo',
                sourceignore),
            'PRINT_TARGET': resolve_links(
                f"[write:{base_env['TARGET_MASK']}](./)", 
                target.root/'repo',
                targetignore)
        }

        
        for message in messages:
            content, env, _, _ = self.resolve(
                message['content'], 
                Path(''), 
                message_base_env
            )
            message['content'] = content

        self.log_json('messages', messages)

        response = completion(
            messages=messages,
            api_key=api_key,
            stream=False,
            **generate_config
        )

        full_text = response.choices[0].message.content

        self.log_text('response', '.md', full_text)

        files_dict = parse_files(full_text)

        self.log_json( "files_dict", files_dict)

        for p, content in files_dict.items():
            path = target.root / 'repo' / Path(p)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding="utf-8") as f:
                f.write(content)

        repo_root = target.root / 'repo'
        for f in repo_root.rglob('*'):
            if f.is_file() and f.stat().st_size == 0:
                f.unlink()
        

    def log_json(self, name, content):
        now  = datetime.now().strftime("%Y%m%d_%H%M%S")
        file = self.root / f'out/{name}_{now}.json'
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
        with open(file,'w', encoding="utf-8") as f:
            json.dump(content, f, indent=4)

    def log_text(self, name, ext, content):
        now  = datetime.now().strftime("%Y%m%d_%H%M%S")
        file = self.root / f'out/{name}_{now}{ext}'
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
