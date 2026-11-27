using System;
using HarmonyLib;

namespace FilterPrinterMod
{
    [HarmonyPatch(typeof(WaterHelper), "HandleFilter")]
    internal static class HandleFilterPatch
    {
        private static bool Prefix(string identifier, int amount, GameItem sourceContainer, GameItem filter, ref int __result)
        {
            if (!Cartridges.IsCartridge(filter))
            {
                return true;
            }
            // 普通水滤芯不按物质拦截：让原版 HandleFilter 用 FILTER_SIZE_TAG 按颗粒大小处理
            if (Cartridges.TargetOf(filter) == RetentionTargets.PlainId)
            {
                return true;
            }
            __result = Filter(identifier, amount, filter);
            return false;
        }

        private static int Filter(string liquidId, int amount, GameItem cartridge)
        {
            if (amount <= 0)
            {
                return 0;
            }
            string target = Cartridges.TargetOf(cartridge);
            if (!RetentionTargets.Blocks(target, liquidId))
            {
                return amount;
            }
            int durability = DurabilityHelper.GetRealDurability(cartridge);
            if (durability <= 0)
            {
                return amount;
            }
            Liquid liquid;
            if (!Liquid.LiquidDict.TryGetValue(liquidId, out liquid) || liquid == null)
            {
                return amount;
            }
            int perVolume = liquid.filterVolumeRemoved > 0 ? liquid.filterVolumeRemoved : 1000;
            int perDurability = liquid.filterDurabilityUsage > 0 ? liquid.filterDurabilityUsage : 1;
            int charges = durability / perDurability;
            if (charges <= 0)
            {
                return amount;
            }
            long capacity = (long)charges * perVolume;
            int removed = (int)Math.Min(amount, capacity);
            if (removed <= 0)
            {
                return amount;
            }
            int used = (int)Math.Ceiling(removed / (double)perVolume);
            if (used > charges)
            {
                used = charges;
            }
            DurabilityHelper.ChangeDurability(cartridge, -used * perDurability);
            return amount - removed;
        }
    }
}
