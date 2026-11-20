# Community skills

This folder is the live skill shelf of the Yochai plugin. The server reads it and offers each skill through the `list_skills` and `load_skill` tools. A skill that is merged here reaches every user on the next deploy. No plugin update is needed.

## How a skill gets here

A skill passes 4 gates. Each one must pass.

1. **Review.** The author publishes the skill on the Yochai Create page. A Yochai reviewer approves it.
2. **Consent.** The author agrees that the skill can be shared in the public plugin, under their name.
3. **Safety check.** An automated check reads the skill. It rejects a skill that asks for anything other than study help, that contains personal details, or that tries to change how the assistant behaves.
4. **A person merges it.** The pipeline opens a pull request that adds the skill here. A member of the Yochai team reads it and merges it.

Nobody adds a skill to this folder by hand without those gates.

## Layout

One folder for each skill. The folder name is the skill name.

```
shelf/community/
  <skill-name>/
    SKILL.md
```

`SKILL.md` starts with this header:

```
---
name: <skill-name, lower case with hyphens>
description: <what the method does and when to use it>
author: <the author's name as they want it shown>
source: <link to the skill on Yochai Create>
---
```

The body is the method, in plain Markdown. It can name only the Yochai tools: `search_passages`, `get_passage`, `get_commentaries`, `get_cross_references`, `get_talmud_discussion`, `search_concepts`, `get_concept`, `get_related_concepts`, `get_learning_path`, `get_concept_sources`, `browse_themes`, `list_texts`, `get_study_path` and `get_jewish_calendar`.

## Rules for every skill

- It is a method for studying Jewish texts, and nothing else.
- It quotes only passages that a tool returned, with the reference and the link.
- It gives no rulings on practice.
- It holds no personal details and no helper files.
- It stays under 500 lines.

## Remove a skill

Open a pull request that deletes its folder. The skill leaves the shelf on the next deploy.

## Held skills

The folder `shelf/_held/` holds skills that wait for an author's written consent. The server does not read that folder.
