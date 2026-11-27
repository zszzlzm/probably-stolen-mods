namespace LuxuryNomoreInjectorMod
{
    internal static class Text
    {
        internal static string Get(string key, params object[] args)
        {
            return ModHelper.GetLocalized(LuxuryNomoreInjectorMod.ModId, key, args);
        }
    }
}
