namespace PharmacyMod
{
    /// <summary>两件药品的构建函数，照着原版 dream_dust / fanta_pill 的结构写。</summary>
    internal static class Items
    {
        internal const string CalmAgentId = "calm_agent";
        internal const string PainkillerId = "painkiller_pill";

        /// <summary>澄心剂：一小瓶抗抑郁剂，结构同梦尘。</summary>
        internal static GameItem CreateCalmAgent()
        {
            GameItem item = ItemDirectory.CreateEmptyItem(CalmAgentId);
            item.SetSpriteAndShapeFromMod(PharmacyMod.ModId, CalmAgentId);
            item.name = Text.Get("item.calm_agent.name");
            item.shortDescription = Text.Get("item.calm_agent.desc");
            item.SetGameItemType("MEDICAL");
            item.SetGameItemType("NARCOTIC");
            item.SetGameItemType("SUBSTANCE");
            item.unitValue = Balance.CalmAgentValue;

            ConsumableHelper.InitNarcotic(item, Balance.CalmAgentNarcoticLevel);

            ChemicalHelper.InitChemItem(item, isBlendable: true, isSoluble: true);
            ChemFinisherRecipe.SetCompositionByPurity(
                item, Balance.MinPurity, Balance.MaxPurity, Balance.CalmAgentVolume, "dream_cap_extract");
            ChemicalProductHelper.InitChemicalProduct(item, "dream_cap_extract");
            // 故意不打 CHEMICAL_INTENT_TAG：原版 DailyFeedback 会把"意图=麻醉品、euphoria 只有 800（等级 1）"
            // 的商品一律判成"药效太弱"，扣声望并要求赔偿。这两件药效温和是设计，不该被投诉。
            // 该标签只被客户反馈逻辑读取（GetChemicalIntent 全库仅 4 处调用），去掉不影响效果/定价/成瘾/扫描。
            AudioHelper.InitGlassVial(item);
            item.ValidateShapeState();
            return item;
        }

        /// <summary>消痛片：一片强效镇痛片，结构同芬太尼药片。</summary>
        internal static GameItem CreatePainkillerPill()
        {
            GameItem item = ItemDirectory.CreateEmptyItem(PainkillerId);
            item.SetSpriteAndShapeFromMod(PharmacyMod.ModId, PainkillerId);
            item.name = Text.Get("item.painkiller_pill.name");
            item.shortDescription = Text.Get("item.painkiller_pill.desc");
            item.unitValue = Balance.PainkillerValue;

            MedicalHelper.InitPillItem(item);
            item.SetGameItemType("NARCOTIC");
            item.SetGameItemType("SUBSTANCE");

            ConsumableHelper.InitNarcotic(item, Balance.PainkillerNarcoticLevel);

            ChemicalHelper.InitChemItem(item, isBlendable: true, isSoluble: true);
            ChemFinisherRecipe.SetCompositionByPurity(
                item, Balance.MinPurity, Balance.MaxPurity, Balance.PainkillerVolume, "fanta");
            ChemicalProductHelper.InitChemicalProduct(item, "fanta");
            // 同上：不打 CHEMICAL_INTENT_TAG，避免"弱效麻醉品"投诉（0.08ml 芬太 = euphoria 800 = 等级 1）。
            item.ValidateShapeState();
            return item;
        }
    }
}
