# The Almuri guide system

Every episode that offers something gets a guide: a branded Notion page that Lina "presents", with a GitHub link for the files, a credit for anyone whose work we feature, and the same calls to action at the end. Follow this for every episode, whatever the episode is about.

**Where the work happens:** Guide Studio in the Almuri HQ Notion workspace (private). It has the same playbook, the brand kit, the branded templates ready to duplicate, the Episodes tracker and the email list. This folder is the public copy of the rules, and the Markdown templates in `templates/` are a backup of the Notion ones. If you change one, change both.

## The loop

1. **Episode.** Lina runs into a problem with an AI tool. The episode ends with "Comment [KEYWORD] and I'll send you [the thing]."
2. **Message.** Meta's own comment-to-message feature sends one message with the Notion link. No other DM tool, ever (the privacy notice promises this).
3. **Guide page.** Branded Notion page, built from a template in `templates/`. Free, no signup needed to read it.
4. **Files.** Everything on the page is also in this repository under `guides/<keyword>/`, linked from the page.
5. **Calls to action at the end, always in this order:**
   - Join the list (optional Notion form, to hear about new episodes).
   - Comment the next keyword on another reel (sends people back to older posts).
   - Follow @heyalmuri.
6. **Library.** The guide is added to the README of this repository.

## Pick the template

| The episode is about... | Template | Example keyword |
| --- | --- | --- |
| Something we made (a prompt, a workflow, a visual, a skit setup) | [`templates/how-we-made-it.md`](templates/how-we-made-it.md) | 3D, SKIT, VOICE |
| Someone else's project (a GitHub repo, an open-source tool) | [`templates/featured-project.md`](templates/featured-project.md) | REPO, FIX |
| A short list or comparison (tools, prompts, settings) | [`templates/quick-list.md`](templates/quick-list.md) | TOOLS, PROMPTS |

Every template is built from the same blocks in [`templates/blocks.md`](templates/blocks.md). If an episode fits none of them, start from the closest one and keep the blocks.

## Branding: the same on every page

Set these once in Notion, then duplicate the template page so every guide starts with them.

- **Cover:** the Lina banner (same image on every page, from the almuri-media repository).
- **Icon:** the Almuri logo.
- **Title format:** "How Lina [did the thing]" for made-it guides, "[Project name]: the fix Lina found" for featured projects, "Lina's [list]" for quick lists.
- **Lina explains:** each step opens with a "Lina says" block: a small Lina image next to a callout in her voice (one or two lines, tired and funny, then useful). Use Notion columns: image on the left (about 1/4 width), callout on the right. Keep a folder of 6–8 Lina poses (pointing, facepalm, coffee, thumbs up, laptop, shrug) and reuse them.
- **Callout colors:** Lina says = gray, tips = blue, warnings = yellow, credit = green, calls to action = purple. Never other colors.
- **Footer:** the same footer on every page (in `blocks.md`): disclaimer, contact, privacy link.
- **Font and width:** Notion default font, full width off, so it reads well on a phone.

## Featured projects: credit rules

When an episode features someone else's work:

1. **Check the license** before showing anything. Link to their repository; never re-host their code here. Use their screenshots or images only if their license allows it, otherwise make our own.
2. **Credit block near the top and again at the end** (`blocks.md` → Credit): owner name, link to the repository, license, and "Almuri is not affiliated with [owner]. All credit for [project] goes to them."
3. **Credit in the episode too:** the owner's name on screen and in the caption.
4. **Tell them.** Open a polite issue or send a message: "We featured your project in a short comedy episode, here's the link. Happy to change or remove anything." Tick "Owner told" on its row in Episodes.
5. **Remove on request**, same day, no argument.
6. **Add it to "The fixes"** in the repository README, credited to the owner.

## Keywords

- One word, capital letters, easy to type on a phone: 3D, SKIT, REPO.
- Never reuse a keyword for a different guide. Each keyword maps to one Notion page, forever.
- Add each one to its row in Episodes before the episode goes out.

## Checklist for every episode

Before posting:
- [ ] Template chosen, Notion page duplicated from it, every [bracket] filled.
- [ ] Lina images added to every step, cover and icon in place.
- [ ] Files committed to `guides/<keyword>/` and the GitHub link on the page works.
- [ ] Featured project? License checked, credit blocks in place.
- [ ] Next keyword and reel link filled in the calls to action.
- [ ] Page shared to the web, "Allow editing", "Allow comments" and "Search engine indexing" checked as intended (editing always off).
- [ ] Meta comment-to-message automation set up with the keyword and the Notion link. Test it from a second account.
- [ ] Caption says what people get: "Comment [KEYWORD] and I'll send you [thing]."

After posting:
- [ ] Guide added to "The guides" in the repository README (and to "The fixes" for featured projects).
- [ ] Featured project owner told.
- [ ] Episode row updated and marked Posted.

## Episode log

Tracked in the Episodes database in Guide Studio (Notion): one row per episode, with its keyword, next keyword, links, and the checks above as checkboxes.
