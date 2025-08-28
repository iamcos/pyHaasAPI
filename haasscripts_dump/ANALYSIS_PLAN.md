# HaasScript Analysis Plan

This document outlines the iterative process for analyzing the HaasScript files in this directory to produce a comprehensive guide.

## Goal
To provide a detailed guide on how to properly use HaasScript, its full feature set, capabilities, limitations, and useful script snippets, based on the provided script dump.

## Iterative Workflow

### Phase 1: Initial Exploration and Data Collection (Completed)
- List all files in `haasscripts_dump`.
- Read the content of all `.hss` files.

### Phase 2: Script Analysis and Feature Extraction (Current)
- **Objective:** Deep dive into individual scripts to identify specific functions, patterns, and unique HaasScript behaviors.
- **Process:**
    1.  **Categorization:** Group scripts by their primary function (e.g., indicators, trading bots, utility functions, examples).
    2.  **Function/API Mapping:** Create a comprehensive list of all built-in HaasScript functions and their typical usage.
    3.  **Pattern Identification:** Document common coding patterns for:
        *   Input definition
        *   Data retrieval (prices, volume)
        *   Indicator calculation
        *   Trading logic (entry, exit, position management)
        *   Error handling and logging
        *   State persistence (`Save`/`Load`)
        *   Plotting and reporting
    4.  **Feature Set Identification:** Based on observed patterns, explicitly list what can be achieved with HaasScript.
    5.  **Limitation Identification:** Infer what cannot be done or what are common pitfalls.
    6.  **Snippet Extraction:** Isolate and document reusable code snippets for common tasks.

### Phase 3: Guide Generation
- **Objective:** Compile all extracted information into a structured and user-friendly guide.
- **Output:** `GUIDE.md` within `haasscripts_dump`.
- **Content:**
    *   Introduction to HaasScript (Lua-based, purpose).
    *   Core Concepts (variables, data types, control flow).
    *   Built-in Functions Reference (categorized: Data, Indicators, Trading, Utility, Plotting, IO).
    *   Common Script Structures (indicators, simple bots, advanced bots).
    *   How to Use HaasScript Properly (best practices, common patterns).
    *   What Can Be Done (detailed feature set with examples).
    *   What Cannot Be Done (explicit limitations).
    *   Useful Script Snippets (ready-to-use code examples).
    *   Debugging and Reporting.

### Phase 4: Workflow Documentation (Current)
- **Objective:** Document the iterative nature of this analysis and how to extend it.
- **Output:** This `ANALYSIS_PLAN.md` file.
- **Content:**
    *   Outline of phases.
    *   Instructions for adding new scripts for analysis.
    *   Guidance on updating the `GUIDE.md` with new discoveries.

### Phase 5: Review and Refinement
- **Objective:** Ensure accuracy, completeness, clarity, and conciseness of the generated guide and plan.

## Iteration Strategy
This process is designed to be iterative. As new scripts are added to `haasscripts_dump` or new insights are gained, the analysis can be re-run, and the `GUIDE.md` updated.

**To add new scripts:**
1.  Place new `.hss` files into the `haasscripts_dump` directory.
2.  Re-run Phase 1 (read all files).
3.  Re-run Phase 2 (analyze new and existing scripts for new patterns/features).
4.  Update `GUIDE.md` (Phase 3) with any new findings.

This iterative approach ensures that the guide remains current and comprehensive as the HaasScript codebase evolves.
