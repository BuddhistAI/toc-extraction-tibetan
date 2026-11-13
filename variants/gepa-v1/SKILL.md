---
name: toc-extraction-tibetan
description: Extract a hierarchical table of contents (sa-bcad outline) from raw Tibetan Buddhist commentary text whose formatting and line breaks have been stripped, and return a TOC tree plus the text with inline XML section markup. Use when given unformatted Tibetan commentary and asked for its outline, TOC or section structure.
metadata:
  task: toc-extraction
  language: tibetan
  language-code: bo
  variant: gepa-v1
  version: 1.0.0
  benchmark: toc-extraction-tibetan@1.0.0
  origin: GEPA-optimised (DSPy 3.4.1), task model claude-haiku-4-5, reflection model claude-sonnet-4-5, 2026-11-02
---


# Extract a TOC from raw Tibetan commentary

You are given a passage of a Tibetan Buddhist commentary in which all formatting and line breaks have been removed. Find every outline heading (ས་བཅད, sa-bcad) in the passage, in reading order. For each heading return: depth (1 = the shallowest heading level present in this passage, 2 = a sub-section of a depth-1 heading, and so on), anchor (the first 40 characters of the heading copied verbatim from the passage, starting at its first character, including a leading ༈ if there is one) and title (a short label of the section). Return an empty list if the passage contains no headings.

Outline headings follow these patterns:

1. Headings typically begin with ordinal markers such as དང་པོ་ ("first"), གཉིས་པ་ ("second"), གསུམ་པ་ ("third"), བཞི་པ་ ("fourth"), ལྔ་པ་ ("fifth"), and so on, often followed by a topic phrase and structural particles ལ་, ནི་, or division markers ལ་གཉིས།, ལ་གསུམ།, ལ་བཞི།, etc.

2. The structural phrase ལ་གཉིས། indicates the section is divided into two parts, ལ་གསུམ། into three parts, ལ་བཞི། into four parts, etc. These division markers signal that the following headings are subsections.

3. Subsections are introduced with ordinal markers that reference back to the parent division. For example, after "ལ་གཉིས།" (divided into two), you will typically find "དང་པོ་" (the first) and "གཉིས་པ་" (the second) as immediate children.

4. Sometimes the heading includes a parenthetical recap of the parent section title in parentheses after the ordinal, e.g., "དང་པོ་(ཆགས་བྲལ་སྔོན་སོང༌)ལ།" means "First (regarding those free from attachment proceeding)".

5. Depth is determined by the hierarchical nesting: top-level sections have depth 1, their immediate subsections have depth 2, subsections of those have depth 3, and so on. Track the parent-child relationships carefully by noting when a section announces subdivisions (ལ་གཉིས། etc.) and then look for the corresponding ordinal-marked subsections that follow.

6. The anchor must be copied character-for-character from the passage, including all Tibetan Unicode characters, spaces, and punctuation exactly as they appear. Do not normalize, transliterate, or modify the text in any way.

7. The title should be a concise descriptive label extracted from the heading phrase, typically the main topic portion without the ordinal and structural particles.

8. Headings may appear anywhere in the passage and are interspersed with explanatory content. Scan the entire passage systematically to identify all headings.

9. Pay special attention to phrases like "ཞུགས་གནས་གཉིས། དང་པོ་(ཞུགས་)" which means "[divided into] two: entering and abiding. First (entering)" — here the parent heading announces a two-part division, and the child heading "དང་པོ་" references the first part.

10. Not every sentence beginning with an ordinal is a heading. Context is important: headings are structural markers that organize the outline and are typically followed by explanatory content on that topic. Ordinal markers embedded in explanatory prose (e.g., when the text is discussing "the first dhyana" or "the second feeling") are NOT headings.

11. རྒྱུ་མཚན་དང༌། རྒྱུ་མཚན་ཅན་གྱི་གང་ཟག་གོ། is a pattern meaning "[divided into] two: the reason and the persons characterized by that reason" — the དང༌ is a connector indicating two topics, and the final གོ། or གོ punctuates the list of divisions.

12. When a heading announces subdivisions (e.g., ལ་གསུམ།), the depth of the following ordinal-marked subsections (དང་པོ་, གཉིས་པ་, གསུམ་པ་) is one greater than the depth of the heading announcing the divisions.

13. Track the depth by maintaining a mental or explicit stack of the current outline level as you read through the passage. When a new subdivision is announced, push the context; when a subdivision sequence is complete (all announced parts have been covered), pop back to the parent level.

14. Always copy the anchor starting exactly at the first character of the heading as it appears in the passage, even if that means including preceding particles or markers that are part of the heading phrase.

15. Ensure every heading returned is actually present verbatim in the passage. Double-check that the anchor text can be found character-for-character in the input.

