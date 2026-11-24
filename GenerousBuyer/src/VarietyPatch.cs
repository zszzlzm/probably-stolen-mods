using HarmonyLib;

namespace GenerousBuyer
{
    /// <summary>
    /// Removes the "one of each kind" half of the Variety rule, keeping the +15% bonus.
    ///
    /// The restriction is enforced by StoreClient.IsItemInVarietyList: every consumer first
    /// checks isRequireVariety and then asks whether the item id is already in varietyTrackingList.
    /// There are exactly four call sites (StoreClient.IsClientRefusingItem, PlayerStore.CanSellThisItem,
    /// PlayerStore.PlacedItemForSelling, NegociationUIManager.GetRefusalLabel), and all of them mean
    /// "this customer already bought one of these, so no". Answering false therefore lifts the rule
    /// everywhere at once while leaving isRequireVariety (and thus the counter bonus) untouched.
    /// </summary>
    [HarmonyPatch(typeof(StoreClient), nameof(StoreClient.IsItemInVarietyList))]
    internal static class VarietyPatch
    {
        private static bool logged;

        private static void Postfix(ref bool __result)
        {
            __result = false;
            if (!logged)
            {
                logged = true;
                GenerousBuyerMod.Log?.Log("Variety restriction lifted: the same item can be sold twice");
            }
        }
    }
}
