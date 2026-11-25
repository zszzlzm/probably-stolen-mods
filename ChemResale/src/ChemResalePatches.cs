using HarmonyLib;

namespace ChemResale
{
    /// <summary>
    /// Reprices on every liquid change (WaterHelper.AddLiquid / pour / blend all funnel here).
    /// </summary>
    [HarmonyPatch(typeof(WaterFeatureHelper), nameof(WaterFeatureHelper.UpdateWaterFeature))]
    internal static class RepriceOnLiquidChange
    {
        private static void Postfix(GameItem gameItem)
        {
            ReagentPricing.Apply(gameItem);
        }
    }

    /// <summary>
    /// Covers bottles that already existed when the mod was installed: the sale check is the
    /// first place the game looks at them, so normalise right before vanilla decides.
    /// </summary>
    [HarmonyPatch(typeof(StoreClient), nameof(StoreClient.IsClientBuyingThisItem), typeof(GameItem), typeof(bool))]
    internal static class NormaliseBeforeSaleCheck
    {
        private static void Prefix(GameItem gameItem)
        {
            ReagentPricing.Apply(gameItem);
        }
    }

    /// <summary>
    /// Last line of defence for the price itself: whatever re-enables the water grading feature
    /// between a liquid change and the deal, the modifier is gone when the value is read.
    /// Cheap on purpose — this path runs for every tooltip and every price lookup.
    /// </summary>
    [HarmonyPatch(typeof(GameItem), nameof(GameItem.GetNegociatedValue))]
    internal static class NormaliseBeforeValueRead
    {
        private static void Prefix(GameItem __instance)
        {
            ReagentPricing.SilenceWaterGrading(__instance);
        }
    }
}
