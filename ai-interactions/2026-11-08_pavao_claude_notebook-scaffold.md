Tool: Claude

Prompts
1. Shared the team repo and the Moodle assignment text
2. Provide step by step instructions for further development

AI response
- Read the human only pair's results and suggested things to add: failure types, interactive charts, calibration by elo, human mistakes against Maia failures
- Generated two starter notebooks, tested only on fake data because the predictions file was not in the repo

Process of development:
- kept: failure types, confident miss analysis, interactive charts, board browser
- changed: shortened all text, wrote our own findings, fixed print labels

Problems
- predictions file was missing, so we ran Maia ourselves with run_maia.py 
- Jupyter used the wrong Python (from another course), pyarrow missing - fixed by registering a separate kernel
- first full run of the notebook was by mistake still on the 20k test data
- clock chart had the x-axis in wrong order, AI needed a second step to fix it
- AI code was only tested on fake data, so all numbers had to be checked on the real file
