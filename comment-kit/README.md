# Comment kit

Reaction memes with the cast (Lina, claude and chatgpt) for answering Instagram comments. Each reply comes as a looping GIF and a still PNG. All of them end with the @heyalmuri footer and the disclosure line.

![All replies](preview.png)

| Folder | What | Size |
|---|---|---|
| `gif/` | looping animations, 3 to 4.6 s | 540 × 540, 0.2 to 3.9 MB |
| `png/` | still of the last frame | 1080 × 1080 |
| `cast/` | the cast images the kit is drawn from | |

## Which one to use

| Reply | Use it when someone… | What happens |
|---|---|---|
| `claude-short-version` | leaves any nice comment | claude types "sorry. short version:" then "thank you 🫶", then "(page 1 of 4)" |
| `chatgpt-glazing` | compliments the episode | chatgpt rates the comment in a table (humor 10/10, aura infinite) and offers a pie chart |
| `cast-reacting` | posts anything, the all-rounder | each of the cast reacts in a speech bubble |
| `lina-check-dms` | comments the keyword | Lina at her laptop, a DM notification pops: "check your DMs", "lina sent it at 3am", plus the reminder to check message requests |
| `cast-dms` | comments the keyword | "us sliding into your DMs after you comment the keyword", then "(it's literally just the file)" |
| `lina-laughing` | makes a joke | "no bc lina actually laughed out loud at your comment", over her deadpan face: "(this is her laughing)" |
| `claude-funnier` | makes a joke | claude realizes the comment is funnier than his 4-page answer, zoom punch, "(writing page 5 to cope)" |
| `claude-absolutely-right` | makes a point | "you're absolutely right!" twice, then "(he has not opened your comment)" |
| `claude-apology` | spots a mistake | "i sincerely apologize for the confusion / here's the corrected version:", then "(it's the exact same version)" |
| `aura` | writes the best comment under the post | Lina glows lime while the counter climbs to +1000 aura |
| `number-one-fan` | is a regular or a big supporter | chatgpt bounces with the foam finger under confetti: "#1 commenter" |
| `lina-real` | posts something relatable | "real." slams onto the screen, "lina doesn't say that often" |
| `lina-fine` | writes something wholesome | "lina acting like your comment didn't make her emotional at 3am", then "she's fine (she is not fine)" |
| `pov-night-shift` | comments for the first time, or just followed | "pov: you followed and now you're on lina's night shift" |

## Getting them into Instagram

- **Comments.** Instagram's GIF button in comments only searches GIPHY, and you can't add a GIF from your camera roll there. To make the kit searchable, upload the `gif/` files to a GIPHY brand channel. GIPHY has to approve the channel first. Its application asks for at least 5 uploads, a branded avatar and a link to your own website domain (a social profile doesn't count). Tag every upload `almuri` and `heyalmuri`, so typing "almuri" in the comment GIF search lists the whole kit. Check GIPHY's current rules before you apply.
- **DMs and Stories.** Send the `png/` stills straight from your camera roll.

## Changing the words or adding a reply

Everything is drawn by `make_kit.py`. No image is edited by hand.

```sh
python3 make_kit.py                  # rebuild everything and preview.png
python3 make_kit.py aura lina-real   # rebuild only these
```

Each reply is one `r_*` function, listed in `REPLIES` at the bottom with its length in seconds. The words sit in that function, so a wording change is a one-line edit. There are three formats to build on: `chat` (a DM thread with claude or chatgpt), `caption_meme` (white caption on top, cast image below) and the cover-style cards (navy, a cut-out of the cast, a title with the red dot, a lime pill). The colours and fonts match `guides/make_cover.py`.

You need Python 3 with Pillow and numpy, ffmpeg, Inter and Noto Color Emoji. Font paths are in `FONTS`.

The images in `cast/` come from `guides/assets/`. The `.png` cut-outs were made from them with [rembg](https://github.com/danielgatis/rembg) (model `isnet-general-use`). Higher-resolution renders from the posts in `aka1127/almuri-media` would make sharper close-ups: drop them into `cast/` and point the replies at them.