16. CRITICAL: A phrase like "བཞི་པ་མི་གཡོ་བར་གཞག་པའི་རྒྱུ་མཚན་ནི།" ("Fourth, the reason for establishing [it] as unmoving:") IS a structural heading when it introduces a new section, even if it does not explicitly announce subdivisions. The ordinal (བཞི་པ་) + topic phrase (མི་གཡོ་བར་གཞག་པའི་རྒྱུ་མཚན) + particle (ནི།) pattern is the canonical heading form.

17. CRITICAL: When you see a sequence like "བཞི་པ་མི་གཡོ་བར་གཞག་པའི་རྒྱུ་མཚན་ནི།" followed later by "གཉིས་པ་འབྲས་བུ་སྐྱེ་བ་ན་ཚོར་བ་དུ་ཡོད་དཔྱད་པ་ནི།" and then "གསུམ་པ་ཇི་ལྟར་འཐོབ་ཚུལ་ནི།", these latter two (གཉིས་པ་ and གསུམ་པ་) are at depth 2 (subsections of བཞི་པ་), NOT depth 1. Even though བཞི་པ་ does not explicitly say "ལ་གསུམ།", the presence of consecutive ordinal-marked subsections indicates an implicit subdivision structure.

18. CRITICAL: Distinguish between two cases: (a) Consecutive independent top-level headings (དང་པོ་, གཉིས་པ་, གསུམ་པ་ as siblings at depth 1), and (b) A parent heading followed by subordinate headings that count as its subdivisions. The key indicator for (b) is when a heading is followed by consecutive ordinals starting from དང་པོ་ that elaborate on sub-topics of that heading, even if the parent does not explicitly announce the number of subdivisions.

19. When ordinal markers appear in explanatory prose (e.g., "བསམ་གཏན་གཉིས་པ་ན་ཡིད་བདེ། གསུམ་པ་ན་སེམས་བདེ།" meaning "in the second dhyana there is mental bliss, in the third there is mental bliss"), these are NOT headings. They are references within the explanation.

20. If the passage begins with a heading like "གཉིས་པ་བརྩམ་པའི་བསྟན་བཅོས་ཀྱི་ལུས་དངོས་ལ་གཉིས།" ("Second, the actual body of the composed treatise [divided into] two:"), then the ordinals that follow (དང་པོ་, གཉིས་པ་) are its children at depth 2, not siblings at depth 1.

21. CRITICAL DEPTH RULE: In the first example, the passage DOES NOT begin with a top-level དང་པོ་ heading that contains everything else. Instead, there are THREE independent top-level sections at depth 1: (1) "དང་པོ་(འདུས་བྱས་ཀྱི་ཕྱོགས་)ནི།", (2) "གཉིས་པ་མིང་གི་རྣམ་གྲངས་ལ་གཉིས།" (which announces two subdivisions), and (3) "གསུམ་པ་ཕུང་ཁམས་སྐྱེ་མཆེད་རྒྱས་པར་བཤད་པ་ལ་གསུམ།" (which announces three subdivisions). The subdivisions of (2) and (3) are at depth 2, not depth 3. This is clear because these are sibling sections (first, second, third) at the top level of THIS passage, even though they may be subsections of some larger work.

22. CRITICAL DEPTH RULE: In the third example, "གཉིས་པ་དེའི་ཁྱད་ཆོས་ལ་གཉིས།" is at depth 4, NOT depth 3. The structure is: (depth 1) གཉིས་པ་མཚུངས་ལྡན་མ་ཡིན་པའི་སྐྱེ་ཚུལ་ལ་གསུམ། > (depth 2) གཉིས་པ་རྒྱས་བཤད་ལ་བདུན། > (depth 3) དང་པོ་(ཐོབ་མ་ཐོབ་)ལ་གཉིས། > (depth 4) དང་པོ་(དངོས་)ནི། AND གཉིས་པ་དེའི་ཁྱད་ཆོས་ལ་གཉིས། The two depth-4 headings (དང་པོ་(དངོས་)ནི། and གཉིས་པ་དེའི་ཁྱད་ཆོས་ལ་གཉིས།) are SIBLINGS, both children of the depth-3 heading that announced "ལ་གཉིས།" (divided into two).

23. When a heading announces "ལ་གཉིས།" (divided into two), you should expect TWO immediate child headings marked དང་པོ་ and གཉིས་པ་ at the next depth level. Both of these children are at the SAME depth (one level deeper than the parent). Do not increment depth again for the second child; both དང་པོ་ and གཉིས་པ་ are siblings.

24. The pattern "[Ordinal]པ་...[topic]...ལ་[number]།" followed by "དང་པོ་...", "གཉིས་པ་...", etc. creates a clear parent-child structure where all the numbered subsections (དང་པོ་, གཉིས་པ་, གསུམ་པ་, etc.) are siblings at depth = (parent depth + 1).

25. CRITICAL DEPTH TRACKING RULE: When processing a passage, you MUST track depth explicitly using the hierarchical structure. The key is to understand parent-child relationships:
   - A heading that announces subdivisions (ལ་གཉིས།, ལ་གསུམ།, etc.) is a PARENT.
   - The subsequent ordinal-marked headings (དང་པོ་, གཉིས་པ་, etc.) are CHILDREN of that parent, at depth = parent_depth + 1.
   - All children of the same parent are SIBLINGS at the same depth.
   - When the announced number of children is complete, depth returns to the parent's level for the next sibling of the parent.

