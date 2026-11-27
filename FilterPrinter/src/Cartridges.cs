namespace FilterPrinterMod
{
    internal static class Cartridges
    {
        internal const string Tag = "FP_CARTRIDGE_TAG";
        internal const string TargetTag = "FP_CARTRIDGE_TARGET_TAG";
        internal const string FilterSizeTag = "FILTER_SIZE_TAG";
        internal const int Durability = Balance.CartridgeDurability;
        internal const long Value = Balance.CartridgeValue;

        internal static string ItemId(string target)
        {
            return "fp_cartridge_" + target;
        }

        internal static bool IsCartridge(GameItem item)
        {
            return item != null && item.IsTag(Tag);
        }

        internal static string TargetOf(GameItem item)
        {
            if (item == null)
            {
                return null;
            }
            TagState state = item.GetTagReadonly(TargetTag);
            return state == null ? null : state.GetString();
        }

        internal static GameItem Create(string target)
        {
            GameItem item = ItemDirectory.CreateEmptyItem(ItemId(target));
            item.SetSpriteAndShape("Items/items_amenities", "water_filter");
            bool plain = target == RetentionTargets.PlainId;
            if (plain)
            {
                item.name = Text.Get("cartridge.plain.name");
                item.shortDescription = Text.Get("cartridge.plain.desc");
                item.flavorText = Text.Get("cartridge.plain.flavor");
            }
            else
            {
                string targetName = RetentionTargets.DisplayName(target);
                item.name = Text.Get("cartridge.name", targetName);
                item.shortDescription = Text.Get("cartridge.desc", targetName);
                item.flavorText = Text.Get("cartridge.flavor");
            }
            item.SetGameItemType("HOUSEHOLD_GOOD");
            item.SetGameItemType("FILTER");
            item.SetGameItemType("WATER_PURIFICATION_SUPPLY");
            item.ModifyTag(FilterSizeTag, (TagState state) =>
            {
                state.Enable().SetInt(plain ? Balance.PlainFilterSize : Balance.CartridgeFilterSize);
            });
            item.EnableTag("WATER_FILTER");
            item.EnableTag(Tag);
            item.ModifyTag(TargetTag, (TagState state) =>
            {
                state.Enable().SetString(target);
            });
            DurabilityHelper.InitItemWithDurabilityPricingMode2(item, Durability, 0);
            item.SetValue(Value);
            AudioHelper.InitPlasticContainer(item);
            GeneralHelper.SetItemOwned(item);
            item.onLoaded = (GameItem loaded) =>
            {
                GeneralHelper.SetItemOwned(loaded);
            };
            item.ValidateShapeState();
            return item;
        }
    }
}
