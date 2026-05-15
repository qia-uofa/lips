import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
import os

from .commands.create import create
from .utils.parse_scripts import env_from_script
def parse_args():
    parser = argparse.ArgumentParser(description="Process input folder for API response.")
    subparsers = parser.add_subparsers(dest='command')

    build = subparsers.add_parser('build', help='Build the target stage from the source stage.')
    build.add_argument('build_file', nargs='?', default='main', help='Use $source$/build/$build_file$.md as prompt.')
    build.add_argument('stage', help='Path to source stage')
    build.add_argument('--config', '-c', default=None, help='')
    build.add_argument('--dotenv', '-d', default='./', help='')
    

    purge = subparsers.add_parser('purge', help='')
    purge.add_argument('--pipeline', '-p', action='store_true', help='')
    purge.add_argument('dir', help='')

    #create = subparsers.add_parser('create', help='Create an empty pipeline.')
    #create.add_argument('pipeline', default='./', help='')

    args = parser.parse_args()
    return args

def run(args):
    if args.command == 'build':

        load_dotenv(Path(args.dotenv) / '.env')
        path = Path(args.stage).resolve()

        if args.config is None:
            p = path
            while not(p / 'config.json').is_file():
                p = p.parent
            config_path = p / 'config.json'
            with open(config_path) as f:
                config = json.load(f)
        api_key = os.getenv(config['api_var'])

        path = Path(args.stage).resolve()

        from .lips import Lips
        lips = Lips(path / '../../', os.environ)
        for pipeline in lips.pipelines.values():
            for stage in pipeline.stages.values():
                if stage.root.resolve() == path:
                    build_file = Path(args.build_file)
                    build_file_full = None
                    build_dir = path / 'build'
                    for suffix in ['.md', '.py', '.sh', '.bat']:
                        if (build_dir / build_file.with_suffix(suffix)).exists():
                                build_file_full = build_file.with_suffix(suffix)
                                break
                            
                    if build_file_full is None:
                        for file in build_dir.iterdir():
                            with open(file, 'r', encoding="utf-8") as f:
                                _, env = env_from_script(f.read(), stage)

                            if "ALIAS" in env.keys():
                                if env["ALIAS"] == str(build_file):
                                    build_file_full = Path(file.name)
                                    break
                                
                    if build_file_full is None:
                        raise FileNotFoundError(
                                f"No build_file found for {args.build_file!r} in {build_dir}"
                            )
                        
                    stage.build(build_file_full, config['messages'], config_path.parent, api_key, config['generate'])

    elif args.command == 'purge':
        path = Path(args.dir).resolve()

        from .lips import Lips
        if args.pipeline:
            lips = Lips(path / '../')
        else:
            lips = Lips(path / '../../')

        for pipeline in lips.pipelines.values():
            if pipeline.root.resolve() == path and args.pipeline:
                pipeline.purge()
            for stage in pipeline.stages.values():
                if stage.root.resolve() == path and not args.pipeline:
                    stage.purge()

    #elif args.command == 'create':
    #    create(args.pipeline)

    else:
        print("No command specified. Use --help for usage.")

def main():
    args = parse_args()
    run(args)
    
if __name__ == '__main__':
    main()