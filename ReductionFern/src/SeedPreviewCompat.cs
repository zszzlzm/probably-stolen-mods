using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace ReductionFernMod
{
    /// <summary>
    /// Compatibility shim for the "Hydroponic Seed Preview" workshop mod (3835902034).
    ///
    /// That mod draws a translucent ghost of the plant over a hydroponic machine whose seed has
    /// not started growing yet. It only knows how to resolve plant art for two other mods
    /// (brewing_expansion / agri_expansion hard-codes) and for every other mod seed it falls back
    /// to the seed's own sprite, so our spores showed the spore packet instead of the fern.
    ///
    /// We do not take a hard reference to that mod: the target is found by reflection and patched
    /// only if present, so a rename, an update or the mod being uninstalled simply means no shim.
    /// </summary>
    internal static class SeedPreviewCompat
    {
        private const string PreviewModEntryType = "HydroponicSeedPreview.ModEntry";
        private const string PreviewMethodName = "AddPreview";

        private static Harmony harmony;
        private static bool installed;
        private static bool reportedError;
        private static bool reportedSuccess;

        internal static void Install()
        {
            if (installed)
            {
                return;
            }
            try
            {
                MethodInfo target = FindPreviewMethod();
                if (target == null)
                {
                    // The preview mod is not installed (or not loaded yet); try again later.
                    return;
                }
                Harmony instance = new Harmony(ReductionFernMod.ModId + ".seedpreviewcompat");
                instance.Patch(target, postfix: new HarmonyMethod(typeof(SeedPreviewCompat), "Postfix"));
                harmony = instance;
                installed = true;
                if (reportedSuccess)
                {
                    return;
                }
                reportedSuccess = true;
                ReductionFernMod.Log.Log("Hydroponic Seed Preview found; its ghost preview will show the mod plant art");
            }
            catch (Exception e)
            {
                if (reportedError)
                {
                    return;
                }
                reportedError = true;
                ReductionFernMod.Log.Warning("Could not hook the Hydroponic Seed Preview mod: " + e.Message);
            }
        }

        internal static void Uninstall()
        {
            if (harmony == null)
            {
                return;
            }
            try
            {
                harmony.UnpatchAll(harmony.Id);
            }
            catch (Exception e)
            {
                ReductionFernMod.Log.Warning("Could not remove the seed preview hook: " + e.Message);
            }
            harmony = null;
            installed = false;
        }

        private static MethodInfo FindPreviewMethod()
        {
            Assembly[] assemblies = AppDomain.CurrentDomain.GetAssemblies();
            for (int i = 0; i < assemblies.Length; i++)
            {
                Type type;
                try
                {
                    type = assemblies[i].GetType(PreviewModEntryType, false);
                }
                catch (Exception)
                {
                    continue;
                }
                if (type == null)
                {
                    continue;
                }
                return AccessTools.Method(type, PreviewMethodName);
            }
            return null;
        }

        // ReSharper disable once InconsistentNaming - Harmony injects __0/__1 by name.
        private static void Postfix(GameItem __0, ref List<ItemSpriteModifier> __1)
        {
            try
            {
                GameItem machine = __0;
                List<ItemSpriteModifier> result = __1;
                if (machine == null || result == null || result.Count == 0)
                {
                    return;
                }
                // While STATE_WORKING vanilla already draws the real plant, and the preview mod
                // leaves the list alone, so there is nothing to repair.
                if (MachineProgressHelper.GetMachineState(machine) == "STATE_WORKING")
                {
                    return;
                }
                GameSlotInventory slot = MachineHydroponic.GetInputSlot(machine);
                GameItem seed = slot == null ? null : slot.childItem;
                if (seed == null || !seed.IsTag("SEED_ITEM_TAG"))
                {
                    return;
                }
                if (!HydroponicPlantArt.TryPlantArt(seed, out Sprite plant))
                {
                    return;
                }
                // The preview mod's fallback ghost is exactly SeedSprite(seed) = the seed's own
                // mod sprite; compare against it so we only swap that one and nothing else.
                Sprite ghost = null;
                CustomUIManager ui = CustomUIManager.Instance;
                if (ui != null)
                {
                    ghost = ui.GetModSprite(seed.spriteAtlasPath, seed.spritePath, true);
                }
                for (int i = 0; i < result.Count; i++)
                {
                    ItemSpriteModifier modifier = result[i];
                    if (modifier.sprite == null || modifier.sprite == plant)
                    {
                        continue;
                    }
                    // Only swap the seed-shaped ghost, never someone else's overlay.
                    if (ghost != null && modifier.sprite != ghost)
                    {
                        continue;
                    }
                    result[i] = new ItemSpriteModifier(plant, modifier.position, modifier.orientation,
                        modifier.isFlipped, modifier.priority, modifier.haveMask, modifier.color);
                }
            }
            catch (Exception e)
            {
                if (reportedError)
                {
                    return;
                }
                reportedError = true;
                ReductionFernMod.Log.Warning("Seed preview compatibility failed: " + e.Message);
            }
        }
    }
}
