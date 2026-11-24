using System.Reflection;
using HarmonyLib;

namespace GenerousBuyer
{
    /// <summary>
    /// Renames the rule in the UI without touching the game's localization tables.
    ///
    /// Every player-visible string in the game goes through LocHelper.Get(table, key, args),
    /// so a postfix there can swap three vanilla entries for our own mod strings (which respect
    /// the current language through ModHelper.GetLocalized):
    ///
    ///   UI      / ui_nego_tag_variety              "种类多样"        -> "慷慨"
    ///   UI      / ui_nego_no_variety               the old refusal   -> the new explanation
    ///   UI      / ui_nego_restrictions             "限制条件："      -> "特殊规则："
    ///   Mechanic/ item_feature_variety_buyer_bonus "多样化买家加成"  -> "慷慨买家加成"
    ///
    /// The item feature name is baked into the ItemFeature instance when the customer arrives,
    /// so features created before this mod loads would keep the old wording until the next visit.
    /// </summary>
    [HarmonyPatch]
    internal static class VarietyTextPatch
    {
        private static bool logged;

        private static MethodInfo Resolve()
        {
            return AccessTools.Method(
                typeof(LocHelper),
                "Get",
                new[] { typeof(string), typeof(string), typeof(object[]) });
        }

        [HarmonyPrepare]
        private static bool Prepare()
        {
            if (Resolve() == null)
            {
                GenerousBuyerMod.Log?.Warning("LocHelper.Get not found; the tag will keep the vanilla wording.");
                return false;
            }
            return true;
        }

        [HarmonyTargetMethod]
        private static MethodBase GetTargetMethod()
        {
            return Resolve();
        }

        // Harmony binds __0/__1 to the original arguments (table, key) and __result to the return value.
        private static void Postfix(string __0, string __1, ref string __result)
        {
            string modKey = ModKeyFor(__0, __1);
            if (modKey == null)
            {
                return;
            }
            string text = Text.Get(modKey);
            // ModHelper.GetLocalized returns the key itself when the entry is missing; never show that.
            if (string.IsNullOrEmpty(text) || text == modKey)
            {
                return;
            }
            __result = text;
            if (!logged)
            {
                logged = true;
                GenerousBuyerMod.Log?.Log("Localized strings applied (tag, tooltip, item feature)");
            }
        }

        private static string ModKeyFor(string table, string key)
        {
            if (table == "UI")
            {
                if (key == "ui_nego_tag_variety")
                {
                    return "tag.variety";
                }
                if (key == "ui_nego_no_variety")
                {
                    return "tag.variety.info";
                }
                // The tag row is headed "Restrictions:", which no longer fits a rule that is only a bonus.
                if (key == "ui_nego_restrictions")
                {
                    return "header.restrictions";
                }
            }
            else if (table == "Mechanic" && key == "item_feature_variety_buyer_bonus")
            {
                return "feature.variety_bonus";
            }
            return null;
        }
    }
}
