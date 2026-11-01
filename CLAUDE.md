# Almuri: how to work in this repository

Almuri is a comedy show on Instagram (@heyalmuri) about Lina, a developer who works nights, and the AI tools she can't stand and can't stop using. The cast: **Lina** (3D, dark hair in a bun, black outfit, laptop and white kettle), **claude** (orange spiky sun with a scarf) and **chatgpt** (green box with a foam finger). They are parody characters. Every public thing we make carries: "made with ai, parody characters, not affiliated with any ai company".

This repository is the public library: free files, the privacy notice, and the guide system. Post images live in the separate public repository `aka1127/almuri-media` (`posts/<post id>/NN.jpg`).

The studio's content and posting system lives in the private repository `aka1127/company-hq`. Its guide spec, `content/strategy/2026-11-01-guides.md`, is the source for the posting copy (caption ask, first comment, DM, the TikTok and X lines) and the voice rules: social lines lowercase with no full stops, the asks in the studio voice, at most one emoji per caption from the cast set (🟢 📌 🗂️ ☕ 🧶 📣). When a session has both repositories, captions are written there (`content/drafts/`) and the guide is built here.

The look and all the reusable copy (caption, pinned comment, DM, CTAs, form) are on the **Theme** page in Notion. The model guide is the visual source of truth. Fetch both before building a guide.

## Rule 1: every piece of content gets a guide, automatically

Whenever Amine asks for content (an episode, reel, carousel, post, script or caption), do all of the steps below **without being asked**, in the same session. Don't stop at the caption.

1. **Keyword.** One word, capitals, easy to type, not a word people use by accident in comments (COMMIT is safer than LINE). Never reuse one: check the Episodes database and the Lina's Guides list.
2. **Content.** Script or slides with the keyword on screen at the end (last 2–3 seconds of a reel, or the last slide). Instagram: the situation line first, then `Comment <KEYWORD> and we'll DM you <the exact thing>, free, nothing else`, the beats, `Or open Lina's Guides from the link in bio, no comment needed`, the disclosure, the tags; the next-move poll goes on the story sticker. TikTok and X keep their next-move lines; X gets the guide link in a studio reply, TikTok `free guide: lina's guides, link in bio` once its bio link is live. First comment and DM: the formats on the Theme page and in the company-hq guide spec.
3. **Template.** *How we made it*, *Featured project* or *Quick list* (IDs below). A pure joke with nothing to offer gets "how we made this episode".
4. **Cover.** `python3 guides/make_cover.py --title "<about 20 characters>" --pill "<what they get, a few words>" --out guides/assets/cover-<keyword>.jpg --preview`. Look at the preview (desktop, phone, link preview) and fix it until all three read well. Delete the preview file before committing.
5. **Files.** `guides/<keyword lowercase>/prompts.txt` with every prompt from the guide, plus any other file the guide offers.
6. **Commit and push**, then note the commit SHA. Images and covers are linked as `https://raw.githubusercontent.com/aka1127/almuri/<commit SHA>/guides/assets/<file>`. Never link to a branch name: branches get deleted.
7. **Build the page under Drafts** (private), copying the model page block for block. Fetch the model first. The rules:
   - No columns. Lina, claude and chatgpt speak in callouts whose icon is their face image (`face-lina.jpg`, `face-claude.jpg`, `face-chatgpt.jpg`, pinned raw URL as the callout `icon`).
   - The thing they commented for is in the first screen ("Copy this"). Code blocks hold one prompt or command, lines of about 30 characters, long commands split with a backslash.
   - At most 2 images, 2:1 scenes from `guides/assets/`. Images in the page body go through the Notion `create-attachment` tool with `source_url` = the pinned raw URL (one attachment per image block). The page cover and icon take the pinned raw URL directly. Don't upload through api.notion.com directly: cloud sessions can't reach it.
   - The ending is always: divider, "Want the next fix?", the email synced block reference, the 🎬 callout, the follow + footer synced block reference. Never retype the shared blocks.
   - Create the page with `preserve_internal_links: true` so links stay links.
   - Fetch it afterwards and check no `[` placeholder is left.
