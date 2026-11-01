# Almuri: how to work in this repository

Almuri is a comedy show on Instagram (@heyalmuri) about Lina, a developer who works nights, and the AI tools she can't stand and can't stop using. The cast: **Lina** (3D, dark hair in a bun, black outfit, laptop and white kettle), **claude** (orange spiky sun with a scarf) and **chatgpt** (green box with a foam finger). They are parody characters. Every public thing we make carries: "made with ai, parody characters, not affiliated with any ai company".

This repository is the public library: free files, the privacy notice, and the guide system. Post images live in the separate public repository `aka1127/almuri-media` (`posts/<post id>/NN.jpg`).

## Rule 1: every piece of content gets a guide, automatically

Whenever Amine asks for content (an episode, reel, carousel, post, script or caption), do all of the steps below **without being asked**, in the same session. Don't stop at the caption.

1. **Pick the keyword.** One word, capitals, easy to type on a phone (LINE, MUG, REPO). Never reuse one: check the Episodes database and "The guides" in `README.md`.
2. **Write the content**: script or slides, plus the caption (format below).
3. **Pick the template** (see `guides/README.md`): *How we made it*, *Featured project* or *Quick list*. If the episode is a pure joke with nothing to offer, the guide is "how we made this episode" (the prompts and the steps).
4. **Make the cover**: `python3 guides/make_cover.py --title "<short title>" --pill "<what you get>" --out guides/assets/cover-<keyword>.jpg` (add `--art` with another image from `guides/assets/` to vary it). Look at the result before using it.
5. **Write the files**: `guides/<keyword lowercase>/prompts.txt` with every prompt from the guide, plus any other file the guide offers.
6. **Commit and push**, so the images and files have public URLs.
7. **Build the Notion guide page** under Lina's Guides (IDs below), by copying the structure and blocks of the model page, "How Lina finally got one line out of an AI". Fetch it first and match it: files box, "Lina says" columns on every step, prompts in code blocks, tip/warning callouts, calls to action, footer.
   - Images: for each image block, call the Notion `create-attachment` tool with `source_url` = `https://raw.githubusercontent.com/aka1127/almuri/<branch>/guides/assets/<file>.jpg`, and put its `file-upload://` source in the page. One attachment per image block, even when the image repeats. Use `main` as the branch once the file is on main, otherwise the branch you pushed.
   - Cover: the raw URL of the cover you made.
   - Don't upload through api.notion.com directly: cloud sessions can't reach it. `create-attachment` with `source_url` works.
8. **Link it everywhere**: add the guide to the "The guides" section of the Lina's Guides page and of `README.md` (for a featured project, also "The fixes"), and add a row to the Episodes database (Status "Guide drafted", Type, Keyword, Next keyword, Guide page, GitHub files).
9. **Chain the next keyword**: the 🎬 call to action points to another episode's keyword, usually the previous one, so readers go from guide to guide.
10. **Report back** with the caption, the Notion link, and what only Amine can do: set the Instagram comment-to-message automation (Meta's own feature only) with the keyword and the Notion link, and post.

Never post, schedule or publish anything yourself, and never change who can see a Notion page. Amine does that.

## Caption format

```
<hook: one short line, the joke of the episode>

<one or two lines of context in Lina's voice>

Comment <KEYWORD> and I'll send you <exactly what they get> 💬

made with ai, parody characters, not affiliated with any ai company
#<3 to 5 relevant hashtags>
```

The caption must say exactly what people get for the keyword. The message they receive is one message with the guide link, nothing else.

## Featured projects (someone else's repository)

Check the license before showing anything. Link to their repository, never re-host their code. Credit block (green callout) near the top and again at the end: owner, link, license, "Almuri is not affiliated with [owner]. All credit for [project] goes to them." Name the owner in the episode and the caption too. Add it to "The fixes" in `README.md`. Remind Amine to tell the owner, and remove it the same day if the owner asks.

## Brand rules for guide pages

- Title: "How Lina [did the thing]", "[Project]: the fix Lina found" or "Lina's [list]".
- Callouts: Lina = gray 💬, claude = orange 🟠, chatgpt = green 🟩, tip = blue 💡, warning = yellow ⚠️, credit = green 🙏, calls to action = purple (💌 email, 🎬 next keyword, 📱 follow), files box = gray 📁.
- Lina's lines: one or two sentences, tired and funny, then useful. Never mean to the reader.
- Images in `guides/assets/`: `lina-laptop`, `lina-standing`, `lina-mugs`, `claude`, `chatgpt`, plus the covers. New crops come from `aka1127/almuri-media` posts.
- Every page ends with the same three calls to action and the footer (copy them from the model page).

## Notion (workspace "Almuri HQ's Space", teamspace HQ)

| What | ID |
| --- | --- |
| Lina's Guides (public parent of every guide) | `40b0f7c4-4542-815a-9181-fa696cbc82bc` |
| Model guide: How Lina finally got one line out of an AI | `40b0f7c4-4542-817b-8163-f3c40f588972` |
| Template: How we made it | `40b0f7c4-4542-81b5-96e2-efcfdabcd184` |
| Template: Featured project | `40b0f7c4-4542-8114-a497-cc970c46805e` |
| Template: Quick list | `40b0f7c4-4542-81b2-b10d-fe3d9556b218` |
| Brand kit | `40b0f7c4-4542-811b-b9eb-e2c925fa28f6` |
| Playbook | `40b0f7c4-4542-8156-9279-e28f356b9796` |
| Guide Studio (private hub) | `40b0f7c4-4542-812a-8562-d3a3bb16f67e` |
| Episodes data source | `collection://e93a83bc-f01c-4547-8d7f-4176864eb4dc` |
| Email list data source | `collection://ccd8cfe0-e93e-42c6-8820-a3025afcb96d` |
| Email form view | `https://app.notion.com/p/f9d76be514a04dc6b6152850a16090a6?v=40b0f7c445428145a829000c6b8bb551` |

If the Notion tools aren't available in the session, write the full page in Notion-flavored Markdown to `guides/<keyword>/notion-page.md`, commit it, and tell Amine the page still has to be created.

## Privacy promises to keep (see PRIVACY.md)

- The keyword message is sent with Meta's own comment-to-message feature or by hand. Never suggest LinkDM, ManyChat or any other DM tool.
- The email list only collects for now. Never send to it, export it or add a sending tool without updating section 4 of `PRIVACY.md` first.
- Guides and files are always free with no signup. The email form is optional, never a gate.

## Git

Commit messages describe what changed and why, in plain words. Don't put model names in commits or files.