26. CRITICAL: In the second example feedback, the depth errors occurred because each heading with "ལ་[number]།" creates a NEW nesting level. For instance:
   - "༈ བཞི་པ་ལས་བསྟན་པའི་གནས་འཆད་པ་ལ་གཉིས།" is depth 1, announcing two children.
   - "དང་པོ་(མཚམས་སྦྱར་བ་)ནི།" and "གཉིས་པ་ལས་དངོས་བཤད་པ་ལ་གཉིས།" are depth 2 (children of the depth-1 parent).
   - "དང་པོ་(ལས་ཀྱི་ངོ་བ་)ལ་གཉིས།" is depth 3 (child of "གཉིས་པ་ལས་དངོས་བཤད་པ་ལ་གཉིས།" which is depth 2).
   - "དང་པོ་(མདོར་བསྟན་པ་)ནི།" is depth 4 (child of "དང་པོ་(ལས་ཀྱི་ངོ་བ་)ལ་གཉིས།" which is depth 3).
   - "གཉིས་པ་རྒྱས་བཤད་ལ་གསུམ།" is ALSO depth 4 (sibling of "དང་པོ་(མདོར་བསྟན་པ་)ནི།" because both are children of "དང་པོ་(ལས་ཀྱི་ངོ་བ་)ལ་གཉིས།").

27. CRITICAL ALGORITHM: To correctly assign depth, use this procedure:
   a. Start with depth = 1 for the first heading.
   b. When you encounter a heading with "ལ་[number]།", it announces [number] children. The NEXT heading will be at depth = current_depth + 1, and it is the FIRST child.
   c. Continue reading subsequent headings. Each ordinal-marked heading (དང་པོ་, གཉིས་པ་, གསུམ་པ་, etc.) at the child level is a sibling at the same depth until all announced children are accounted for.
   d. After all announced children are found, the next heading returns to the parent's depth level (or deeper if it's a child of one of the siblings).
   e. Keep a stack or nested count to track how many children each parent expects and when to pop back to a shallower depth.

28. EXAMPLE DEPTH CALCULATION: For the structure "A ལ་གཉིས། > B དང་པོ་ ལ་གསུམ། > C དང་པོ་ > D གཉིས་པ་ > E གསུམ་པ་ > F གཉིས་པ་":
   - A is depth 1 (announces 2 children)
   - B is depth 2 (first child of A, announces 3 children)
   - C, D, E are depth 3 (the three children of B)
   - F is depth 2 (second child of A, sibling of B)

29. CRITICAL: Not all ordinal phrases followed by topic and particle patterns are subdivision announcements. Some, like "མདོ་ལས་འབྱུང་བའི་རྣམ་གྲངས།" and "བསྟན་བཅོས་ལས་འབྱུང་བའི་རྣམ་གྲངས་སོ།" from the feedback, may be simple topic labels without ordinal markers and thus not true outline headings. Only phrases with explicit ordinal markers (དང་པོ་, གཉིས་པ་, etc.) are outline headings. In the first example feedback, these were marked as spurious because they lack ordinal markers at the beginning.

30. HEADING IDENTIFICATION RULE: A true outline heading MUST start with an ordinal marker (དང་པོ་, གཉིས་པ་, གསུམ་པ་, བཞི་པ་, ལྔ་པ་, etc.) or be part of a subdivision announcement pattern. Simple topic phrases listed after a parent heading are NOT independent headings unless they have ordinal markers. For example, after "ལྔ་པ་རྣམ་གྲངས་བཤད་པ་ལ་གཉིས། མདོ་ལས་འབྱུང་བའི་རྣམ་གྲངས། བསྟན་བཅོས་ལས་འབྱུང་བའི་རྣམ་གྲངས་སོ།", the two topic labels are just enumerations of what the two parts will cover, not actual headings themselves. The actual headings would be ordinal-marked sections that follow.

## Output format

Return a JSON list, in reading order, of objects:

```json
[{"depth": 1, "anchor": "<first <=40 characters of the heading, verbatim>", "title": "<short label>"}]
```

* `depth` is relative: 1 is the shallowest level present in the passage you were given.
* `anchor` must be an exact substring of the passage and must start at the first character of the heading
  (including a leading ༈).

## Rendering the two deliverables

1. **TOC tree** - one line per heading, indented two spaces per depth level, prefixed with a dotted
   sibling number (1, 1.1, 1.1.1, ...) followed by the title.
2. **Inline XML** - wrap the whole passage in `<text>`; at each heading's start insert
   `<section depth="N" title="...">` and close it (`</section>`) just before the next heading of the same or a
   shallower depth, or at the end of the text. Escape `& < >`. Removing the tags must give back the input
   text exactly.
