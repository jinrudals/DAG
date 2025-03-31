# DAG
A simple DAG-based workflow runner designed for managing build/test/verify stages in complex hardware or software projects.

## 🔧 Features

- Target/stage abstraction
- Dependency-respecting execution (via DAG)
- Run only command, only post, or both
- CLI-friendly design
- Easily extensible

---
## 📦 Installation

```shell
pip install -e .
```

This installs the workscript command via pyproject.toml.
---
## 🚀 Usage

### Merge stages and targets

```
workscript merge -s configs/stages.json -t configs/targets.json -o merged.json
```

### Run full pipeline (command + post)

```
workscript run -s merged.json -j 4
```

### Run only post steps

```
workscript post -s merged.json -j 4
```

### Collect post output files

```
workscript collect -s merged.json -o analyzed.json
```
---

## 🔍 Command Reference

`merge`

Merge stages and targets into a single DAG.

- `--stages`, `-s`: JSON file containing stage templates

- `--targets`, `-t`: JSON file listing targets

- `--output`, `-o`: Output path for merged DAG

`run`

Execute all commands and post steps.

- `--stages`, `-s`: Path to merged DAG

- `--max_workers`, `-j`: Number of parallel workers

`post`

Run only the post sections of each stage.

- `--stages`, `-s`: Path to merged DAG

- `--max_workers`, `-j`: Number of parallel workers

`collect`

Collect results from each post.output file.

- `--stages`, `-s`: Path to merged DAG

- `--output`, `-o`: Collected results in JSON

`report` *(TODO)*

Intended to send collected info to a database.
---
## 📁 Project Structure
```
project-root/
├── configs/
│   ├── stages.json
│   └── targets.json
├── src/
│   └── bos_dag/
│       ├── builder.py
│       ├── runner.py
│       ├── parser.py
│       ├── main.py
│       ├── logger.py
│       └── exceptions.py
├── tests/
│   └── bos_dag/
│       ├── test_scenario.py
│       └── test_unittest.py
├── README.md
├── pyproject.toml
└── test.py
```
--
## 🚧 Feature Roadmap

| Feature                                  | Status     |
|------------------------------------------|------------|
| `--start` / `--end` range execution      | ❌ Not yet |
| Graph visualization or stage dumping     | ❌ Not yet |
| `--with-children` (opposite of `--with-deps`) | ❌ Not yet |
| Post output file validation (rules)      | ❌ Not yet |
| Reporting to database or dashboard       | ❌ Reserved |
| Retry failed stages or resumable execution | ❌ Future |
