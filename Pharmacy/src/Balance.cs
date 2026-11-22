namespace PharmacyMod
{
    /// <summary>数值集中在这里，方便之后平衡。</summary>
    internal static class Balance
    {
        // 澄心剂：0.8 ml 梦帽菇萃取液（体积单位 1000 = 1 ml）
        internal const int CalmAgentVolume = 800;
        internal const long CalmAgentValue = 7L;
        internal const int CalmAgentNarcoticLevel = 1;

        // 消痛片：0.08 ml 芬太
        internal const int PainkillerVolume = 80;
        internal const long PainkillerValue = 2L;
        internal const int PainkillerNarcoticLevel = 2;

        // 与梦尘一致：要求容器里没有水一类的挥发性液体
        internal const bool RequireDry = true;

        // 街头成色：有效成分占 60%~80%
        internal const int MinPurity = 60;
        internal const int MaxPurity = 80;
    }
}
