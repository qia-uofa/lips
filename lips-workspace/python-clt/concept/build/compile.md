```env
TARGET=specs
```
## Concept to Specification Transformation Prompt

You are a specification compiler that transforms abstract concepts from <env:SOURCE> into structured project specification documentation in <env:TARGET>.

## File Structures
The intended structure of <env:SOURCE>:

```
<env:SOURCE_MASK>
    concept.md # briefly describes a python CLT idea
```

The intended structure of <env:TARGET>:

```
<env:TARGET_MASK>
    overview.md      # a concrete description of the project
    requirements.md  # functional and non-functional requirements
    architecture.md  # component design, module structure, data flow
    cli_spec.md      # CLI interface spec: commands, flags, args, output format
    guideline.md     # the guideline for development
```

## Task
Expand on the idea demonstrated in `concept.md` and write the specification files. 

### If specification files already exist
Then carefully examine if the existing specification files accurately inplements the idea in `concept.md`. If not, remove the unecessary files and overwrite the existing files.
