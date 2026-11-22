namespace ReductionFernMod
{
    internal static class Text
    {
        internal static string Get(string key, params object[] args)
        {
            return ModHelper.GetLocalized(ReductionFernMod.ModId, key, args);
        }
    }
}
