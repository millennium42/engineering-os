FROM ghcr.io/openhands/agent-canvas@sha256:64d73ec6c066b425e872e1a58d52d8b5d901b617a8e945b1430415c5fd4ea4d1
USER root
RUN python -m pip install --no-cache-dir openhands-tools==1.46.0
RUN python -c "import site; from pathlib import Path; p=Path(site.getsitepackages()[0]) / 'engos_openhands_tools.pth'; p.write_text('import openhands.tools.terminal.definition; import openhands.tools.file_editor.definition; import openhands.tools.task_tracker.definition\\n')"
USER 10001:10001
