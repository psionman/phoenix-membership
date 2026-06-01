[project]
name = "phoenix-members-files"
version = "0.1.0"
description = "Handle Members files for Phoenix"
authors = [{name = "Jeff", "email" = "<jeffwatkins2000@gmail.com>"}]
readme = "README.md"
requires-python = ">=3.10"

# pyproject.toml
[tool.ruff]
line-length = 79
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "UP"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true