import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
import os

from .commands.create import create

def parse_args():
    parser = argparse.ArgumentParser(description="Process input folder for API response.")
    subparsers = parser.add_subparsers(dest='command')

    build = subparsers.add_parser('build', help='Build the target stage from the source stage.')
    build.add_argument('script', nargs='?', default='compile', help='Use $source$/build/$script$.md as prompt.')
    build.add_argument('stage', help='Path to source stage')
    build.add_argument('--config', '-a', default='config.json', help='')

    purge = subparsers.add_parser('purge', help='')
    purge.add_argument('--pipeline', '-p', action='store_true', help='')
    purge.add_argument('dir', help='')

    create = subparsers.add_parser('create', help='Create an empty pipeline.')
    create.add_argument('pipeline', default='./', help='')

    args = parser.parse_args()
    return args

def main():
    load_dotenv('./.env')
    args = parse_args()

    if args.command == 'build':
        with open(args.config) as f:
            config = json.load(f)
        api_key = os.getenv(config['api_var'])

        path = Path(args.stage).resolve()

        from .lips import Lips
        lips = Lips(path / '../../')
        for pipeline in lips.pipelines.values():
            for stage in pipeline.stages.values():
                if stage.root.resolve() == path:
                    script = Path(args.script)
                    build_dir = path / 'build'
                    if not (build_dir / script).exists():
                        for suffix in ['.md', '.py', '.sh', '.bat']:
                            if (build_dir / script.with_suffix(suffix)).exists():
                                script = script.with_suffix(suffix)
                                break
                        else:
                            raise FileNotFoundError(
                                f"No script found for {args.script!r} in {build_dir}"
                            )
                    stage.build(script, config['messages'], api_key, config['generate'])

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

    elif args.command == 'create':
        create(args.pipeline)

    else:
        print("No command specified. Use --help for usage.")

if __name__ == '__main__':
    main()