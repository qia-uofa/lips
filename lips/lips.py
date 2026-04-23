from pathlib import Path
import pathspec
import json
from datetime import datetime
from litellm import completion
import shutil

from .utils.content_from_file import message_from_files
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
    
    def state_message(self, ignore=''):
        state_path = (self.root / 'state')
        state_path.mkdir(parents=True, exist_ok=True)
        spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore.splitlines())
        files = [
            f.resolve()
            for f in state_path.rglob('*')
            if f.is_file() and not spec.match_file(f.relative_to(state_path))]
        return message_from_files(files)
    
    def purge(self):
        state_path = (self.root / 'state')
        state_path.mkdir(parents=True, exist_ok=True)
        
        for f in state_path.rglob('*'):
            if f.is_dir():
                shutil.rmtree(f)
            else:
                if f.name != '.gitignore':
                    f.unlink()
    
        out_path = (self.root / 'out')
        if out_path.exists() and out_path.is_dir():
            shutil.rmtree(out_path)

    def build(self, build_mode, api_key, api_config, debug=False):

        with open(self.root / f'config/{build_mode}.md', 'r') as f:
            prompt = f.read()
            target = self.pipeline.stages[env_from_md(prompt)['TARGET']]
            ignore = ignore_from_md(prompt)
        
        messages = []
        
        if target.name == self.name:
            messages.append(self.state_message(ignore))
            messages.append({
                'role': 'assistant',
                'content': f'I see. This is the current state of {self.name} needed to be updated.'
            })
        else:
            messages.append(self.state_message(ignore))
            messages.append({
                'role': 'assistant',
                'content': f'I see. This is the current state of {self.name} needed to be referenced for generation of {target.name}.'
            })
            messages.append(target.state_message('*.verify.md'))
            messages.append({
                'role': 'assistant',
                'content': f'I see. This is the current state of {target.name} needed to be updated, based on the state of {self.name}.'
            })

        messages.append({
            'role': 'user',
            'content': prompt
        })
        messages.append({
            'role': 'assistant',
            'content': f'I see. This is the prompt for generating/updating the state of {target.name}.'
        })

        messages.append({
            'role': 'user',
            'content': update_files_prompt(target.root / 'state')
        })

        self.log_json('messages', messages)

        response = completion(
            messages=messages,
            api_key=api_key,
            stream=False,
            **api_config
        )

        full_text = response.choices[0].message.content

        self.log_text('response', 'md', full_text)

        files_dict = parse_files(full_text)

        self.log_json( "files_dict", files_dict)

        for p, content in files_dict.items():
            path = Path(p)
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
