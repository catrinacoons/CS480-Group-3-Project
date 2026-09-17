# CS480-Group-3-Project
We are data mining the last 4 years of the zephyr GitHub repository for the CS480 Class Project 4: How Are GenAI Outputs Evaluated in Zephyr Development? We are answering research question: How do Zephyr contributors evaluate and respond to GenAI-generated outputs in development conversations?


## Project 4 Description
Project 4: How Are GenAI Outputs Evaluated in Zephyr Development?

Goal: Understand how Zephyr contributors assess, verify, correct, or reject GenAI-generated
suggestions during software development.

Research question: How do Zephyr contributors evaluate and respond to GenAI-generated outputs in
development conversations?

Data: You will mine the last 4 years of public Zephyr GitHub pull requests, review comments, issues,
and discussions containing observable signs of GenAI involvement.

To identify potential signs of GenAI use, follow the approach described by this paper: https://arxiv.org/pdf/2608.03329

Each candidate must be validated before inclusion. The goal is not to determine whether GenAI outputs are objectively better or worse than human-generated outputs. Instead, the project examines how contributors evaluate GenAI outputs once they become visible in development conversations.

The unit of analysis should generally be the conversation or review thread, so you can understand what GenAI produced, how contributors reacted, and what happened afterward.

You will need to explain your strategies to:

● Select which GitHub data to analyze and detect candidate GenAI signals

● Validate candidates and remove false positives

● Examine the surrounding conversation to identify how contributors evaluated the GenAI
output

● Qualitatively derive response categories from the data and develop a codebook

● Scale the analysis when appropriate, with human validation of automated classification

Expected analysis:
Develop a taxonomy of how GenAI outputs are evaluated and handled in Zephyr development conversations. Categories may include outputs being accepted, modified, corrected, questioned, or rejected, but the final taxonomy should come from the data.

Report how frequently each response type appears and examine the reasons contributors give for their decisions. Prepare a dataset of validated conversations and a qualitative codebook with the identified response categories and representative examples.
for their decisions.
Prepare a dataset of validated conversations and a qualitative codebook with the identified
response categories and representative examples.

## Delivery 1 - Research Design and Data Preparation
Each team selected has a project, which has a research question. For this delivery, your goal is to define exactly how you will answer the RQ and prepare the Zephyr data needed for the analysis.

Only one group member needs to submit the deliverable. Each group will receive a grade based on peer evaluations collected after submission.

Deliverables
### 1. Research Design

Use the provided Overleaf template and complete all sections that apply to your project.

You do not need to run the final analysis yet.

By this deadline, you must have:

mined the required Zephyr data;
applied the study filters;
cleaned the data;
constructed the variables needed for your RQ;
organized the dataset according to your unit of analysis.
The final dataset should be ready for analysis.

### 2. Replication Package

Submit a replication package that allows someone to reproduce and verify your dataset.

It must include:

code to retrieve the data in Python;
code to filter and clean the data in Python;
code to construct derived variables and the final dataset in Python;
raw data (CSV);
the final analysis-ready dataset (CSV);
a README explaining exactly how to run the pipeline (TXT.
The README should also report important checkpoints, for example: 

Artifacts retrieved: N

After observation-period filter: N

After exclusions: N

Final observations: N

Assignment 1 ends with a well-defined Research Design and a reproducible, analysis-ready dataset.

Peer Evaluation Process: Each team member will complete a separate individual assignment. In this assignment, you will independently evaluate your own and your teammates' contributions by distributing 400 points across the group members. Points should reflect each person's actual participation in the deliverable.

Individual Grade Calculation: Your final individual grade combines two components: The group's grade (based on this deliverable quality) and Your peer evaluation score (based on the average points you receive from all teammates). The instructor will use the peer evaluation average to adjust individual grades according to demonstrated participation.

Default Evaluation: If a team member does not submit their peer evaluation, the system will automatically assign equal points (100 points per member) for that evaluation.
