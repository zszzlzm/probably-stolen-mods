using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace ReductionFernMod
{
    /// <summary>
    /// Vanilla draws the plant growing inside a hydroponic machine by loading
    /// "&lt;HARVEST_ITEM_ID&gt;_p" from the vanilla atlas "Items/items_hydroponic_plant"
    /// (MachineHydroponic.getItemSpriteModifierForItemFunc). A mod plant has no entry in that
    /// atlas, so RenderHandler.LoadFromAtlas falls back to the 'unknown' dummy sprite and the
    /// machine shows a placeholder instead of the fern.
    ///
    /// We keep the vanilla delegate untouched and wrap it: when the vanilla atlas cannot supply
    /// the sprite, we look the same key up in the loaded mods' sprite packs (this mod ships
    /// restoring_fern_p.png under Textures/Items/). Vanilla plants are never affected because
    /// they resolve from the atlas before we get involved.
    /// </summary>
    internal static class HydroponicPlantArt
    {
        internal const string Atlas = "Items/items_hydroponic_plant";

        private static Harmony harmony;
        private static readonly Dictionary<string, Sprite> spriteCache = new Dictionary<string, Sprite>();
        private static readonly HashSet<string> loggedKeys = new HashSet<string>();

        internal static void Install()
        {
            if (harmony != null)
            {
                return;
            }
            try
            {
                var target = AccessTools.Method(typeof(MachineHydroponic), "Hydroponic", Type.EmptyTypes);
                if (target == null)
                {
                    ReductionFernMod.Log.Warning("Hydroponic() not found; the plant will render as 'unknown'.");
                    return;
                }
                Harmony instance = new Harmony(ReductionFernMod.ModId + ".plantart");
                instance.Patch(target, postfix: new HarmonyMethod(typeof(HydroponicPlantArt), "Postfix"));
                harmony = instance;
                ReductionFernMod.Log.Log("Hydroponic plant art hook installed");
            }
            catch (Exception e)
            {
                ReductionFernMod.Log.Error("Could not hook the hydroponic plant art: " + e);
            }
        }

        internal static void Uninstall()
        {
            if (harmony != null)
            {
                try
                {
                    harmony.UnpatchAll(harmony.Id);
                }
                catch (Exception e)
                {
                    ReductionFernMod.Log.Warning("Could not remove the hydroponic plant art hook: " + e.Message);
                }
                harmony = null;
            }
            ClearCache();
        }

        internal static void ClearCache()
        {
            spriteCache.Clear();
            loggedKeys.Clear();
        }

        // ReSharper disable once InconsistentNaming - Harmony injects __result by name.
        private static void Postfix(GameItem __result)
        {
            if (__result == null || __result.getItemSpriteModifierForItemFunc == null)
            {
                return;
            }
            Func<GameItem, List<ItemSpriteModifier>> original = __result.getItemSpriteModifierForItemFunc;
            __result.getItemSpriteModifierForItemFunc = (GameItem self) => Wrap(self, original);
        }

        private static List<ItemSpriteModifier> Wrap(GameItem self, Func<GameItem, List<ItemSpriteModifier>> original)
        {
            // Only take over when vanilla would fall back to the 'unknown' placeholder; otherwise the
            // vanilla delegate runs untouched. Calling vanilla first would log its "sprite not found"
            // warning on every redraw, so decide before delegating.
            if (TryModPlantSprite(self, out Sprite sprite))
            {
                return new List<ItemSpriteModifier>
                {
                    new ItemSpriteModifier(sprite, Vector2.zero, 0, false, 0, false, Color.white)
                };
            }
            return original == null ? null : original(self);
        }

        /// <summary>True when the machine shows a mod plant whose "_p" art is not in the vanilla atlas.</summary>
        private static bool TryModPlantSprite(GameItem machine, out Sprite sprite)
        {
            sprite = null;
            if (machine == null)
            {
                return false;
            }
            // Same condition vanilla uses: only a working machine draws a plant.
            if (MachineProgressHelper.GetMachineState(machine) != "STATE_WORKING")
            {
                return false;
            }
            GameSlotInventory slot = MachineHydroponic.GetInputSlot(machine);
            return TryPlantArt(slot == null ? null : slot.childItem, out sprite);
        }

        /// <summary>
        /// Resolves "&lt;harvestId&gt;_p" from a mod sprite pack for a seed whose art is not in the
        /// vanilla atlas. Shared with <see cref="SeedPreviewCompat"/>.
        /// </summary>
        internal static bool TryPlantArt(GameItem seed, out Sprite sprite)
        {
            sprite = null;
            if (seed == null)
            {
                return false;
            }
            string harvestId = HydroponicHelper.GetHarvestItemId(seed);
            if (string.IsNullOrEmpty(harvestId))
            {
                return false;
            }
            if (RenderHandler.TryLoadFromAtlas(Atlas, harvestId + "_p") != null)
            {
                // Vanilla plant: the game has real art and must keep using it.
                return false;
            }
            string key = harvestId + "_p";
            if (HydroponicHelper.IsPerennial(seed) && HydroponicHelper.IsRipening(seed)
                && FindModSprite(harvestId + "_p2") != null)
            {
                key = harvestId + "_p2";
            }
            sprite = FindModSprite(key);
            return sprite != null;
        }

        private static Sprite FindModSprite(string key)
        {
            if (spriteCache.TryGetValue(key, out Sprite cached))
            {
                return cached;
            }
            Sprite found = null;
            List<LoadedMod> mods = ModLoader.Mods;
            for (int i = 0; i < mods.Count; i++)
            {
                LoadedMod mod = mods[i];
                if (mod == null)
                {
                    continue;
                }
                if (mod.Sprites != null && mod.Sprites.TryGetValue(key, out Sprite sprite) && sprite != null)
                {
                    found = sprite;
                    break;
                }
            }
            spriteCache[key] = found;
            if (found != null)
            {
                if (loggedKeys.Add(key))
                {
                    ReductionFernMod.Log.Log("Using mod sprite '" + key + "' for the growing plant");
                }
            }
            else if (loggedKeys.Add(key))
            {
                ReductionFernMod.Log.Warning("No mod provides the plant sprite '" + key
                    + "'; the machine will show the vanilla 'unknown' placeholder.");
            }
            return found;
        }
    }
}
