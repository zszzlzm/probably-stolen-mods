namespace PharmacyMod
{
    internal static class Text
    {
        internal static string Get(string key, params object[] args)
        {
            return ModHelper.GetLocalized(PharmacyMod.ModId, key, args);
        }
    }
}
