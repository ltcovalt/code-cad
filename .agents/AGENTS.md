# Workspace Instructions: build123d CAD Modeling

When building CAD models in this repository:
1. Always follow the syntax and patterns defined in the `build123d` skill ([SKILL.md](file:///home/luke/repos/cad/.agents/skills/build123d/SKILL.md)).
2. Rely on the extracted API reference documents in [.agents/skills/build123d/references/](file:///home/luke/repos/cad/.agents/skills/build123d/references/) for accurate parameters and method signatures.
3. Validate models by running python scripts with `ocp_vscode` `show()` or checking export operations.
4. **Clean Workspace Rule**: Do NOT create temporary test or validation scripts in the root project directory. Store reusable test/utility scripts inside `.agents/scripts/` or delete temporary scratch scripts immediately after validation completes.
