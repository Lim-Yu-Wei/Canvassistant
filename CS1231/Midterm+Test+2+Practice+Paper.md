---
module: CS1231
course: CS1231 Discrete Structures [2520]
date: 2026-03-14
source: Midterm+Test+2+Practice+Paper.pdf
tags: [cs1231, lecture-notes, auto-generated]
up: "[[MOD_INDEX]]"
---

# Midterm 2 Practice Paper Solutions Overview

> [!info] Navigation
> ↑ Back to [[MOD_INDEX]]

## Summary
This note provides detailed solutions and analysis for the CS1231 Midterm 2 Practice Paper. It covers function properties, floor and ceiling functions, and set operations. The questions test fundamental understanding in determining if relations are functions, evaluating injectivity and surjectivity, manipulating floors and ceilings, and applying set theory laws, including De Morgan's laws and membership rules.

## Key Concepts
- [[Function]] — A relation from a domain to a codomain that assigns exactly one output to each input.
- [[Injective Function]] — A function where each element in the range is mapped from a unique element in the domain.
- [[Surjective Function]] — A function where every element of the codomain has a preimage in the domain.
- [[Floor Function]], [[Ceiling Function]] — Functions that map a real number to the greatest integer less than or equal to the number or to the smallest integer not less than the number respectively.
- [[Set Difference]], [[Union]], [[Intersection]] — Basic set operations used to manipulate and relate sets.

## Detailed Notes

### Functions and Their Properties

1. **Problem 1: Function Verification**
   - (a) Is $f : \mathbb{Z}^+ \to \mathbb{Z}^+$ with $f(n) = \sqrt{n}$ a function? 
     - Answer: NO
   - (b) Is $g : \mathbb{Z} \to \mathbb{R}$ with $g(x) = \frac{1}{x^2 - 5}$ a function? 
     - Answer: NO

### Floor and Ceiling Functions

2. **Problem 2: Function Attributes**
   - For $f : \mathbb{R} \to \mathbb{Z}$ where $f(x) = \lfloor x/2 \rfloor$:
     - (a) Is $f$ 1-1? 
       - Answer: NO
       - Justification: Multiple $x$ values can result in the same $\lfloor x/2 \rfloor$.
     - (b) Is $f$ onto? 
       - Answer: NO
       - Justification: Not all integers can be represented as $\lfloor x/2 \rfloor$.

3. **Problem 3: Floor-Ceiling Conjecture**
   - Prove or disprove: $\forall x \in \mathbb{R}^+, \lfloor \lceil x \rceil \rfloor = \lfloor x \rfloor$.
     - Proof: This is true because $\lceil x \rceil$ is an integer, so applying $\lfloor \rceil$ returns the same integer unless $x$ itself is already an integer.

4. **Problem 4: Ceiling Result**
   - Prove $\lceil x/2 \rceil/2 = \lceil x/4 \rceil$.
     - Start by analyzing boundary cases and performing algebraic manipulation to equate both sides under the definitions of ceiling.

### Set Theory

5. **Problem 5: Set Identities**
   - Mark each as TRUE or FALSE:
     - (a) $A - (B - C) = (A - B) - C$. Answer: FALSE
     - (b) $(A - C) - (B - C) = A - B$. Answer: FALSE
     - (c) $A \cap (B \cup C) = (A \cup B) \cap (A \cup C)$. Answer: TRUE
     - (d) If $A \cup C = B \cup C$, then $A = B$. Answer: FALSE
     - (e) If $A \oplus B = A$, then $B = A$. Answer: TRUE

6. **Problem 6: Set Difference Proof**
   - (i) Using De Morgan's Laws:
     - $A - (B \cap C) = (A - B) \cup (A - C)$
     - Utilize De Morgan's and distribution laws to reframe the expression
   - (ii) Membership Equivalence:
     - Show for any element $x$, $x \in A - (B \cap C)$ if and only if $x \in (A - B) \cup (A - C)$
   - (iii) Visualization with Venn diagrams or a membership table.

## Worked Examples
- Example problem solutions are included above with typical CS1231 examination style justifications and steps.

## Exam Relevance
> [!warning] Exam Topics
> - Function properties: injectivity, surjectivity, and definitions.
> - Floor and ceiling functions with integrative problems.
> - Set operation identities and their derivations.