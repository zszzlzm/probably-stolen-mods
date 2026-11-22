using System;
using System.Reflection;
using HarmonyLib;

namespace LuxuryNomoreInjectorMod
{
    /// <summary>
    /// Marks the Nomore Injector (pink_alt_injector) as a luxury item and raises its base value.
    ///
    /// Every instance of the item is built by the vanilla factory MedsItemDirectory.Injector(...)
    /// (registered in MedsItemDirectory.InitDirectory, line "Add(\"pink_alt_injector\", ...)"), so a
    /// postfix there covers every creation path: directory spawns, chem-finisher output, store stock.
    /// The vanilla factory sets unitValue = 50 and type MEDICAL; we only add LUXURY_ITEM and reprice,
    /// which is exactly how the Synaprest Injector (black_injector) is set up in the base game
    /// (unitValue 350, MEDICAL + LUXURY_ITEM).
    /// </summary>
    public sealed class LuxuryNomoreInjectorMod : IMod
    {
        internal const string ModId = "harness.luxury-nomore-injector";
        internal const string ItemId = "pink_alt_injector";
        internal const long NewValue = 350L;
        internal const string LuxuryType = "LUXURY_ITEM";

        // The factory runs *before* Directory<T>.Create assigns identifier (Directory.cs:26-40),
        // so inside the postfix item.identifier is still null. The sprite is set by the factory
        // itself, so it is the reliable signature of this item.
        internal const string ItemSprite = "injector_pink_alt";

        internal static ModLog Log { get; private set; }

        private static Harmony harmony;
        private static bool loggedOnce;

        public void Init(ModManifest manifest)
        {
            Log = new ModLog(manifest);
            Install();
            Log.Log("Initialized");
        }

        public void OnEnable()
        {
            Install();
            Log.Log("Enabled. Patching " + ItemId + " -> " + LuxuryType + " / value " + NewValue);
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
            __result.SetGameItemType(LuxuryType);
            __result.SetValue(NewValue);
            if (!loggedOnce)
            {
                loggedOnce = true;
                Log.Log("Applied: " + ItemId + " is now " + LuxuryType + " with value " + NewValue);
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
