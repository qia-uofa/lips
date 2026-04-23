import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
import os

from .lips import Lips

def parse_args():
    parser = argparse.ArgumentParser(description="Process input folder for API response.")
    subparsers = parser.add_subparsers(dest='command')

    build = subparsers.add_parser('build', help='Build the target stage from the source stage.')
    build.add_argument('mode', nargs='?', default='compile', help='Use $source$/config/$mode$.md as prompt.')
    build.add_argument('stage', help='Path to source stage')
    build.add_argument('--api-config', '-a', default='api-config.json', help='')


    build = subparsers.add_parser('purge', help='')
    build.add_argument('--pipeline', '-p', action='store_true', help='')
    build.add_argument('dir', help='')
    
    create = subparsers.add_parser('create', help='Create an empty pipeline.')
    
    args = parser.parse_args()
    return args

def create():
    pass

if __name__ == '__main__':
    load_dotenv()


    args = parse_args()

    if args.command == 'build':
        api_key = os.getenv('API_KEY')
        with open(args.api_config) as f:
            api_config = json.load(f)

        path = Path(args.stage).resolve()

        lips = Lips(path / '../../')
        for pipeline in lips.pipelines.values():
            for stage in pipeline.stages.values():
                if stage.root.resolve() == path:
                    stage.build(args.mode, api_key, api_config)

    elif args.command == 'purge':
        path = Path(args.dir).resolve()
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
        create()

    else:
        print("No command specified. Use --help for usage.")