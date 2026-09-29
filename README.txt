TODO - 
[ ] write this README.txt file explaining exactly how to run the pipeline

Notes: 
- The README should also report important checkpoints, for example: 
      1. Artifacts retrieved: N
      2. After observation-period filter: N
      3. After exclusions: N
      4. Final observations: N

API Auth token and RABBIT Setup:
-- Allows Rabbit to run 5,000 queries/hr compared to 60/hr without a token (Source: RABBIT-ng repo description)
-- Rabbit requires Python version 3.11 or newer: check using <python --version> and update if necessary (current version = 3.14.7)
      Ensure you have a venv folder then <pip install PyGithub>
      Install Rabbit packages (must have pydriller installed first) <pip install pandas pydriller PyGithub rabbit-ng>
-- Generate a token and link it to the project
      Input <https://github.com/settings/tokens> -> Token (classic) tab -> Generate new token -> (classic)
            -> Leave all boxes unchecked -> Name token -> Set expiration to class completion (or graduation)
                  -> Copy token immediately (GitHub shows it once)
                  -> Store that token in a safe place. 
- Following command below changes a bit for Windows (it's correct for Mac/Linux)
      Input <export GITHUB_TOKEN="input_token">
            (Token only persists as long as terminal tab is open, redo as needed.)
