# The Almuri guide system

Every episode gets a guide: a free, branded Notion page that Lina presents, with the thing people commented for in the first screen, the files here on GitHub, credit for anyone whose work we feature, and the same email signup and footer on every page.

It's automatic. Any Claude chat on this repository follows [`CLAUDE.md`](../CLAUDE.md): when asked for content, it also makes the keyword, caption, cover, files and the Notion guide.

Where things live:

- **Look and copy:** the Theme page in Notion (private workspace). The model guide, "How Lina finally got one line out of an AI", is the visual source of truth.
- **Covers:** `python3 guides/make_cover.py --title "..." --pill "..." --out guides/assets/cover-<keyword>.jpg --preview`, then check the three crops.
- **Images:** `guides/assets/` (faces for callout icons, 2:1 scenes, covers), cut from the posts in `aka1127/almuri-media`.
- **Files for each guide:** `guides/<keyword>/`.
