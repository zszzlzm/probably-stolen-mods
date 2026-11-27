using System;
using System.Reflection;
using HarmonyLib;

namespace LuxuryNomoreInjectorMod
{
    /// <summary>
    /// Marks the Nomore Injector (pink_alt_injector) as a luxury item and reprices it.
    ///
    /// Every instance of the item is built by the vanilla factory MedsItemDirectory.Injector(...)
    /// (registered in MedsItemDirectory.InitDirectory, line "Add(\"pink_alt_injector\", ...)"), so a
    /// postfix there covers every creation path: directory spawns, chem-finisher output, store stock.
    /// The vanilla factory sets unitValue = 50 and type MEDICAL; we only add LUXURY_ITEM and multiply
    /// the value, which is how the Synaprest Injector (black_injector) is set up in the base game
    /// (unitValue 350, MEDICAL + LUXURY_ITEM).
    ///
    /// 1.0.x used a flat 350 (a 7x markup). Players asked for 2-4x and for a knob, so the markup is now
    /// the "value_multiplier" mod setting (1-10, default 4) applied to whatever the factory set.
    /// </summary>
    public sealed class LuxuryNomoreInjectorMod : IMod
    {
        internal const string ModId = "harness.luxury-nomore-injector";
        internal const string ItemId = "pink_alt_injector";
        internal const string LuxuryType = "LUXURY_ITEM";

        // The factory runs *before* Directory<T>.Create assigns identifier (Directory.cs:26-40),
        // so inside the postfix item.identifier is still null. The sprite is set by the factory
        // itself, so it is the reliable signature of this item.
        internal const string ItemSprite = "injector_pink_alt";

        internal static ModLog Log { get; private set; }

        private static ConfigEntry<int> valueMultiplier;
        private static Harmony harmony;
        private static bool loggedOnce;

        /// <summary>Markup over the vanilla base value, clamped to the range offered in the mod settings.</summary>
        internal static int ValueMultiplier
        {
            get
            {
                int value = valueMultiplier != null ? valueMultiplier.Value : Balance.DefaultMultiplier;
                if (value < Balance.MinMultiplier)
                {
                    return Balance.MinMultiplier;
                }
                if (value > Balance.MaxMultiplier)
                {
                    return Balance.MaxMultiplier;
                }
                return value;
            }
        }

        public void Init(ModManifest manifest)
        {
            Log = new ModLog(manifest);
            DefineSettings(manifest);
            Install();
            Log.Log("Initialized");
        }

        public void OnEnable()
        {
            Install();
            Log.Log("Enabled. Patching " + ItemId + " -> " + LuxuryType + " / markup x" + ValueMultiplier);
        }

        public void OnDisable()
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
                Log.Warning("Could not remove the patch: " + e.Message);
            }
            harmony = null;
            loggedOnce = false;
            Log.Log("Disabled");
        }

        private static void DefineSettings(ModManifest manifest)
        {
            try
            {
                valueMultiplier = ModHelper.GetConfig(manifest.ID).Define(
                    Balance.ConfigKey,
                    Balance.DefaultMultiplier,
                    Balance.ConfigSection,
                    () => Text.Get("config.multiplier", ValueMultiplier),
                    Balance.MinMultiplier,
                    Balance.MaxMultiplier,
                    tooltip: () => Text.Get("config.multiplier_help"));
            }
            catch (Exception e)
            {
                Log.Warning("Could not define the multiplier setting: " + e.Message);
            }
        }

        private static void Install()
        {
            if (harmony != null)
            {
                return;
            }
            try
            {
                MethodInfo target = AccessTools.Method(typeof(MedsItemDirectory), "Injector");
                if (target == null)
                {
                    Log.Warning("MedsItemDirectory.Injector not found; the item will keep its vanilla price.");
                    return;
                }
                Harmony instance = new Harmony(ModId + ".patch");
                instance.Patch(target, postfix: new HarmonyMethod(typeof(LuxuryNomoreInjectorMod), "Postfix"));
                harmony = instance;
                Log.Log("Patched MedsItemDirectory.Injector");
            }
            catch (Exception e)
            {
                Log.Error("Could not patch MedsItemDirectory.Injector: " + e);
            }
        }

        // Harmony injects __result by name; the method itself is a plain instance method.
        private static void Postfix(GameItem __result)
        {
            if (__result == null || !IsTarget(__result))
            {
                return;
            }
            // Read the value the factory just set (50 in 0.46D) and apply the configured markup, so a
            // vanilla rebalance or another mod's pricing still flows through instead of being overwritten.
            long baseValue = __result.unitValue > 0 ? __result.unitValue : Balance.FallbackBaseValue;
            long newValue = baseValue * ValueMultiplier;
            __result.SetGameItemType(LuxuryType);
            __result.SetValue(newValue);
            if (!loggedOnce)
            {
                loggedOnce = true;
                Log.Log("Applied: " + ItemId + " is now " + LuxuryType + " with value " + newValue
                        + " (" + baseValue + " x" + ValueMultiplier + ")");
            }
        }

        private static bool IsTarget(GameItem item)
        {
            if (string.Equals(item.identifier, ItemId, StringComparison.Ordinal))
            {
                return true;
            }
            return string.Equals(item.spritePath, ItemSprite, StringComparison.Ordinal);
        }
    }
}
