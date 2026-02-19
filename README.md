# PVC+ Resource Pack

A custom resource pack for Minecraft 1.21.5+ that applies custom textures to PVC-specific items based on their display names (NBT data). That means if the name changes, this pack will need to be updated.

## Features

### Custom Items
| Base Item | Trigger Name | Internal Model |
|-----------|-------------|----------------|
| **Book** | "Playtime Certificate" | `playtime_cert` |
| **Book** | "T2 Playtime Certificate" | `playtime_cert_t2` |
| **Paper** | "Inactivity Ticket" | `part-cert` |
| **Amethyst Shard** | "Caddozzo" | `caddozzo` |
| **Diamond** | "50 Votes Certificate" | `vote_token` |

### Custom Blocks
- **Protection Block** (Coal Ore):
  - **Trigger**: "Standard Protection Block"
  - **Model Logic**: Uses `minecraft:block/cube_column` as the parent.
  - **Rendering**: Preserves the standard Coal Ore texture on the **Top/Bottom** (end) faces, while applying a custom texture to the **Side** faces.

## Installation

1. Download the final zip file.
2. Place the zip file in your Minecraft `resourcepacks` folder.
3. Enable the resource pack in Minecraft settings.

## File Structure

The pack follows a strict separation between vanilla logic overrides and custom assets.

pvc-plus/
├── pack.mcmeta
├── pack.png
└── assets/
    ├── pvc-plus/               <-- CUSTOM ASSETS
    │   ├── models/
    │   │   └── item/           <-- Item Models
    │   │       ├── playtime_cert.json
    │   │       ├── playtime_cert_t2.json
    │   │       ├── part-cert.json
    │   │       ├── caddozzo.json
    │   │       ├── vote_token.json
    │   │       └── protection_coal_ore.json
    │   └── textures/
    │       ├── item/
    │       └── block/
    └── minecraft/              <-- VANILLA LOGIC
        └── items/
            ├── book.json       <-- Checks for Certificates
            ├── paper.json      <-- Checks for Tickets
            ├── diamond.json    <-- Checks for Vote Tokens
            ├── amethyst_shard.json
            └── coal_ore.json   <-- Checks for Protection Block