8. **🎬 next.** Point it only to a guide whose Episodes row is Posted, with a reel link and a tested automation. Otherwise: "More fixes from the show: Lina's Guides".
9. **Episodes row.** Status "Guide drafted", Type, Keyword, Guide page, GitHub files (blob link on main).
10. **Report back** with the caption, the pinned comment, the DM text, the draft link, and what only Amine can do: set Meta's comment-to-message automation (KEYWORD, Keyword, keyword → one DM with the notion.site link), post, pin the comment, and tell Claude "posted" with the reel link. Remind him the guide's GitHub links need this branch merged into main.

**When Amine says an episode is posted:** move its guide from Drafts to Lina's Guides, add it to "The guides" there (keyword · one line · page) and to `README.md` ("The fixes" too for a featured project), fill Reel, Post date and Public link in Episodes, set Status "Posted", and repoint the 🎬 of older guides to this newest one. That move is the only time Claude changes what is public, and only on his word.

Never post, schedule or publish anything yourself, and never change Notion sharing settings. Amine does that.

## Featured projects (someone else's repository)

Check the license before showing anything. Link to their repository, never re-host their code. Credit block (green 🙏 callout) near the top and again at the end: owner, link, license, "Almuri is not affiliated with [owner]. All credit for [project] goes to them." Name the owner in the episode and the caption too. Remind Amine to tell the owner, and remove it the same day if the owner asks.

## Notion (workspace "Almuri HQ's Space", teamspace HQ)

| What | ID |
| --- | --- |
| Lina's Guides (public parent; holds the shared blocks) | `40b0f7c4-4542-815a-9181-fa696cbc82bc` |
| Model guide: How Lina finally got one line out of an AI | `40b0f7c4-4542-8141-bb47-e1550ba0e707` |
| Drafts (private, new guides start here) | `40b0f7c4-4542-8179-8b7d-fd8cea513f00` |
| Theme (look and copy) | `40b0f7c4-4542-811b-b9eb-e2c925fa28f6` |
| Playbook (steps and checks) | `40b0f7c4-4542-8156-9279-e28f356b9796` |
| Template: How we made it | `40b0f7c4-4542-81b5-96e2-efcfdabcd184` |
| Template: Featured project | `40b0f7c4-4542-8114-a497-cc970c46805e` |
| Template: Quick list | `40b0f7c4-4542-81b2-b10d-fe3d9556b218` |
| Guide Studio (private hub) | `40b0f7c4-4542-812a-8562-d3a3bb16f67e` |
| Shared block: email signup | `https://app.notion.com/p/40b0f7c44542815a9181fa696cbc82bc#c3a7d90366cf48bd8c8b7061ac60e341` |
| Shared block: follow + footer | `https://app.notion.com/p/40b0f7c44542815a9181fa696cbc82bc#8c2210c80b414826b65324dc87ef7eda` |
| Episodes data source | `collection://e93a83bc-f01c-4547-8d7f-4176864eb4dc` |
| Email list data source | `collection://ccd8cfe0-e93e-42c6-8820-a3025afcb96d` |

A shared block is placed with `<synced-block-reference url="..."></synced-block-reference>` (left empty). To change the email link or the footer, edit the original on Lina's Guides once.

If the Notion tools aren't available in the session, write the full page in Notion-flavored Markdown to `guides/<keyword>/notion-page.md`, commit it, and tell Amine the page still has to be created.

## Privacy promises to keep (see PRIVACY.md)

- The keyword message is sent with Meta's own comment-to-message feature or by hand. Never suggest LinkDM, ManyChat or any other DM tool.
- The email list only collects for now. Never send to it, export it or add a sending tool without updating section 4 of `PRIVACY.md` first. Suggest choosing a tool when the second guide ships or the list reaches about 25 people.
- Guides and files are always free with no signup. The email form is optional, never a gate.
- No analytics, pixels or link shorteners on guide pages or in DMs.

## Git

Commit messages describe what changed and why, in plain words. Don't put model names in commits or files.
