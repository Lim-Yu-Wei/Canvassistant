---
module: CS1231
course: CS1231 Discrete Structures [2520]
date: 2026-03-14
source: Midterm+Test+2+Practice+Paper+with+Reference+Solutions.pdf
tags: [cs1231, lecture-notes, auto-generated]
up: "[[MOD_INDEX]]"
---

# Midterm Test 2 Practice Paper Notes

> [!info] Navigation
> ↑ Back to [[MOD_INDEX]]

## Summary
This note summarizes solutions from the Midterm Test 2 Practice Paper for CS1231. Problem sets cover various topics including functions, proof techniques, set operations, and advanced problem-solving in logical and mathematical structures. Each question is addressed with a direct solution, showcasing typical answer specifications that students might find in an examination setting.

## Key Concepts
- [[Functions]] — Definitions and verification of whether certain provided mappings satisfy the properties of being functions.
- [[Set Operations]] — Use of set operations such as differences and intersections, employing De Morgan’s Laws and other set identities.
- [[Ceiling and Floor]] — Utilization of ceiling and floor functions within problem-solving.
- [[Proof Techniques]] — Application of logical proofs and set theory arguments to validate expressions and relationships among sets.

## Detailed Notes

### Functions
1. Verification of functions:
   - Given functions $f : \mathbb{Z}^+ \to \mathbb{Z}^+$ where $f(n) = \sqrt{n}$ and $g : \mathbb{Z} \to \mathbb{R}$ where $g(x) = \frac{1}{x^2 - 5}$: concluded that $f$ is not a function since it does not map integers to non-negative results uniquely, while $g$ is well-defined as a real-valued function for $x \neq 5$.

### Analysis of Set Operations
- Prove and disprove statements regarding set identities using logical and set-theoretical reasoning.
  
### Proving or Disproving Mathematical Statements
- Example: To disprove $\forall x \in \mathbb{R}^+, \lfloor \lceil \sqrt{x} \rceil \rfloor = \lfloor \sqrt{x} \rfloor$, consider $x = 8.5$: LHS gives 3 and RHS gives 2, thus disproven.
  
### Worked Example Using Ceil/Floor Functions
- Proving $\lceil x/2 \rceil / 2 = \lceil x/4 \rceil$ by considering cases:
  - If $\lceil x/4 \rceil = n$, then $2n - 2 < x/2 \leq 2n - 1$ yields $\lceil x/2 \rceil = 2n - 1$, resulting in $n$.

### Set Theory Identities
- Using logical notation and set operations, proving or disproving identities like $A − (B ∩ C) = (A − B) ∪ (A − C)$ using direct proofs and membership tables.

## Worked Examples
1. Function verification exercises:
   - Example answers without justification — aiming to develop the habit of quick identification practices in exams.

2. Set-theoretical identities:
   - Application of Venn diagrams and detailed argument steps to derive true identities from false assumptions.

## Exam Relevance
> [!warning] Exam Topics
> - Function verification under given conditions.
> - Comprehensive use of set operations and identities.
> - Proof-based questions: demonstrating proficiency in both symbolic and verbal reasoning.
> - Application of ceiling and floor functions within quantitative reasoning problems.