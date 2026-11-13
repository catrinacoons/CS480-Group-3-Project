# Qualitative Codebook v0.9

**Codebook Editor**: Julia Wilson
> related tasks to pull into codebook: T8. Draft the Category List (done), T11. Merge the Entries into Codebook v0.9 (done), T13. Revise and Freeze Codebook v1.0, and T18. Revision Round (only if T17 says revise)

## How to Code Each Thread

- The unit of analysis is the thread.
- **Primary Category:** the human reaction to the GenAI output. Use the most prominent reaction within the thread.
- **Secondary Category:** the source of the GenAI output that the primary category responds to.
- Multi-label rule: one primary category and at most one secondary cateogry.
- Reliability is measured on the primary label only.
- **False Positive:** the thread doesn't contain GenAI output.
  - Set `not_genai_flag` to `yes`.
  - Leave the primary and secondary categories as blank.
  - Flagged threads are left out of the category percentages and the denominator is stated.

## Identified Response Categories

### Primary Categories (human reaction to the GenAI output)

#### No Engagement
GenAI output is visible within the thread, however no human either replies to it, mentions it or acts on it.
- **Applies when:**
  - The thread contains visible GenAi output, like an AI reviewers comment or an AI-assisted contribution, but no human comment responds to it specifically.
  - The GenAI output is the last item before the mining window closed, then its 'No Engagement' and add a note that the window ended.
- **Doesn't apply when:**
  - Any human comment either replies to, mentions, applies, rejects, tests or asks about the GenAI output, code that response instead.
  - No GenAI output is clearly visible in the thread. That's a 'False Positive'.
- **Boundary rule:** If any human comment engages with the GenAI output, even if they didn't agree or reject it, its not 'No Engagement'. Silence on that specific output is the test.
- **Examples:**
  - An Assisted-by tag is present and clearly disclosed by the contributor, however no human response mentioning it.
  - Copilot posts a review and the author doesn't respond to it at all or say "done".
  
#### Accepted and Applied
GenAI suggestions were either applied, fixed or agreed with.
- **Applies when:**
  - A human comment says that a GenAI suggestion was either applied, fixed, addressed or they agree with it.
  - The human applies more GenAI suggestions then they reject.
- **Doesn't apply when:**
  - A human replies without either agreeing or applying, that's 'Questioned or Discussed'.
  - A human either declines the suggestion or rejects more suggestions than they apply, that's 'Rejected or Rebutted'.
  - Either "fixed" or "done" is given as a reply to a human reviewer, and not to the GenAI output.
- **Boundary rule:** When a human applies some GenAI suggestions and rejects others, then the majority decides. If more applied than rejected, then it is 'Accepted and Applied'.
- **Examples:**
  - Thread 112837: author replies "done" and "added" to Copilot's review comments.
  - Thread 114433: author fixes 4 of Copilot's 6 suggestions and rejects only 2.
  
#### Questioned or Discussed
Either a question, concern or change request about the GenAI output is raised, but without giving a clear acceptance or rejection.
- **Applies when:**
  - There is a discussion around a GenAI suggestion, but with no resolution.
  - A contributor comments on the suggestion, but no human or GenAI responds to it.
- **Doesn't apply when:**
  - The suggestion is either accepted or rejected.
- **Boundary rule:** If at least 1 suggestion is accepted or rejected or if the suggestion is not directly addressed, then it isn't 'Questioned or Discussed'.
- **Examples:**
  - A reviewer asks if a GenAi suggestion is correct and thread ends without it being either accepted or rejected.
  - Contributors discuss a GenAI suggestion, without coming to a final decision.
  
#### Rejected or Rebutted
GenAI output is declined or argued against, either with or without a clear reason given.
- **Applies when:**
  - A human rejects a GenAI suggestion, by either replying to the AI or by responding to another contributor regarding it.
  - Multiple suggestions are present and the majority of them are rejected.
- **Doesn't apply when:**
  - The suggestion is either ignored or no human responds to it, 'No Engagement'.
- **Boundary rule 1:** The majority decides when a human applies some GenAI suggestions and rejects others. If more are rejected, it is 'Rejected or Rebutted'. The rejection must directly respond to the GenAI suggestion itself.
- **Boundary rule 2:** If humans discuss a suggestion and decide to reject it, then its 'Rejected or Rebutted'. If the thread doesn't end in a rejection, then its 'Questioned or Discussed'.
- **Examples:**
  - Thread 119073: contributors discuss a Copilot suggestion, and the author then explains why it would not work.
  - Thread 111295: a maintainer replies that the line that Copilot flagged "was fine" and then explains why.

