<p align="center">
  <img src="media/showcase-loop.gif" alt="Frostbyte and Bolt animated showcase" width="720">
</p>

<h1 align="center">Frostbyte × Bolt</h1>

<p align="center">
  Two high-quality elemental companions for Codex: one cool-headed, one high-voltage.
</p>

<p align="center">
  <a href="https://ashyboy219.github.io/codex-elemental-pets/"><strong>Open the interactive showcase</strong></a>
  ·
  <a href="https://github.com/Ashyboy219/codex-elemental-pets/releases/latest/download/codex-elemental-pets-drag-and-drop.zip"><strong>Get the pet pack</strong></a>
  ·
  <a href="ULTRA_EVOLUTION_PROPOSAL.md"><strong>Read the Ultra evolved-forms proposal</strong></a>
</p>

## Meet the pets

| Frostbyte | Bolt |
| --- | --- |
| ![Frostbyte waving](media/frostbyte-waving.gif) | ![Bolt waving](media/bolt-waving.gif) |
| A cool-headed crystal companion for precise, patient work. | A bright, restless spark for rapid experiments and brave first passes. |

Their personalities are built into their silhouettes and motion. Frostbyte is balanced, faceted, and composed. Bolt is asymmetric, forward-leaning, and visibly impatient to move.

## Install

The official desktop path is the recommended method:

1. Download the [drag-and-drop pet pack](https://github.com/Ashyboy219/codex-elemental-pets/releases/latest/download/codex-elemental-pets-drag-and-drop.zip).
2. In Codex, open **Settings → Pets → Custom pets → Open folder**.
3. Copy the `frostbyte` and/or `bolt` folder from the downloaded pack into the folder Codex opened.
4. Return to **Settings → Pets**, choose **Refresh**, then select your new companion.

See OpenAI's [official Pets documentation](https://developers.openai.com/codex/pets) for the current desktop, web, and CLI behavior.

The [interactive showcase](https://ashyboy219.github.io/codex-elemental-pets/#install) also provides one-click Codex desktop install links backed by the hosted v2 spritesheets.

### Optional command-line installers

On macOS or Linux:

```bash
git clone https://github.com/Ashyboy219/codex-elemental-pets.git
cd codex-elemental-pets
./install.sh
```

On Windows PowerShell:

```powershell
git clone https://github.com/Ashyboy219/codex-elemental-pets.git
cd codex-elemental-pets
./install.ps1
```

If a newly copied pet is not visible, use **Refresh** in Pets before restarting Codex.

## Ultra evolved-forms concept

The showcase includes Normal and Ultra visual studies for both pets. The proposed Ultra form is a static evolved design shown through an immediate, non-animated swap—there is no transformation sequence or ambient effect. Ultra is an upstream concept, not current runtime behavior: Codex custom pets do not receive reasoning-effort events and currently load one atlas per pet. The [v3 manifest and event proposal](ULTRA_EVOLUTION_PROPOSAL.md) describes a backwards-compatible path for selecting alternate forms.

## Why these are more than character stickers

Each pet includes:

- a validated `1536 × 2288` transparent WebP atlas;
- 11 animation rows and 73 populated frames;
- idle, directional movement, waving, jumping, failure, waiting, active-work, and review states;
- 16 clockwise look directions with explicit cardinal, continuity, and blind-direction QA;
- `spriteVersionNumber: 2` packaging for the extended custom-pet format;
- a stable identity, palette, silhouette, face, and personality across every state.

## Media kit

- [Ultra evolved-form concept video — Reels, TikTok, and Shorts](media/evolution-showcase-vertical-1080x1920.mp4)
- [Ultra evolved-form concept video — X, LinkedIn, and YouTube](media/evolution-showcase-landscape-1920x1080.mp4)
- [Vertical video — Reels, TikTok, Shorts, and mobile feeds](media/showcase-vertical-1080x1920.mp4)
- [Landscape video — X, LinkedIn, YouTube, and presentations](media/showcase-landscape-1920x1080.mp4)
- [Square launch image](media/poster-square-1080x1080.png)
- [Landscape launch image](media/poster-landscape-1200x675.png)
- [Ready-to-post captions and launch checklist](social/POSTS.md)
- [Prepared OpenAI Developer Showcase submission](SHOWCASE_SUBMISSION.md)

## Build notes

The pets were designed and produced through Codex using grounded image generation plus deterministic atlas assembly and validation. The social media was rendered from the final approved spritesheets; it does not redraw or replace the pet artwork.

Rebuild the installable-pet media and the Ultra evolved-form concept cut with the bundled workspace Python runtime and FFmpeg:

```bash
python3 scripts/build_media.py
python3 scripts/build_evolution_media.py
```

## License and status

Code is MIT licensed. Pet art, animation assets, and promotional media are shared under CC BY 4.0; see [ASSET-LICENSE.md](ASSET-LICENSE.md).

This is an unofficial community project and is not affiliated with or endorsed by OpenAI. The custom pet format may evolve.
