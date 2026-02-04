# Minecraft Custom Items Resource Pack

A resource pack for Minecraft 1.21.5+ that replaces textures for specific server-side custom items based on their display names.

## Features

- **Playtime Certificate** - Custom texture for books named "Playtime Certificate"
- **50-vote Token** - Custom texture for diamonds named "50-vote token"
-

## Installation

1. Download or clone this repository
2. Place the folder in your Minecraft `resourcepacks` folder
3. Enable the resource pack in Minecraft settings

## Structure

pvc-plus/
├── pack.mcmeta
├── pack.png
└── assets/
    ├── pvc-plus/               <-- YOUR SAFE SPACE (Models & Textures)
    │   ├── models/
    │   │   ├── playtime_certificate.json
    │   │   └── vote_diamond.json
    │   └── textures/
    │       ├── certificate.png
    │       └── vote_diamond.png
    └── minecraft/              <-- VANILLA OVERRIDES (The Logic)
        └── items/
            ├── book.json       <-- Intercepts all books
            └── diamond.json    <-- Intercepts all diamonds

## Adding More Items

To add custom textures for additional items:

1. Add the ...

## Notes

- 1.21.5+