#### Disclosure Requested
GenAI use is reacted to and a disclosure of its use is requested by someone.
- **Applies when:**
  - A human asks how something was created or asks the author to disclose AI use by adding an "Assisted-by" or "co-authored-by" tag. Or the author is requested to follow Zephyr's AI policy.
- **Doesn't apply when:**
  - AI use was disclosed voluntarily and nobody reacts to it, that's 'No Engagement'.
  - The AI output is either accepted or rejected without any questions surrounding its use.
- **Boundary rule:** A human must ask for the AI disclosure, and if the author discloses AI use and nobody responds to i, then its 'No Engagement'.
- **Examples:**
  - Thread 114006: a reviewer writes "Nice catch. How did you find this?", and the author replies that he used Claude Code Fable.
  - Thread 110787: the maintainer asks the author to follow Zephyr's AI policy by adding an "Assisted-by" tag to the commit. The author follows this advice, and adds the tag.

#### Tested or Verified
The author or reviewer checks the GenAI output and reports a result.
- **Applies when:**
  - A human either runs, builds, or tests the GenAI output and reports what happened.
- **Doesn't apply when:**
  - The output is accepted or rejected based solely on reading or reasoning alone, with no reported check 'Accepted and Applied' or 'Rejected or Rebutted'.
- **Boundary rule (vs. Accepted and Applied):** If any test or check of the GenAi output is reported, that's 'Tested or Verified', regardless if the output is accepted afterwards. Use 'Accepted and Applied' only when the output is applied with no reported check.
- **Examples:**
  - Thread 105778: a tester runs AI-assisted fixes, like "Assisted-by: Claude" on hardware and reports it worked.
  - Thread 114096: the author describes the revert test he ran to confirm that the Claude-assisted fix corrects the bug.

### Secondary Categories (source of the GenAI output the primary category responds to)

- Code the source of the GenAI output that the primary category is about.
- If a thread has both sources, then use the one behind the primary category and mention the others in the notes section.
- Include the model or tool name in the notes when its known.

#### AI Reviewer
Comments posted by an AI review account. Use when reviewers respond to AI comments.
- **Examples:**
  - Copilot
  - Claude
  - ChatGPT

#### AI Assisted, Disclosed
The author discloses their use of GenAI immediately, without being asked anywhere in the thread about it. Use when reviewers respond to AI-assisted code.
- **Examples:**
  - An Assisted-by or Co-authored-by tag is listed.
  - GenAI use is stated in plaintext somewhere in the PR without a tag.

#### AI Assisted, Disclosed Later
GenAI use is disclosed only after the author is asked about it, anywhere in the thread.
- **Examples:**
  - Someone asks a question like "How did you find this?"
  - Zephyr's AI disclosure policy is mentioned and the author is asked to follow it.

### Not Applicable Category

#### False Positive
The thread was detected as GenAI, but thread has no GenAI output. 
- **How to code:** set `not_genai_flag` to `yes`, and leave the primary and secondary category as blank.
- **Examples:**
  - AI is mentioned in the discussion, possibly as a tool someone could use but it never appears and was never disclosed as used.
  - GenAI is missing from the thread. It may be used in a linked commit, but it doesn't appear in the thread being reviewed.

## Representative Examples

- **No Engagement**: Copilot review with no response, see entry examples
- **Accepted and Applied**: threads 112837, 114433
- **Rejected or Rebutted**: see entry examples
- **Disclosure Requested**: threads 119073, 111295
- **Tested or Verified**: threads 105778, 114096

### Table 1 outline

|Category|Type|Definition|
|:-------|:-------|:-------|
|No Engagement|Primary|GenAI output is visible but no human responds to it.|
|Accepted and Applied|Primary|GenAI suggestions were either applied, fixed, or agreed with.|
|Questioned or Discussed|Primary|GenAI output is questioned or discussed without being either accepted or rejected.|
|Rejected or Rebutted|Primary|GenAI output is declined or argued against, either with or without a reason.|
|Disclosure Requested|Primary|A human asks how something was made or asks for AI use to be disclosed.|
|Tested or Verified|Primary|A human tests or checks the GenAI output and reports the result.|
|AI Reviewer|Secondary|GenAI output comes from an AI review account.|
|AI Assisted, Disclosed|Secondary|The author disclosed GenAI use without being asked.|
|AI Assisted, Disclosed Later|Secondary|GenAI use was disclosed only after someone asked.|
|False Positive|Not applicable|The thread has no GenAI output. Flag it and then leave both categories blank.|
