from pathlib import Path
import pathspec
import json
from datetime import datetime
from litellm import completion
import shutil

from .utils.message_from_files import message_from_files
from .utils.parse_md import env_from_md, ignore_from_md
from .utils.parse_files import parse_files
from .utils.prompts import update_files_prompt


class Lips:
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.pipelines = {}
        for root in self.workspace.iterdir():
            if root.is_dir():
                self.pipelines[root.name] = Pipeline(root)

class Pipeline:
    def __init__(self, root):
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
    
    def repo_message(self, ignore='', mask = ''):
        repo_path = (self.root / 'repo')
        repo_path.mkdir(parents=True, exist_ok=True)
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore.splitlines())
        files = [
            f.resolve()
            for f in repo_path.rglob('*')
            if f.is_file() and not spec.match_file(f.relative_to(repo_path))]
        return message_from_files(files, repo_path, mask)
    
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

    def build(self, build_mode, api_key, generate_config, debug=False):

        with open(self.root / f'build/{build_mode}.md', 'r', encoding='utf-8') as f:
            prompt = f.read()
            target = self.pipeline.stages[env_from_md(prompt)['TARGET']]
            ignore = ignore_from_md(prompt)
        
        messages = []
        
        if target.name == self.name:
            messages.append(self.repo_message(ignore, '<masked-path-to-input-repo>'))
            messages.append({
                'role': 'assistant',
                'content': f'I see. This is the current repo of {self.name} needed to be updated.'
            })
        else:
            messages.append(self.repo_message(ignore, '<masked-path-to-output-repo>'))
            messages.append({
                'role': 'assistant',
                'content': f'I see. This is the current repo of {self.name} needed to be referenced for generation of {target.name}.'
            })
            messages.append(target.repo_message('*.verify.md'))
            messages.append({
                'role': 'assistant',
                'content': f'I see. This is the current repo of {target.name} needed to be updated, based on the repo of {self.name}.'
            })

        messages.append({
            'role': 'user',
            'content': prompt
        })
        messages.append({
            'role': 'assistant',
            'content': f'I see. This is the prompt for generating/updating the repo of {target.name}.'
        })

        messages.append({
            'role': 'user',
            'content': update_files_prompt(target.root / 'repo')
        })

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
            with open(path,'w', encoding="utf-8") as f:
                f.write(content)

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
