# Concrete Examples of the Comparisons

Here are **two actual examples** of the comparisons a computer has to perform 9 trillion times to find duplicates without ML:

## Comparison 1: The False Negative (Typos & Abbreviations)
* **Record A**: `TYT HLX D/C 4X4 2.7`
* **Record B**: `Toyota Hilux Double Cabin 4x4 Active`
* **Traditional String Search**: Compares characters letter-by-letter. The character distance (Levenshtein) is **18 edits**. Because the words look completely different to a basic string-matching algorithm, the computer flags them as **unrelated** (a false negative), losing the duplicate link.

## Comparison 2: The Wasted CPU cycles
* **Record A**: `TYT HLX D/C 4X4 2.7`
* **Record B**: `Hyundai Tucson 2.0 Active`
* **Traditional String Search**: Runs a character-by-character comparison, loops through the text, and calculates a high edit distance.
* **The Problem**: A human instantly knows a Toyota Hilux is not a Hyundai Tucson. But the non-ML computer must spend CPU cycles comparing them letter-by-letter anyway. Across 9.27 trillion comparisons, **99.9% of the CPU power is wasted** comparing completely unrelated brands (e.g. Ford vs. Suzuki).
