```env
TARGET=target
```
## Specification to Source Code Transformation Prompt

You are a code synthesis engine that transforms structured project specifications from <env:SOURCE> into a complete, working Python CLI implementation in <env:TARGET>.

## File Structures

The intended structure of <env:SOURCE>:
```
<env:TARGET_MASK>
    overview.md      # a concrete description of the project
    requirements.md  # functional and non-functional requirements
    architecture.md  # component design, module structure, data flow
    cli_spec.md      # CLI interface spec: commands, flags, args, output format
    guideline.md     # the guideline for development
```

The intended structure of <env:TARGET>:
```
<env:TARGET_MASK>
    module_name/
        __init__.py 
        ... 
    tests/ 
        ... # unit and integration tests 
    pyproject.tomlS
    README.mdi_spec.md
    requirements.txt
```
## Task

Read all specification files and synthesize a complete, runnable Python CLI project in `<env:TARGET>`.

### If source files already exist

Then carefully examine if the existing source files accurately implement the specifications. If not, remove the unnecessary files and overwrite the existing problematic files to realign with the specifications.