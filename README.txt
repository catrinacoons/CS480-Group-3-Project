 *---------------------------------* Group 3 Project  *---------------------------------*

○  Research Question Topic: How do Zephyr contributors evaluate and respond to Gen-AI-generated outputs in development conversations?

○  Repository mined: zephyrproject-rtos/zephyr (branch: main)
○  Period of time: 2022-09-21 00:00 UTC to 2026-09-21 00:00 UTC
      We are mining the last 4 years of the public zephyr Github repository, for project on How Are          GenAI Outputs Evaluated in Zephyr Development. 
○  Unit of Analysis: conversion thread, issue or pull request and its commits
      Includes pull request, review comments, issues, and discussions containing observable signs of         GenAI involvement.

○  Goal: Understand how Zephyr contributors assess, verify, correct, or reject GenAI-generated suggestions during software development.


*================* The Setup *================* 
○ Repository:
      Create a 480 directory and then clone both repositories into it:
      >>    git clone --depth 1 https://github.com/zephyrproject-rtos/zephyr.git
      >>    git clone https://github.com/catrinacoons/CS480-Group-3-Project.com

+====+ API Auth token and RABBIT Setup +====+ 
○  Allows Rabbit to run 5,000 queries/hr compared to 60/hr without a token (Source: RABBIT-ng repo description)
○  Rabbit requires Python version 3.11 or newer: check using <python --version> and update if necessary (current version = 3.14.7)
      Ensure you have a venv folder then <pip install PyGithub>
      Install Rabbit packages (must have pydriller installed first) <pip install pandas pydriller PyGithub rabbit-ng>
○  Generate a token and link it to the project
      Input <https://github.com/settings/tokens> -> Token (classic) tab -> Generate new token -> (classic)
            -> Leave all boxes unchecked -> Name token -> Set expiration to class completion (or graduation)
                  -> Copy token immediately (GitHub shows it once)
                  -> Store that token in a safe place. 
○  Following command below changes a bit for Windows (it's correct for Mac/Linux):
      Input <export GITHUB_TOKEN="input_token">
            (Token only persists as long as terminal tab is open, redo as needed.)
○  Install remaining packages: 
      <pip install requests python-dotenv>


*================* How to Run the Pipeline *================* 
○ Run the following stages in order
      python zephyr_mining.py commits    -> commits.csv
      python zephyr_mining.py threads    -> threads.cv
      python zephyr_mining.py comments   -> comments.csv
      python zephyr_mining.py links      -> commit_pr_links.csv
      python zephyr_mining.py build      -> final_dataset.csv
      python zephyr_mining.py rabbit     -> rabbit.csv
      python zephyr_mining.py build      # rebuild via rabbit.csv

○ Note 1 - "all" will run rabbit prior to build.
○ Note 2 - Can take hours to run stages, but they will save as the progress forward.

*================* Step Breakdown *================* 
○ Detection procedure -  regarding gen_signals.py; regex on the commit messages, the thread titles plus bodies, and comments for: assisted_by_tag, ai_coauthor, and ai_keyword.

○ Flagged -> comments by any AI bot accounts, plus PRs that were linked to any flagged commits. 

○ Our Filters -> zephyr_build_dataset.py - 
      -> Removed duplicate threads or comments from restarted collection runs.
      -> Observation period filter applied, dates given above.
      -> Exclusions used for automation-bots, and AI assistant bots were marked and kept.
      -> Threads with at least 1 GenAI signal, were also kept. 

○ Derived variables per a thread -> n_comments, n_participants, n_ai_bot_comments, n_genai_comments, all_signals, strongest_signal, has_assisted_by_tag, linked_flagged_commit, is_merged, censored, days_open, days_to_first_genai_comment 

○  Validation - validation_sample.csv used up to 20 candidates (at random) per the signal type; and 40 non-canidates. 

*================* The Checkpoints *================* 
|                                            |  Threads   |    Comments    |   Commits   | 
○ Artifacts retrieved ->                        67,036         496,268         81,079
○ After deduplication ->                        67,036         496,268
○ After observation period filter ->            67,036         496,268
○ After exclusions [aka automation bots] ->     62,408         515,584
○ Final Observations [the GenAI candidates] ->  3,065          49,833                
○ Commits w. GenAi signals ->                                                  3,148
○ Unique authors sent to RABBIT ->  922
○ The full counts -> checkpoints.json Run settings/versions: provenance.json

*================* The Files *================* 
○ The Code - zephyr_mining.py (the runner), zephyr_pydriller.py, zephyr_github_api.py, genai_signals.py, zephyr_build_dataset.py, backfill_provenance.py

○ The Raw Data - commits.csv, threads.csv, comments.zip (aka comments.csv), commit_pr_links.csv, rabbit.csv

○ The Final Files - final_dataset.csv [with 1 row per candidate thread], final_comments.csv, threads_derived.csv [all the threads with derived variables], validation_sample.csv
                        







