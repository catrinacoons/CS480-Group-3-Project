# Group 3 Project

* **Research Question:** How do Zephyr contributors evaluate and respond to Gen-AI-generated outputs in development conversations?

* **Repository mined:** zephyrproject-rtos/zephyr (branch: main)

* **Period of time:** ```2022-09-21 00:00 UTC to 2026-09-21 00:00 UTC```

  *  We are mining the last 4 years of the public zephyr Github repository, for project on How Are GenAI Outputs Evaluated in Zephyr Development. 

* **Unit of Analysis:** conversion thread, issue or pull request and its commits.

  * Includes pull request, review comments, issues, and discussions containing observable signs of GenAI involvement.

* **Goal:** Understand how Zephyr contributors assess, verify, correct, or reject GenAI-generated suggestions during software development.

## The Setup

* **Repository:**
  
  * Create a 480 directory and then clone both repositories into it:
  
      ```git clone --depth 1 https://github.com/zephyrproject-rtos/zephyr.git```
    
      ```git clone https://github.com/catrinacoons/CS480-Group-3-Project.com```


### API Auth token and RABBIT Setup

* Allows Rabbit to run 5,000 queries/hr compared to 60/hr without a token (Source: RABBIT-ng repo description)

* **Rabbit requires Python version 3.11 or newer:** check using ```<python --version>``` and update if necessary (current version = 3.14.7)
  
   * Ensure you have a ```venv``` folder then ```<pip install PyGithub>```
      
   * Install Rabbit packages (must have pydriller installed first) ```<pip install pandas pydriller PyGithub rabbit-ng>```

* **Generate a token and link it to the project:**

  * ```Input <https://github.com/settings/tokens>``` -> Token (classic) tab -> Generate new token -> (classic) ->
  
    * Leave all boxes unchecked -> Name token -> Set expiration to class completion (or graduation) ->

      * Copy token immediately (GitHub shows it once) ->

        * Store that token in a safe place. 

* **Following command below changes a bit for Windows (it's correct for Mac/Linux):**
        
   ```Input <export GITHUB_TOKEN="input_token">```
  
  * (Token only persists as long as terminal tab is open, redo as needed.)

* **Install remaining packages:**
  
  ```<pip install requests python-dotenv>```

## How to Run the Pipeline

* **Run the following stages in order:**
  1. ```python zephyr_mining.py commits```    -> ```commits.csv```

  2. ```python zephyr_mining.py threads```    -> ```threads.csv```
     
  3. ```python zephyr_mining.py comments```   -> ```comments.csv```

  4. ```python zephyr_mining.py links```      -> ```commit_pr_links.csv```

  5. ```python zephyr_mining.py build```      -> ```final_dataset.csv```

  6. ```python zephyr_mining.py rabbit```     -> ```rabbit.csv```

  7. ```python zephyr_mining.py build```      # rebuild via ```rabbit.csv```

**Notes:**
* ```all``` will run rabbit prior to build.
* It can take hours to run stages, but they will save as they progress forward.


## Step Breakdown

1. **Detection procedure:** -> regarding ```gen_signals.py```, regex on the commit messages, the thread titles plus bodies, and comments for: ```assisted_by_tag```, ```ai_coauthor```, and ```ai_keyword```.

2. **Flagged:** comments by any AI bot accounts, plus PRs that were linked to any flagged commits. 

3. **Our Filters** -> ```zephyr_build_dataset.py```
   
      * Removed duplicate threads or comments from restarted collection runs.
        
      * Observation period filter applied, dates given above.
        
      * Exclusions used for automation-bots, and AI-assistant bots were marked and kept.
  
      * Threads with at least 1 GenAI signal, were also kept. 

* **Derived variables per a thread** -> ```n_comments```,```n_participants```, ```n_ai_bot_comments```, ```n_genai_comments```, ```all_signals```, ```strongest_signal```, ```has_assisted_by_tag```, ```linked_flagged_commit```, ```is_merged```, ```censored```, ```days_open```, ```days_to_first_genai_comment```

* **Validation** -> ```validation_sample.csv``` used up to 20 candidates (at random) per the signal type; and 40 candidates. 

### The Checkpoints

| - | Threads | Comments | Commits | Unique authors |
| :--- | :---: | :---: | :---: | :---: |
| Artifacts retrieved | 67,036 | 496,268 | 81,079 | |
| After deduplication | 67,036 | 496,268 | | |
| After observation period filter | 67,036 | 496,268 | | |
| After exclusions (the automation bots) | 62,408 | 414,584 | | |
| Final Observations (the GenAI candidates) | 3,065 | 49,833 | | |
| Commits w. GenAI signals | | |    3,148    | |
| Unique authors sent to RABBIT | | | | 922 |
| Coding sample threads | 300| | | |
| Validation sample threads | 120 | | | | 

* **The full counts** -> ```checkpoints.json```
  
  * **Run:** settings/versions -> ```provenance.json```

## The Files

1. **The Code:** ```zephyr_mining.py``` (the runner), ```zephyr_pydriller.py```, ```zephyr_github_api.py```, ```genai_signals.py```, ```zephyr_build_dataset.py```, ```zephyr_thread_views.py```, ```zephyr_split_coding_sample.py```, ```backfill_provenance.py```

2. **Raw Data:** ```commits.csv```, ```threads.csv```, ```comments.zip``` (aka ```comments.csv```), ```commit_pr_links.csv```, ```rabbit.csv```, ```rabbit_users.csv```

3. **Final Files:** ```final_dataset.csv``` (w. 1 row per candidate thread), ```final_comments.csv```, ```threads_derived.csv``` (all the threads with derived variables), ```validation_sample.csv```, ```coding_sample.csv```, ```coding_sample_comments.csv```, ```validation_results.json```, ```provenance.json```
