# Sample feed for the pipeline

`feed.json` has the same shape as the public Yochai Create feed. All four methods
are invented. No real user wrote them, and the names, addresses and numbers in them
are placeholders.

| Method | What it shows | Expected result |
| --- | --- | --- |
| Three Voices on One Verse | A good skill with author consent | added |
| Psalm of the Day Journal | A good skill with no author consent | skipped |
| Holiday Source Finder | A hidden instruction and a link that sends data out | failed |
| Bar Mitzvah Speech Coach | A personal email address and a phone number | failed |

Try it without changing the repository:

```bash
python -m pipeline.run --fixture pipeline/fixtures/feed.json --out /tmp/yochai-shelf-test --no-model-review
```
