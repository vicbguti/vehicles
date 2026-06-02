# Mathematical Complexity of the Search Space

When deduplicating our dataset of $N = 4,306,526$ registration records, checking every record against every other record requires pairwise comparisons:

$$\text{Total Comparisons} = \frac{N(N-1)}{2} = \frac{4,306,526 \times 4,306,525}{2} = \mathbf{9,273,047,381,275} \text{ (9.27 Trillion Comparisons)}$$

* **Without ML (Fuzzy/Regex)**: If a server runs a standard fuzzy string comparison (like Levenshtein distance) taking just **1 microsecond** per check, completing 9.27 trillion checks would take:
  $$\frac{9.27 \times 10^{12} \text{ microseconds}}{10^6 \text{ s/min}} \approx 9,273,047 \text{ seconds} \approx \mathbf{107 \text{ days of continuous computing}}.$$
* **With ML (Vector Indexing)**: Converting the text to vectors allows us to use spatial indexing (like KD-Trees or HNSW), which reduces the search complexity from $O(N^2)$ to $O(N \log N)$, reducing the deduplication process from **107 days to less than 15 minutes**.
