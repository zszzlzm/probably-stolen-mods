namespace GenerousBuyer
{
    internal static class Text
    {
        internal static string Get(string key, params object[] args)
        {
            return ModHelper.GetLocalized(GenerousBuyerMod.ModId, key, args);
        }
    }
}
